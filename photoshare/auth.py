"""PIN and session helpers for optional link protection."""

from __future__ import annotations

import hashlib
import hmac
import secrets

AUTH_COOKIE = "photoshare_auth"


def generate_pin() -> str:
    """Default passphrase-style PIN (8 chars, URL-safe)."""
    return secrets.token_urlsafe(6)[:8]


def hash_pin(pin: str) -> str:
    salt = b"photoshare-v1"
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 120_000)
    return digest.hex()


def verify_pin(pin: str, pin_hash: str) -> bool:
    try:
        return hmac.compare_digest(hash_pin(pin), pin_hash)
    except (TypeError, ValueError):
        return False


def make_auth_token(session_secret: str) -> str:
    return hmac.new(
        session_secret.encode("utf-8"),
        b"photoshare-granted",
        hashlib.sha256,
    ).hexdigest()


def verify_auth_token(session_secret: str, token: str | None) -> bool:
    if not token:
        return False
    try:
        return hmac.compare_digest(make_auth_token(session_secret), token)
    except (TypeError, ValueError):
        return False


def parse_cookie(header: str | None, name: str) -> str | None:
    if not header:
        return None
    prefix = f"{name}="
    for part in header.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix) :]
    return None
