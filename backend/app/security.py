"""Password hashing, session tokens and credential validation.

Passwords are hashed with scrypt from the standard library using OWASP's
recommended parameters (N=2^14, r=8, p=5). Parameters are stored in the hash
so they can be raised later without invalidating existing hashes.
"""

import base64
import hashlib
import hmac
import re
import secrets
from functools import lru_cache

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 5
SCRYPT_DKLEN = 64
SALT_BYTES = 16
# Upper bounds applied when verifying, so a tampered hash cannot trigger huge work.
MAX_SCRYPT_N = 2**20
MAX_SCRYPT_R = 32
MAX_SCRYPT_P = 16
SCRYPT_MAXMEM = 256 * 1024 * 1024
HASH_SCHEME = "scrypt"

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024
SESSION_TOKEN_BYTES = 32

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=SCRYPT_MAXMEM,
        dklen=SCRYPT_DKLEN,
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return "$".join(
        [
            HASH_SCHEME,
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against a stored hash. Malformed hashes never match."""
    try:
        scheme, n_str, r_str, p_str, salt_b64, digest_b64 = stored_hash.split("$")
        n, r, p = int(n_str), int(r_str), int(p_str)
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
    except ValueError:
        return False
    params_ok = 1 < n <= MAX_SCRYPT_N and 0 < r <= MAX_SCRYPT_R and 0 < p <= MAX_SCRYPT_P
    if scheme != HASH_SCHEME or not params_ok or len(password) > MAX_PASSWORD_LENGTH:
        return False
    try:
        actual = _scrypt(password, salt, n, r, p)
    except ValueError:  # e.g. n not a power of two, or memory limit exceeded
        return False
    return hmac.compare_digest(actual, expected)


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password(secrets.token_urlsafe(16))


def burn_verification_time(password: str) -> None:
    """Spend the same time as a real check, so unknown usernames are not revealed."""
    verify_password(password, _dummy_hash())


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_username(username: str) -> None:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 1-64 characters: letters, digits, '_', '.' or '-'")


def validate_new_password(password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters"
        )
