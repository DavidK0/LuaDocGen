from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tree_sitter import Language, Node, Parser
import tree_sitter_lua as tslua

from .model import CommentBlock, FileDoc, FunctionSymbol, RequireSymbol, SourceRange


def parse_file(path: str | Path) -> FileDoc:
    file_path = Path(path)
    source_bytes = file_path.read_bytes()
    return parse_source(source_bytes.decode("utf-8"), file_path)


def parse_source(source: str, path: str | Path = "<memory>") -> FileDoc:
    source_bytes = source.encode("utf-8")
    parser = Parser(Language(tslua.language()))
    tree = parser.parse(source_bytes)
    root = tree.root_node

    return FileDoc(
        path=Path(path),
        source=source,
        comments=_collect_comment_blocks(root, source_bytes),
        functions=_collect_functions(root, source_bytes),
        requires=_collect_requires(root, source_bytes),
    )


def node_text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def node_range(node: Node) -> SourceRange:
    return SourceRange(
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        start_column=node.start_point[1],
        end_column=node.end_point[1],
    )


def meaningful_top_level_nodes(root: Node) -> list[Node]:
    return [child for child in root.children if child.type != "comment"]


def _collect_comment_blocks(root: Node, source: bytes) -> list[CommentBlock]:
    comments = [node for node in _walk(root) if node.type == "comment"]
    comments.sort(key=lambda node: node.start_byte)

    blocks: list[CommentBlock] = []
    current: list[Node] = []
    for comment in comments:
        if not current:
            current = [comment]
            continue

        previous = current[-1]
        if comment.start_point[0] <= previous.end_point[0] + 1:
            current.append(comment)
        else:
            blocks.append(_build_comment_block(current, source))
            current = [comment]

    if current:
        blocks.append(_build_comment_block(current, source))
    return blocks


def _build_comment_block(nodes: list[Node], source: bytes) -> CommentBlock:
    raw_lines: list[str] = []
    for node in nodes:
        raw_lines.extend(node_text(source, node).splitlines() or [""])
    return CommentBlock(raw_lines=raw_lines, range=node_range_span(nodes))


def node_range_span(nodes: list[Node]) -> SourceRange:
    first = nodes[0]
    last = nodes[-1]
    return SourceRange(
        start_line=first.start_point[0] + 1,
        end_line=last.end_point[0] + 1,
        start_byte=first.start_byte,
        end_byte=last.end_byte,
        start_column=first.start_point[1],
        end_column=last.end_point[1],
    )


def _collect_functions(root: Node, source: bytes) -> list[FunctionSymbol]:
    functions: list[FunctionSymbol] = []
    for node in _walk(root):
        symbol = _function_from_node(node, source)
        if symbol is not None:
            functions.append(symbol)
    return sorted(functions, key=lambda symbol: symbol.range.start_byte)


def _function_from_node(node: Node, source: bytes) -> FunctionSymbol | None:
    if node.type == "function_declaration":
        name_node = _first_child_of_type(
            node, {"identifier", "dot_index_expression", "method_index_expression"}
        )
        params_node = _first_child_of_type(node, {"parameters"})
        if name_node is None or params_node is None:
            return None
        display_name = node_text(source, name_node).strip()
        return FunctionSymbol(
            name=display_name.replace(":", "."),
            display_name=display_name,
            params=_extract_params(params_node, source),
            range=node_range(node),
            is_local=any(child.type == "local" for child in node.children),
            is_method=name_node.type == "method_index_expression",
            form="declaration",
            nested=_is_nested_function(node),
        )

    assignment = _assignment_node_for_function(node)
    if assignment is None:
        return None

    name_node = _assignment_lhs_name_node(assignment)
    definition = _first_descendant_of_type(assignment, {"function_definition"})
    if name_node is None or definition is None:
        return None

    params_node = _first_child_of_type(definition, {"parameters"})
    if params_node is None:
        return None

    display_name = node_text(source, name_node).strip()
    return FunctionSymbol(
        name=display_name.replace(":", "."),
        display_name=display_name,
        params=_extract_params(params_node, source),
        range=node_range(node),
        is_local=node.type == "variable_declaration",
        is_method=name_node.type == "method_index_expression" or ":" in display_name,
        form="assignment",
        nested=_is_nested_function(node),
    )


def _assignment_node_for_function(node: Node) -> Node | None:
    if node.type == "assignment_statement" and node.parent and node.parent.type == "variable_declaration":
        return None
    if node.type == "assignment_statement" and _direct_function_assignment(node):
        return node
    if node.type == "variable_declaration":
        assignment = _first_child_of_type(node, {"assignment_statement"})
        if assignment is not None and _direct_function_assignment(assignment):
            return assignment
    return None


def _direct_function_assignment(assignment: Node) -> bool:
    expression_list = _first_child_of_type(assignment, {"expression_list"})
    if expression_list is None:
        return False
    expressions = [child for child in expression_list.children if child.is_named]
    return bool(expressions and expressions[0].type == "function_definition")


def _assignment_lhs_name_node(assignment: Node) -> Node | None:
    variable_list = _first_child_of_type(assignment, {"variable_list"})
    if variable_list is None:
        return None
    for child in variable_list.children:
        if child.is_named:
            return child
    return None


def _extract_params(params_node: Node, source: bytes) -> list[str]:
    params: list[str] = []
    for child in params_node.children:
        if child.type in {"identifier", "vararg_expression"}:
            params.append(node_text(source, child).strip())
    return params


def _is_nested_function(node: Node) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type in {"function_declaration", "function_definition"}:
            return True
        parent = parent.parent
    return False


def _collect_requires(root: Node, source: bytes) -> list[RequireSymbol]:
    requires: list[RequireSymbol] = []
    for call in _walk(root):
        if call.type != "function_call":
            continue
        callee = next((child for child in call.children if child.is_named), None)
        if callee is None or node_text(source, callee) != "require":
            continue
        module = _require_module(call, source)
        if module is not None:
            requires.append(RequireSymbol(module=module, range=node_range(call)))
    return requires


def _require_module(call: Node, source: bytes) -> str | None:
    arguments = _first_child_of_type(call, {"arguments"})
    if arguments is None:
        return None
    string_node = _first_descendant_of_type(arguments, {"string"})
    if string_node is None:
        return None
    content = _first_child_of_type(string_node, {"string_content"})
    if content is not None:
        return node_text(source, content)
    return node_text(source, string_node).strip("\"'")


def _walk(node: Node) -> Iterable[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def _first_child_of_type(node: Node, types: set[str]) -> Node | None:
    for child in node.children:
        if child.type in types:
            return child
    return None


def _first_descendant_of_type(node: Node, types: set[str]) -> Node | None:
    for child in _walk(node):
        if child is not node and child.type in types:
            return child
    return None

