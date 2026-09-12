"""Email templates kept independent from the eventual delivery provider."""

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    text: str
    html: str


def confirmation_email(*, recipient: str, confirmation_url: str, logo_url: str) -> EmailMessage:
    """Build the account-confirmation email without sending it.

    URLs are escaped for HTML; the caller remains responsible for creating a
    short-lived, single-use confirmation token before passing the URL here.
    """
    safe_recipient = escape(recipient)
    safe_url = escape(confirmation_url, quote=True)
    safe_logo = escape(logo_url, quote=True)
    subject = "confirm your raffael account"
    text = (
        f"hello {recipient},\n\n"
        "confirm your raffael account with this link:\n"
        f"{confirmation_url}\n\n"
        "if you did not create this account, you can ignore this email.\n"
    )
    html = f"""<!doctype html>
<html lang="en"><body style="margin:0;background:#020406;color:#eef2f3;font-family:Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#020406;">
    <tr><td align="center" style="padding:56px 20px;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;">
        <tr><td align="center" style="padding-bottom:48px;"><img src="{safe_logo}" alt="raffael" width="88" style="display:block;max-width:88px;height:auto;"></td></tr>
        <tr><td style="padding:0 4px;">
          <p style="margin:0 0 24px;color:#8fa1ad;font-size:11px;letter-spacing:2px;text-transform:uppercase;">raffael / account</p>
          <h1 style="margin:0 0 30px;font-size:32px;font-weight:400;letter-spacing:-1px;">confirm your account</h1>
          <p style="margin:0 0 28px;color:#c7d0d5;font-size:15px;line-height:1.7;">hello {safe_recipient}, confirm your account to continue.</p>
          <a href="{safe_url}" style="display:inline-block;padding:14px 22px;background:#eef2f3;color:#020406;text-decoration:none;font-size:12px;letter-spacing:1px;text-transform:uppercase;">confirm account</a>
          <p style="margin:42px 0 0;color:#71818d;font-size:12px;line-height:1.6;">if you did not create this account, you can ignore this email.</p>
        </td></tr>
        <tr><td style="padding-top:56px;color:#52616b;font-size:10px;letter-spacing:1px;">raffael · local infrastructure</td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    return EmailMessage(subject=subject, text=text, html=html)
