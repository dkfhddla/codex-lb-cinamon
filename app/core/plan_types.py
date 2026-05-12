from __future__ import annotations

from typing import Final

ACCOUNT_PLAN_TYPES: Final[set[str]] = {
    "free",
    "plus",
    "pro_lite",
    "pro",
    "team",
    "business",
    "enterprise",
    "edu",
}

ACCOUNT_PLAN_TYPE_ALIASES: Final[dict[str, str]] = {
    "prolite": "pro_lite",
    "pro-lite": "pro_lite",
    "pro lite": "pro_lite",
}

RATE_LIMIT_PLAN_TYPES: Final[set[str]] = {
    *ACCOUNT_PLAN_TYPES,
    "guest",
    "go",
    "free_workspace",
    "education",
    "quorum",
    "k12",
}


def _clean_plan_type(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def normalize_account_plan_type(value: str | None) -> str | None:
    cleaned = _clean_plan_type(value)
    if not cleaned:
        return None
    normalized = cleaned.lower()
    normalized = ACCOUNT_PLAN_TYPE_ALIASES.get(normalized, normalized)
    return normalized if normalized in ACCOUNT_PLAN_TYPES else None


def canonicalize_account_plan_type(value: str | None) -> str | None:
    cleaned = _clean_plan_type(value)
    if not cleaned:
        return None
    normalized = cleaned.lower()
    normalized = ACCOUNT_PLAN_TYPE_ALIASES.get(normalized, normalized)
    if normalized in ACCOUNT_PLAN_TYPES:
        return normalized
    return cleaned


def coerce_account_plan_type(value: str | None, default: str) -> str:
    cleaned = _clean_plan_type(value)
    if cleaned is None:
        return default
    canonical = canonicalize_account_plan_type(cleaned)
    return canonical if canonical is not None else default


def normalize_rate_limit_plan_type(value: str | None) -> str | None:
    cleaned = _clean_plan_type(value)
    if not cleaned:
        return None
    normalized = cleaned.lower()
    normalized = ACCOUNT_PLAN_TYPE_ALIASES.get(normalized, normalized)
    return normalized if normalized in RATE_LIMIT_PLAN_TYPES else None
