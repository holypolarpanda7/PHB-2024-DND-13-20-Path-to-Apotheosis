-- Indomitable Might (Barbarian 18, PHB 2024, issue #22): a Strength check or saving throw totals at least
-- your Strength score. Stats can only floor the d20, so the floor is score - (that roll's bonus), computed
-- here from the character's real stats and applied as APO_IM_<SAVE|ATH|STR>_<n> statuses
-- (Status_IndomitableMight.txt, generated). Recomputed when gameplay starts, on level-up and on combat start.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local IM = {}
local PASSIVE = "Barbarian_IndomitableMight"
local TYPES = { "SAVE", "ATH", "STR" }

local function strengthSaveProficient(entity)
    for _, entry in pairs(entity.BoostsContainer.Boosts) do
        if tostring(entry.Type) == "ProficiencyBonus" then
            for _, b in ipairs(entry.Boosts) do
                local c = b.ProficiencyBonusBoost
                if c and tostring(c.Type) == "SavingThrow" and tostring(c.Ability) == "Strength" then return true end
            end
        end
    end
    return false
end

-- d20 floors per roll type; nil = no floor needed (1 or less)
function IM.Floors(character)
    local e = Ext.Entity.Get(character)
    if not e or not e.Stats then return nil end
    local s = e.Stats
    local score = s.Abilities[2]          -- [1] is None, [2] Strength
    local mod = s.AbilityModifiers[2]
    local save = mod + (strengthSaveProficient(e) and s.ProficiencyBonus or 0)
    local ath = s.Skills[Ext.Enums.SkillId.Athletics.Value + 1]
    local function clamp(n) if n < 2 then return nil end return math.min(n, 20) end
    return { SAVE = clamp(score - save), ATH = clamp(score - ath), STR = clamp(score - mod) }, score
end

function IM.Clear(character)
    for _, t in ipairs(TYPES) do
        for n = 2, 20 do
            local st = "APO_IM_" .. t .. "_" .. n
            if Osi.HasActiveStatus(character, st) == 1 then Osi.RemoveStatus(character, st) end
        end
    end
end

function IM.Refresh(character)
    if Osi.HasPassive(character, PASSIVE) ~= 1 then
        IM.Clear(character)
        return
    end
    local floors, score = IM.Floors(character)
    if not floors then return end
    for _, t in ipairs(TYPES) do
        local want = floors[t] and ("APO_IM_" .. t .. "_" .. floors[t]) or nil
        for n = 2, 20 do
            local st = "APO_IM_" .. t .. "_" .. n
            if st ~= want and Osi.HasActiveStatus(character, st) == 1 then Osi.RemoveStatus(character, st) end
        end
        if want and Osi.HasActiveStatus(character, want) ~= 1 then Osi.ApplyStatus(character, want, -1, 1, character) end
    end
    Log.Info(string.format("Indomitable Might: %s Str %d -> d20 floors save %s, Athletics %s, Strength check %s",
        tostring(character), score, tostring(floors.SAVE), tostring(floors.ATH), tostring(floors.STR)))
end

function IM.RefreshParty()
    for _, row in pairs(Osi.DB_Players:Get(nil) or {}) do IM.Refresh(row[1]) end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("IndomitableMight " .. name .. ": " .. tostring(err)) end
    end
end

-- not SessionLoaded: the party database can't be read there ("restricted context", seen in game 2026-09-30)
Ext.Osiris.RegisterListener("LevelGameplayStarted", 2, "after", guard("LevelGameplayStarted", function() IM.RefreshParty() end))
Ext.Osiris.RegisterListener("LeveledUp", 1, "after", guard("LeveledUp", function(c) IM.Refresh(c) end))
Ext.Osiris.RegisterListener("EnteredCombat", 2, "after", guard("EnteredCombat", function(c)
    if Osi.HasPassive(c, PASSIVE) == 1 then IM.Refresh(c) end
end))

-- Second layer for spell Strength saves (2026-10-02). The d20 floor above holds on only ~5/8 real spell saves
-- (MinimumRollResult is unreliable on saves, even unconditionally). Interrupt_IndomitableMight (Interrupt.txt) fires
-- on the bearer's failed Strength saves against spells and runs SetRoll; here, just before it executes, the d20 is set
-- so the total equals the Strength score - the exact PHB 2024 rule (bonuses such as Bless no longer stack on top).
-- UNTESTED in game: OnPostRoll interrupts never fire on script-issued casts, so the test harness can't reach it; it
-- needs a real enemy spell (as Legendary Resistance does). See issue #22. Passive and status-tick saves stay a gap.
local PLACEHOLDER = 20  -- the Roll in Interrupt.txt's SetRoll(20), restored after every use (the functor is shared)

local function strengthScore(entity)
    local ok, v = pcall(function() return entity.Stats.Abilities[2] end)
    return ok and v or nil
end

Ext.Events.ExecuteFunctor:Subscribe(function(e)
    local ok, err = pcall(function()
        local p, f = e.Params, e.Functor
        if tostring(p.Type) ~= "Interrupt" or tostring(f.TypeId) ~= "SetRoll" or f.Roll ~= PLACEHOLDER then return end
        local ev = p.Interrupt.Event
        if tostring(ev.Ability) ~= "Strength" or not ev.Roll then return end
        local observer = p.Observer
        local guid = observer and observer.Uuid and observer.Uuid.EntityUuid
        if not guid or Osi.HasPassive(guid, PASSIVE) ~= 1 then return end
        local score = strengthScore(observer)
        if not score then return end
        local bonus = ev.Roll.Total - ev.Roll.NaturalRoll
        local d20 = math.max(ev.Roll.NaturalRoll, score - bonus)  -- never lower the roll
        f.Roll = d20
        Log.Info(string.format("Indomitable Might: %s Strength save total %d -> %d (score %d)", tostring(guid),
            ev.Roll.Total, d20 + bonus, score))
    end)
    if not ok then Log.Error("IndomitableMight interrupt: " .. tostring(err)) end
end)
Ext.Events.AfterExecuteFunctor:Subscribe(function(e)
    pcall(function()
        if tostring(e.Params.Type) == "Interrupt" and tostring(e.Functor.TypeId) == "SetRoll" and e.Functor.Roll ~= PLACEHOLDER then
            local ev = e.Params.Interrupt.Event
            if tostring(ev.Ability) == "Strength" then e.Functor.Roll = PLACEHOLDER end
        end
    end)
end)

Apotheosis = Apotheosis or {}
Apotheosis.IndomitableMight = IM
return IM
