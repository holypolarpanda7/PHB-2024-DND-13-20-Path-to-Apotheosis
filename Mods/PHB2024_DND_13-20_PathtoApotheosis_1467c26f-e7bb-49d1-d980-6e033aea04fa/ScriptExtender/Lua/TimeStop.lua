-- Time Stop (9th level, PHB 2024, issue #19): no time passes for other creatures while you take 1d4+1 turns in a
-- row. The spell ends if anything you do affects another creature (or something worn/carried by one), or if you
-- move more than 1,000 feet from where you cast it. Stats side (Status_TimeStop.txt): Shout_TimeStop applies
-- TIME_STOP to the caster; this module rolls the turns, puts TIME_STOPPED (skips turns) on every other creature
-- in the caster's combat (out of combat: within FREEZE_RANGE), counts the caster's turns and ends the spell.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local TS = { active = {} }
local CASTER_STATUS, FROZEN_STATUS = "TIME_STOP", "TIME_STOPPED"
local FREEZE_RANGE = 30       -- metres, out of combat
local MAX_DISTANCE = 304.8    -- 1,000 feet

local function id(guid)
    return guid and string.sub(guid, -36) or nil
end

local function isCharacter(guid)
    return guid and Osi.IsCharacter(guid) == 1
end

local function others(caster)
    local combat = Osi.IsInCombat(caster) == 1 and Osi.CombatGetGuidFor(caster) or nil
    local list = {}
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local g = e.Uuid and e.Uuid.EntityUuid
        if g and g ~= id(caster) and Osi.IsDead(g) ~= 1 then
            local include
            if combat then
                include = Osi.IsInCombat(g) == 1 and Osi.CombatGetGuidFor(g) == combat
            else
                local d = Osi.GetDistanceTo(g, caster)
                include = d and d <= FREEZE_RANGE
            end
            if include then list[#list + 1] = g end
        end
    end
    return list
end

function TS.End(caster, reason)
    local s = TS.active[id(caster)]
    if not s then return end
    TS.active[id(caster)] = nil
    for g in pairs(s.frozen) do
        if Osi.HasActiveStatus(g, FROZEN_STATUS) == 1 then Osi.RemoveStatus(g, FROZEN_STATUS) end
    end
    if Osi.HasActiveStatus(caster, CASTER_STATUS) == 1 then Osi.RemoveStatus(caster, CASTER_STATUS) end
    Log.Info(string.format("Time Stop: %s ended after %d/%d turns (%s)", tostring(caster), s.taken, s.turns, reason))
end

function TS.Start(caster)
    if TS.active[id(caster)] then return end
    local s = { caster = caster, turns = math.random(1, 4) + 1, taken = 0, frozen = {}, combat = Osi.IsInCombat(caster) == 1 }
    s.x, s.y, s.z = Osi.GetPosition(caster)
    TS.active[id(caster)] = s
    for _, g in ipairs(others(caster)) do
        s.frozen[g] = true
        Osi.ApplyStatus(g, FROZEN_STATUS, -1, 1, caster)
    end
    local n = 0
    for _ in pairs(s.frozen) do n = n + 1 end
    Log.Info(string.format("Time Stop: %s takes %d turns in a row; %d creatures frozen (%s)", tostring(caster),
        s.turns, n, s.combat and "combat" or "out of combat"))
    if not s.combat then  -- no turns out of combat: a turn is 6 seconds
        Ext.Timer.WaitFor(s.turns * 6000, function()
            if TS.active[id(caster)] == s then s.taken = s.turns TS.End(caster, "turns done") end
        end)
    end
end

-- the caster affected someone else: the spell ends
local function affected(source, target, how)
    local s = source and TS.active[id(source)]
    if s and isCharacter(target) and id(target) ~= id(source) then TS.End(s.caster, how .. " " .. tostring(target)) end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("TimeStop " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(obj, status, causee)
    if status == CASTER_STATUS then
        TS.Start(obj)
    elseif status ~= FROZEN_STATUS then
        affected(causee, obj, "status " .. status .. " on")
    end
end))
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("StatusRemoved", function(obj, status)
    if status == CASTER_STATUS then TS.End(obj, "status removed") end
end))
Ext.Osiris.RegisterListener("UsingSpellOnTarget", 6, "after", guard("UsingSpellOnTarget", function(caster, target, spell)
    affected(caster, target, spell .. " on")
end))
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, attackerOwner)
    affected(attackerOwner, defender, "attacked")
end))
-- a creature that joins the caster's combat mid-spell is frozen too
Ext.Osiris.RegisterListener("EnteredCombat", 2, "after", guard("EnteredCombat", function(obj, combat)
    for _, s in pairs(TS.active) do
        if s.combat and id(obj) ~= id(s.caster) and not s.frozen[id(obj)] and Osi.CombatGetGuidFor(s.caster) == combat then
            s.frozen[id(obj)] = true
            Osi.ApplyStatus(obj, FROZEN_STATUS, -1, 1, s.caster)
            Log.Info("Time Stop: froze " .. tostring(obj) .. " (joined the combat)")
        end
    end
end))
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c)
    local s = TS.active[id(c)]
    if s then s.taken = s.taken + 1 Log.Info(string.format("Time Stop: %s turn %d/%d", tostring(c), s.taken, s.turns)) end
end))
Ext.Osiris.RegisterListener("TurnEnded", 1, "after", guard("TurnEnded", function(c)
    local s = TS.active[id(c)]
    if not s then return end
    local x, y, z = Osi.GetPosition(c)
    if x and s.x and math.sqrt((x - s.x) ^ 2 + (y - s.y) ^ 2 + (z - s.z) ^ 2) > MAX_DISTANCE then
        TS.End(c, "moved more than 1,000 feet")
    elseif s.taken >= s.turns then
        TS.End(c, "turns done")
    end
end))
Ext.Osiris.RegisterListener("Died", 1, "after", guard("Died", function(c)
    if TS.active[id(c)] then TS.End(c, "caster died") end
end))
-- the turn state isn't saved: a loaded game ends any Time Stop in progress
Ext.Osiris.RegisterListener("LevelGameplayStarted", 2, "after", guard("LevelGameplayStarted", function()
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local g = e.Uuid and e.Uuid.EntityUuid
        if g and Osi.HasActiveStatus(g, FROZEN_STATUS) == 1 then Osi.RemoveStatus(g, FROZEN_STATUS) end
        if g and Osi.HasActiveStatus(g, CASTER_STATUS) == 1 then Osi.RemoveStatus(g, CASTER_STATUS) end
    end
end))

Apotheosis = Apotheosis or {}
Apotheosis.TimeStop = TS
return TS
