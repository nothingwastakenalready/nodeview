from raffael.email_templates import confirmation_email, newsletter_confirmation_email


def test_confirmation_email_has_text_and_html_variants():
    message = confirmation_email(
        recipient="user@example.com",
        confirmation_url="https://example.com/confirm?token=abc&next=/",
        logo_url="https://example.com/logo.png",
    )

    assert message.subject == "confirm your raffael account"
    assert "https://example.com/confirm?token=abc&next=/" in message.text
    assert "&amp;next=/" in message.html
    assert ">verify<" in message.html
    assert "user@example.com" not in message.html
    assert "local infrastructure" not in message.html


def test_confirmation_email_escapes_html_values():
    message = confirmation_email(
        recipient="<user>@example.com",
        confirmation_url="https://example.com/?q=\"unsafe\"",
        logo_url="https://example.com/logo?a=\"x\"",
    )

    assert "&quot;unsafe&quot;" in message.html


def test_newsletter_email_uses_the_same_minimal_canvas():
    message = newsletter_confirmation_email(
        recipient="user@example.com",
        confirmation_url="https://example.com/newsletter?token=abc",
        logo_url="https://example.com/logo.png",
    )

    assert message.subject == "confirm your raffael newsletter subscription"
    assert "join the newsletter" in message.html
    assert ">confirm<" in message.html
    assert "user@example.com" not in message.html
