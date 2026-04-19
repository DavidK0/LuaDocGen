from docgen.associate import associate_comments
from docgen.parser import parse_source
from docgen.render_markdown import render_markdown


def test_markdown_renders_from_structured_model():
    source = open("tests/fixtures/all_forms.lua", encoding="utf-8").read()
    doc = associate_comments(parse_source(source, "all_forms.lua"))

    output = render_markdown(doc)

    assert output.startswith("# all_forms.lua")
    assert "## Requires" in output
    assert "- `alpha`" in output
    assert "### `tbl:qux(a, b)`" in output
    assert "Method declaration docs." in output
    assert "### `inner(hidden)`" not in output

