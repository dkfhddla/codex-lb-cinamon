from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.auth.dependencies import set_dashboard_error_format
from app.core.exceptions import DashboardAuthError
from app.core.request_locality import is_local_request
from app.dependencies import RuntimeStatusContext, get_runtime_status_context
from app.modules.runtime_status.schemas import RuntimeStatusResponse

router = APIRouter(
    prefix="/api/runtime",
    tags=["dashboard"],
    dependencies=[Depends(set_dashboard_error_format)],
)


def validate_local_runtime_status_request(request: Request) -> None:
    if not is_local_request(request):
        raise DashboardAuthError("Runtime status is only available to local requests", code="local_request_required")


@router.get(
    "/status",
    response_model=RuntimeStatusResponse,
    dependencies=[Depends(validate_local_runtime_status_request)],
)
async def get_runtime_status(
    context: RuntimeStatusContext = Depends(get_runtime_status_context),
) -> RuntimeStatusResponse:
    return await context.service.get_status()
