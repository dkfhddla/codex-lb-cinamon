from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.active_requests import ActiveRequest, get_active_request_registry
from app.core.crypto import TokenEncryptor
from app.core.utils.time import naive_utc_to_epoch, utcnow
from app.db.models import Account, AccountStatus
from app.db.session import SessionLocal
from app.modules.accounts.repository import AccountsRepository
from app.modules.usage.repository import UsageRepository

pytestmark = pytest.mark.integration


def _make_account(account_id: str, email: str, plan_type: str = "plus") -> Account:
    encryptor = TokenEncryptor()
    return Account(
        id=account_id,
        email=email,
        plan_type=plan_type,
        access_token_encrypted=encryptor.encrypt("access"),
        refresh_token_encrypted=encryptor.encrypt("refresh"),
        id_token_encrypted=encryptor.encrypt("id"),
        last_refresh=utcnow(),
        status=AccountStatus.ACTIVE,
        deactivation_reason=None,
    )


@pytest.mark.asyncio
async def test_runtime_status_reports_primary_usage_and_active_requests(async_client, db_setup):
    now = utcnow()
    registry = get_active_request_registry()
    registry.clear()
    registry.register(
        ActiveRequest(
            request_id="req_active",
            provider_kind="chatgpt_web",
            routing_subject_id="acc_active",
            account_id="acc_active",
            model="gpt-5.4",
            reasoning_effort="high",
            transport="http",
            route_class="chatgpt_private",
            started_at=now - timedelta(seconds=42),
        )
    )
    async with SessionLocal() as session:
        accounts_repo = AccountsRepository(session)
        usage_repo = UsageRepository(session)
        await accounts_repo.upsert(_make_account("acc_active", "active@example.com"))
        await accounts_repo.upsert(_make_account("acc_idle", "idle@example.com"))
        await usage_repo.add_entry(
            "acc_active",
            28.0,
            window="primary",
            reset_at=naive_utc_to_epoch(now + timedelta(minutes=102)),
            window_minutes=300,
            recorded_at=now - timedelta(minutes=1),
        )
        await usage_repo.add_entry(
            "acc_idle",
            71.0,
            window="primary",
            reset_at=naive_utc_to_epoch(now + timedelta(minutes=54)),
            window_minutes=300,
            recorded_at=now - timedelta(minutes=1),
        )

    response = await async_client.get("/api/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["usageAvailable"] is True
    assert payload["overallUsage"]["accountId"] == "acc_idle"
    assert payload["overallUsage"]["usedPercent"] == pytest.approx(71.0)
    assert payload["activeRequests"][0]["requestId"] == "req_active"
    assert payload["activeRequests"][0]["accountId"] == "acc_active"
    accounts = {item["accountId"]: item for item in payload["accounts"]}
    assert accounts["acc_active"]["activeSummary"] == "gpt-5.4 high 실행 중"
    assert accounts["acc_idle"]["activeSummary"] is None

    registry.clear()
