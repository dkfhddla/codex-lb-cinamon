from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import RLock

from app.core.utils.time import utcnow

DEFAULT_ACTIVE_REQUEST_TTL_SECONDS = 30 * 60


@dataclass(frozen=True, slots=True)
class ActiveRequest:
    request_id: str
    provider_kind: str | None
    routing_subject_id: str | None
    account_id: str | None
    model: str
    reasoning_effort: str | None
    transport: str | None
    route_class: str | None
    started_at: datetime


@dataclass(frozen=True, slots=True)
class ActiveRequestSnapshot:
    request_id: str
    provider_kind: str | None
    routing_subject_id: str | None
    account_id: str | None
    model: str
    reasoning_effort: str | None
    transport: str | None
    route_class: str | None
    started_at: datetime
    elapsed_seconds: int


class ActiveRequestRegistry:
    def __init__(self, *, ttl_seconds: int = DEFAULT_ACTIVE_REQUEST_TTL_SECONDS) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl_seconds = ttl_seconds
        self._requests: dict[str, ActiveRequest] = {}
        self._lock = RLock()

    def register(self, request: ActiveRequest) -> None:
        if not request.request_id.strip():
            raise ValueError("request_id must not be empty")
        with self._lock:
            self._requests[request.request_id] = request

    def complete(self, request_id: str) -> None:
        with self._lock:
            self._requests.pop(request_id, None)

    def snapshot(self, *, now: datetime | None = None) -> list[ActiveRequestSnapshot]:
        current = now or utcnow()
        cutoff = current - timedelta(seconds=self._ttl_seconds)
        snapshots: list[ActiveRequestSnapshot] = []
        stale_ids: list[str] = []
        with self._lock:
            for request_id, request in self._requests.items():
                if request.started_at < cutoff:
                    stale_ids.append(request_id)
                    continue
                elapsed = max(0, int((current - request.started_at).total_seconds()))
                snapshots.append(
                    ActiveRequestSnapshot(
                        request_id=request.request_id,
                        provider_kind=request.provider_kind,
                        routing_subject_id=request.routing_subject_id,
                        account_id=request.account_id,
                        model=request.model,
                        reasoning_effort=request.reasoning_effort,
                        transport=request.transport,
                        route_class=request.route_class,
                        started_at=request.started_at,
                        elapsed_seconds=elapsed,
                    )
                )
            for request_id in stale_ids:
                self._requests.pop(request_id, None)
        return sorted(snapshots, key=lambda item: item.started_at)

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()


_active_request_registry = ActiveRequestRegistry()


def get_active_request_registry() -> ActiveRequestRegistry:
    return _active_request_registry
