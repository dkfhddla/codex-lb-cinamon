from __future__ import annotations

from typing import cast

import pytest
from fastapi import Request

import app.modules.runtime_status.api as runtime_status_api
from app.core.exceptions import DashboardAuthError

pytestmark = pytest.mark.unit


def test_runtime_status_rejects_non_local_requests(monkeypatch) -> None:
    monkeypatch.setattr(runtime_status_api, "is_local_request", lambda request: False)

    with pytest.raises(DashboardAuthError, match="only available to local requests"):
        runtime_status_api.validate_local_runtime_status_request(cast(Request, object()))
