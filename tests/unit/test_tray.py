from __future__ import annotations

from pathlib import Path

import pytest

from app import tray
from app.cli_runtime import RuntimeMetadata
from app.windows_startup import StartupRegistration

pytestmark = pytest.mark.unit


def test_require_windows_raises_clear_error_on_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(tray.os, "name", "posix")

    with pytest.raises(RuntimeError, match="Windows tray mode is only supported on Windows"):
        tray.require_windows_tray_support()


def test_get_tray_status_reports_running_metadata(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "server.log"
    metadata = RuntimeMetadata(pid=1234, host="127.0.0.1", port=2455, log_file=str(log_file))

    monkeypatch.setattr(tray, "load_running_metadata", lambda pid_file: (metadata, False))
    monkeypatch.setattr(tray, "default_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(
        tray, "default_startup_registration", lambda: StartupRegistration(command='"pythonw" -m app.cli tray')
    )
    monkeypatch.setattr(tray, "is_startup_enabled", lambda registration: True)

    status = tray.get_tray_status()

    assert status.running is True
    assert status.pid == 1234
    assert status.dashboard_url == "http://127.0.0.1:2455"
    assert status.log_file == log_file
    assert status.startup_enabled is True


def test_get_tray_status_reports_stopped_when_no_metadata(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tray, "load_running_metadata", lambda pid_file: (None, False))
    monkeypatch.setattr(tray, "default_pid_file", lambda: tmp_path / "server.pid")
    monkeypatch.setattr(tray, "default_log_file", lambda: tmp_path / "server.log")
    monkeypatch.setattr(
        tray, "default_startup_registration", lambda: StartupRegistration(command='"pythonw" -m app.cli tray')
    )
    monkeypatch.setattr(tray, "is_startup_enabled", lambda registration: False)

    status = tray.get_tray_status()

    assert status.running is False
    assert status.pid is None
    assert status.dashboard_url == "http://127.0.0.1:2455"
    assert status.log_file == tmp_path / "server.log"
    assert status.startup_enabled is False
