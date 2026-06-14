import json
import re
from typing import Callable

from . import discover_tools

_TOOL_MAP_CACHE = None


def get_tool_map() -> dict[str, Callable]:
    global _TOOL_MAP_CACHE
    if _TOOL_MAP_CACHE is None:
        _TOOL_MAP_CACHE = discover_tools()
    return _TOOL_MAP_CACHE


def refresh_tool_map() -> dict[str, Callable]:
    global _TOOL_MAP_CACHE
    _TOOL_MAP_CACHE = discover_tools(force_reload=True)
    return _TOOL_MAP_CACHE


def _repair_json(text: str) -> str:
    text = re.sub(r'"""\s*(.*?)\s*"""', lambda m: '"' + m.group(1).replace('"', '\\"').replace('\n', '\\n') + '"', text, flags=re.DOTALL)
    text = re.sub(r"(?<=[^\\])'(?=[^']*')", '"', text)
    return text


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


def parse_tool_call(text: str) -> tuple[str, dict] | None:
    json_str = _extract_json_object(text)
    if not json_str:
        return None

    try:
        obj = json.loads(json_str)
        tool_name = obj.get("tool", "")
        params = obj.get("params", {})
        if not params:
            params = {k: v for k, v in obj.items() if k != "tool"}
        elif isinstance(params, dict):
            for k, v in obj.items():
                if k not in ("tool", "params"):
                    params[k] = v
        return tool_name, params
    except json.JSONDecodeError:
        pass

    repaired = _repair_json(json_str)
    try:
        obj = json.loads(repaired)
        tool_name = obj.get("tool", "")
        params = obj.get("params", {})
        if not params:
            params = {k: v for k, v in obj.items() if k != "tool"}
        elif isinstance(params, dict):
            for k, v in obj.items():
                if k not in ("tool", "params"):
                    params[k] = v
        return tool_name, params
    except json.JSONDecodeError:
        pass

    for pattern in [
        r'(?:"tool"\s*:\s*)"([^"]+)"',
        r"(?:tool\s*:\s*)'([^']+)'",
    ]:
        m = re.search(pattern, json_str)
        if m:
            tool_name = m.group(1)
            text_params = {}
            for param_match in re.finditer(r'(?:"([^"]+)"\s*:\s*)"([^"]*)"', json_str):
                key = param_match.group(1)
                val = param_match.group(2)
                if key != "tool":
                    text_params[key] = val
            if tool_name:
                return tool_name, text_params

    return None


def execute_tool(tool_name: str, params: dict) -> str:
    tool_map = get_tool_map()
    func = tool_map.get(tool_name)
    if func is None:
        tool_map = refresh_tool_map()
        func = tool_map.get(tool_name)
        if func is None:
            return f"(unknown tool: {tool_name})"
    try:
        return func(**params)
    except Exception as e:
        return f"(tool error: {e})"
