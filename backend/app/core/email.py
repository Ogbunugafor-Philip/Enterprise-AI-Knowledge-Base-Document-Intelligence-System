import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings


def _build_html_email(
    title: str,
    body: str,
    action_text: str | None = None,
    action_url: str | None = None,
) -> str:
    if action_url and action_text:
        action_html = (
            f"<div style='margin-top:24px;'>"
            f"<a href='{action_url}' style='display:inline-block;background:#2563eb;color:#ffffff;"
            f"text-decoration:none;padding:12px 28px;border-radius:6px;font-size:14px;"
            f"font-weight:600;'>{action_text}</a>"
            f"<p style='margin-top:16px;font-size:12px;color:#94a3b8;word-break:break-all;'>"
            f"Or copy this link: {action_url}</p>"
            f"</div>"
        )
    elif action_text:
        action_html = (
            f"<div style='margin-top:24px;font-size:24px;font-weight:700;letter-spacing:4px'>{action_text}</div>"
        )
    else:
        action_html = ""
    return f"""
    <html>
      <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 0;">
          <tr>
            <td align="center">
              <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:32px;">
                <tr><td style="font-size:20px;font-weight:700;color:#2563eb;">DocIntel</td></tr>
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
        "Verify your DocIntel account",
        "Use this one-time code to complete your account verification. The code expires in 10 minutes.",
        otp_code,
    )
    await send_email(to_email, "DocIntel — account verification code", html)


async def send_temporary_password_email(to_email: str, temporary_password: str) -> None:
    html = _build_html_email(
        "Your DocIntel temporary password",
        "A temporary password has been generated for your account. Sign in and change it immediately.",
        temporary_password,
    )
    await send_email(to_email, "DocIntel — temporary password", html)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html = _build_html_email(
        "Reset your DocIntel password",
        "Click the button below to set a new password. This link expires in 30 minutes and can only be used once.",
        "Reset Password",
        reset_url,
    )
    await send_email(to_email, "DocIntel — password reset link", html)


async def send_account_locked_email(to_email: str) -> None:
    html = _build_html_email(
        "Account locked",
        "Your account was locked after multiple failed login attempts. Try again after 30 minutes or contact your administrator.",
    )
    await send_email(to_email, "Ent_RAG account locked", html)
