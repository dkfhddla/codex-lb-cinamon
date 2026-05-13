from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE_NAME = "codex-lb-cinamon-tray"
_LOCAL_PATH = type(Path())


class _RegistryKey(Protocol):
    def __enter__(self) -> _RegistryKey: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...


class _Registry(Protocol):
    HKEY_CURRENT_USER: object
    KEY_READ: int
    KEY_SET_VALUE: int
    REG_SZ: int

    def OpenKey(self, root: object, path: str, reserved: int = 0, access: int = 0) -> _RegistryKey: ...  # noqa: N802

    def CreateKey(self, root: object, path: str) -> _RegistryKey: ...  # noqa: N802

    def QueryValueEx(self, key: Any, name: str) -> tuple[str, int]: ...  # noqa: N802

    def SetValueEx(self, key: Any, name: str, reserved: int, value_type: int, value: str) -> None: ...  # noqa: N802

    def DeleteValue(self, key: Any, name: str) -> None: ...  # noqa: N802


@dataclass(frozen=True, slots=True)
class StartupRegistration:
    command: str
    value_name: str = STARTUP_VALUE_NAME


def build_tray_startup_command(python_executable: str | None = None) -> str:
    executable = python_executable or _default_tray_python_executable()
    return f'"{executable}" -m app.cli tray'


def _default_tray_python_executable() -> str:
    executable = _LOCAL_PATH(sys.executable)
    if os.name == "nt" and executable.name.lower() == "python.exe":
        pythonw = executable.with_name("pythonw.exe")
        if pythonw.exists():
            return str(pythonw)
    return str(executable)


def default_startup_registration() -> StartupRegistration:
    return StartupRegistration(command=build_tray_startup_command())


def is_startup_enabled(registration: StartupRegistration | None = None, *, registry: _Registry | None = None) -> bool:
    reg = registry or _import_winreg()
    target = registration or default_startup_registration()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, reg.KEY_READ) as key:
            value, _value_type = reg.QueryValueEx(key, target.value_name)
    except FileNotFoundError:
        return False
    return value == target.command


def enable_startup(registration: StartupRegistration | None = None, *, registry: _Registry | None = None) -> None:
    reg = registry or _import_winreg()
    target = registration or default_startup_registration()
    with reg.CreateKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH) as key:
        reg.SetValueEx(key, target.value_name, 0, reg.REG_SZ, target.command)


def disable_startup(registration: StartupRegistration | None = None, *, registry: _Registry | None = None) -> None:
    reg = registry or _import_winreg()
    target = registration or default_startup_registration()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, reg.KEY_SET_VALUE) as key:
            reg.DeleteValue(key, target.value_name)
    except FileNotFoundError:
        return


def _import_winreg() -> _Registry:
    import winreg

    return cast(_Registry, winreg)
