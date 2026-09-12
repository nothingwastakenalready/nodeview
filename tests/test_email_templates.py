from raffael.email_templates import confirmation_email


def test_confirmation_email_has_text_and_html_variants():
    message = confirmation_email(
        recipient="user@example.com",
        confirmation_url="https://example.com/confirm?token=abc&next=/",
        logo_url="https://example.com/logo.png",
    )

    assert message.subject == "confirm your raffael account"
    assert "https://example.com/confirm?token=abc&next=/" in message.text
    assert "&amp;next=/" in message.html
    assert "confirm account" in message.html


def test_confirmation_email_escapes_html_values():
    message = confirmation_email(
        recipient="<user>@example.com",
        confirmation_url="https://example.com/?q=\"unsafe\"",
        logo_url="https://example.com/logo?a=\"x\"",
    )

    assert "&lt;user&gt;" in message.html
    assert "&quot;unsafe&quot;" in message.html
