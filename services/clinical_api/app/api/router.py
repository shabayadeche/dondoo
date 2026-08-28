from fastapi import APIRouter

from app.api.routes.cases import router as cases_router
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.api.routes.session import router as session_router

router = APIRouter()
router.include_router(health_router)
router.include_router(meta_router, prefix="/api")
router.include_router(session_router, prefix="/api")
router.include_router(cases_router, prefix="/api")
