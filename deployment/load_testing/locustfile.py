"""
Locust load testing for Ent_RAG at https://docintel.space

Run commands:
  Baseline test:  locust --host=https://docintel.space -u 10  -r 2  --run-time 5m  --headless
  Stress test:    locust --host=https://docintel.space -u 50  -r 5  --run-time 10m --headless
  Peak test:      locust --host=https://docintel.space -u 100 -r 10 --run-time 5m  --headless
"""

import random

from locust import HttpUser, between, task


SAMPLE_QUESTIONS = [
    "What is our leave policy?",
    "How do I submit an expense report?",
    "What are the IT security guidelines?",
    "How do I request time off?",
    "What is the onboarding process for new employees?",
    "Where can I find the employee handbook?",
    "What are the company values?",
    "How do I access the VPN?",
]


class HealthCheckUser(HttpUser):
    wait_time = between(1, 3)
    weight = 1

    @task
    def check_health(self):
        self.client.get("/health", name="GET /health")


class AuthenticatedUser(HttpUser):
    wait_time = between(2, 5)
    weight = 5

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@docintel.space", "password": "TestUser123!"},
            name="POST /api/v1/auth/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token", "")
        else:
            self.token = ""

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(40)
    def ask_question(self):
        self.client.post(
            "/api/v1/chat/ask",
            json={
                "question": random.choice(SAMPLE_QUESTIONS),
                "session_id": None,
            },
            headers=self._auth_headers(),
            name="POST /api/v1/chat/ask",
        )

    @task(20)
    def get_sessions(self):
        self.client.get(
            "/api/v1/chat/sessions",
            headers=self._auth_headers(),
            name="GET /api/v1/chat/sessions",
        )

    @task(15)
    def get_profile(self):
        self.client.get(
            "/api/v1/users/me",
            headers=self._auth_headers(),
            name="GET /api/v1/users/me",
        )

    @task(10)
    def search_conversations(self):
        self.client.get(
            "/api/v1/chat/search?query=policy",
            headers=self._auth_headers(),
            name="GET /api/v1/chat/search",
        )

    @task(15)
    def get_sample_questions(self):
        self.client.get(
            "/api/v1/chat/sample-questions",
            headers=self._auth_headers(),
            name="GET /api/v1/chat/sample-questions",
        )


class AdminUser(HttpUser):
    wait_time = between(3, 7)
    weight = 2

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@docintel.space", "password": "Admin123!"},
            name="POST /api/v1/auth/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token", "")
        else:
            self.token = ""

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(30)
    def get_documents(self):
        self.client.get(
            "/api/v1/admin/documents",
            headers=self._auth_headers(),
            name="GET /api/v1/admin/documents",
        )

    @task(30)
    def get_dashboard_stats(self):
        self.client.get(
            "/api/v1/admin/dashboard/stats",
            headers=self._auth_headers(),
            name="GET /api/v1/admin/dashboard/stats",
        )

    @task(40)
    def get_approval_queue(self):
        self.client.get(
            "/api/v1/admin/approvals/queue",
            headers=self._auth_headers(),
            name="GET /api/v1/admin/approvals/queue",
        )
