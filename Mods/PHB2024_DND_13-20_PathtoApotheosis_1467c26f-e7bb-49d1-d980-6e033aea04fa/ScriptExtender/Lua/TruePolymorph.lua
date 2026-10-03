-- True Polymorph (9th level, PHB 2024, issue #20).
-- Creature into creature: the target keeps its own hit points and gains temporary HP equal to the new form's
-- (TRUE_POLYMORPH_TEMPHP_<FORM>, the dnd55e Wild Shape pattern); the transformation ends when they run out.
-- "If you maintain Concentration on this spell for the full duration, the transformation lasts until it is
-- dispelled": each form's status (TRUE_POLYMORPH_<FORM>, 600 rounds) is tied to concentration, so if it is still
-- there in its last round the caster concentrated for the whole hour - swap in TRUE_POLYMORPH_<FORM>_PERMANENT.
-- Both statuses share the POLYMORPH stack, and the permanent one doesn't apply over the timed one (seen in game
-- 2026-10-01), so the swap removes the timed status first. The temporary HP status is applied here rather than by
-- the spell: a spell-applied status ends with concentration, even after the swap.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local TP = { tracked = {}, converting = {} }
local POLL_MS = 2000
local PREFIX = "TRUE_POLYMORPH_"

-- seconds left on the status (CurrentLifeTime; Osi.GetStatusTurns lags behind it - seen in game 2026-10-01)
local function secondsLeft(obj, status)
    local ok, left = pcall(function()
        for _, s in pairs(Ext.Entity.Get(obj).ServerCharacter.StatusManager.Statuses) do
            if s.StatusId == status then return s.CurrentLifeTime end
        end
    end)
    if ok and left then return left end
    local turns = Osi.GetStatusTurns(obj, status)
    return turns and turns * 6.0 or nil
end

local function tempHp(obj)
    local ok, v = pcall(function() return Ext.Entity.Get(obj).Health.TemporaryHp end)
    return ok and v or nil
end

-- TRUE_POLYMORPH_<FORM> -> FORM (not the _PERMANENT or TEMPHP_ statuses)
local function timedForm(status)
    return status:match("^TRUE_POLYMORPH_(%u+)$")
end

local function remove(obj, status)
    if Osi.HasActiveStatus(obj, status) == 1 then Osi.RemoveStatus(obj, status) end
end

-- back to the true form: temporary HP ran out
function TP.EndForm(obj, form)
    TP.tracked[obj] = nil
    remove(obj, PREFIX .. form)
    remove(obj, PREFIX .. form .. "_PERMANENT")
    remove(obj, PREFIX .. "TEMPHP_" .. form)
    remove(obj, PREFIX .. "TEMPHP_" .. form .. "_HARDY")
    Log.Info("True Polymorph: " .. tostring(obj) .. " ran out of temporary hit points - back to its true form")
end

function TP.MakePermanent(obj, t)
    TP.converting[obj] = true
    remove(obj, PREFIX .. t.form)
    Osi.ApplyStatus(obj, PREFIX .. t.form .. "_PERMANENT", -1, 1, t.caster or obj)
    t.permanent = true
    Ext.Timer.WaitFor(1000, function() TP.converting[obj] = nil end)
    Log.Info(string.format("True Polymorph: %s kept concentration for the full hour - %s is now permanent",
        tostring(t.caster), tostring(obj)))
end

function TP.Check(obj)
    local t = TP.tracked[obj]
    if not t then return end
    local status = PREFIX .. t.form .. (t.permanent and "_PERMANENT" or "")
    if Osi.HasActiveStatus(obj, status) ~= 1 then
        if not TP.converting[obj] then TP.tracked[obj] = nil end
        return
    end
    if t.hasTemp and (tempHp(obj) or 1) <= 0 then return TP.EndForm(obj, t.form) end
    if not t.permanent and not t.fluid then  -- a Fluid Forms shape just lasts its hour
        local left = secondsLeft(obj, status)
        if left and left >= 0 and left <= 7.0 then TP.MakePermanent(obj, t) end  -- its last round
    end
