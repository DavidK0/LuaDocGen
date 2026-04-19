from docgen.parser import parse_source


def test_parser_extracts_required_function_forms():
    source = open("tests/fixtures/all_forms.lua", encoding="utf-8").read()
    doc = parse_source(source, "all_forms.lua")

    symbols = {symbol.display_name: symbol for symbol in doc.functions}

    assert list(symbols) == [
        "foo",
        "local_foo",
        "foo_assigned",
        "local_assigned",
        "tbl.foo",
        "tbl.baz",
        "tbl:qux",
        "outer",
        "inner",
        "undocumented",
        "block_documented",
    ]
    assert symbols["local_foo"].params == ["x", "y"]
    assert symbols["local_foo"].is_local is True
    assert symbols["local_assigned"].is_local is True
    assert symbols["tbl:qux"].name == "tbl.qux"
    assert symbols["tbl:qux"].is_method is True
    assert symbols["inner"].nested is True
    assert symbols["outer"].nested is False


def test_parser_extracts_comments_and_requires_syntax_aware():
    source = open("tests/fixtures/all_forms.lua", encoding="utf-8").read()
    doc = parse_source(source, "all_forms.lua")

    assert [required.module for required in doc.requires] == ["alpha", "beta"]
    assert any("Block docs." in comment.text for comment in doc.comments)
