from docgen.associate import associate_comments
from docgen.parser import parse_source


def _doc():
    source = open("tests/fixtures/all_forms.lua", encoding="utf-8").read()
    return associate_comments(parse_source(source, "all_forms.lua"))


def test_association_attaches_module_and_function_comments():
    doc = _doc()
    symbols = {symbol.display_name: symbol for symbol in doc.functions}

    assert doc.module_comment is not None
    assert "Module comment" in doc.module_comment.text
    assert symbols["foo"].doc_comment is not None
    assert "Updates top-level state." in symbols["foo"].doc_comment.text
    assert symbols["local_foo"].doc_comment is not None
    assert symbols["block_documented"].doc_comment is not None
    assert "Keep paragraphs." in symbols["block_documented"].doc_comment.text


def test_association_respects_code_barriers_and_nested_comments():
    doc = _doc()
    symbols = {symbol.display_name: symbol for symbol in doc.functions}

    assert symbols["undocumented"].doc_comment is None
    assert symbols["inner"].doc_comment is None
    orphan_text = "\n".join(comment.text for comment in doc.orphan_comments)
    assert "inside-function comment" in orphan_text
    assert "Orphan because code is between it" in orphan_text

