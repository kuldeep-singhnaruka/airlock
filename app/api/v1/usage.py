from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.schemas.usage import UsageResponse

router = APIRouter(tags=["usage"])


@router.get("/usage", response_model=UsageResponse)
async def my_usage(
    request: Request,
    user: Annotated[str, Depends(get_current_user)],
) -> UsageResponse:
    snapshot = await request.app.state.usage.snapshot(user)
    return UsageResponse(
        username=user,
        requests=snapshot.requests,
        prompt_tokens=snapshot.prompt_tokens,
        completion_tokens=snapshot.completion_tokens,
        total_tokens=snapshot.total_tokens,
    )
