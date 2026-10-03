import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request

from app import __version__
from app.api.v1.router import router as v1_router
from app.config import ensure_production_secret, get_settings
from app.providers.factory import build_provider
from app.schemas.usage import HealthResponse
from app.services.rate_limit import SlidingWindowLimiter
from app.services.usage import UsageLedger

logger = logging.getLogger("airlock")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_production_secret(settings)
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    provider = build_provider(settings)
    app.state.settings = settings
    app.state.provider = provider
    app.state.usage = UsageLedger()
    app.state.limiter = SlidingWindowLimiter(
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    logger.info("provider=%s model=%s", provider.name, provider.model)
    try:
        yield
    finally:
        await provider.aclose()


app = FastAPI(
    title="Airlock",
    version=__version__,
    lifespan=lifespan,
)
app.include_router(v1_router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", uuid4().hex[:12])
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health(request: Request) -> HealthResponse:
    provider = request.app.state.provider
    return HealthResponse(
        status="ok",
        service=request.app.state.settings.app_name,
        provider=provider.name,
        model=provider.model,
        version=__version__,
    )
