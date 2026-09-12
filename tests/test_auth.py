from datetime import datetime, timezone

import pytest

from raffael.auth import (
    AuthStore,
    hash_password,
    new_session_token,
    normalize_email,
    session_digest,
    session_expiry,
    verify_password,
)


def test_email_and_newsletter_tokens_are_single_use(tmp_path):
    store = AuthStore(f"sqlite:///{tmp_path / 'auth.db'}")
    store.initialize()
    user = store.register("owner@example.com", "a sufficiently long password")

    email_token = store.issue_token(user.id, "email_verification")
    assert store.confirm_email(email_token) is True
    assert store.confirm_email(email_token) is False

    newsletter_token = store.start_newsletter(user.id, "i want the raffael newsletter")
    assert store.confirm_newsletter(newsletter_token) is True
    assert store.confirm_newsletter(newsletter_token) is False
    store.close()


def test_password_reset_updates_password_and_revokes_sessions(tmp_path):
    store = AuthStore(f"sqlite:///{tmp_path / 'reset.db'}")
    store.initialize()
    user = store.register("owner@example.com", "a sufficiently long password")
    store.create_session(user.id)
    issued = store.request_password_reset("OWNER@example.com")
    assert issued is not None
    _, token = issued
    assert store.reset_password(token, "a new sufficiently long password") is True
    assert store.authenticate("owner@example.com", "a new sufficiently long password") is not None
    assert store.authenticate("owner@example.com", "a sufficiently long password") is None
    assert store.reset_password(token, "another sufficiently long password") is False
    store.close()


def test_normalize_email_is_stable():
    assert normalize_email("  User@Example.COM ") == "user@example.com"


def test_passwords_are_argon2id_and_verify():
    hashed = hash_password("a sufficiently long password")
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, "a sufficiently long password")
    assert not verify_password(hashed, "wrong password")


def test_short_passwords_are_rejected():
    with pytest.raises(ValueError):
        hash_password("too short")


def test_session_tokens_are_opaque_and_digestable():
    token = new_session_token()
    assert len(token) >= 40
    assert token != new_session_token()
    assert session_digest(token) != token


def test_session_expiry_is_timezone_aware():
    now = datetime(2026, 9, 12, tzinfo=timezone.utc)
    assert (session_expiry(now) - now).days == 7
