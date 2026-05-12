from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

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
    runtime: TrayRuntimeSnapshot | None = None


@dataclass(frozen=True, slots=True)
class TrayActiveRequest:
    request_id: str
    label: str
    model: str
    reasoning_effort: str | None
    elapsed_seconds: int


@dataclass(frozen=True, slots=True)
class TrayRuntimeAccount:
    account_id: str
    label: str
    used_percent: float | None
    seconds_until_reset: int | None
    active_summary: str | None


@dataclass(frozen=True, slots=True)
class TrayRuntimeSnapshot:
    usage_available: bool
    usage_unavailable_reason: str | None
    overall_used_percent: float | None
    overall_seconds_until_reset: int | None
    active_requests: list[TrayActiveRequest]
    accounts: list[TrayRuntimeAccount]


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

    host = metadata.host
    port = metadata.port
    return TrayStatus(
        running=True,
        pid=metadata.pid,
        host=host,
        port=port,
        dashboard_url=_dashboard_url(host, port),
        log_file=Path(metadata.log_file),
        startup_enabled=startup_enabled,
        stale_metadata_removed=stale,
        runtime=_fetch_runtime_snapshot(host, port),
    )


def run_tray_app() -> None:
    require_windows_tray_support()
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Tray mode requires the optional dependencies: pystray and pillow.") from exc

    state: dict[str, Any] = {"status": get_tray_status(), "error": ""}

    def refresh(icon: object | None = None) -> None:
        state["status"] = get_tray_status()
        status = state["status"]
        if hasattr(icon, "title"):
            cast(Any, icon).title = _tooltip(status, str(state["error"]))
        if hasattr(icon, "icon"):
            cast(Any, icon).icon = _build_icon(Image, ImageDraw, status.running)
        if icon is not None:
            refresh_menu(icon)

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
        cast(Any, icon).stop()

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

    def build_menu() -> object:
        current = state["status"]
        return pystray.Menu(
            pystray.MenuItem("Start server", start_server, enabled=is_stopped),
            pystray.MenuItem("Stop server", stop_server, enabled=is_running),
            pystray.MenuItem("Refresh status", lambda icon, item: refresh(icon)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("5h usage", lambda icon, item: None, enabled=False),
            *[
                pystray.MenuItem(label, lambda icon, item: None, enabled=False)
                for label in _account_usage_menu_labels(current.runtime)
            ],
            pystray.MenuItem("Active requests", lambda icon, item: None, enabled=False),
            *[
                pystray.MenuItem(label, lambda icon, item: None, enabled=False)
                for label in _active_request_menu_labels(current.runtime)
            ],
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open dashboard", open_dashboard),
            pystray.MenuItem("Open log", open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start with Windows", toggle_startup, checked=startup_checked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit tray", quit_tray),
        )

    def refresh_menu(icon: object) -> None:
        if hasattr(icon, "menu"):
            cast(Any, icon).menu = build_menu()
        if hasattr(icon, "update_menu"):
            cast(Any, icon).update_menu()

    icon = pystray.Icon(
        "codex-lb-cinamon",
        _build_icon(Image, ImageDraw, status.running),
        _tooltip(status, ""),
        build_menu(),
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
        lines = [f"codex-lb-cinamon running (pid {status.pid}, {status.host}:{status.port})"]
        lines.extend(_runtime_tooltip_lines(status.runtime))
        return "\n".join(lines)
    if status.stale_metadata_removed:
        return "codex-lb-cinamon stopped (stale PID removed)"
    return "codex-lb-cinamon stopped"


def _build_icon(image_module: Any, image_draw_module: Any, running: bool) -> object:
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


def _fetch_runtime_snapshot(host: str, port: int) -> TrayRuntimeSnapshot | None:
    url = f"{_dashboard_url(host, port)}/api/runtime/status"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return TrayRuntimeSnapshot(
            usage_available=False,
            usage_unavailable_reason="usage unavailable",
            overall_used_percent=None,
            overall_seconds_until_reset=None,
            active_requests=[],
            accounts=[],
        )
    if not isinstance(payload, dict):
        return None
    return _runtime_snapshot_from_payload(payload)


def _runtime_snapshot_from_payload(payload: dict[str, Any]) -> TrayRuntimeSnapshot:
    overall = payload.get("overallUsage")
    overall_used_percent: float | None = None
    overall_seconds_until_reset: int | None = None
    if isinstance(overall, dict):
        overall_used_percent = _optional_float(overall.get("usedPercent"))
        overall_seconds_until_reset = _optional_int(overall.get("secondsUntilReset"))
    active_requests = [
        TrayActiveRequest(
            request_id=str(item.get("requestId") or ""),
            label=str(item.get("label") or item.get("accountId") or item.get("routingSubjectId") or "unknown"),
            model=str(item.get("model") or "unknown"),
            reasoning_effort=_optional_str(item.get("reasoningEffort")),
            elapsed_seconds=_optional_int(item.get("elapsedSeconds")) or 0,
        )
        for item in payload.get("activeRequests", [])
        if isinstance(item, dict)
    ]
    accounts = [
        TrayRuntimeAccount(
            account_id=str(item.get("accountId") or ""),
            label=str(item.get("label") or item.get("accountId") or "unknown"),
            used_percent=_optional_float(item.get("usedPercent")),
            seconds_until_reset=_optional_int(item.get("secondsUntilReset")),
            active_summary=_optional_str(item.get("activeSummary")),
        )
        for item in payload.get("accounts", [])
        if isinstance(item, dict)
    ]
    return TrayRuntimeSnapshot(
        usage_available=bool(payload.get("usageAvailable")),
        usage_unavailable_reason=_optional_str(payload.get("usageUnavailableReason")),
        overall_used_percent=overall_used_percent,
        overall_seconds_until_reset=overall_seconds_until_reset,
        active_requests=active_requests,
        accounts=accounts,
    )


def _runtime_tooltip_lines(runtime: TrayRuntimeSnapshot | None) -> list[str]:
    if runtime is None:
        return []
    if runtime.usage_available and runtime.overall_used_percent is not None:
        reset = _format_duration(runtime.overall_seconds_until_reset)
        lines = [f"5h 사용 {_format_percent(runtime.overall_used_percent)} · 다음 주기 {reset}"]
    else:
        lines = [runtime.usage_unavailable_reason or "usage unavailable"]
    if runtime.active_requests:
        lines.append(f"현재: {_active_request_label(runtime.active_requests[0])}")
    else:
        lines.append("현재: idle")
    return lines


def _account_usage_menu_labels(runtime: TrayRuntimeSnapshot | None, *, limit: int = 6) -> list[str]:
    if runtime is None:
        return []
    if not runtime.usage_available:
        return [runtime.usage_unavailable_reason or "usage unavailable"]
    labels = []
    for account in runtime.accounts[:limit]:
        used = _format_percent(account.used_percent) if account.used_percent is not None else "unknown"
        reset = _format_duration(account.seconds_until_reset)
        active = account.active_summary or "idle"
        labels.append(f"{account.label}  {used} · {reset} · {active}")
    if len(runtime.accounts) > limit:
        labels.append(f"+{len(runtime.accounts) - limit} more accounts")
    return labels


def _active_request_menu_labels(runtime: TrayRuntimeSnapshot | None, *, limit: int = 3) -> list[str]:
    if runtime is None:
        return ["idle"]
    if not runtime.active_requests:
        return ["idle"]
    labels = [_active_request_label(request) for request in runtime.active_requests[:limit]]
    if len(runtime.active_requests) > limit:
        labels.append(f"+{len(runtime.active_requests) - limit} more active")
    return labels


def _active_request_label(request: TrayActiveRequest) -> str:
    pieces = [request.label, request.model]
    if request.reasoning_effort:
        pieces.append(request.reasoning_effort)
    pieces.append(_format_duration(request.elapsed_seconds))
    return " · ".join(pieces)


def _format_percent(value: float) -> str:
    return f"{value:.0f}%"


def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    value = max(0, int(seconds))
    if value < 60:
        return f"{value}s"
    minutes = value // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remainder = minutes % 60
    if remainder == 0:
        return f"{hours}h"
    return f"{hours}h {remainder}m"


def _optional_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
