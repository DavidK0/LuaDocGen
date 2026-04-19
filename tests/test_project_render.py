from docgen.project import build_project_doc
from docgen.render_project_markdown import render_project_markdown


def test_build_project_doc_associates_each_file(tmp_path):
    (tmp_path / "one.lua").write_text("-- One\nfunction one() end\n", encoding="utf-8")
    (tmp_path / "two.lua").write_text("-- Two\nfunction two() end\n", encoding="utf-8")

    project = build_project_doc(tmp_path)

    assert [file_doc.path.name for file_doc in project.files] == ["one.lua", "two.lua"]
    assert all(file_doc.module_comment is not None for file_doc in project.files)


def test_render_project_markdown_includes_summary_and_sections(tmp_path):
    (tmp_path / "one.lua").write_text("-- One\nfunction one() end\n", encoding="utf-8")

    project = build_project_doc(tmp_path)
    output = render_project_markdown(project)

    assert output.startswith(f"# {tmp_path.name} Documentation")
    assert "- Lua files: `1`" in output
    assert "- [`one.lua`](#one-lua) - 1 functions" in output
    assert "## one.lua" in output
    assert "#### `one()`" in output
