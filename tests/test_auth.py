from datetime import datetime, timezone

import pytest

from raffael.auth import (
    hash_password,
    new_session_token,
    normalize_email,
    session_digest,
    session_expiry,
    verify_password,
)


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
