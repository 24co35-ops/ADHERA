import logging
from typing import Optional

import httpx

from app.config import settings
from app.services.audit import log_audit_action

logger = logging.getLogger("adhera.email")

RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "Adhera <noreply@adhera.app>"


async def send_resend_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Sends a transactional email via Resend API using httpx.
    Returns True if sent successfully, False otherwise.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Email to %s skipped: %s", to, subject)
        return False

    payload = {
        "from": SENDER_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(RESEND_API_URL, json=payload, headers=headers)
            if response.status_code in (200, 201):
                logger.info("Email successfully dispatched to %s via Resend", to)
                log_audit_action("EMAIL_SENT", user_id, {"to": to, "subject": subject})
                return True
            else:
                logger.error(
                    "Resend API error sending to %s: HTTP %s - %s",
                    to, response.status_code, response.text
                )
                log_audit_action("EMAIL_FAILED", user_id, {"to": to, "status": response.status_code, "error": response.text})
                return False
    except Exception as e:
        logger.error("Exception occurred while sending email via Resend to %s: %s", to, str(e))
        log_audit_action("EMAIL_FAILED", user_id, {"to": to, "error": str(e)})
        return False


def get_confirmation_email_template(confirmation_url: str) -> str:
    """
    Returns dark-themed HTML email template for email verification.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Confirm Your Adhera Account</title>
</head>
<body style="margin: 0; padding: 0; background-color: #111318; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #111318; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="560px" border="0" cellspacing="0" cellpadding="0" style="max-width: 560px; background-color: #181b22; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 24px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.06);">
              <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; background: linear-gradient(135deg, #0096a4 0%, #00dbe7 100%); border-radius: 12px; margin-bottom: 12px; font-weight: 900; font-size: 20px; color: #111318;">
                A
              </div>
              <h1 style="margin: 0; font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">ADHERA</h1>
              <p style="margin: 4px 0 0; font-size: 13px; color: #94a3b8;">Smart Medication Adherence Ecosystem</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding: 32px;">
              <h2 style="margin: 0 0 16px; font-size: 18px; font-weight: 700; color: #ffffff;">Confirm Your Email Address</h2>
              <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #cbd5e1;">
                Thank you for creating an account with Adhera. To activate your account and start receiving medication reminders and tracking adherence, please verify your email address.
              </p>
              <!-- Button -->
              <div style="text-align: center; margin: 32px 0;">
                <a href="{confirmation_url}" target="_blank" style="display: inline-block; background-color: #00dbe7; color: #111318; font-weight: 700; font-size: 14px; text-decoration: none; padding: 14px 32px; border-radius: 12px; box-shadow: 0 0 15px rgba(0, 219, 231, 0.3);">
                  Confirm Email Address
                </a>
              </div>
              <p style="margin: 24px 0 0; font-size: 12px; line-height: 1.5; color: #64748b; text-align: center;">
                ⏱️ This confirmation link will expire in <strong>30 minutes</strong>.
              </p>
              <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; line-height: 1.4; color: #64748b;">
                <p style="margin: 0;">If the button above does not work, copy and paste this link into your browser:</p>
                <p style="margin: 6px 0 0; word-break: break-all; color: #00dbe7;">{confirmation_url}</p>
              </div>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background-color: #14171d; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06);">
              If you didn't create an account with Adhera, you can safely ignore this email.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_confirmation_email(to_email: str, token: str, user_id: Optional[str] = None) -> bool:
    """
    Generates and sends the email verification link to a user.
    """
    confirmation_url = f"{settings.FRONTEND_URL}/auth/confirm?token={token}"
    subject = "Confirm your Adhera account"
    html = get_confirmation_email_template(confirmation_url)
    text = f"Welcome to Adhera!\n\nPlease confirm your email address by opening the following link:\n{confirmation_url}\n\nThis link expires in 30 minutes."
    return await send_resend_email(to=to_email, subject=subject, html=html, text=text, user_id=user_id)
