from pathlib import Path

from docgen.cli import main
from docgen.discover import discover_lua_files


def test_discover_lua_file_and_directory(tmp_path):
    lua_file = tmp_path / "a.lua"
    txt_file = tmp_path / "a.txt"
    vendor_file = tmp_path / "vendor" / "skip.lua"
    lua_file.write_text("function a() end", encoding="utf-8")
    txt_file.write_text("", encoding="utf-8")
    vendor_file.parent.mkdir()
    vendor_file.write_text("function skip() end", encoding="utf-8")

    assert discover_lua_files(lua_file) == [lua_file]
    assert discover_lua_files(tmp_path) == [lua_file]


def test_cli_writes_markdown_file(tmp_path):
    lua_file = tmp_path / "sample.lua"
    out_file = tmp_path / "sample.md"
    lua_file.write_text("-- Docs\nfunction sample() end\n", encoding="utf-8")

    assert main([str(lua_file), "-o", str(out_file)]) == 0
    assert "# sample.lua" in out_file.read_text(encoding="utf-8")


def test_cli_writes_directory_docs_and_index(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "docs"
    nested = src / "nested"
    nested.mkdir(parents=True)
    (src / "a.lua").write_text("-- A\nfunction a() end\n", encoding="utf-8")
    (nested / "b.lua").write_text("-- B\nfunction b() end\n", encoding="utf-8")

    assert main([str(src), "-o", str(out)]) == 0

    assert "# a.lua" in (out / "a.lua.md").read_text(encoding="utf-8")
    assert "# b.lua" in (out / "nested" / "b.lua.md").read_text(encoding="utf-8")
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "[a.lua](a.lua.md)" in index
    assert "[nested/b.lua](nested/b.lua.md)" in index


def test_cli_writes_combined_project_markdown(tmp_path):
    src = tmp_path / "src"
    out_file = tmp_path / "project.md"
    src.mkdir()
    (src / "a.lua").write_text("-- A\nfunction a() end\n", encoding="utf-8")
    (src / "b.lua").write_text("-- B\nfunction b() end\n", encoding="utf-8")

    assert main([str(src), "--single-file", "-o", str(out_file)]) == 0

    output = out_file.read_text(encoding="utf-8")
    assert output.startswith("# src Documentation")
    assert "- Lua files: `2`" in output
    assert "## a.lua" in output
    assert "## b.lua" in output
    assert "#### `a()`" in output
