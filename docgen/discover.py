from __future__ import annotations

from pathlib import Path


DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    "vendor",
    "build",
    "dist",
}


def discover_lua_files(path: str | Path) -> list[Path]:
    root = Path(path)
    if root.is_file():
        return [root] if root.suffix == ".lua" else []

    files: list[Path] = []
    for candidate in root.rglob("*.lua"):
        if any(part in DEFAULT_SKIP_DIRS for part in candidate.parts):
            continue
        files.append(candidate)
    return sorted(files)

