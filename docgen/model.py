from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceRange:
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    start_column: int
    end_column: int


@dataclass
class CommentBlock:
    raw_lines: list[str]
    range: SourceRange
    attached_to: str | None = None

    @property
    def start_line(self) -> int:
        return self.range.start_line

    @property
    def end_line(self) -> int:
        return self.range.end_line

    @property
    def text(self) -> str:
        return "\n".join(self.raw_lines)


@dataclass
class RequireSymbol:
    module: str
    range: SourceRange


@dataclass
class FunctionSymbol:
    name: str
    display_name: str
    params: list[str]
    range: SourceRange
    is_local: bool
    is_method: bool
    form: str
    nested: bool
    doc_comment: CommentBlock | None = None

    @property
    def line(self) -> int:
        return self.range.start_line

    @property
    def end_line(self) -> int:
        return self.range.end_line


@dataclass
class FileDoc:
    path: Path
    source: str
    comments: list[CommentBlock] = field(default_factory=list)
    functions: list[FunctionSymbol] = field(default_factory=list)
    requires: list[RequireSymbol] = field(default_factory=list)
    module_comment: CommentBlock | None = None
    orphan_comments: list[CommentBlock] = field(default_factory=list)


@dataclass
class ProjectDoc:
    root: Path
    files: list[FileDoc] = field(default_factory=list)
