"""Provider-neutral transactional email templates."""

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    text: str
    html: str


def _minimal_email(*, heading: str, action: str, confirmation_url: str, logo_url: str) -> str:
    """Render the shared, email-client-safe Raffael canvas."""
    safe_url = escape(confirmation_url, quote=True)
    safe_logo = escape(logo_url, quote=True)
    return f"""<!doctype html>
<html lang="en">
<body style="margin:0;background:#020406;color:#f3f5f6;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#020406;">
    <tr>
      <td align="center" style="padding:72px 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:420px;">
          <tr>
            <td align="center" style="padding-bottom:64px;">
              <img src="{safe_logo}" alt="raffael" width="120" style="display:block;width:120px;max-width:120px;height:auto;border:0;">
            </td>
          </tr>
          <tr>
            <td align="center">
              <h1 style="margin:0 0 36px;font-size:28px;line-height:1.2;font-weight:400;letter-spacing:-0.7px;color:#f3f5f6;">{heading}</h1>
              <a href="{safe_url}" style="display:inline-block;color:#f3f5f6;text-decoration:none;font-size:14px;line-height:1.2;border-bottom:1px solid #f3f5f6;padding:0 0 5px;">{action}</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def confirmation_email(*, recipient: str, confirmation_url: str, logo_url: str) -> EmailMessage:
    """Build the short-lived account confirmation message."""
    return EmailMessage(
        subject="confirm your raffael account",
        text=f"verify email:\n{confirmation_url}\n",
        html=_minimal_email(
            heading="verify email",
            action="verify",
            confirmation_url=confirmation_url,
            logo_url=logo_url,
        ),
    )


def newsletter_confirmation_email(*, recipient: str, confirmation_url: str, logo_url: str) -> EmailMessage:
    """Build the separate newsletter double-opt-in message."""
    return EmailMessage(
        subject="confirm your raffael newsletter subscription",
        text=f"confirm subscription:\n{confirmation_url}\n",
        html=_minimal_email(
            heading="join the newsletter",
            action="confirm",
            confirmation_url=confirmation_url,
            logo_url=logo_url,
        ),
    )


def password_reset_email(*, recipient: str, reset_url: str, logo_url: str) -> EmailMessage:
    return EmailMessage(
        subject="reset your raffael password",
        text=f"reset password:\n{reset_url}\n",
        html=_minimal_email(
            heading="reset password",
            action="reset",
            confirmation_url=reset_url,
            logo_url=logo_url,
        ),
    )
