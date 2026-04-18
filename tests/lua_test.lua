-- File comment

-- Updates player state.
function Player:update(dt)
    self.x = self.x + dt
end

-- Creates an enemy.
local function make_enemy(x, y)
    return { x = x, y = y }
end

-- Spawns a bullet.
Bullet.spawn = function(x, y)
    return { x = x, y = y }
end