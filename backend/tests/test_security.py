import pytest

from app import security
from app.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    validate_new_password,
    validate_username,
    verify_password,
)


def test_hash_and_verify_roundtrip() -> None:
    stored = hash_password("a long enough password")
    assert stored.startswith("scrypt$16384$8$5$")
    assert verify_password("a long enough password", stored)
    assert not verify_password("wrong password!!", stored)


def test_hashes_are_salted() -> None:
    assert hash_password("same password 123") != hash_password("same password 123")


@pytest.mark.parametrize(
    "stored",
    [
        "",
        "not-a-hash",
        "bcrypt$16384$8$5$c2FsdA==$ZGlnZXN0",
        "scrypt$abc$8$5$c2FsdA==$ZGlnZXN0",
        "scrypt$16384$8$5$***$ZGlnZXN0",
        "scrypt$1$8$5$c2FsdA==$ZGlnZXN0",
        "scrypt$16384$0$5$c2FsdA==$ZGlnZXN0",
        "scrypt$16384$8$0$c2FsdA==$ZGlnZXN0",
        f"scrypt${2**30}$8$5$c2FsdA==$ZGlnZXN0",
        "scrypt$16384$64$5$c2FsdA==$ZGlnZXN0",
        "scrypt$16384$8$17$c2FsdA==$ZGlnZXN0",
        "scrypt$1000$8$1$c2FsdA==$ZGlnZXN0",  # n not a power of two
    ],
)
def test_malformed_or_unsafe_hashes_never_match(stored: str) -> None:
    assert not verify_password("anything at all", stored)


def test_oversized_password_is_rejected_without_hashing() -> None:
    stored = hash_password("a long enough password")
    assert not verify_password("x" * (security.MAX_PASSWORD_LENGTH + 1), stored)


def test_burn_verification_time_runs_a_real_check(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_verify(password: str, _stored: str) -> bool:
        calls.append(password)
        return False

    monkeypatch.setattr(security, "verify_password", fake_verify)
    security.burn_verification_time("guess")
    assert calls == ["guess"]


def test_session_tokens_are_random_and_hashed() -> None:
    first, second = generate_session_token(), generate_session_token()
    assert first != second
    assert len(first) >= 43
    assert hash_session_token(first) == hash_session_token(first)
    assert len(hash_session_token(first)) == 64
    assert hash_session_token(first) != first


@pytest.mark.parametrize("username", ["admin", "john.doe", "user_1", "a-b", "x" * 64])
def test_valid_usernames(username: str) -> None:
    validate_username(username)


@pytest.mark.parametrize("username", ["", "x" * 65, "bad user", "rm;-rf", "../etc", "ñandú"])
def test_invalid_usernames(username: str) -> None:
    with pytest.raises(ValueError):
        validate_username(username)


@pytest.mark.parametrize("password", ["short", "x" * 11, "x" * 1025])
def test_invalid_new_passwords(password: str) -> None:
    with pytest.raises(ValueError):
        validate_new_password(password)


def test_valid_new_password() -> None:
    validate_new_password("x" * 12)
