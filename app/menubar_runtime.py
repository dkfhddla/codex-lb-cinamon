from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.cli_runtime import (
    RuntimeMetadata,
    ServeOptions,
    load_running_metadata,
    shutdown_background_server,
    start_background_server,
)
from app.menubar_summary import MenuBarSnapshot


@dataclass(frozen=True, slots=True)
class MenuBarRuntimeOptions:
    host: str
    port: int
    ssl_certfile: str | None
    ssl_keyfile: str | None
    pid_file: Path
    log_file: Path
    startup_timeout_seconds: float
    start_on_launch: bool


@dataclass(frozen=True, slots=True)
class MenuBarRuntimeStatus:
    running: bool
    pid: int | None
    host: str
    port: int
    dashboard_url: str
    log_file: Path
    stale_metadata_removed: bool


def get_menu_bar_runtime_status(
    *,
    pid_file: Path,
    log_file: Path,
    default_host: str,
    default_port: int,
) -> MenuBarRuntimeStatus:
    metadata, stale = load_running_metadata(pid_file)
    if metadata is None:
        return MenuBarRuntimeStatus(
            running=False,
            pid=None,
            host=default_host,
            port=default_port,
            dashboard_url=dashboard_url(default_host, default_port),
            log_file=log_file.expanduser(),
            stale_metadata_removed=stale,
        )

    return MenuBarRuntimeStatus(
        running=True,
        pid=metadata.pid,
        host=metadata.host,
        port=metadata.port,
        dashboard_url=dashboard_url(metadata.host, metadata.port),
        log_file=Path(metadata.log_file).expanduser(),
        stale_metadata_removed=stale,
    )


def status_from_options(options: MenuBarRuntimeOptions) -> MenuBarRuntimeStatus:
    return get_menu_bar_runtime_status(
        pid_file=options.pid_file,
        log_file=options.log_file,
        default_host=options.host,
        default_port=options.port,
    )


def start_menu_bar_runtime(options: MenuBarRuntimeOptions) -> RuntimeMetadata:
    return start_background_server(
        ServeOptions(
            host=options.host,
            port=options.port,
            ssl_certfile=options.ssl_certfile,
            ssl_keyfile=options.ssl_keyfile,
        ),
        pid_file=options.pid_file,
        log_file=options.log_file,
        startup_timeout_seconds=options.startup_timeout_seconds,
    )


def stop_menu_bar_runtime(options: MenuBarRuntimeOptions) -> RuntimeMetadata | None:
    return shutdown_background_server(options.pid_file)


def stopped_runtime_snapshot(status: MenuBarRuntimeStatus) -> MenuBarSnapshot:
    status_label = "Stopped"
    if status.stale_metadata_removed:
        status_label = "Stopped (stale PID removed)"
    return MenuBarSnapshot(
        title="Stopped",
        rows=(
            ("Status", status_label),
            ("Dashboard", status.dashboard_url),
            ("Log file", str(status.log_file)),
        ),
        error_message=status_label,
    )


def dashboard_url(host: str, port: int) -> str:
    dashboard_host = "127.0.0.1" if host in {"", "0.0.0.0", "::"} else host
    if ":" in dashboard_host and not dashboard_host.startswith("["):
        dashboard_host = f"[{dashboard_host}]"
    return f"http://{dashboard_host}:{port}"
