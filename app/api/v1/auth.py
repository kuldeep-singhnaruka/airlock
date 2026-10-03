from fastapi import APIRouter, HTTPException, Request

from app.auth.security import create_access_token, verify_credentials
from app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest, request: Request) -> TokenResponse:
    settings = request.app.state.settings
    if not verify_credentials(body.username, body.password, settings):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(body.username, settings)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)
