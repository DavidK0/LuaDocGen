from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from tree_sitter import Language, Parser

# Requires: pip install tree-sitter tree-sitter-lua
import tree_sitter_lua as tslua


@dataclass
class CommentBlock:
    start_line: int
    end_line: int
    text: str


@dataclass
class FunctionInfo:
    kind: str
    name: str
    params: str
    start_line: int
    end_line: int
    comment: Optional[CommentBlock]


def node_text(source: bytes, node) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8")


def line_number(node) -> int:
    # Tree-sitter rows are 0-based
    return node.start_point[0] + 1


def end_line_number(node) -> int:
    return node.end_point[0] + 1


def collect_comment_blocks(root, source: bytes) -> List[CommentBlock]:
    """
    Collect consecutive comment nodes into a single block.
    """
    comments = []

    def walk(node):
        if node.type == "comment":
            comments.append(node)
        for child in node.children:
            walk(child)

    walk(root)
    comments.sort(key=lambda n: (n.start_point[0], n.start_point[1]))

    blocks: List[CommentBlock] = []
    current: List = []

    for comment in comments:
        if not current:
            current = [comment]
            continue

        prev = current[-1]
        # Group consecutive comments, allowing only blank lines between them.
        if comment.start_point[0] <= prev.end_point[0] + 1:
            current.append(comment)
        else:
            blocks.append(build_comment_block(current, source))
            current = [comment]

    if current:
        blocks.append(build_comment_block(current, source))

    return blocks


def build_comment_block(nodes, source: bytes) -> CommentBlock:
    lines = [node_text(source, n) for n in nodes]
    text = "\n".join(lines)
    return CommentBlock(
        start_line=nodes[0].start_point[0] + 1,
        end_line=nodes[-1].end_point[0] + 1,
        text=text,
    )


def find_identifier_like_name(node, source: bytes) -> Optional[str]:
    """
    Best-effort name extraction from various Tree-sitter node shapes.
    This is intentionally defensive because grammar node fields may vary.
    """
    for child in node.children:
        if child.type in {
            "identifier",
            "dot_index_expression",
            "method_index_expression",
            "variable",
        }:
            return node_text(source, child).strip()

    # Fallback: first non-keyword-ish child text
    for child in node.children:
        text = node_text(source, child).strip()
        if text and text not in {"function", "local", "=", "(", ")", "end"}:
            return text
    return None


def find_parameter_list_text(node, source: bytes) -> str:
    for child in node.children:
        if child.type in {"parameters", "parameter_list"}:
            return node_text(source, child).strip()
    return ""


def iter_top_level_statements(root):
    """
    Most Tree-sitter grammars expose top-level statements as children of the root chunk.
    """
    for child in root.children:
        # Skip comments and punctuation-like extras
        if child.type == "comment":
            continue
        yield child


def extract_functions(root, source: bytes, comment_blocks: List[CommentBlock]) -> List[FunctionInfo]:
    functions: List[FunctionInfo] = []

    top_level_nodes = list(iter_top_level_statements(root))

    for node in top_level_nodes:
        name = None
        params = ""
        kind = None

        # Direct function declaration forms, for example:
        #   function foo(...) ... end
        #   local function foo(...) ... end
        if "function" in node.type and node.type != "comment":
            name = find_identifier_like_name(node, source)
            params = find_parameter_list_text(node, source)
            kind = node.type

        # Function assignment forms, for example:
        #   foo = function(...) ... end
        #   local foo = function(...) ... end
        #
        # We look for assignment-ish nodes whose text contains "= function".
        elif "assignment" in node.type or "variable" in node.type:
            text = node_text(source, node)
            if "= function" in text or "=function" in text:
                kind = node.type
                # Very small fallback for POC purposes only
                lhs = text.split("=", 1)[0].strip()
                rhs = text.split("=", 1)[1].strip()
                name = lhs
                if rhs.startswith("function"):
                    open_paren = rhs.find("(")
                    close_paren = rhs.find(")", open_paren)
                    if open_paren != -1 and close_paren != -1:
                        params = rhs[open_paren:close_paren + 1]

        if not name:
            continue

        comment = attach_preceding_comment(
            node=node,
            comment_blocks=comment_blocks,
            top_level_nodes=top_level_nodes,
        )

        functions.append(
            FunctionInfo(
                kind=kind or "unknown",
                name=name,
                params=params,
                start_line=line_number(node),
                end_line=end_line_number(node),
                comment=comment,
            )
        )

    return functions


def attach_preceding_comment(node, comment_blocks, top_level_nodes) -> Optional[CommentBlock]:
    """
    Attach the nearest preceding comment block if no other top-level code node
    sits between that block and this node.
    """
    node_start_row = node.start_point[0]

    candidate = None
    for block in comment_blocks:
        if block.end_line < node_start_row + 1:
            candidate = block
        else:
            break

    if candidate is None:
        return None

    # Barrier rule: if any other top-level node starts after the comment block
    # and before this node, the comment does not belong to this node.
    for other in top_level_nodes:
        if other == node or other.type == "comment":
            continue

        other_start_line = other.start_point[0] + 1
        if candidate.end_line < other_start_line < node_start_row + 1:
            return None

    return candidate


def print_tree(node, source: bytes, indent: int = 0, max_depth: int = 4):
    if indent > max_depth:
        return
    snippet = node_text(source, node).strip().replace("\n", "\\n")
    if len(snippet) > 60:
        snippet = snippet[:57] + "..."
    print("  " * indent + f"{node.type} [{line_number(node)}-{end_line_number(node)}] {snippet}")
    for child in node.children:
        print_tree(child, source, indent + 1, max_depth=max_depth)


def main(lua_path: str):
    source = Path(lua_path).read_bytes()

    lua_lang = Language(tslua.language())
    parser = Parser(lua_lang)
    tree = parser.parse(source)
    root = tree.root_node

    print("=== TREE (truncated) ===")
    print_tree(root, source, max_depth=2)

    print("\n=== COMMENT BLOCKS ===")
    comment_blocks = collect_comment_blocks(root, source)
    for block in comment_blocks:
        print(f"[{block.start_line}-{block.end_line}]")
        print(block.text)
        print()

    print("=== FUNCTIONS ===")
    functions = extract_functions(root, source, comment_blocks)
    for fn in functions:
        print(f"{fn.name} {fn.params}  [{fn.start_line}-{fn.end_line}]  kind={fn.kind}")
        if fn.comment:
            print("  Associated comment:")
            for line in fn.comment.text.splitlines():
                print(f"    {line}")
        else:
            print("  Associated comment: None")
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python ts_lua_poc.py path/to/file.lua")
        raise SystemExit(1)

    main(sys.argv[1])