end

function TP.Poll()
    for obj in pairs(TP.tracked) do TP.Check(obj) end
    TP.polling = next(TP.tracked) ~= nil
    if TP.polling then Ext.Timer.WaitFor(POLL_MS, function() TP.Poll() end) end
end

local function fluidForms(obj, caster)  -- Boon of Fluid Forms: a self-cast shape, not the spell
    if not caster or string.sub(caster, -36) ~= string.sub(obj, -36) then return false end
    for _, s in ipairs({ "Int", "Wis", "Cha" }) do if Osi.HasPassive(obj, "EpicBoon_FluidForms_" .. s) == 1 then return true end end
    return false
end

function TP.Track(obj, form, caster, permanent)
    local fluid = fluidForms(obj, caster)
    local hp = PREFIX .. "TEMPHP_" .. form .. (fluid and "_HARDY" or "")  -- Hardy Transformation: form HP + 20
    local hasTemp = Ext.Stats.Get(hp) ~= nil
    if hasTemp and not permanent and Osi.HasActiveStatus(obj, hp) ~= 1 then Osi.ApplyStatus(obj, hp, -1, 1, caster or obj) end
    TP.tracked[obj] = { form = form, caster = caster, permanent = permanent, hasTemp = hasTemp, fluid = fluid }
    if not TP.polling then
        TP.polling = true
        Ext.Timer.WaitFor(POLL_MS, function() TP.Poll() end)
    end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("TruePolymorph " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(obj, status, causee)
    local form = timedForm(status)
    if form and form ~= "TEMPHP" then TP.Track(obj, form, causee, false) end
end))
-- the form ended (concentration broken, dispelled, expired): its leftover temporary HP go too
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("StatusRemoved", function(obj, status)
    local form = timedForm(status) or status:match("^TRUE_POLYMORPH_(%u+)_PERMANENT$")
    if form and form ~= "TEMPHP" and not TP.converting[obj] then
        TP.tracked[obj] = nil
        remove(obj, PREFIX .. "TEMPHP_" .. form)
        remove(obj, PREFIX .. "TEMPHP_" .. form .. "_HARDY")
    end
end))
-- damage: check the temporary HP right away rather than at the next poll
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender)
    for obj in pairs(TP.tracked) do
        if string.sub(obj, -36) == string.sub(defender, -36) then
            Ext.Timer.WaitFor(200, function() TP.Check(obj) end)
        end
    end
end))
-- the tracking table isn't saved: pick up transformations in progress after a load
Ext.Osiris.RegisterListener("LevelGameplayStarted", 2, "after", guard("LevelGameplayStarted", function()
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local g = e.Uuid and e.Uuid.EntityUuid
        if g then
            for _, form in ipairs({ "SHEEP", "DIREWOLF", "SHADOWMASTIFF", "PHASESPIDER", "MINOTAUR", "CHEESE",
                                    "EARTHMYRMIDON", "FIREMYRMIDON", "AIRMYRMIDON", "WATERMYRMIDON", "MINDFLAYER" }) do
                if Osi.HasActiveStatus(g, PREFIX .. form) == 1 then TP.Track(g, form, nil, false) end
                if Osi.HasActiveStatus(g, PREFIX .. form .. "_PERMANENT") == 1 then TP.Track(g, form, nil, true) end
            end
        end
    end
end))

