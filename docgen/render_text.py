from __future__ import annotations

from .model import FileDoc
from .render_markdown import _clean_comment_line


def render_text(file_doc: FileDoc) -> str:
    lines: list[str] = [str(file_doc.path)]
    if file_doc.module_comment is not None:
        lines.append("")
        lines.extend(_clean_comment_line(line) for line in file_doc.module_comment.raw_lines)
    for symbol in file_doc.functions:
        if symbol.nested:
            continue
        lines.append("")
        lines.append(f"{symbol.display_name}({', '.join(symbol.params)}) [{symbol.line}-{symbol.end_line}]")
        if symbol.doc_comment is not None:
            lines.extend(f"  { _clean_comment_line(line) }" for line in symbol.doc_comment.raw_lines)
    return "\n".join(lines).rstrip() + "\n"

