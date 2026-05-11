from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app import windows_startup

pytestmark = pytest.mark.unit


@dataclass
class FakeKey:
    path: str

    def __enter__(self) -> FakeKey:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.opened: list[tuple[str, int]] = []

    def OpenKey(self, root: object, path: str, reserved: int = 0, access: int = 0) -> FakeKey:  # noqa: N802
        del root, reserved
        self.opened.append((path, access))
        return FakeKey(path)

    def CreateKey(self, root: object, path: str) -> FakeKey:  # noqa: N802
        del root
        return FakeKey(path)

    def QueryValueEx(self, key: FakeKey, name: str) -> tuple[str, int]:  # noqa: N802
        del key
        try:
            return self.values[name], self.REG_SZ
        except KeyError as exc:
            raise FileNotFoundError(name) from exc

    def SetValueEx(self, key: FakeKey, name: str, reserved: int, value_type: int, value: str) -> None:  # noqa: N802
        del key, reserved
        assert value_type == self.REG_SZ
        self.values[name] = value

    def DeleteValue(self, key: FakeKey, name: str) -> None:  # noqa: N802
        del key
        try:
            del self.values[name]
        except KeyError as exc:
            raise FileNotFoundError(name) from exc


def test_build_tray_startup_command_uses_current_module_entrypoint() -> None:
    command = windows_startup.build_tray_startup_command("C:\\Python313\\pythonw.exe")

    assert command == '"C:\\Python313\\pythonw.exe" -m app.cli tray'


def test_enable_startup_writes_current_user_run_value() -> None:
    registry = FakeRegistry()
    registration = windows_startup.StartupRegistration(command='"pythonw" -m app.cli tray')

    windows_startup.enable_startup(registration, registry=registry)

    assert registry.values[windows_startup.STARTUP_VALUE_NAME] == '"pythonw" -m app.cli tray'


def test_is_startup_enabled_requires_matching_command() -> None:
    registry = FakeRegistry()
    registration = windows_startup.StartupRegistration(command='"pythonw" -m app.cli tray')
    registry.values[windows_startup.STARTUP_VALUE_NAME] = '"other" -m app.cli tray'

    assert windows_startup.is_startup_enabled(registration, registry=registry) is False

    registry.values[windows_startup.STARTUP_VALUE_NAME] = '"pythonw" -m app.cli tray'
    assert windows_startup.is_startup_enabled(registration, registry=registry) is True


def test_disable_startup_removes_value_and_ignores_missing_value() -> None:
    registry = FakeRegistry()
    registration = windows_startup.StartupRegistration(command='"pythonw" -m app.cli tray')
    registry.values[windows_startup.STARTUP_VALUE_NAME] = registration.command

    windows_startup.disable_startup(registration, registry=registry)
    windows_startup.disable_startup(registration, registry=registry)

    assert windows_startup.STARTUP_VALUE_NAME not in registry.values


def test_default_startup_command_prefers_pythonw_on_windows(monkeypatch, tmp_path: Path) -> None:
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_text("", encoding="utf-8")
    pythonw.write_text("", encoding="utf-8")

    monkeypatch.setattr(windows_startup.os, "name", "nt")
    monkeypatch.setattr(windows_startup.sys, "executable", str(python))

    command = windows_startup.build_tray_startup_command()

    assert command == f'"{pythonw}" -m app.cli tray'
