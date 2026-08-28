from fastapi import APIRouter, Depends

from app.auth import get_optional_authenticated_session
from app.core.settings import get_settings
from app.repositories.cases import get_dashboard_snapshot
from app.schemas import MetaPayload
from app.workflow_seed import COLONOSCOPY_WORKFLOW_STEPS, DASHBOARD_SNAPSHOT, WORKFLOW_STEPS_BY_PROCEDURE

router = APIRouter()


@router.get("/meta", response_model=MetaPayload)
def get_meta(session=Depends(get_optional_authenticated_session)) -> MetaPayload:
    settings = get_settings()
    try:
        snapshot = get_dashboard_snapshot(session=session)
    except Exception:
        snapshot = DASHBOARD_SNAPSHOT
    return MetaPayload(
        appName=settings.app_name,
        odooRecommendedModule=settings.odoo_recommended_module,
        odooRecommendedModuleLabel=settings.odoo_recommended_module_label,
        workflowSteps=COLONOSCOPY_WORKFLOW_STEPS,
        workflowStepsByProcedure=WORKFLOW_STEPS_BY_PROCEDURE,
        dashboardSnapshot=snapshot,
    )
