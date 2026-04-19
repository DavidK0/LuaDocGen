# LuaDocGen

LuaDocGen is a small documentation generator for Lua projects. It parses Lua with
Tree-sitter, finds functions and nearby documentation comments, and writes
Markdown documentation files.

The project is intentionally syntax-aware. It uses the Lua parse tree instead of
regular expressions for function and `require` detection, which makes it more
reliable on real Lua source files.

## Features

- Parses `.lua` files with Tree-sitter
- Extracts top-level Lua functions
- Supports common declaration and assignment forms, including table functions and
  method syntax
- Detects local vs global functions
- Reads multiline parameter lists
- Associates comments with functions using source positions
- Preserves block comment line structure
- Detects `require "mod"` and `require("mod")` calls from syntax nodes
- Generates either one Markdown file per Lua file or one combined project file

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Generate documentation for one Lua file:

```bash
python3 -m docgen.cli path/to/file.lua
```

By default, this writes a Markdown file next to the input file:

```text
path/to/file.lua.md
```

Generate documentation for a directory:

```bash
python3 -m docgen.cli path/to/lua/project
```

By default, directory input writes one Markdown file next to each Lua file and an
`index.md` file in the input directory.

Write output somewhere specific:

```bash
python3 -m docgen.cli path/to/file.lua -o docs/file.md
python3 -m docgen.cli path/to/lua/project -o docs
```

For directory input, the output directory keeps the same relative file layout and
adds `.md` after each `.lua` filename. It also writes `index.md`.

Write one combined Markdown file for a whole project:

```bash
python3 -m docgen.cli path/to/lua/project --single-file -o docs/project.md
```

If `--single-file` is used without `-o`, directory input writes
`DOCUMENTATION.md` inside the input directory.

## Example

Given this Lua file:

```lua
-- Player helpers.

-- Updates player state.
function Player:update(dt)
    self.x = self.x + dt
end
```

LuaDocGen produces Markdown like:

```markdown
# player.lua

Player helpers.

## Functions

### `Player:update(dt)`

Updates player state.

- Scope: `global`
- Lines: `4-6`
```

## Supported Function Forms

LuaDocGen currently recognizes these common forms:

```lua
function foo(a, b) end
local function foo(a, b) end
foo = function(a, b) end
local foo = function(a, b) end
tbl.foo = function(a, b) end
function tbl.foo(a, b) end
function tbl:foo(a, b) end
```

Nested functions are parsed and represented internally, but the default Markdown
renderer only emits top-level functions.

## Development

Run the test suite with:

```bash
python3 -m pytest
```

The main modules are:

- `docgen.discover`: finds Lua files
- `docgen.parser`: parses source and builds the raw structured model
- `docgen.associate`: attaches comments to symbols
- `docgen.project`: builds a project-level documentation model
- `docgen.render_markdown`: renders Markdown output
- `docgen.render_project_markdown`: renders combined project docs and indexes
- `docgen.cli`: command-line entry point

The detailed project rules and architecture notes live in `AGENTS.md`.

For guidance on writing Lua comments that LuaDocGen can associate correctly,
see `style_guide.md`.
