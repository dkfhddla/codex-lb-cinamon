from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.plan_types import normalize_account_plan_type, normalize_rate_limit_plan_type
from app.core.usage import (
    capacity_for_plan,
    normalize_usage_window,
    normalize_weekly_only_rows,
    used_credits_from_percent,
)
from app.core.usage.types import UsageWindowRow, UsageWindowSummary
from app.core.utils.time import utcnow

pytestmark = pytest.mark.unit


def test_used_credits_from_percent():
    assert used_credits_from_percent(25.0, 200.0) == 50.0
    assert used_credits_from_percent(None, 200.0) is None


def test_normalize_usage_window_defaults():
    summary = UsageWindowSummary(
        used_percent=None,
        capacity_credits=0.0,
        used_credits=0.0,
        reset_at=None,
        window_minutes=None,
    )
    window = normalize_usage_window(summary)
    assert window.used_percent == 0.0
    assert window.capacity_credits == 0.0
    assert window.used_credits == 0.0


def test_capacity_for_plan():
    assert capacity_for_plan("plus", "5h") is not None
    assert capacity_for_plan("plus", "7d") is not None
    assert capacity_for_plan("unknown", "5h") is None


@pytest.mark.parametrize("plan_type", ["pro_lite", "prolite", "pro-lite", "pro lite", "pro100", "pro-100", "pro 100"])
def test_capacity_for_pro_lite_uses_current_codex_promo_until_may_2026(plan_type: str):
    assert capacity_for_plan(plan_type, "5h", today=date(2026, 5, 31)) == 2250.0
    assert capacity_for_plan(plan_type, "7d", today=date(2026, 5, 31)) == 75600.0


@pytest.mark.parametrize("plan_type", ["pro_lite", "prolite", "pro-lite", "pro lite", "pro100", "pro-100", "pro 100"])
def test_capacity_for_pro_lite_falls_back_to_standard_multiplier_after_promo(plan_type: str):
    assert capacity_for_plan(plan_type, "5h", today=date(2026, 6, 1)) == 1125.0
    assert capacity_for_plan(plan_type, "7d", today=date(2026, 6, 1)) == 37800.0


@pytest.mark.parametrize("plan_type", ["pro", "pro200", "pro-200", "pro 200"])
def test_capacity_for_pro_200_uses_current_codex_multiplier(plan_type: str):
    assert capacity_for_plan(plan_type, "5h") == 4500.0
    assert capacity_for_plan(plan_type, "7d") == 151200.0


@pytest.mark.parametrize("plan_type", ["education", "higher_education", "higher education"])
def test_education_plan_aliases_normalize_to_edu(plan_type: str):
    assert normalize_account_plan_type(plan_type) == "edu"
    assert normalize_rate_limit_plan_type(plan_type) == "edu"


def test_go_plan_is_recognized_without_fixed_capacity():
    assert normalize_account_plan_type("go") == "go"
    assert normalize_rate_limit_plan_type("go") == "go"
    assert capacity_for_plan("go", "5h") is None
    assert capacity_for_plan("go", "7d") is None


def test_normalize_weekly_only_rows_prefers_newer_primary_over_stale_secondary():
    now = utcnow()
    weekly_primary = UsageWindowRow(
        account_id="acc_weekly",
        used_percent=65.0,
        window_minutes=10080,
        reset_at=300,
        recorded_at=now,
    )
    stale_secondary = UsageWindowRow(
        account_id="acc_weekly",
        used_percent=5.0,
        window_minutes=10080,
        reset_at=100,
        recorded_at=now - timedelta(days=2),
    )

    normalized_primary, normalized_secondary = normalize_weekly_only_rows(
        [weekly_primary],
        [stale_secondary],
    )

    assert normalized_primary == []
    assert normalized_secondary == [weekly_primary]


def test_normalize_weekly_only_rows_keeps_newer_secondary():
    now = utcnow()
    older_weekly_primary = UsageWindowRow(
        account_id="acc_weekly",
        used_percent=65.0,
        window_minutes=10080,
        reset_at=100,
        recorded_at=now - timedelta(days=1),
    )
    newer_secondary = UsageWindowRow(
        account_id="acc_weekly",
        used_percent=15.0,
        window_minutes=10080,
        reset_at=300,
        recorded_at=now,
    )

    normalized_primary, normalized_secondary = normalize_weekly_only_rows(
        [older_weekly_primary],
        [newer_secondary],
    )

    assert normalized_primary == []
    assert normalized_secondary == [newer_secondary]
