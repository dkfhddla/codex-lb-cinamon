from __future__ import annotations

import importlib
import sys
import warnings
from threading import Thread
from typing import Any, cast

from app.menubar_runtime import (
    MenuBarRuntimeOptions,
    MenuBarRuntimeStatus,
    dashboard_page_url,
    start_menu_bar_runtime,
    status_from_options,
    stop_menu_bar_runtime,
    stopped_runtime_snapshot,
)
from app.menubar_summary import (
    AccountMenuCard,
    MenuBarConfig,
    MenuBarSnapshot,
    fetch_menu_bar_snapshot,
)


def run_menu_bar_app(config: MenuBarConfig, *, runtime_options: MenuBarRuntimeOptions | None = None) -> None:
    if sys.platform != "darwin":
        raise SystemExit("The macOS menu bar app is only supported on macOS.")

    try:
        _run_cocoa_app(config, runtime_options)
    except ImportError as exc:
        raise SystemExit(
            "The macOS menu bar app requires PyObjC. Install dependencies with `uv sync` and try again."
        ) from exc


def _run_cocoa_app(config: MenuBarConfig, runtime_options: MenuBarRuntimeOptions | None) -> None:
    appkit = importlib.import_module("AppKit")
    foundation = importlib.import_module("Foundation")
    objc = importlib.import_module("objc")
    app_helper = importlib.import_module("PyObjCTools.AppHelper")
    warnings.filterwarnings("ignore", category=cast(type[Warning], getattr(objc, "ObjCPointerWarning")))

    NSApplication = getattr(appkit, "NSApplication")
    NSApplicationActivationPolicyAccessory = getattr(appkit, "NSApplicationActivationPolicyAccessory")
    NSButton = getattr(appkit, "NSButton")
    NSColor = getattr(appkit, "NSColor")
    NSFont = getattr(appkit, "NSFont")
    NSMenu = getattr(appkit, "NSMenu")
    NSMenuItem = getattr(appkit, "NSMenuItem")
    NSStatusBar = getattr(appkit, "NSStatusBar")
    NSTextField = getattr(appkit, "NSTextField")
    NSView = getattr(appkit, "NSView")
    NSVariableStatusItemLength = getattr(appkit, "NSVariableStatusItemLength")
    NSWorkspace = getattr(appkit, "NSWorkspace")
    NSMakeRect = getattr(foundation, "NSMakeRect")
    NSURL = getattr(foundation, "NSURL")
    NSObject = getattr(foundation, "NSObject")
    NSTimer = getattr(foundation, "NSTimer")
    call_after = getattr(app_helper, "callAfter")
    run_event_loop = getattr(app_helper, "runEventLoop")
    objc_super = getattr(objc, "super")

    def add_action(controller: Any, title: str, action: str) -> None:
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
        item.setTarget_(controller)
        controller.menu.addItem_(item)

    content_width = 340.0

    def add_view_item(menu: Any, view: Any) -> None:
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
        item.setView_(view)
        menu.addItem_(item)

    def make_account_card_view(controller: Any, card: AccountMenuCard, index: int) -> Any:
        width = content_width
        height = 158.0
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        view.setWantsLayer_(True)
        view.layer().setCornerRadius_(10)
        view.layer().setBorderWidth_(1)
        view.layer().setBorderColor_(NSColor.separatorColor().colorWithAlphaComponent_(0.55).CGColor())
        view.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())

        title = make_label(card.title, 14, True)
        title.setFrame_(NSMakeRect(14, 124, 190, 20))
        view.addSubview_(title)

        subtitle = make_label(card.subtitle, 12, False)
        subtitle.setTextColor_(NSColor.secondaryLabelColor())
        subtitle.setFrame_(NSMakeRect(14, 104, 150, 18))
        view.addSubview_(subtitle)

        status = make_status_badge(card.status_label)
        status.setFrame_(NSMakeRect(width - 106, 122, 90, 24))
        view.addSubview_(status)

        if card.is_current:
            current = make_label("Current", 10, True)
            current.setTextColor_(NSColor.systemBlueColor())
            current.setFrame_(NSMakeRect(width - 86, 101, 70, 16))
            view.addSubview_(current)

        if card.shows_quota:
            add_usage_bar(view, "5h", card.primary_percent, card.primary_reset, 14, 52)
            add_usage_bar(view, "Weekly", card.secondary_percent, card.secondary_reset, 176, 52)
        else:
            platform_note = make_label("Platform fallback for compatible API routes", 11, False)
            platform_note.setTextColor_(NSColor.secondaryLabelColor())
            platform_note.setFrame_(NSMakeRect(14, 69, width - 28, 16))
            view.addSubview_(platform_note)

        separator = NSView.alloc().initWithFrame_(NSMakeRect(14, 39, width - 28, 1))
        separator.setWantsLayer_(True)
        separator.layer().setBackgroundColor_(NSColor.separatorColor().colorWithAlphaComponent_(0.75).CGColor())
        view.addSubview_(separator)

        details = NSButton.buttonWithTitle_target_action_("Details", controller, "openAccountDetails:")
        details.setBordered_(False)
        details.setTag_(index)
        details.setFrame_(NSMakeRect(9, 9, 74, 22))
        view.addSubview_(details)
        return view

    def make_overview_view(rows: tuple[tuple[str, str], ...]) -> Any:
        row_map = dict(rows)
        width = content_width
        height = 126.0
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

        heading = make_label("Overview", 11, True)
        heading.setTextColor_(NSColor.secondaryLabelColor())
        heading.setFrame_(NSMakeRect(14, 102, width - 28, 16))
        view.addSubview_(heading)

        left_items = (
            ("5h", row_map.get("5h remaining", "--")),
            ("7d", row_map.get("7d remaining", "--")),
            ("Requests", row_map.get("Requests", "--")),
            ("Tokens", row_map.get("Tokens", "--")),
        )
        right_items = (
            ("Cost", row_map.get("Cost", "--")),
            ("Error", row_map.get("Error rate", "--")),
            ("Accounts", row_map.get("Active accounts", "--")),
            ("Current", row_map.get("Current", "--")),
        )
        add_info_column(view, left_items, 14, 76)
        add_info_column(view, right_items, 176, 76)

        routing = make_label(f"Routing: {row_map.get('Routing', '--')}", 11, False)
        routing.setTextColor_(NSColor.secondaryLabelColor())
        routing.setFrame_(NSMakeRect(14, 6, width - 28, 14))
        view.addSubview_(routing)
        return view

    def make_runtime_view(status: MenuBarRuntimeStatus, error: str) -> Any:
        width = content_width
        height = 80.0 if error else 64.0
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

        heading = make_label("Server", 11, True)
        heading.setTextColor_(NSColor.secondaryLabelColor())
        heading.setFrame_(NSMakeRect(14, height - 24, width - 28, 16))
        view.addSubview_(heading)

        status_text = "Running" if status.running else "Stopped"
        if status.stale_metadata_removed:
            status_text = "Stopped (stale PID removed)"
        pid_text = "--" if status.pid is None else str(status.pid)
        add_info_column(
            view,
            (
                ("Status", status_text),
                ("PID", pid_text),
                ("Port", str(status.port)),
            ),
            14,
            height - 44,
        )
        log = make_label(str(status.log_file), 10, False)
        log.setTextColor_(NSColor.secondaryLabelColor())
        log.setFrame_(NSMakeRect(176, height - 44, 150, 14))
        view.addSubview_(log)
        if error:
            error_label = make_label(error, 10, False)
            error_label.setTextColor_(NSColor.systemRedColor())
            error_label.setFrame_(NSMakeRect(14, 8, width - 28, 14))
            view.addSubview_(error_label)
        return view

    def add_info_column(view: Any, items: tuple[tuple[str, str], ...], x: float, y: float) -> None:
        for index, (label, value) in enumerate(items):
            row_y = y - (index * 17)
            label_view = make_label(label, 11, False)
            label_view.setTextColor_(NSColor.secondaryLabelColor())
            label_view.setFrame_(NSMakeRect(x, row_y, 64, 14))
            view.addSubview_(label_view)

            value_view = make_label(value, 11, True)
            value_view.setTextColor_(NSColor.labelColor())
            value_view.setFrame_(NSMakeRect(x + 65, row_y, 78, 14))
            view.addSubview_(value_view)

    def add_usage_bar(
        view: Any,
        label: str,
        percent: int | None,
        reset: str,
        x: float,
        y: float,
    ) -> None:
        color = quota_color(percent)
        text = make_label(label, 12, False)
        text.setTextColor_(NSColor.secondaryLabelColor())
        text.setFrame_(NSMakeRect(x, y + 28, 70, 18))
        view.addSubview_(text)

        value = make_label("--" if percent is None else f"{percent}%", 12, True)
        value.setTextColor_(color)
        value.setFrame_(NSMakeRect(x + 116, y + 28, 36, 18))
        view.addSubview_(value)

        track_width = 142.0
        track = NSView.alloc().initWithFrame_(NSMakeRect(x, y + 17, track_width, 5))
        track.setWantsLayer_(True)
        track.layer().setCornerRadius_(2.5)
        track.layer().setBackgroundColor_(color.colorWithAlphaComponent_(0.16).CGColor())
        view.addSubview_(track)

        if percent is not None and percent > 0:
            fill_width = max(4.0, track_width * (min(percent, 100) / 100))
            fill = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, fill_width, 5))
            fill.setWantsLayer_(True)
            fill.layer().setCornerRadius_(2.5)
            fill.layer().setBackgroundColor_(color.CGColor())
            track.addSubview_(fill)

        reset_label = make_label(f"◷ {reset}", 11, False)
        reset_label.setTextColor_(NSColor.secondaryLabelColor())
        reset_label.setFrame_(NSMakeRect(x, y - 4, 142, 16))
        view.addSubview_(reset_label)

    def make_status_badge(status_label: str) -> Any:
        color = status_color(status_label)
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 90, 24))
        view.setWantsLayer_(True)
        view.layer().setCornerRadius_(12)
        view.layer().setBackgroundColor_(color.colorWithAlphaComponent_(0.12).CGColor())
        view.layer().setBorderWidth_(1)
        view.layer().setBorderColor_(color.colorWithAlphaComponent_(0.28).CGColor())

        label = make_label(f"• {status_label}", 11, True)
        label.setAlignment_(2)
        label.setTextColor_(color)
        label.setFrame_(NSMakeRect(8, 4, 74, 16))
        view.addSubview_(label)
        return view

    def make_label(text: str, size: float, bold: bool) -> Any:
        label = NSTextField.labelWithString_(text)
        font = NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
        label.setFont_(font)
        return label

    def status_color(status_label: str) -> Any:
        if status_label == "Active":
            return NSColor.systemGreenColor()
        if status_label in {"Limited", "Exceeded"}:
            return NSColor.systemRedColor()
        if status_label == "Paused":
            return NSColor.systemOrangeColor()
        return NSColor.secondaryLabelColor()

    def quota_color(percent: int | None) -> Any:
        if percent is None:
            return NSColor.secondaryLabelColor()
        if percent >= 70:
            return NSColor.systemGreenColor()
        if percent >= 30:
            return NSColor.systemOrangeColor()
        return NSColor.systemRedColor()

    def details_url(config: MenuBarConfig, card: AccountMenuCard) -> str:
        return config.base_url.rstrip("/") + card.details_path

    class MenuBarController(NSObject):
        def init(self) -> Any:
            self = objc_super(MenuBarController, self).init()
            if self is None:
                return None
            self.config = config
            self.runtime_options = runtime_options
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            self.menu = NSMenu.alloc().init()
            self.status_item.setMenu_(self.menu)
            self.status_item.button().setTitle_("5h --")
            self._timer = None
            self._refresh_in_progress = False
            self._detail_urls = []
            self._runtime_status = None
            self._runtime_error = ""
            self._start_on_launch_attempted = False
            self.applySnapshot_(MenuBarSnapshot(title="5h --", rows=(("Status", "Loading..."),)))
            return self

        def start(self) -> None:
            self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                float(self.config.refresh_interval_seconds),
                self,
                "refreshNow:",
                None,
                True,
            )
            if self.runtime_options is not None and self.runtime_options.start_on_launch:
                self._start_on_launch_attempted = True
                self.startServer_(None)
                return
            self.refreshNow_(None)

        def refreshNow_(self, _sender: object) -> None:
            if self._refresh_in_progress:
                return
            self._refresh_in_progress = True

            def worker() -> None:
                if self.runtime_options is not None:
                    status = status_from_options(self.runtime_options)
                    self._runtime_status = status
                    if not status.running:
                        call_after(self.applySnapshot_, stopped_runtime_snapshot(status))
                        return
                snapshot = fetch_menu_bar_snapshot(self.config)
                call_after(self.applySnapshot_, snapshot)

            Thread(target=worker, daemon=True).start()

        def openDashboard_(self, _sender: object) -> None:
            base_url = self.config.base_url
            if self._runtime_status is not None:
                base_url = self._runtime_status.dashboard_url
            NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(dashboard_page_url(base_url)))

        def openAccountDetails_(self, sender: Any) -> None:
            tag = int(sender.tag())
            if tag < 0 or tag >= len(self._detail_urls):
                return
            NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(self._detail_urls[tag]))

        def openLog_(self, _sender: object) -> None:
            if self._runtime_status is None:
                return
            NSWorkspace.sharedWorkspace().openURL_(NSURL.fileURLWithPath_(str(self._runtime_status.log_file)))

        def startServer_(self, _sender: object) -> None:
            if self.runtime_options is None or self._refresh_in_progress:
                return
            self._refresh_in_progress = True

            def worker() -> None:
                try:
                    self._runtime_error = ""
                    status = status_from_options(self.runtime_options)
                    if not status.running:
                        start_menu_bar_runtime(self.runtime_options)
                except Exception as exc:  # pragma: no cover - surfaced in menu UI
                    self._runtime_error = str(exc)
                finally:
                    self._refresh_in_progress = False
                    call_after(self.refreshNow_, None)

            Thread(target=worker, daemon=True).start()

        def stopServer_(self, _sender: object) -> None:
            if self.runtime_options is None or self._refresh_in_progress:
                return
            self._refresh_in_progress = True

            def worker() -> None:
                try:
                    self._runtime_error = ""
                    stop_menu_bar_runtime(self.runtime_options)
                except Exception as exc:  # pragma: no cover - surfaced in menu UI
                    self._runtime_error = str(exc)
                finally:
                    self._refresh_in_progress = False
                    call_after(self.refreshNow_, None)

            Thread(target=worker, daemon=True).start()

        def quit_(self, _sender: object) -> None:
            NSApplication.sharedApplication().terminate_(None)

        def applySnapshot_(self, snapshot: MenuBarSnapshot) -> None:
            self._refresh_in_progress = False
            self.status_item.button().setTitle_(snapshot.title)
            self.menu.removeAllItems()
            self._detail_urls = []
            for card in snapshot.account_cards:
                add_view_item(self.menu, make_account_card_view(self, card, len(self._detail_urls)))
                self._detail_urls.append(details_url(self.config, card))
            if snapshot.account_cards:
                self.menu.addItem_(NSMenuItem.separatorItem())
            add_view_item(self.menu, make_overview_view(snapshot.rows))
            if self.runtime_options is not None:
                self._runtime_status = status_from_options(self.runtime_options)
                self.menu.addItem_(NSMenuItem.separatorItem())
                add_view_item(self.menu, make_runtime_view(self._runtime_status, self._runtime_error))
                self.menu.addItem_(NSMenuItem.separatorItem())
                add_action(self, "Start Server", "startServer:")
                add_action(self, "Stop Server", "stopServer:")
                add_action(self, "Open Log", "openLog:")
            self.menu.addItem_(NSMenuItem.separatorItem())
            add_action(self, "Refresh Now", "refreshNow:")
            add_action(self, "Open Dashboard", "openDashboard:")
            self.menu.addItem_(NSMenuItem.separatorItem())
            add_action(self, "Quit", "quit:")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = MenuBarController.alloc().init()
    app.setDelegate_(controller)
    controller.start()
    run_event_loop()
