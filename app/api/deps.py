from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import AuthError, decode_subject
from app.services.rate_limit import RateLimitExceeded

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_subject(credentials.credentials, request.app.state.settings)
    except AuthError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def enforce_rate_limit(
    request: Request,
    user: Annotated[str, Depends(get_current_user)],
) -> str:
    try:
        await request.app.state.limiter.check(user)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return user