-- ---------------------------------------------------------------- object into creature (issue #23)
-- TRUE_POLYMORPH_OBJECT_<FORM> on an item: the item leaves the stage and a <FORM> that follows the caster takes
-- its place. If the status ends early (Concentration broken), the creature goes and the object comes back; if it
-- ran the whole hour (last seen in its final round), the creature stays and the object is gone for good.
local OBJECT_TEMPLATES = {
    MINOTAUR = "867c3061-624e-4b02-babb-a23e743fb5d3", DIREWOLF = "67f39af3-b9ea-4e95-8237-7aa4f6bd7cef",
    PHASESPIDER = "5acff443-0e4f-4d26-ae1c-deb640d2f729", SHADOWMASTIFF = "94696b69-bd4b-4ddb-885a-51790025f758",
}
TP.objects = TP.objects or {}  -- item -> { creature, caster, status, left }

local function itemSecondsLeft(item, status)
    local ok, left = pcall(function()
        local e = Ext.Entity.Get(item)
        local sm = (e.ServerItem and e.ServerItem.StatusManager) or (e.ServerCharacter and e.ServerCharacter.StatusManager)
        for _, st in pairs(sm.Statuses) do if st.StatusId == status then return st.CurrentLifeTime end end
    end)
    return ok and left or nil
end

function TP.ObjectApplied(item, status, caster)
    local key = status:match("^TRUE_POLYMORPH_OBJECT_(%u+)$")
    local template = key and OBJECT_TEMPLATES[key]
    if not template then return end
    local x, y, z = Osi.GetPosition(item)
    Osi.SetOnStage(item, 0)  -- the object's own footprint blocks the spot (CreateAt failed there, 2026-10-02)
    local creature
    for _, d in ipairs({ { 0, 0 }, { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 }, { 2, 0 }, { -2, 0 }, { 0, 2 } }) do
        creature = Osi.CreateAt(template, x + d[1], y, z + d[2], 0, 1, "")
        if creature then break end
    end
    if not creature then
        Osi.SetOnStage(item, 1)
        Log.Warn("True Polymorph: couldn't create a " .. key .. " near " .. tostring(item))
        return
    end
    if caster then
        pcall(Osi.SetFaction, creature, Osi.GetFaction(caster))
        pcall(Osi.AddPartyFollower, creature, caster)
    end
    TP.objects[item] = { creature = creature, caster = caster, status = status, left = 3600 }
    Log.Info(string.format("True Polymorph: object %s is now a %s (%s)", item, key, creature))
    local function watch()
        local t = TP.objects[item]
        if not t then return end
        local gone = not pcall(Ext.Entity.Get, item) or Ext.Entity.Get(item) == nil
        if gone or Osi.IsDead(t.creature) == 1 then  -- object destroyed (no StatusRemoved then) or creature killed
            TP.objects[item] = nil
            if gone then pcall(Osi.RemovePartyFollower, t.creature, t.caster) pcall(Osi.RequestDelete, t.creature) end
            Log.Info("True Polymorph: the transformation of " .. item .. " ends (" .. (gone and "object gone" or "creature died") .. ")")
            return
        end
        t.left = itemSecondsLeft(item, status) or t.left
        Ext.Timer.WaitFor(POLL_MS, watch)
    end
    Ext.Timer.WaitFor(POLL_MS, watch)
end

function TP.ObjectRemoved(item, status)
    local t = TP.objects[item]
    if not t or t.status ~= status then return end
    TP.objects[item] = nil
    if t.left and t.left <= 6.5 then  -- concentration held the whole hour: the creature stays
        Osi.RequestDelete(item)
        Log.Info("True Polymorph: the hour passed - " .. t.creature .. " stays a creature")
    else
        pcall(Osi.RemovePartyFollower, t.creature, t.caster)
        Osi.RequestDelete(t.creature)
        Osi.SetOnStage(item, 1)
        Log.Info("True Polymorph: the object " .. item .. " returns")
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("ObjectApplied", function(obj, status, causee)
    if status:find("^TRUE_POLYMORPH_OBJECT_") then TP.ObjectApplied(obj, status, causee) end
end))
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("ObjectRemoved", function(obj, status)
    if status:find("^TRUE_POLYMORPH_OBJECT_") then TP.ObjectRemoved(obj, status) end
end))

Apotheosis = Apotheosis or {}
Apotheosis.TruePolymorph = TP
return TP
