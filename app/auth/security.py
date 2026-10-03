import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import jwt

from app.config import Settings


class AuthError(Exception):
    """Raised when a token is missing, expired, or signed with the wrong secret."""


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    user_ok = hmac.compare_digest(_digest(username), _digest(settings.demo_username))
    password_ok = hmac.compare_digest(_digest(password), _digest(settings.demo_password))
    return user_ok and password_ok


def create_access_token(subject: str, settings: Settings) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_subject(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid token") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthError("Invalid token subject")
    return subject
