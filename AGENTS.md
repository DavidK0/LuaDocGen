# AGENTS.md

## Project goal

Build a parser-based Lua documentation generator that:

* uses Tree-sitter for syntax-aware analysis
* extracts structure and comments from real-world Lua code
* associates comments with the correct symbols using source locations
* avoids fragile regex or heuristic-based parsing
* produces clean, structured, and extensible documentation output

The system must behave predictably on real Lua code, not just simple cases.

---

## Core architecture

The system is divided into four layers. Maintain strict separation between them:

1. File discovery
2. Source analysis (parsing)
3. Comment-to-symbol association
4. Documentation rendering

Do not merge responsibilities across layers.

---

## Required pipeline

The pipeline must follow this order:

1. Parse source → extract syntax + comments
2. Build structured intermediate representation
3. Associate comments with symbols
4. Render output

Never render directly from parser output.

---

## Data model (required)

All processing must go through a structured intermediate representation.

Use dataclasses (not ad hoc dicts) for core structures:

* CommentBlock
* FunctionSymbol
* FileDoc

This model is the single source of truth between parsing and rendering.

---

## Parsing requirements

Use Tree-sitter for Lua.

The parser must identify:

* function declarations (all Lua forms)
* parameter lists (including multiline)
* local vs global functions
* method syntax (`:` vs `.`)
* assignment-based functions
* nesting (top-level vs nested)
* source ranges (line/byte positions)
* comment positions

Supported function forms include:

* `function foo(a, b) end`
* `local function foo(a, b) end`
* `foo = function(a, b) end`
* `local foo = function(a, b) end`
* `tbl.foo = function(a, b) end`
* `tbl:foo(a, b)`
* `function tbl.foo(a, b) end`
* `function tbl:foo(a, b) end`

Do not approximate these with regex.

---

## Comment handling rules

Comment handling must be location-based, not heuristic.

### Module/file comments

A comment block is a module comment if:

* it appears before the first meaningful code node
* only whitespace or comments precede it

### Function documentation comments

Attach a comment block to a function only if:

* the comment ends before the function begins
* no code node exists between them
* only whitespace/comments are between them
* allow at most one blank line

### Inside-function comments

* Do NOT treat them as documentation for the function

### Block comments

* Preserve structure (paragraphs, line breaks)
* Do not flatten into a single string

---

## Comment association algorithm

Association must be based on syntax boundaries.

For each top-level symbol:

1. Find the nearest preceding unattached comment block
2. Attach it only if no intervening code node exists
3. Treat other comments as orphaned

Explicitly track orphaned comments for debugging.

Avoid “pending comment buffer” logic.

---

## Rendering rules

Rendering must be a separate layer.

* Input: structured model
* Output: text, Markdown, or JSON

Do not mix parsing logic into rendering.

Initial goal: reproduce current text output.

---

## Project structure

Target structure:

```
docgen/
  cli.py
  discover.py
  parser.py
  associate.py
  model.py
  render_text.py
  render_markdown.py
tests/
  fixtures/
  test_parser.py
  test_associate.py
  test_render.py
```

Keep modules focused and small.

---

## Implementation phases

Follow this order strictly:

### Phase 1: Parser

* Parse one file
* Extract syntax + comments
* Output raw structured data

### Phase 2: Association

* Attach comments to symbols
* Identify module comments and orphan comments

### Phase 3: Requires

* Replace regex-based require detection with syntax-aware parsing

### Phase 4: Rendering

* Generate output from structured model

### Phase 5: Enhancements (optional)

* module/table detection
* constants
* Love2D callback grouping
* tag parsing (`@param`, etc.)

Do not implement Phase 5 before earlier phases are stable.

---

## Coding rules

* Prefer clarity over cleverness
* Avoid regex for structural parsing
* Do not introduce new dependencies unless necessary
* Keep experimental code isolated
* Do not rewrite working components without a clear reason

---

## Testing requirements

Tests are required for:

* parser correctness
* comment association correctness
* rendering output

Use fixture Lua files covering:

* all function forms
* block and line comments
* nested functions
* spacing edge cases
* requires inside code vs comments

---

## Definition of done

A task is complete only if:

* the code runs without errors
* the implementation matches the architecture
* behavior is verified on sample Lua files
* tests pass (if applicable)
* no unrelated files were modified

---

## Constraints

* Do not fall back to regex-based parsing
* Do not collapse layers into one script
* Do not attach comments based only on proximity
* Do not flatten structured comment data prematurely

---

## Notes for working in this repo

* `tests/tree_sitter_POC.py` and `tests/lua_test.lua` are experimental and may be replaced
* Prioritize correctness of structure before improving output formatting

---

## Feedback on your project description

Overall, the description in  is unusually solid and already aligned with how Codex works best. A few targeted observations:

1. Strong points

* The enforced separation (parse → associate → render) is exactly what prevents Codex from drifting into messy rewrites.
* The “code node barrier” rule for comments is a key improvement over naive approaches.
* The insistence on an intermediate model is correct and critical.

2. Potential risks / clarifications

* “Allow one blank line” in comment association: this is a policy decision. You may later want this configurable.
* Nested functions: you defined extraction vs rendering policy later, but Codex may still try to filter too early. The AGENTS.md explicitly prevents that.
* Require parsing: good to delay, but Codex may try to “fix” it early unless constrained (now handled).

3. Minor gap

* No explicit CLI behavior defined yet (input paths, output format). Codex will eventually need that to avoid guessing.

4. One practical addition you might consider later

* Define a canonical output example (even small). Codex performs better when it can match a concrete target format.

Nothing in your design is fundamentally off. The main improvement was making the rules enforceable so Codex does not take shortcuts.

## Environment

- Language: Python
- Dependencies installed via: requirements.txt
- Tree-sitter via Python bindings (`tree-sitter`, `tree-sitter-lua`)

## Entry point

Main CLI:
python -m docgen.cli <path>

## Input/output

- Input: .lua file or directory
- Output: documentation file(s) in Markdown
- Default: one output per input file

## Compatibility goal

- First reproduce behavior of generate_documents.py
- Then improve architecture without changing output semantics

## Tests

Run:
pytest

All tests must pass before completion