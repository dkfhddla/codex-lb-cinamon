from __future__ import annotations

from pathlib import Path

import pytest

from app.tray import (
    TrayActiveRequest,
    TrayRuntimeAccount,
    TrayRuntimeSnapshot,
    TrayStatus,
    _account_usage_menu_labels,
    _tooltip,
)

pytestmark = pytest.mark.unit


def test_tooltip_includes_usage_reset_and_active_request() -> None:
    status = TrayStatus(
        running=True,
        pid=123,
        host="127.0.0.1",
        port=2455,
        dashboard_url="http://127.0.0.1:2455",
        log_file=Path("server.log"),
        startup_enabled=False,
        stale_metadata_removed=False,
        runtime=TrayRuntimeSnapshot(
            usage_available=True,
            usage_unavailable_reason=None,
            overall_used_percent=71.2,
            overall_seconds_until_reset=54 * 60,
            active_requests=[
                TrayActiveRequest(
                    request_id="req_1",
                    label="acc-1",
                    model="gpt-5.4",
                    reasoning_effort="high",
                    elapsed_seconds=42,
                )
            ],
            accounts=[],
        ),
    )

    tooltip = _tooltip(status, "")

    assert "5h 사용 71% · 다음 주기 54m" in tooltip
    assert "현재: acc-1 · gpt-5.4 · high · 42s" in tooltip


def test_account_usage_menu_labels_include_running_model_or_idle() -> None:
    labels = _account_usage_menu_labels(
        TrayRuntimeSnapshot(
            usage_available=True,
            usage_unavailable_reason=None,
            overall_used_percent=71.0,
            overall_seconds_until_reset=54 * 60,
            active_requests=[],
            accounts=[
                TrayRuntimeAccount(
                    account_id="acc_1",
                    label="acc-1",
                    used_percent=28.0,
                    seconds_until_reset=102 * 60,
                    active_summary="gpt-5.4 high 실행 중",
                ),
                TrayRuntimeAccount(
                    account_id="acc_2",
                    label="acc-2",
                    used_percent=71.0,
                    seconds_until_reset=54 * 60,
                    active_summary=None,
                ),
            ],
        )
    )

    assert labels == [
        "acc-1  28% · 1h 42m · gpt-5.4 high 실행 중",
        "acc-2  71% · 54m · idle",
    ]
