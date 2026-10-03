from fastapi import APIRouter

from app.api.v1 import auth, inference, usage

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(inference.router)
router.include_router(usage.router)
