import fnmatch
import re
from pathlib import Path


def grep(pattern: str, path: str = "", include: str = "") -> str:
    search_path = Path(path) if path else Path.cwd()
    results = []

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"(invalid regex: {e})"

    glob_pattern = f"**/{include}" if include else "**/*"

    try:
        for file_path in sorted(search_path.rglob("*")):
            if not file_path.is_file():
                continue
            if include and not fnmatch.fnmatch(file_path.name, include):
                continue
            try:
                for i, line in enumerate(file_path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{file_path.relative_to(search_path)}:{i}: {line.strip()}")
            except Exception:
                continue
    except Exception as e:
        return f"(error: {e})"

    if not results:
        return "(no matches found)"
    return "\n".join(results[:200])
