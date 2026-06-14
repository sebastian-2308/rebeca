from __future__ import annotations

import asyncio
import re
import shutil
from datetime import datetime
from typing import ClassVar

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, RichLog, Static, Tabs
from textual.widgets import Tab

from ..config import WORK_DIR
from ..session.manager import SessionManager

COLORS = {
    "user": "bold cyan",
    "assistant": "bold green",
    "tool": "dim yellow",
    "system": "dim italic white",
    "thinking": "yellow",
    "error": "bold red",
    "stream": "italic #7dcfff",
}


def strip_tool_calls(text: str) -> str:
    return re.sub(
        r'```(?:json)?\s*\n?\s*\{[^}]*"tool"[^}]*\}\s*\n?\s*```',
        "",
        text,
    ).strip()


class SessionTab:
    def __init__(self, sid: str, name: str, log: RichLog, inp: Input):
        self.id = sid
        self.name = name
        self.log = log
        self.input = inp


class RebecaApp(App):
    TITLE: ClassVar[str] = "Rebeca"
    CSS: ClassVar[str] = """
    Screen {
        background: #1a1b26;
    }

    Header {
        background: #24253a;
        color: #a9b1d6;
    }

    Footer {
        background: #24253a;
        color: #565f89;
    }

    #main-container {
        layout: vertical;
        height: 100%;
    }

    #tabs-bar {
        background: #1f2135;
        height: 3;
        dock: top;
    }

    Tabs {
        background: #1f2135;
    }

    Tabs Tab {
        background: #1f2135;
        color: #565f89;
        padding: 0 2;
    }

    Tabs Tab.-active {
        background: #24253a;
        color: #7dcfff;
        text-style: bold;
    }

    Tabs Tab:hover {
        background: #2a2c42;
    }

    #chat-area {
        background: #1a1b26;
        height: 1fr;
        margin: 0 1;
    }

    #chat-display {
        height: 1fr;
    }

    RichLog {
        background: #1a1b26;
        color: #c0caf5;
        border: none;
        padding: 0 1;
    }

    #input-container {
        background: #1f2135;
        height: 3;
        dock: bottom;
        padding: 0 1 1 1;
    }

    #message-input {
        background: #24253a;
        color: #c0caf5;
        border: solid #3b4261;
        width: 100%;
    }

    #message-input:focus {
        border: solid #7dcfff;
    }

    #status-bar {
        background: #1f2135;
        color: #565f89;
        height: 1;
        dock: bottom;
        padding: 0 1;
    }

    #sidebar {
        background: #1f2135;
        width: 22;
        dock: left;
        display: none;
    }

    #sidebar.-visible {
        display: block;
    }

    ListView {
        background: #1f2135;
    }

    ListItem {
        background: #1f2135;
        color: #a9b1d6;
        padding: 1;
    }

    ListItem:hover {
        background: #2a2c42;
    }

    ListItem.-active {
        background: #3b4261;
    }

    .label-dim {
        color: #565f89;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+w", "close_session", "Close"),
        Binding("ctrl+l", "toggle_sidebar", "Sessions"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f5", "rename_session", "Rename"),
    ]

    def __init__(self, manager: SessionManager):
        super().__init__()
        self.manager = manager
        self.session_widgets: dict[str, SessionTab] = {}
        self.current_session_id: str | None = None
        self._processing: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Tabs(id="tabs-bar")
            with Container(id="sidebar"):
                yield ListView(id="session-list")
            with Vertical(id="chat-display"):
                pass
            with Container(id="input-container"):
                yield Input(placeholder="Type a message...", id="message-input")
        yield Static(id="status-bar")

    def on_mount(self) -> None:
        self.query_one("#message-input").visible = False
        session = self.manager.create_session("Main")
        self._add_session_tab(session.id, "Main")
        self.current_session_id = session.id
        sid = session.id
        log = self.session_widgets[sid].log
        log.visible = True
        inp = self.session_widgets[sid].input
        inp.visible = True
        log.write(Text(" Rebeca - AI Coding Assistant", style="bold #7dcfff"))
        self.query_one(Tabs).active = f"s_{session.id}"
        log.write(Text(f" Working directory: {WORK_DIR}", style="dim #565f89"))
        log.write(Text(f" Provider: {self.manager.config.provider} | Model: {self.manager.config.model}", style="dim #565f89"))
        log.write(Text("─" * 50, style="dim #3b4261"))
        self._update_status()

    def _add_session_tab(self, sid: str, name: str) -> None:
        tabs = self.query_one(Tabs)
        tab_id = f"s_{sid}"
        tabs.add_tab(Tab(name, id=tab_id))

        log = RichLog(highlight=True, markup=True, wrap=True)
        log.visible = False
        inp = Input(placeholder="Type a message...", id=f"input-{sid}")
        inp.visible = False

        self.session_widgets[sid] = SessionTab(sid, name, log, inp)

        chat = self.query_one("#chat-display")
        chat.mount(log)

        input_container = self.query_one("#input-container")
        input_container.mount(inp, before="#message-input")

    def _switch_to_session(self, sid: str) -> None:
        if sid and sid.startswith("s_"):
            sid = sid[2:]
        if sid == self.current_session_id:
            return

        if self.current_session_id and self.current_session_id in self.session_widgets:
            old = self.session_widgets[self.current_session_id]
            old.log.visible = False
            old.input.visible = False

        self.current_session_id = sid
        if sid in self.session_widgets:
            new = self.session_widgets[sid]
            new.log.visible = True
            new.input.visible = True
            new.input.focus()
        self.manager.switch_session(sid)
        self._update_status()

    def _get_current_widgets(self) -> SessionTab | None:
        if self.current_session_id and self.current_session_id in self.session_widgets:
            return self.session_widgets[self.current_session_id]
        return None

    def _update_status(self) -> None:
        bar = self.query_one("#status-bar")
        session = self.manager.get_active()
        if session:
            total = len(self.manager.sessions)
            idx = list(self.manager.sessions.keys()).index(session.id) + 1 if session.id in self.manager.sessions else 0
            status_text = f" Session {idx}/{total} | {session.name} | {session.status} | Ctrl+N: new | Ctrl+L: list | Ctrl+Q: quit"
        else:
            status_text = " No active session"
        bar.update(Text(status_text, style="dim #565f89"))

    def action_new_session(self) -> None:
        count = len(self.manager.sessions) + 1
        name = f"Session {count}"
        session = self.manager.create_session(name)
        self._add_session_tab(session.id, name)
        self._switch_to_session(session.id)

        tabs = self.query_one(Tabs)
        tabs.active = f"s_{session.id}"

        log = self.session_widgets[session.id].log
        log.write(Text(f"--- New session: {name} ---", style="bold #7dcfff"))
        self._update_status()

    def action_close_session(self) -> None:
        if not self.current_session_id:
            return
        if len(self.manager.sessions) <= 1:
            self.query_one("#status-bar").update(Text(" Cannot close the last session", style="bold red"))
            return

        sid = self.current_session_id
        self.manager.delete_session(sid)

        tab_id = f"s_{sid}"
        tabs = self.query_one(Tabs)
        try:
            tabs.remove_tab(tab_id)
        except Exception:
            pass

        if sid in self.session_widgets:
            sw = self.session_widgets[sid]
            sw.log.remove()
            sw.input.remove()
            del self.session_widgets[sid]

        new_id = self.manager.active_id
        if new_id:
            tabs.active = f"s_{new_id}"
            self._switch_to_session(new_id)

        self._update_status()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.toggle_class("-visible")
        if "-visible" in sidebar.classes:
            self._refresh_session_list()

    def action_rename_session(self) -> None:
        session = self.manager.get_active()
        if not session:
            return
        inp = self.session_widgets[session.id].input
        old_placeholder = inp.placeholder
        inp.placeholder = "Enter new name..."

        def on_submit(msg: Input.Changed) -> None:
            new_name = msg.value.strip()
            if new_name:
                self.manager.rename_session(session.id, new_name)
                tab_id = f"s_{session.id}"
                tabs = self.query_one(Tabs)
                try:
                    tabs.remove_tab(tab_id)
                except Exception:
                    pass
                tabs.add_tab(Tab(new_name, id=tab_id))
                tabs.active = tab_id
                self.session_widgets[session.id].name = new_name
                self._update_status()
            inp.placeholder = old_placeholder
            inp.value = ""
            self._refresh_session_list()

        inp.on_change = on_submit

    def _refresh_session_list(self) -> None:
        lv = self.query_one("#session-list")
        lv.clear()
        for sid, session in self.manager.sessions.items():
            marker = ">" if sid == self.current_session_id else " "
            lv.append(ListItem(Label(f"{marker} {session.name}")))

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        self._switch_to_session(event.tab.id)
        self._refresh_session_list()
        self._update_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._processing:
            return
        if not event.input.id or not event.input.id.startswith("input-"):
            return
        user_text = event.input.value.strip()
        if not user_text:
            return
        event.input.value = ""

        sid = self.current_session_id
        if not sid or sid not in self.session_widgets:
            return

        log = self.session_widgets[sid].log
        log.write(Text(f" You: {user_text}", style=COLORS["user"]))

        self._processing = True
        self._update_status()
        self._process_message(sid, user_text)

    @work(thread=True)
    def _process_message(self, sid: str, user_text: str) -> None:
        def on_update(update: dict) -> None:
            t = update["type"]
            if t == "tool_call":
                self.call_from_thread(self._write_tool_call, sid, update["name"], update["params"])
            elif t == "tool_result":
                self.call_from_thread(self._write_tool_result, sid, update["name"], update["result"])
            elif t == "done_say":
                self.call_from_thread(self._append_response, sid, update["text"])
            elif t == "done":
                pass

        try:
            self.manager.process_message(sid, user_text, on_update=on_update)
        except Exception as e:
            self.call_from_thread(self._append_response, sid, f"Error: {e}")
        finally:
            self.call_from_thread(self._finish_processing)

    def _write_tool_call(self, sid: str, tool_name: str, params: dict) -> None:
        sw = self.session_widgets.get(sid)
        if not sw:
            return
        params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        sw.log.write(Text(f"  \u2699 {tool_name}({params_str})", style=COLORS["tool"]))

    def _write_tool_result(self, sid: str, tool_name: str, result: str) -> None:
        sw = self.session_widgets.get(sid)
        if not sw:
            return
        short = result[:300].replace("\n", " ")
        if len(result) > 300:
            short += "..."
        sw.log.write(Text(f"  \u21b3 {short}", style=COLORS["tool"]))

    def _append_response(self, sid: str, text: str) -> None:
        sw = self.session_widgets.get(sid)
        if not sw:
            return
        sw.log.write(Text(f" Rebeca: {text}", style=COLORS["assistant"]))

    def _finish_processing(self) -> None:
        self._processing = False
        self._update_status()
        if self.current_session_id and self.current_session_id in self.session_widgets:
            self.session_widgets[self.current_session_id].input.focus()
