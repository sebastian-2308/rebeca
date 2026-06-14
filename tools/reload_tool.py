import importlib


def reload(*modules: str) -> str:
    """Reload Rebeca modules after self-modification.

    Call this AFTER writing/editing any file in the rebeca/ directory
    so the changes take effect immediately.

    Examples:
        reload()              -> reload all tools
        reload("prompts")     -> reload only prompts module
        reload("agent")       -> reload only agent module
    """
    import sys

    base = "rebeca"
    reloaded = []

    if modules:
        targets = [f"{base}.{m}" if not m.startswith(base) else m for m in modules]
    else:
        targets = sorted(
            name for name in sys.modules
            if name.startswith(base) and name != base
        )

    for name in targets:
        if name in sys.modules:
            try:
                importlib.reload(sys.modules[name])
                reloaded.append(name)
            except Exception as e:
                return f"(error reloading {name}: {e})"

    # refresh tool map
    from . import refresh_tools

    refresh_tools()

    if not reloaded:
        return "(no modules to reload)"

    return f"(reloaded: {', '.join(reloaded)})"
