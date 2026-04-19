-- Module comment
-- with two lines

local dep = require "alpha"
require("beta")
print("not require('fake')")

-- Updates top-level state.
function foo(a, b) end

-- Local function docs.
local function local_foo(
  x,
  y
) end

-- Assigned docs.
foo_assigned = function(a, b) end

-- Local assigned docs.
local local_assigned = function(a, b) end

-- Table assigned docs.
tbl.foo = function(a, b) end

-- Table declaration docs.
function tbl.baz(a, b) end

-- Method declaration docs.
function tbl:qux(a, b) end

-- Outer docs.
function outer()
  -- This is an inside-function comment.
  local function inner(hidden) end
end

-- Orphan because code is between it and the next function.
local value = 1
function undocumented() end

--[[
Block docs.

Keep paragraphs.
]]
function block_documented() end
