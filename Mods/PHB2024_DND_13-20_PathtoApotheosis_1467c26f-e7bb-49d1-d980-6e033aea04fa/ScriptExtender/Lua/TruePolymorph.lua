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
    if not t.permanent then
        local left = secondsLeft(obj, status)
        if left and left >= 0 and left <= 7.0 then TP.MakePermanent(obj, t) end  -- its last round
    end
end

function TP.Poll()
    for obj in pairs(TP.tracked) do TP.Check(obj) end
    TP.polling = next(TP.tracked) ~= nil
    if TP.polling then Ext.Timer.WaitFor(POLL_MS, function() TP.Poll() end) end
end

function TP.Track(obj, form, caster, permanent)
    local hp = PREFIX .. "TEMPHP_" .. form
    local hasTemp = Ext.Stats.Get(hp) ~= nil
    if hasTemp and not permanent and Osi.HasActiveStatus(obj, hp) ~= 1 then Osi.ApplyStatus(obj, hp, -1, 1, caster or obj) end
    TP.tracked[obj] = { form = form, caster = caster, permanent = permanent, hasTemp = hasTemp }
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
            for _, form in ipairs({ "SHEEP", "DIREWOLF", "SHADOWMASTIFF", "PHASESPIDER", "MINOTAUR", "CHEESE" }) do
                if Osi.HasActiveStatus(g, PREFIX .. form) == 1 then TP.Track(g, form, nil, false) end
                if Osi.HasActiveStatus(g, PREFIX .. form .. "_PERMANENT") == 1 then TP.Track(g, form, nil, true) end
            end
        end
    end
end))

Apotheosis = Apotheosis or {}
Apotheosis.TruePolymorph = TP
return TP
