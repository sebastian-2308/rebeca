from pathlib import Path


def read(file_path: str, offset: int = 0, limit: int = 2000) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"(file not found: {file_path})"
    if path.is_dir():
        try:
            entries = []
            for p in path.iterdir():
                suffix = "/" if p.is_dir() else ""
                entries.append(f"{p.name}{suffix}")
            return "\n".join(entries)
        except Exception as e:
            return f"(error reading directory: {e})"

    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception as e:
        return f"(error: {e})"

    if offset > 0:
        lines = lines[offset - 1:]
    if len(lines) > limit:
        lines = lines[:limit]
        lines.append("...(truncated)")

    return "".join(
        f"{i + offset + 1}: {line}" if offset > 0 else f"{i + 1}: {line}"
        for i, line in enumerate(lines)
    )


def write(file_path: str, content: str) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
        return f"(written {len(content)} bytes to {file_path})"
    except Exception as e:
        return f"(error: {e})"


def edit(file_path: str, old_string: str, new_string: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"(file not found: {file_path})"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"(error: {e})"

    if old_string not in content:
        return f"(old_string not found in {file_path})"

    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content, encoding="utf-8")
    return f"(edited {file_path})"


def glob(pattern: str, path: str = "") -> str:
    search_path = Path(path) if path else Path.cwd()
    try:
        matches = list(search_path.rglob(pattern))
        if not matches:
            return "(no matches found)"
        return "\n".join(str(m.relative_to(search_path)) for m in sorted(matches))
    except Exception as e:
        return f"(error: {e})"
