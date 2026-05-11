from __future__ import annotations

import os
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from app.cli_runtime import (
    ServeOptions,
    default_log_file,
    default_pid_file,
    load_running_metadata,
    shutdown_background_server,
    start_background_server,
)
from app.windows_startup import (
    default_startup_registration,
    disable_startup,
    enable_startup,
    is_startup_enabled,
)

DEFAULT_TRAY_HOST = "127.0.0.1"
DEFAULT_TRAY_PORT = 2455


@dataclass(frozen=True, slots=True)
class TrayStatus:
    running: bool
    pid: int | None
    host: str
    port: int
    dashboard_url: str
    log_file: Path
    startup_enabled: bool
    stale_metadata_removed: bool


def require_windows_tray_support() -> None:
    if os.name != "nt":
        raise RuntimeError("Windows tray mode is only supported on Windows.")


def get_tray_status() -> TrayStatus:
    metadata, stale = load_running_metadata(default_pid_file())
    registration = default_startup_registration()
    startup_enabled = is_startup_enabled(registration)
    if metadata is None:
        host = DEFAULT_TRAY_HOST
        port = DEFAULT_TRAY_PORT
        log_file = default_log_file()
        return TrayStatus(
            running=False,
            pid=None,
            host=host,
            port=port,
            dashboard_url=_dashboard_url(host, port),
            log_file=log_file,
            startup_enabled=startup_enabled,
            stale_metadata_removed=stale,
        )

    return TrayStatus(
        running=True,
        pid=metadata.pid,
        host=metadata.host,
        port=metadata.port,
        dashboard_url=_dashboard_url(metadata.host, metadata.port),
        log_file=Path(metadata.log_file),
        startup_enabled=startup_enabled,
        stale_metadata_removed=stale,
    )


def run_tray_app() -> None:
    require_windows_tray_support()
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Tray mode requires the optional dependencies: pystray and pillow.") from exc

    state = {"status": get_tray_status(), "error": ""}

    def refresh(icon: object | None = None) -> None:
        state["status"] = get_tray_status()
        status = state["status"]
        if hasattr(icon, "title"):
            icon.title = _tooltip(status, str(state["error"]))
        if hasattr(icon, "icon"):
            icon.icon = _build_icon(Image, ImageDraw, status.running)
        if hasattr(icon, "update_menu"):
            icon.update_menu()

    def start_server(icon: object, item: object) -> None:
        del item
        try:
            state["error"] = ""
            status = get_tray_status()
            if not status.running:
                start_background_server(
                    ServeOptions(host=DEFAULT_TRAY_HOST, port=DEFAULT_TRAY_PORT, ssl_certfile=None, ssl_keyfile=None),
                    pid_file=default_pid_file(),
                    log_file=default_log_file(),
                )
        except Exception as exc:  # pragma: no cover - shown through tray tooltip
            state["error"] = str(exc)
        finally:
            refresh(icon)

    def stop_server(icon: object, item: object) -> None:
        del item
        try:
            state["error"] = ""
            shutdown_background_server(default_pid_file())
        except Exception as exc:  # pragma: no cover - shown through tray tooltip
            state["error"] = str(exc)
        finally:
            refresh(icon)

    def open_dashboard(icon: object, item: object) -> None:
        del icon, item
        webbrowser.open(get_tray_status().dashboard_url)

    def open_log(icon: object, item: object) -> None:
        del icon, item
        _open_path(get_tray_status().log_file)

    def toggle_startup(icon: object, item: object) -> None:
        del item
        try:
            registration = default_startup_registration()
            if is_startup_enabled(registration):
                disable_startup(registration)
            else:
                enable_startup(registration)
            state["error"] = ""
        except Exception as exc:  # pragma: no cover - shown through tray tooltip
            state["error"] = str(exc)
        finally:
            refresh(icon)

    def quit_tray(icon: object, item: object) -> None:
        del item
        icon.stop()

    def is_running(item: object) -> bool:
        del item
        return bool(state["status"].running)

    def is_stopped(item: object) -> bool:
        del item
        return not bool(state["status"].running)

    def startup_checked(item: object) -> bool:
        del item
        return bool(state["status"].startup_enabled)

    status = state["status"]
    icon = pystray.Icon(
        "codex-lb-cinamon",
        _build_icon(Image, ImageDraw, status.running),
        _tooltip(status, ""),
        pystray.Menu(
            pystray.MenuItem("Start server", start_server, enabled=is_stopped),
            pystray.MenuItem("Stop server", stop_server, enabled=is_running),
            pystray.MenuItem("Refresh status", lambda icon, item: refresh(icon)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open dashboard", open_dashboard),
            pystray.MenuItem("Open log", open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start with Windows", toggle_startup, checked=startup_checked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit tray", quit_tray),
        ),
    )
    icon.run()


def _dashboard_url(host: str, port: int) -> str:
    dashboard_host = "127.0.0.1" if host in {"", "0.0.0.0", "::"} else host
    if ":" in dashboard_host and not dashboard_host.startswith("["):
        dashboard_host = f"[{dashboard_host}]"
    return f"http://{dashboard_host}:{port}"


def _tooltip(status: TrayStatus, error: str) -> str:
    if error:
        return f"codex-lb-cinamon - Error: {error}"
    if status.running:
        return f"codex-lb-cinamon running (pid {status.pid}, {status.host}:{status.port})"
    if status.stale_metadata_removed:
        return "codex-lb-cinamon stopped (stale PID removed)"
    return "codex-lb-cinamon stopped"


def _build_icon(image_module: object, image_draw_module: object, running: bool) -> object:
    image = image_module.new("RGB", (64, 64), "#111827")
    draw = image_draw_module.Draw(image)
    accent = "#22c55e" if running else "#ef4444"
    draw.ellipse((12, 12, 52, 52), fill=accent)
    draw.rectangle((29, 18, 35, 46), fill="#ffffff")
    draw.rectangle((20, 29, 44, 35), fill="#ffffff")
    return image


def _open_path(path: Path) -> None:
    if os.name != "nt":
        return
    os.startfile(path)  # type: ignore[attr-defined]
