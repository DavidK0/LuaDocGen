from __future__ import annotations

import argparse
from pathlib import Path

from .project import build_project_doc
from .render_markdown import render_markdown
from .render_project_markdown import render_project_index, render_project_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Markdown documentation for Lua files.")
    parser.add_argument("path", help="Lua file or directory to document")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file for a single input file, or output directory for an input directory.",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="For directory input, write one combined Markdown file instead of one file per Lua file.",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.path)
    project = build_project_doc(input_path)
    if not project.files:
        parser.error(f"no .lua files found at {input_path}")

    if args.single_file:
        output_path = _single_file_output_path(input_path, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_project_markdown(project), encoding="utf-8")
        print(output_path)
        return 0

    if input_path.is_file():
        doc = project.files[0]
        output_text = render_markdown(doc)
        output_path = _output_path(doc.path, input_path, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(output_path)
        return 0

    output_base = args.output or input_path
    for doc in project.files:
        output_text = render_markdown(doc)
        output_path = _output_path(doc.path, input_path, output_base)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(output_path)

    index_path = output_base / "index.md"
    index_path.write_text(render_project_index(project, output_base), encoding="utf-8")
    print(index_path)
    return 0


def _output_path(lua_file: Path, input_path: Path, output_base: Path | None) -> Path:
    if output_base is None:
        return lua_file.with_suffix(lua_file.suffix + ".md")
    if input_path.is_file():
        return output_base
    relative = lua_file.relative_to(input_path)
    return output_base / relative.with_suffix(relative.suffix + ".md")


def _single_file_output_path(input_path: Path, output: Path | None) -> Path:
    if output is not None:
        return output
    if input_path.is_file():
        return input_path.with_suffix(input_path.suffix + ".md")
    return input_path / "DOCUMENTATION.md"


if __name__ == "__main__":
    raise SystemExit(main())
