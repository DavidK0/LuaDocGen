## Goal

A parser-based documentation generator that behaves predictably on real Lua code that:
* parses Lua source into syntax structure
* collects comments
* associates comments with the correct declarations using source locations
* supports Lua forms without fragile heuristics
* produces clean, rich documentation output
* uses tree-sitter for sytax-aware documentation generation

---

## What the architecture should look like

The architecture should be split into four layers:
1. **File discovery**
2. **Source analysis**
3. **Comment-to-symbol association**
4. **Documentation rendering**

### 1. File discovery

Responsibilities:
* walk the project tree
* collect `.lua` files
* normalize relative paths
* skip generated/vendor directories if desired

### 2. Source analysis

You want a parser that can tell:
* where a function declaration begins
* where its parameter list is
* whether it is local/global/table-assigned/method syntax
* whether it is nested or top-level
* where comments sit relative to it

### 3. Comment-to-symbol association

Responsibilities:
* identify top-of-file/module comments
* identify doc comments that belong to functions
* ignore comments inside function bodies unless explicitly enabled
* optionally support inline trailing comments
* preserve block comment formatting

### 4. Documentation rendering

Responsibilities:
* build a structured intermediate representation
* output plain text, Markdown, JSON, or other formats
* optionally group symbols by module/table/class-like namespace

---

## The data model you should target

Do not render directly from parser output. First build a structured representation.

Something like this:

```python
{
    "file": "src/player.lua",
    "module_comment": [...],
    "requires": [...],
    "symbols": [
        {
            "kind": "function",
            "name": "Player.update",
            "display_name": "Player:update",
            "scope": "top_level",
            "local": False,
            "params": ["dt"],
            "returns": None,
            "line": 42,
            "end_line": 57,
            "doc_comments": [...],
            "inline_comment": None,
            "nested": False,
        }
    ]
}
```

This intermediate model is important because:

* parsing rules stay separate from formatting rules
* you can later emit Markdown/HTML/JSON without rewriting extraction
* testing becomes much easier

---

## What features the parser-based rewrite should support

At minimum, the rewrite should support these function forms:

```lua
function foo(a, b) end
local function foo(a, b) end
foo = function(a, b) end
local foo = function(a, b) end
tbl.foo = function(a, b) end
tbl:foo(a, b)
function tbl.foo(a, b) end
function tbl:foo(a, b) end
```

It should also correctly identify:

* top-level vs nested functions
* method syntax using `:`
* local vs non-local functions
* multiline parameter lists
* comments before functions even if separated by a small amount of whitespace
* block comments without flattening them into a single line

Optional but valuable:

* detect tables/modules
* document constants
* detect returned module tables
* recognize Love2D callbacks specially (`love.load`, `love.update`, `love.draw`, etc.)

---

## Comment association rules for the rewrite

Define the rules explicitly.

### Module/file comments

Treat a comment block as a file/module comment if:

* it appears before the first meaningful code node
* only whitespace or comments precede it

### Function doc comments

Attach a comment block to a function if:
* the comment ends before the function starts
* there is no other code node between them
* only whitespace/comments are between them
* allow one blank line between comment and function

### Comments inside function bodies

Do not treat them as documentation for the containing function

### Block comments

Preserve their paragraph structure instead of turning them into one sentence.
For example, store them as raw lines or paragraphs, not as a single flattened string.

---

## Parser: Tree-sitter for Lua

Tree-sitter gives:
* a real syntax tree
* byte/point ranges for nodes
* robust parsing for incomplete or messy files
* the ability to separately scan comments and match them by location

## Recommended rewrite strategy

I would structure the rewrite in phases.

## Phase 1: Build a syntax-backed extractor

Create a new module, something like:

```python
analyzer.py
```

Its job:

* parse one Lua file
* return a structured model of code declarations and comments

Do not generate docs yet. Just return extracted data.

Core outputs:

* file/module comment blocks
* require statements
* function declarations
* source ranges
* raw comments with positions

At this stage, success means:

* one file in, one structured object out

---

## Phase 2: Build a comment association engine

Create a second module, something like:

```python
association.py
```

Input:

* syntax nodes
* comment blocks
* file text

Output:

* symbols with attached documentation

This stage should answer questions like:

* which comment block belongs to which function?
* which comments are module-level?
* which comments are orphaned?

It is worth explicitly representing orphaned comments for debugging.

---

## Phase 3: Replace raw regex require extraction

Your current `require` extraction is separate and regex-based. You can keep it temporarily, but ideally this also becomes syntax-aware.

Detect patterns like:

