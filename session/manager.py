from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from ..config import Config
from ..llm import LLMClient
from ..prompts import TOOL_DESCRIPTION_PROMPT
from ..tools import parse_tool_call, execute_tool


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = "Session"
    messages: list = field(default_factory=list)
    status: str = "idle"


UpdateCallback = Callable[[dict], None]


class SessionManager:
    def __init__(self, config: Config):
        self.config = config
        self.sessions: dict[str, Session] = {}
        self.active_id: str | None = None
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._llm_cache: dict[str, LLMClient] = {}

    def create_session(self, name: str = "Session") -> Session:
        session = Session(name=name)
        session.messages = [
            {"role": "system", "content": self.config.system_prompt + "\n\n" + TOOL_DESCRIPTION_PROMPT},
        ]
        self.sessions[session.id] = session
        self.active_id = session.id
        return session

    def get_active(self) -> Session | None:
        if self.active_id and self.active_id in self.sessions:
            return self.sessions[self.active_id]
        return None

    def switch_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            self.active_id = session_id
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions and len(self.sessions) > 1:
            del self.sessions[session_id]
            if self.active_id == session_id:
                self.active_id = next(iter(self.sessions.keys()))
            return True
        return False

    def rename_session(self, session_id: str, name: str) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id].name = name
            return True
        return False

    def _get_llm(self, session_id: str) -> LLMClient:
        if session_id not in self._llm_cache:
            self._llm_cache[session_id] = LLMClient(self.config)
        return self._llm_cache[session_id]

    def process_message(
        self,
        session_id: str,
        user_input: str,
        on_update: UpdateCallback | None = None,
    ) -> list[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return [{"role": "assistant", "content": "Session not found"}]

        session.status = "thinking"
        session.messages.append({"role": "user", "content": user_input})

        turn_count = 0
        max_turns = self.config.max_turns
        llm = self._get_llm(session_id)

        while turn_count < max_turns:
            turn_count += 1

            full_text = ""
            for token in llm.send_message_stream(session.messages):
                full_text += token
                if on_update:
                    on_update({"type": "token", "text": token})

            session.messages.append({"role": "assistant", "content": full_text})

            tool_call = parse_tool_call(full_text)

            if tool_call is None:
                # Model didn't use a tool. Remind and loop.
                reminder = "[SYSTEM: You MUST use a tool. Say nothing else. Just output the tool call JSON.]"
                session.messages.append({"role": "user", "content": reminder})
                if on_update:
                    on_update({"type": "tool_result", "name": "_reminder", "result": reminder})
                continue

            tool_name, params = tool_call

            # 'say' tool = final response to user, don't feed back
            if tool_name == "say":
                session.status = "idle"
                text = params.get("text", "")
                if on_update:
                    on_update({"type": "done_say", "text": text})
                return [{"role": "assistant", "content": text}]

            if on_update:
                on_update({"type": "tool_call", "name": tool_name, "params": params})

            result_text = execute_tool(tool_name, params)

            if on_update:
                on_update({"type": "tool_result", "name": tool_name, "result": result_text})

            session.messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}:\n{result_text}"
            })

        session.status = "idle"
        if on_update:
            on_update({"type": "done"})
        return [{"role": "assistant", "content": "(max turns reached)"}]
