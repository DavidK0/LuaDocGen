from __future__ import annotations

from .model import CommentBlock, FileDoc


def render_markdown(file_doc: FileDoc) -> str:
    return render_markdown_section(file_doc, title=file_doc.path.name, heading_level=1)


def render_markdown_section(file_doc: FileDoc, title: str, heading_level: int = 1) -> str:
    title_marker = "#" * heading_level
    section_marker = "#" * (heading_level + 1)
    function_marker = "#" * (heading_level + 2)
    lines: list[str] = [f"{title_marker} {title}", ""]

    if file_doc.module_comment is not None:
        lines.extend(_render_comment_text(file_doc.module_comment))
        lines.append("")

    if file_doc.requires:
        lines.extend([f"{section_marker} Requires", ""])
        for required in file_doc.requires:
            lines.append(f"- `{required.module}`")
        lines.append("")

    top_level_functions = [symbol for symbol in file_doc.functions if not symbol.nested]
    if top_level_functions:
        lines.extend([f"{section_marker} Functions", ""])
        for symbol in top_level_functions:
            signature = f"{symbol.display_name}({', '.join(symbol.params)})"
            lines.extend([f"{function_marker} `{signature}`", ""])
            if symbol.doc_comment is not None:
                lines.extend(_render_comment_text(symbol.doc_comment))
                lines.append("")
            lines.append(f"- Scope: `{'local' if symbol.is_local else 'global'}`")
            lines.append(f"- Lines: `{symbol.line}-{symbol.end_line}`")
            lines.append("")

    return "\n".join(lines).rstrip()


def _render_comment_text(comment: CommentBlock) -> list[str]:
    return [_clean_comment_line(line) for line in comment.raw_lines]


def _clean_comment_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("--[["):
        stripped = stripped[4:]
    elif stripped.startswith("--"):
        stripped = stripped[2:]
    if stripped.endswith("]]"):
        stripped = stripped[:-2]
    return stripped.lstrip()
