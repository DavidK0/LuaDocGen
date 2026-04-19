from __future__ import annotations

from .model import CommentBlock, FileDoc, FunctionSymbol, RequireSymbol


def associate_comments(file_doc: FileDoc, max_blank_lines: int = 1) -> FileDoc:
    """Attach module and function comments using syntax ranges as barriers."""
    attached_ids: set[int] = set()
    code_nodes = sorted(
        [*file_doc.functions, *file_doc.requires],
        key=lambda item: item.range.start_byte,
    )
    top_level_functions = [symbol for symbol in file_doc.functions if not symbol.nested]

    file_doc.module_comment = _module_comment(file_doc.comments, code_nodes, file_doc.source)
    if file_doc.module_comment is not None:
        file_doc.module_comment.attached_to = "<module>"
        attached_ids.add(id(file_doc.module_comment))

    for symbol in sorted(top_level_functions, key=lambda item: item.range.start_byte):
        candidate = _nearest_preceding_unattached_comment(symbol, file_doc.comments, attached_ids)
        if candidate is None:
            continue
        if _can_attach(candidate, symbol, code_nodes, file_doc.source, max_blank_lines):
            symbol.doc_comment = candidate
            candidate.attached_to = symbol.display_name
            attached_ids.add(id(candidate))

    file_doc.orphan_comments = [
        comment for comment in file_doc.comments if id(comment) not in attached_ids
    ]
    return file_doc


def _module_comment(
    comments: list[CommentBlock],
    code_nodes: list[FunctionSymbol | RequireSymbol],
    source: str,
) -> CommentBlock | None:
    if not comments:
        return None
    first_code = min((node.range.start_byte for node in code_nodes), default=len(source))
    candidates = [comment for comment in comments if comment.range.end_byte < first_code]
    if not candidates:
        return None
    first = candidates[0]
    if source[: first.range.start_byte].strip():
        return None
    return first


def _nearest_preceding_unattached_comment(
    symbol: FunctionSymbol,
    comments: list[CommentBlock],
    attached_ids: set[int],
) -> CommentBlock | None:
    preceding = [
        comment
        for comment in comments
        if id(comment) not in attached_ids and comment.range.end_byte < symbol.range.start_byte
    ]
    if not preceding:
        return None
    return max(preceding, key=lambda comment: comment.range.end_byte)


def _can_attach(
    comment: CommentBlock,
    symbol: FunctionSymbol,
    code_nodes: list[FunctionSymbol | RequireSymbol],
    source: str,
    max_blank_lines: int,
) -> bool:
    for node in code_nodes:
        if node is symbol:
            continue
        if comment.range.end_byte < node.range.start_byte < symbol.range.start_byte:
            return False

    between = source[comment.range.end_byte : symbol.range.start_byte]
    if between.strip():
        return False
    return symbol.range.start_line - comment.range.end_line - 1 <= max_blank_lines
