from __future__ import annotations

from pathlib import Path

from app.cli_runtime import RuntimeMetadata
from app.menubar_runtime import (
    MenuBarRuntimeOptions,
    dashboard_page_url,
    get_menu_bar_runtime_status,
    start_menu_bar_runtime,
    stopped_runtime_snapshot,
)


def test_get_menu_bar_runtime_status_reports_running_metadata(monkeypatch, tmp_path: Path) -> None:
    log_file = tmp_path / "server.log"
    metadata = RuntimeMetadata(pid=1234, host="127.0.0.1", port=2455, log_file=str(log_file))

    monkeypatch.setattr("app.menubar_runtime.load_running_metadata", lambda pid_file: (metadata, False))

    status = get_menu_bar_runtime_status(
        pid_file=tmp_path / "server.pid",
        log_file=tmp_path / "fallback.log",
        default_host="127.0.0.1",
        default_port=2455,
    )

    assert status.running is True
    assert status.pid == 1234
    assert status.dashboard_url == "http://127.0.0.1:2455"
    assert status.log_file == log_file


def test_get_menu_bar_runtime_status_reports_stopped_defaults(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("app.menubar_runtime.load_running_metadata", lambda pid_file: (None, True))

    status = get_menu_bar_runtime_status(
        pid_file=tmp_path / "server.pid",
        log_file=tmp_path / "server.log",
        default_host="0.0.0.0",
        default_port=2455,
    )

    assert status.running is False
    assert status.pid is None
    assert status.dashboard_url == "http://127.0.0.1:2455"
    assert status.stale_metadata_removed is True


def test_start_menu_bar_runtime_uses_background_lifecycle(monkeypatch, tmp_path: Path) -> None:
    runtime = RuntimeMetadata(pid=4321, host="127.0.0.1", port=2455, log_file=str(tmp_path / "server.log"))
    calls: list[object] = []
    options = MenuBarRuntimeOptions(
        host="127.0.0.1",
        port=2455,
        ssl_certfile=None,
        ssl_keyfile=None,
        pid_file=tmp_path / "server.pid",
        log_file=tmp_path / "server.log",
        startup_timeout_seconds=3.0,
        start_on_launch=False,
    )

    def fake_start(*args, **kwargs):
        calls.append((args, kwargs))
        return runtime

    monkeypatch.setattr("app.menubar_runtime.start_background_server", fake_start)

    assert start_menu_bar_runtime(options) == runtime
    assert len(calls) == 1


def test_stopped_runtime_snapshot_reports_stopped_state(tmp_path: Path) -> None:
    status = get_menu_bar_runtime_status(
        pid_file=tmp_path / "server.pid",
        log_file=tmp_path / "server.log",
        default_host="127.0.0.1",
        default_port=2455,
    )

    snapshot = stopped_runtime_snapshot(status)

    assert snapshot.title == "Stopped"
    assert ("Status", "Stopped") in snapshot.rows
    assert ("Dashboard", "http://127.0.0.1:2455") in snapshot.rows


def test_dashboard_page_url_points_to_spa_dashboard_route() -> None:
    assert dashboard_page_url("http://127.0.0.1:2455") == "http://127.0.0.1:2455/dashboard"
    assert dashboard_page_url("http://127.0.0.1:2455/") == "http://127.0.0.1:2455/dashboard"
