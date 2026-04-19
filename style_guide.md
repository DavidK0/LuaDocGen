# LuaDocGen Comment Style Guide

This guide explains how to write Lua comments so LuaDocGen can turn them into
predictable documentation.

LuaDocGen uses source locations and the Lua syntax tree to attach comments to
symbols. It does not guess based only on nearby text, so comment placement
matters.

## Quick Rules

- Put function documentation before the function, not inside it.
- Leave zero or one blank line between a doc comment and the function.
- Do not put code between a doc comment and the function it describes.
- Use a top-of-file comment for module or file documentation.
- Use regular Lua line comments or block comments.
- Keep implementation notes inside function bodies if they are not public docs.

## Module Comments

A module comment describes the whole file. Put it at the very top of the file,
before any code.

Recommended:

```lua
-- Player movement and collision helpers.
-- Used by the main gameplay loop.

local physics = require "physics"

function Player:update(dt)
end
```

LuaDocGen treats the first leading comment block as module documentation when
only whitespace or other comments appear before the first code node.

Avoid putting module docs after code has started:

```lua
local physics = require "physics"

-- Player movement and collision helpers.
function Player:update(dt)
end
```

That comment is no longer a module comment.

## Function Comments

Function documentation should go immediately before the function.

Recommended:

```lua
-- Updates the player position and velocity.
function Player:update(dt)
end
```

This also works with one blank line:

```lua
-- Updates the player position and velocity.

function Player:update(dt)
end
```

Do not leave more than one blank line:

```lua
-- Updates the player position and velocity.


function Player:update(dt)
end
```

LuaDocGen will not attach that comment to the function.

## Do Not Put Code Between Comment And Function

The comment must be directly associated with the function. If any code appears
between the comment and the function, LuaDocGen treats the comment as orphaned.

Avoid:

```lua
-- Updates the player position and velocity.
local DEFAULT_SPEED = 120

function Player:update(dt)
end
```

Recommended:

```lua
local DEFAULT_SPEED = 120

-- Updates the player position and velocity.
function Player:update(dt)
end
```

## Inside-Function Comments Are Not Documentation

Comments inside a function body are treated as implementation notes, not public
documentation for the function.

```lua
function Player:update(dt)
    -- Clamp velocity before applying movement.
    self.vx = math.min(self.vx, self.max_vx)
end
```

That comment will not become documentation for `Player:update`.

If a function needs documentation, put it before the declaration:

```lua
-- Updates the player and clamps velocity before movement.
function Player:update(dt)
    self.vx = math.min(self.vx, self.max_vx)
end
```

## Supported Function Forms

LuaDocGen can attach comments to these forms:

```lua
-- Docs for foo.
function foo(a, b) end

-- Docs for local_foo.
local function local_foo(a, b) end

-- Docs for assigned.
assigned = function(a, b) end

-- Docs for local_assigned.
local local_assigned = function(a, b) end

-- Docs for tbl.foo.
tbl.foo = function(a, b) end

-- Docs for tbl.foo.
function tbl.foo(a, b) end

-- Docs for tbl:foo.
function tbl:foo(a, b) end
```

## Block Comments

Use Lua block comments for longer descriptions. LuaDocGen preserves line breaks
instead of flattening the comment into one sentence.

Recommended:

```lua
--[[
Creates a new player object.

The returned table contains movement state, collision bounds,
and rendering state.
]]
function Player.new(x, y)
end
```

## Parameters And Return Values

LuaDocGen currently extracts parameter names from the function signature. You can
describe parameters in prose for now.

Recommended:

```lua
-- Moves the player by the given delta time.
--
-- dt is the frame time in seconds.
function Player:update(dt)
end
```

Future versions may add structured tags such as `@param` and `@return`, but they
are not required today.

## Good Comment Style

Prefer comments that describe the public behavior of the function.

Recommended:

```lua
-- Returns true when the player can start a jump.
function Player:can_jump()
end
```

Less useful:

```lua
-- Checks some stuff.
function Player:can_jump()
end
```

Avoid comments that only repeat the function name:

```lua
-- can_jump function.
function Player:can_jump()
end
```

## Orphan Comments

LuaDocGen tracks comments it cannot attach to a module or function. These are
called orphan comments. Common causes are:

- More than one blank line between the comment and function
- Code between the comment and function
- A comment inside a function body
- A standalone note that is not attached to any symbol

Orphan comments are useful during development because they show where
documentation may need to be moved or clarified.

