from __future__ import annotations

from pathlib import Path

from .model import FileDoc, ProjectDoc
from .render_markdown import render_markdown_section


def format_lines(lines: list[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"

def render_project_markdown(project: ProjectDoc) -> str:
    title = project.root.name if project.root.is_dir() else project.root.name
    lines: list[str] = [f"# {title} Documentation", ""]

    if not project.files:
        lines.append("No Lua files found.")
        return format_lines(lines)

    total_functions = sum(1 for file_doc in project.files for symbol in file_doc.functions if not symbol.nested)
    total_requires = sum(len(file_doc.requires) for file_doc in project.files)

    lines.extend(
        [
            f"- Lua files: `{len(project.files)}`",
            f"- Top-level functions: `{total_functions}`",
            f"- Requires: `{total_requires}`",
            "",
            "## Files",
            "",
        ]
    )

    for file_doc in project.files:
        relative = _relative_path(project.root, file_doc.path)
        function_count = sum(1 for symbol in file_doc.functions if not symbol.nested)
        lines.append(f"- [`{relative}`](#{_anchor(relative)}) - {function_count} functions")

    lines.append("")

    for file_doc in project.files:
        relative = _relative_path(project.root, file_doc.path)
        lines.append(render_markdown_section(file_doc, title=str(relative), heading_level=2).rstrip())
        lines.append("")

    return format_lines(lines)


def render_project_index(project: ProjectDoc, output_root: Path) -> str:
    title = project.root.name if project.root.is_dir() else project.root.name
    lines: list[str] = [f"# {title} Documentation", ""]

    if not project.files:
        lines.append("No Lua files found.")
        return format_lines(lines)

    lines.extend(["## Files", ""])
    for file_doc in project.files:
        relative = _relative_path(project.root, file_doc.path)
        doc_path = output_root / relative.with_suffix(relative.suffix + ".md")
        function_count = sum(1 for symbol in file_doc.functions if not symbol.nested)
        lines.append(f"- [{relative}]({doc_path.relative_to(output_root).as_posix()}) - {function_count} functions")

    return format_lines(lines)


def _relative_path(root: Path, path: Path) -> Path:
    if root.is_file():
        return Path(path.name)
    return path.relative_to(root)


def _anchor(path: Path) -> str:
    text = str(path).lower()
    chars = [char if char.isalnum() else "-" for char in text]
    anchor = "".join(chars).strip("-")
    while "--" in anchor:
        anchor = anchor.replace("--", "-")
    return anchor
