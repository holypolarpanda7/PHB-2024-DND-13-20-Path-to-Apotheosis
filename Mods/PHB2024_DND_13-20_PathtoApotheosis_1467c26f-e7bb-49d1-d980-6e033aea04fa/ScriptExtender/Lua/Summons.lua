-- PHB 2024 summon spells (issue #10, Scripts/gen_summons.py): the parts stats can't express.
--  * Mordenkainen's Faithful Hound: bites an enemy within 5 ft at the start of your turns (APO_FAITHFUL_HOUND_BITE
--    rolls the Dexterity save against your DC); "Move Faithful Hound" teleports it (up to 30 ft); it skips its own
--    turns and ends if you are more than 300 ft apart.
--  * Bigby's Hand: Hit Points equal to your Hit Point maximum; Forceful Hand's push (Force() can't take a formula).
--  * Animate Objects: each targeted object (marked APO_ANIMATE_OBJECTS_<level>) is hidden and its Animated Object is
--    summoned where it stood, within your spellcasting modifier's budget (Medium or smaller 1, Large 2, Huge 3); the
--    object comes back when the creature drops to 0 HP, is dismissed, or your Concentration on the spell ends.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local SM = {}

local function short(g) return g and string.sub(g, -36) or nil end

local function dist(a, b)
    local x1, y1, z1 = Osi.GetPosition(a)
    local x2, y2, z2 = Osi.GetPosition(b)
    if not x1 or not x2 then return math.huge end
    return math.sqrt((x1 - x2) ^ 2 + (y1 - y2) ^ 2 + (z1 - z2) ^ 2)
end

local function summoner(g)
    local s
    pcall(function() s = Ext.Entity.Get(g).IsSummon.Summoner.Uuid.EntityUuid end)
    return s
end

local function statsId(g)
    local s
    pcall(function() s = Ext.Entity.Get(g).Data.StatsId end)
    return s
end

local function castingModifierOf(c)
    local mod
    pcall(function()
        local st = Ext.Entity.Get(c).Stats
        local names = { "None", "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma" }
        local ab = tostring(st.SpellCastingAbility)
        for i, n in ipairs(names) do
            if n == ab then mod = math.floor((st.Abilities[i] - 10) / 2) end
        end
    end)
    return mod or 3
end


local function summonsOf(owner, stats)
    local out, oe = {}, Ext.Entity.Get(owner)
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("IsSummon")) do
        local ok, mine = pcall(function() return e.IsSummon.Summoner == oe end)
        if ok and mine then
            local g = e.Uuid.EntityUuid
            if (not stats or (e.Data and e.Data.StatsId) == stats) and Osi.IsDead(g) == 0 then out[#out + 1] = g end
        end
    end
    return out
end

-- ---------------------------------------------------------------- Faithful Hound
local HOUND = "Apo_FaithfulHound"

local function nearestEnemy(owner, hound, range)
    local best, bestD
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local ok, g = pcall(function() return e.Uuid.EntityUuid end)
        if ok and g and g ~= hound and Osi.IsDead(g) == 0 and Osi.IsEnemy(owner, g) == 1 then
            local d = dist(hound, g)
            if d <= range and (not bestD or d < bestD) then best, bestD = g, d end
        end
    end
    return best
end

function SM.HoundTurn(owner)
    for _, hound in ipairs(summonsOf(owner, HOUND)) do
        if dist(owner, hound) > 91.5 then  -- more than 300 feet apart: the spell ends
            Osi.Die(hound, 0, "NULL_00000000-0000-0000-0000-000000000000", 0, 1)
            Log.Info("Faithful Hound: more than 300 ft from its caster - dismissed")
        else
            local target = nearestEnemy(owner, hound, 2.5)  -- 5 ft reach plus the creatures' footprints
            if target then
                Osi.ApplyStatus(target, "APO_FAITHFUL_HOUND_BITE", 0, 1, owner)
                Log.Info("Faithful Hound bites " .. target)
            end
        end
    end
    if #summonsOf(owner, HOUND) == 0 and Osi.HasActiveStatus(owner, "APO_FAITHFUL_HOUND_OWNER") == 1 then
        Osi.RemoveStatus(owner, "APO_FAITHFUL_HOUND_OWNER")
    end
end

function SM.MoveHound(caster, x, y, z)
    local hound = summonsOf(caster, HOUND)[1]
    if not hound then return end
    local hx, hy, hz = Osi.GetPosition(hound)
    local dx, dz = x - hx, z - hz
    local d = math.sqrt(dx * dx + dz * dz)
    if d > 9 then x, z = hx + dx / d * 9, hz + dz / d * 9 end  -- up to 30 feet
    Osi.TeleportToPosition(hound, x, y, z, "", 0, 0, 0, 0, 1)
end

-- ---------------------------------------------------------------- Bigby's Hand
function SM.HandAppeared(hand)
    local owner = summoner(hand)
    if not owner then return end
    Ext.Timer.WaitFor(200, function()
        local want, have = Osi.GetMaxHitpoints(owner), Osi.GetMaxHitpoints(hand)
        if want and have and want > have then
            Osi.AddBoosts(hand, "IncreaseMaxHP(" .. (want - have) .. ")", "BigbysHand", owner)
        end
        Ext.Timer.WaitFor(200, function() Osi.SetHitpointsPercentage(hand, 100) end)
        Log.Info("Bigby's Hand: " .. tostring(want) .. " Hit Points (its caster's maximum)")
    end)
end

-- Forceful Hand: pushed 5 ft + 5 ft x the caster's spellcasting modifier, straight away from the hand
function SM.Push(target, causee)
    local owner, hand = causee, nil
    if summoner(causee) then owner, hand = summoner(causee), causee end
    hand = hand or summonsOf(owner, "Apo_BigbysHand")[1] or owner
    local d = 1.5 + 1.5 * math.max(0, castingModifierOf(owner))
    local tx, ty, tz = Osi.GetPosition(target)
    local hx, _, hz = Osi.GetPosition(hand)
    local dx, dz = tx - hx, tz - hz
    local len = math.sqrt(dx * dx + dz * dz)
    if len < 0.01 then dx, dz, len = 1, 0, 1 end
    Osi.TeleportToPosition(target, tx + dx / len * d, ty, tz + dz / len * d, "", 0, 0, 0, 0, 1)
    Log.Info(string.format("Forceful Hand: %s pushed %.1f m", target, d))
end

-- ---------------------------------------------------------------- Animate Objects
local SIZE_NAME = { [0] = "Medium", [1] = "Medium", [2] = "Medium", [3] = "Large", [4] = "Huge" }
local COST = { Medium = 1, Large = 2, Huge = 3 }
local animated = {}  -- caster -> { { item, size, cost, summon, x, y, z } }
local watching = false


local function concentratingOnAnimate(c)
    local ok, id = pcall(function() return Ext.Entity.Get(c).Concentration.SpellId.OriginatorPrototype end)
    if not ok then return nil end  -- can't tell
    return id ~= nil and string.find(tostring(id), "Target_ApoAnimateObjects", 1, true) ~= nil
end

local function restore(entry)
    local x, y, z = entry.x, entry.y, entry.z
    if entry.summon then
        local sx, sy, sz = Osi.GetPosition(entry.summon)
        if sx then x, y, z = sx, sy, sz end
    end
    pcall(Osi.TeleportToPosition, entry.item, x, y, z, "", 0, 0, 0, 0, 1)
    Osi.SetOnStage(entry.item, 1)
    pcall(Osi.RemoveStatus, entry.item, "APO_ANIMATE_OBJECTS")
end

local function watch()
    if watching then return end
    watching = true
    local function tick()
        local any = false
        for caster, list in pairs(animated) do
            -- Concentration ended: only once it was seen on the spell (a scripted cast may not set it)
            local conc = concentratingOnAnimate(caster)
            if conc then list.conc = true end
            local keepConc = not (list.conc and conc == false)
            for i = #list, 1, -1 do
                local en = list[i]
                local gone = en.summon and (Osi.IsDead(en.summon) == 1 or not Osi.GetPosition(en.summon))
                local stale = not en.summon and (Ext.Utils.MonotonicTime() - en.at) > 5000  -- the summon never came
                if gone or stale or not keepConc then
                    if en.summon and Osi.IsDead(en.summon) == 0 then
                        Osi.Die(en.summon, 0, "NULL_00000000-0000-0000-0000-000000000000", 0, 1)
                    end
                    restore(en)
                    table.remove(list, i)
                    Log.Info("Animate Objects: " .. en.item .. " is an object again")
                end
            end
            if #list > 0 then any = true else animated[caster] = nil end
        end
        if any then Ext.Timer.WaitFor(1000, tick) else watching = false end
    end
    Ext.Timer.WaitFor(1000, tick)
end

function SM.AnimateObject(item, level, caster)
    local size
    pcall(function() size = Ext.Entity.Get(item).ObjectSize.Size end)
    local name = SIZE_NAME[size or 2]
    if not name then
        Log.Warn("Animate Objects: " .. item .. " is too big (Gargantuan)")
        return
    end
    local list = animated[caster] or {}
    animated[caster] = list
    for _, en in ipairs(list) do
        if en.item == item then return end  -- already animated (a multi-target cast can name an object twice)
    end
    local used = 0
    for _, en in ipairs(list) do used = used + en.cost end
    local budget = castingModifierOf(caster)
    if used + COST[name] > budget then
        Log.Info(string.format("Animate Objects: %s (%s) doesn't fit (%d of %d used)", item, name, used, budget))
        return
    end
    local x, y, z = Osi.GetPosition(item)
    local entry = { item = item, size = name, cost = COST[name], x = x, y = y, z = z, at = Ext.Utils.MonotonicTime() }
    list[#list + 1] = entry
    local delay = 300 + 700 * (#list - 1)  -- one scripted cast at a time
    Osi.SetOnStage(item, 0)  -- its footprint would block the spot
    Ext.Timer.WaitFor(delay, function()
        Osi.UseSpellAtPosition(caster, string.format("Target_ApoAnimatedObject_Spawn_%s_%d", name, level), x, y, z, 1)
    end)
    Log.Info(string.format("Animate Objects: %s becomes a %s Animated Object (level %d; %d of %d used)", item, name, level,
        used + entry.cost, budget))
    watch()
end

function SM.ObjectAppeared(summon, size)
    local owner = summoner(summon)
    local list = owner and animated[owner]
    if not list then return end
    local best, bestD
    for _, en in ipairs(list) do
        if not en.summon and en.size == size then
            local sx, sy, sz = Osi.GetPosition(summon)
            local d = math.sqrt((sx - en.x) ^ 2 + (sz - en.z) ^ 2)
            if not bestD or d < bestD then best, bestD = en, d end
        end
    end
    if best then best.summon = summon end
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("Summons " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c)
    c = short(c)
    if statsId(c) == HOUND then
        pcall(Osi.EndTurn, c)  -- the hound acts at the start of your turn instead
        return
    end
    if Osi.HasActiveStatus(c, "APO_FAITHFUL_HOUND_OWNER") == 1 then SM.HoundTurn(c) end
end))

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(target, status, causee)
    if status == "APO_BIGBYS_HAND_PUSHED" then
        SM.Push(short(target), short(causee))
    elseif status:sub(1, 15) == "APO_BIGBYSHAND_" then
        SM.HandAppeared(short(target))
    elseif status:match("^APO_ANIMATE_OBJECTS_%d$") then
        SM.AnimateObject(short(target), tonumber(status:match("(%d)$")), short(causee))
    elseif status:sub(1, 19) == "APO_ANIMATEDOBJECT_" then
        local size = status:match("^APO_ANIMATEDOBJECT_(%u+)_")
        SM.ObjectAppeared(short(target), size and (size:sub(1, 1) .. size:sub(2):lower()))
    end
end))

Ext.Osiris.RegisterListener("UsingSpellAtPosition", 8, "after", guard("UsingSpellAtPosition", function(c, x, y, z, spell)
    if spell == "Target_ApoFaithfulHound_Move" then
        Ext.Timer.WaitFor(800, function() SM.MoveHound(short(c), x, y, z) end)
    end
end))

return SM
