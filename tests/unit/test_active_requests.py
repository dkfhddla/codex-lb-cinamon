from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.active_requests import ActiveRequest, ActiveRequestRegistry

pytestmark = pytest.mark.unit


def test_active_request_registry_tracks_and_completes_request() -> None:
    now = datetime(2026, 5, 8, 12, 0, 0)
    registry = ActiveRequestRegistry(ttl_seconds=300)

    registry.register(
        ActiveRequest(
            request_id="req_1",
            provider_kind="chatgpt_web",
            routing_subject_id="acc_1",
            account_id="acc_1",
            model="gpt-5.4",
            reasoning_effort="high",
            transport="http",
            route_class="chatgpt_private",
            started_at=now,
        )
    )

    snapshot = registry.snapshot(now=now + timedelta(seconds=42))

    assert len(snapshot) == 1
    assert snapshot[0].request_id == "req_1"
    assert snapshot[0].elapsed_seconds == 42

    registry.complete("req_1")

    assert registry.snapshot(now=now + timedelta(seconds=43)) == []


def test_active_request_registry_excludes_stale_entries() -> None:
    now = datetime(2026, 5, 8, 12, 0, 0)
    registry = ActiveRequestRegistry(ttl_seconds=10)
    registry.register(
        ActiveRequest(
            request_id="req_stale",
            provider_kind="chatgpt_web",
            routing_subject_id="acc_1",
            account_id="acc_1",
            model="gpt-5.4",
            reasoning_effort=None,
            transport="http",
            route_class=None,
            started_at=now,
        )
    )

    assert registry.snapshot(now=now + timedelta(seconds=11)) == []
    assert registry.snapshot(now=now + timedelta(seconds=12)) == []
