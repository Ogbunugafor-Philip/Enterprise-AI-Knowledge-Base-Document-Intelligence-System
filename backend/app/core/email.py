import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings


def _build_html_email(title: str, body: str, action_text: str | None = None) -> str:
    action_html = (
        f"<div style='margin-top:24px;font-size:24px;font-weight:700;letter-spacing:4px'>{action_text}</div>"
        if action_text
        else ""
    )
    return f"""
    <html>
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 0;">
          <tr>
            <td align="center">
              <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:32px;">
                <tr><td style="font-size:20px;font-weight:700;">Ent_RAG</td></tr>
                <tr><td style="padding-top:24px;font-size:18px;font-weight:700;">{title}</td></tr>
                <tr><td style="padding-top:12px;font-size:14px;line-height:22px;color:#475569;">{body}</td></tr>
                <tr><td>{action_html}</td></tr>
                <tr><td style="padding-top:28px;font-size:12px;line-height:18px;color:#64748b;">If you did not request this message, contact your organization administrator.</td></tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def _send_email_sync(to_email: str, subject: str, html_body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_email(to_email: str, subject: str, html_body: str) -> None:
    await asyncio.to_thread(_send_email_sync, to_email, subject, html_body)


async def send_otp_verification_email(to_email: str, otp_code: str) -> None:
    html = _build_html_email(
        "Verify your account",
        "Use this one-time code to complete your Ent_RAG account verification. The code expires in 10 minutes.",
        otp_code,
    )
    await send_email(to_email, "Ent_RAG account verification code", html)


async def send_temporary_password_email(to_email: str, temporary_password: str) -> None:
    html = _build_html_email(
        "Temporary password issued",
        "A temporary password has been generated for your account. Sign in and change it immediately.",
        temporary_password,
    )
    await send_email(to_email, "Ent_RAG temporary password", html)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    html = _build_html_email(
        "Password reset requested",
        "Use this secure reset token to set a new password. The token expires in 10 minutes.",
        reset_token,
    )
    await send_email(to_email, "Ent_RAG password reset", html)


async def send_account_locked_email(to_email: str) -> None:
    html = _build_html_email(
        "Account locked",
        "Your account was locked after multiple failed login attempts. Try again after 30 minutes or contact your administrator.",
    )
    await send_email(to_email, "Ent_RAG account locked", html)
