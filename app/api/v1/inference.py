from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import enforce_rate_limit
from app.schemas.inference import ChatRequest, ChatResponse, StructuredRequest, StructuredResponse
from app.schemas.usage import ModelInfo
from app.services.errors import ModelBackendError, SchemaMismatchError, ToolLoopError
from app.services.inference import InferenceService
from app.services.tools import tool_names

router = APIRouter(tags=["inference"])


def _service(request: Request) -> InferenceService:
    return InferenceService(
        provider=request.app.state.provider,
        usage=request.app.state.usage,
        settings=request.app.state.settings,
    )


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, ModelBackendError):
        return HTTPException(status_code=502, detail="Model provider request failed.")
    if isinstance(exc, SchemaMismatchError):
        return HTTPException(status_code=422, detail="Model output did not match the schema.")
    if isinstance(exc, ToolLoopError):
        return HTTPException(status_code=502, detail="Tool loop did not finish.")
    raise exc


@router.get("/models", response_model=ModelInfo)
async def models(
    request: Request,
    _: Annotated[str, Depends(enforce_rate_limit)],
) -> ModelInfo:
    provider = request.app.state.provider
    return ModelInfo(provider=provider.name, model=provider.model, tools=tool_names())


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user: Annotated[str, Depends(enforce_rate_limit)],
) -> ChatResponse:
    try:
        return await _service(request).chat(user, body)
    except (ModelBackendError, SchemaMismatchError, ToolLoopError) as exc:
        raise _translate(exc) from exc


@router.post("/extract", response_model=StructuredResponse)
async def extract(
    body: StructuredRequest,
    request: Request,
    user: Annotated[str, Depends(enforce_rate_limit)],
) -> StructuredResponse:
    try:
        return await _service(request).extract(user, body)
    except (ModelBackendError, SchemaMismatchError, ToolLoopError) as exc:
        raise _translate(exc) from exc
