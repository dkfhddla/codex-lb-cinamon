from __future__ import annotations

from datetime import datetime

from app.core import usage as usage_core
from app.core.active_requests import ActiveRequestRegistry
from app.core.usage.types import UsageWindowRow
from app.core.utils.time import from_epoch_seconds, to_utc_naive, utcnow
from app.db.models import Account
from app.modules.accounts.repository import AccountsRepository
from app.modules.runtime_status.schemas import (
    RuntimeActiveRequest,
    RuntimeOverallUsage,
    RuntimeStatusResponse,
    RuntimeUsageAccount,
)
from app.modules.usage.repository import UsageRepository


class RuntimeStatusService:
    def __init__(
        self,
        *,
        accounts_repo: AccountsRepository,
        usage_repo: UsageRepository,
        active_requests: ActiveRequestRegistry,
    ) -> None:
        self._accounts_repo = accounts_repo
        self._usage_repo = usage_repo
        self._active_requests = active_requests

    async def get_status(self) -> RuntimeStatusResponse:
        now = utcnow()
        accounts = await self._accounts_repo.list_accounts()
        account_map = {account.id: account for account in accounts}
        active = [
            RuntimeActiveRequest(
                request_id=item.request_id,
                provider_kind=item.provider_kind,
                routing_subject_id=item.routing_subject_id,
                account_id=item.account_id,
                label=_label_for_request(item.account_id, item.routing_subject_id, account_map),
                model=item.model,
                reasoning_effort=item.reasoning_effort,
                transport=item.transport,
                route_class=item.route_class,
                started_at=item.started_at,
                elapsed_seconds=item.elapsed_seconds,
            )
            for item in self._active_requests.snapshot(now=now)
        ]

        try:
            primary_rows_raw = await self._latest_usage_rows("primary")
            secondary_rows_raw = await self._latest_usage_rows("secondary")
            primary_rows, _secondary_rows = usage_core.normalize_weekly_only_rows(
                primary_rows_raw,
                secondary_rows_raw,
            )
        except Exception as exc:
            return RuntimeStatusResponse(
                usage_available=False,
                usage_unavailable_reason=str(exc) or "usage unavailable",
                active_requests=active,
            )

        active_by_account = _active_summary_by_account(active)
        usage_accounts = [
            _usage_account_response(account, primary_rows, active_by_account, now)
            for account in accounts
        ]
        available_accounts = [account for account in usage_accounts if account.used_percent is not None]
        overall = _overall_usage(available_accounts)
        return RuntimeStatusResponse(
            usage_available=True,
            overall_usage=overall,
            accounts=usage_accounts,
            active_requests=active,
        )

    async def _latest_usage_rows(self, window: str) -> list[UsageWindowRow]:
        latest = await self._usage_repo.latest_by_account(window=window)
        return [
            UsageWindowRow(
                account_id=entry.account_id,
                used_percent=entry.used_percent,
                reset_at=entry.reset_at,
                window_minutes=entry.window_minutes,
                recorded_at=entry.recorded_at,
            )
            for entry in latest.values()
        ]


def _usage_account_response(
    account: Account,
    usage_rows: list[UsageWindowRow],
    active_by_account: dict[str, str],
    now: datetime,
) -> RuntimeUsageAccount:
    usage_by_account = {row.account_id: row for row in usage_rows}
    row = usage_by_account.get(account.id)
    reset_at = from_epoch_seconds(row.reset_at) if row and row.reset_at is not None else None
    return RuntimeUsageAccount(
        account_id=account.id,
        label=_account_label(account),
        used_percent=float(row.used_percent) if row and row.used_percent is not None else None,
        reset_at=reset_at,
        seconds_until_reset=_seconds_until_reset(reset_at, now),
        active_summary=active_by_account.get(account.id),
    )


def _overall_usage(accounts: list[RuntimeUsageAccount]) -> RuntimeOverallUsage | None:
    if not accounts:
        return None
    highest = max(accounts, key=lambda item: item.used_percent or 0.0)
    assert highest.used_percent is not None
    return RuntimeOverallUsage(
        account_id=highest.account_id,
        label=highest.label,
        used_percent=highest.used_percent,
        reset_at=highest.reset_at,
        seconds_until_reset=highest.seconds_until_reset,
    )


def _label_for_request(
    account_id: str | None,
    routing_subject_id: str | None,
    account_map: dict[str, Account],
) -> str:
    if account_id and account_id in account_map:
        return _account_label(account_map[account_id])
    return routing_subject_id or account_id or "unknown"


def _account_label(account: Account) -> str:
    return account.email or account.id


def _active_summary_by_account(active: list[RuntimeActiveRequest]) -> dict[str, str]:
    summaries: dict[str, str] = {}
    for request in active:
        if request.account_id is None or request.account_id in summaries:
            continue
        pieces = [request.model]
        if request.reasoning_effort:
            pieces.append(request.reasoning_effort)
        summaries[request.account_id] = f"{' '.join(pieces)} 실행 중"
    return summaries


def _seconds_until_reset(reset_at: datetime | None, now: datetime) -> int | None:
    if reset_at is None:
        return None
    reset_naive = to_utc_naive(reset_at)
    return max(0, int((reset_naive - now).total_seconds()))
