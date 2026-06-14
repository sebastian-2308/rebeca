import importlib
import inspect
from pathlib import Path

TOOLS_DIR = Path(__file__).parent

CORE_TOOLS = {
    "bash": "bash.bash",
    "read": "file_ops.read",
    "write": "file_ops.write",
    "edit": "file_ops.edit",
    "glob": "file_ops.glob",
    "grep": "search.grep",
    "webfetch": "webfetch.webfetch",
}


def discover_tools(force_reload=False):
    tools = {}
    for name, import_path in CORE_TOOLS.items():
        try:
            parts = import_path.split(".")
            mod = importlib.import_module(f".{parts[0]}", __package__)
            if force_reload:
                mod = importlib.reload(mod)
            tools[name] = getattr(mod, parts[1])
        except Exception as e:
            tools[name] = lambda *a, **kw: f"(error loading {name}: {e})"

    for pyfile in sorted(TOOLS_DIR.glob("*.py")):
        if pyfile.name.startswith("_"):
            continue
        modname = pyfile.stem
        if modname in ("bash", "file_ops", "search", "webfetch", "parser", "__init__"):
            continue
        try:
            mod = importlib.import_module(f".{modname}", __package__)
            if force_reload:
                mod = importlib.reload(mod)
            for fname, func in inspect.getmembers(mod, inspect.isfunction):
                if not fname.startswith("_") and fname not in tools:
                    tools[fname] = func
        except Exception:
            pass

    return tools


def refresh_tools():
    return discover_tools(force_reload=True)

from .parser import parse_tool_call, execute_tool, get_tool_map, refresh_tool_map  # noqa: E402