```lua
require "mod"
require("mod")
local x = require("mod")
```

AST-based detection avoids false positives inside comments and strings.

---

## Phase 4: Build a renderer layer

Create something like:

```python
render_text.py
render_markdown.py
```

These should consume the structured model and format it.

This gives you flexibility:

* current `DOCUMENTATION.txt`
* a nicer `DOCUMENTATION.md`
* machine-readable JSON for future tooling

---

## Phase 5: Add richer symbol understanding

Once function extraction is stable, expand the model.

Possible additions:

* module name inference from file path or returned table
* table fields/constants
* “class-like” method grouping
* callback grouping for Love2D lifecycle functions
* tag parsing in comments (`@param`, `@return`, `@private`, etc.)

This should come after the parser rewrite, not before.

---

## Concrete internal representation

I would use dataclasses instead of plain dicts.

Example:

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CommentBlock:
    kind: str              # "line" or "block"
    start_line: int
    end_line: int
    text: str
    lines: List[str] = field(default_factory=list)

@dataclass
class FunctionSymbol:
    name: str
    display_name: str
    params: List[str]
    start_line: int
    end_line: int
    is_local: bool
    is_method: bool
    scope: str             # "top_level" or "nested"
    doc_comment: Optional[CommentBlock] = None
    inline_comment: Optional[str] = None

@dataclass
class FileDoc:
    path: str
    module_comment: Optional[CommentBlock]
    requires: List[str]
    functions: List[FunctionSymbol]
    orphan_comments: List[CommentBlock] = field(default_factory=list)
```

This will make the system much easier to reason about than nested ad hoc dicts.

---

## How the comment matching algorithm should work

This part matters more than the renderer.

A good approach is:

1. Parse all syntax nodes with source ranges.
2. Collect all comment blocks with source ranges.
3. Build a list of “documentable top-level symbols.”
4. For each symbol, find the nearest preceding unattached comment block.
5. Attach it only if:

   * the comment ends before the symbol starts
   * only whitespace/comments lie between them
   * no other top-level code node is between them

This “code node barrier” rule is much stronger than your current pending-comment buffer approach.

It means the association is based on syntax regions, not text accidents.

---

## How to preserve comment formatting

Preserve lines and paragraphs.

For block comments:
* strip only the outer delimiters
* normalize indentation
* keep paragraph breaks

For line comments:
* keep them as a consecutive block
* join into a paragraph only at render time if desired

That lets you render:
* as bullets
* as paragraphs
* as tag-aware sections later

---

## What to do about nested functions

You need a policy. I would recommend:

* extract all function nodes
* mark whether they are top-level or nested
* render only top-level by default
* allow an option like `--include-nested`

That gives flexibility without cluttering normal output.

---

## What to do about tags like `@param`

The parser should not interpret tags during extraction. That belongs in a doc-comment parser layer after comment association.

Pipeline:
* parse code
* attach comment block to symbol
* parse comment text into structured fields

That way a comment like:

```lua
-- Moves the player.
-- @param dt Delta time in seconds.
-- @return nil
```

can later become:

```python
{
    "summary": "Moves the player.",
    "params": [{"name": "dt", "description": "Delta time in seconds."}],
    "returns": "nil"
}
```

But do this after the parser rewrite is working.

---

## Testing plan

A parser-based rewrite needs tests from the start.

You should create fixture `.lua` files covering:

* top-of-file comments
* single-line function comments
* block comments
* multiline signatures
* local functions
* assigned functions
* method syntax with `:`
* nested functions
* inline comments
* comments separated by blank lines
* unrelated comments between symbols
* requires in code vs comments vs strings

Then test both:

* extraction correctness
* rendered output correctness

The current script is small enough that you can build a strong test suite quickly.

---

## Suggested directory structure for the rewrite

Something like this:

```text
docgen/
  __init__.py
  cli.py
  discover.py
  parser.py
  comments.py
  associate.py
  model.py
  render_text.py
  render_markdown.py
tests/
  fixtures/
    basic.lua
    methods.lua
    nested.lua
    multiline.lua
    requires.lua
  test_parser.py
  test_associate.py
  test_render_text.py
```

This is a much better long-term shape than one large script.

---

## Recommended implementation order

If I were doing the rewrite, I would implement in this order:

1. `model.py`
2. `discover.py`
3. `parser.py` to extract syntax nodes and raw comments
4. `associate.py` to attach comments to symbols
5. `render_text.py` to recreate current output format
6. tests for all the above
7. optional `render_markdown.py`
8. optional tag parsing

This keeps the rewrite controlled and testable.