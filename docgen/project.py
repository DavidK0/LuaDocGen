from __future__ import annotations

from pathlib import Path

from .associate import associate_comments
from .discover import discover_lua_files
from .model import ProjectDoc
from .parser import parse_file


def build_project_doc(path: str | Path) -> ProjectDoc:
    root = Path(path)
    files = [associate_comments(parse_file(lua_file)) for lua_file in discover_lua_files(root)]
    return ProjectDoc(root=root, files=files)
