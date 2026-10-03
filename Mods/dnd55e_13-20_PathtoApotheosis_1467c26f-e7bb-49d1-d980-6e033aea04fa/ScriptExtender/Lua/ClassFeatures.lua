-- Single PHB 2024 class features (Scripts/gen_class_features.py) that need a script.
--  * Battle Master 15 Relentless: once per turn, the first Superiority Die a maneuver spends comes back (the d8
--    "instead of expending a die"). Base maneuvers charge the die on hit (HitCosts) or as an interrupt cost, so a
--    cost-swapping spell variant can't cover them; this watches the pool after each cast instead.
--  * Open Hand 17 Quivering Palm: the vibrations are on one creature at a time.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local CF = {}

local function short(g) return g and string.sub(g, -36) or nil end

local function pool(c, name)
    local amt, entry
    pcall(function()
        for u, entries in pairs(Ext.Entity.Get(c).ActionResources.Resources) do
            local def = Ext.StaticData.Get(u, "ActionResource")
            if def and def.Name == name then entry = entries[1]; amt = entry.Amount end
        end
    end)
    return amt, entry
end

local lastDice, usedTurn = {}, {}

function CF.OnTurnStarted(c)
    c = short(c)
    usedTurn[c] = nil
    lastDice[c] = pool(c, "SuperiorityDie")
end

function CF.OnCasted(c)
    c = short(c)
    if Osi.HasPassive(c, "BattleMaster_Relentless") ~= 1 then return end
    Ext.Timer.WaitFor(300, function()  -- HitCosts are charged as the hit resolves
        local now, entry = pool(c, "SuperiorityDie")
        local before = lastDice[c]
        lastDice[c] = now
        if not now or not before or now >= before or usedTurn[c] then return end
        if Osi.IsInCombat(c) == 1 then usedTurn[c] = true
        else Ext.Timer.WaitFor(6000, function() usedTurn[c] = nil end) usedTurn[c] = true end
        entry.Amount = now + 1
        Ext.Entity.Get(c):Replicate("ActionResources")
        lastDice[c] = now + 1
        Log.Info("Relentless: " .. c .. " keeps the Superiority Die (once this turn)")
    end)
end

-- ---------------------------------------------------------------- Quivering Palm: one creature at a time
local palmOn = {}  -- Monk -> creature
function CF.OnStatusApplied(target, status, causee)
    if status ~= "QUIVERING_PALM" or not causee then return end
    local monk, t = short(causee), short(target)
    local prev = palmOn[monk]
    if prev and prev ~= t then Osi.RemoveStatus(prev, "QUIVERING_PALM") end
    palmOn[monk] = t
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("ClassFeatures " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c) CF.OnTurnStarted(c) end))
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(t, s, c) CF.OnStatusApplied(t, s, c) end))
Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(c) CF.OnCasted(c) end))
Ext.Osiris.RegisterListener("UsingSpell", 5, "before", guard("UsingSpell", function(c)
    c = short(c)
    if Osi.HasPassive(c, "BattleMaster_Relentless") == 1 then lastDice[c] = pool(c, "SuperiorityDie") end
end))

return CF
