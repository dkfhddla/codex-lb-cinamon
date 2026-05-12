from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.modules.shared.schemas import DashboardModel


class RuntimeActiveRequest(DashboardModel):
    request_id: str
    provider_kind: str | None = None
    routing_subject_id: str | None = None
    account_id: str | None = None
    label: str
    model: str
    reasoning_effort: str | None = None
    transport: str | None = None
    route_class: str | None = None
    started_at: datetime
    elapsed_seconds: int


class RuntimeUsageAccount(DashboardModel):
    account_id: str
    label: str
    used_percent: float | None = None
    reset_at: datetime | None = None
    seconds_until_reset: int | None = None
    active_summary: str | None = None


class RuntimeOverallUsage(DashboardModel):
    account_id: str
    label: str
    used_percent: float
    reset_at: datetime | None = None
    seconds_until_reset: int | None = None


class RuntimeStatusResponse(DashboardModel):
    usage_available: bool
    usage_unavailable_reason: str | None = None
    overall_usage: RuntimeOverallUsage | None = None
    accounts: list[RuntimeUsageAccount] = Field(default_factory=list)
    active_requests: list[RuntimeActiveRequest] = Field(default_factory=list)
