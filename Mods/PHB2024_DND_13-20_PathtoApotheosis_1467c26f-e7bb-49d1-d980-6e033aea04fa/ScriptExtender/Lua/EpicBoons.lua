-- Epic Boons (PHB 2024 level-19 feats), Script Extender half. Stats half: Scripts/gen_epic_boons.py.
-- Only the parts stats can't express (VISION principle 4):
--   Dimensional Travel  Blink Steps after an Attack or Magic action (a cast that costs an ActionPoint)
--   Spell Recall        roll 1d4 after a level 1-4 slot spell; on a match the slot comes back
--   Irresistible Off.   Overwhelming Strike: extra damage = the boosted ability score on a critical hit
--   Recovery            Last Stand heals to 1 + half the Hit Point maximum
--   Fate                Improve Fate recharges when you roll Initiative
--   Energy Resistance   Energy Redirection: spends your Reaction to send the damage back at the attacker
--   Ability pick        a restricted boon (+1 built in) plus a separate +1 would double the increase
-- Documented gaps: Overwhelming Strike and Peerless Aim trigger on any critical / keep natural 1s as misses;
-- Energy Redirection targets whoever damaged you and fires automatically.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = function() end }
local EB = {}

local VARIANT_ABILITY = {
    EpicBoon_IrresistibleOffense_Str = "Strength", EpicBoon_IrresistibleOffense_Dex = "Dexterity",
    EpicBoon_SpellRecall_Int = "Intelligence", EpicBoon_SpellRecall_Wis = "Wisdom", EpicBoon_SpellRecall_Cha = "Charisma",
}
local ABILITY_PICKS = { "EpicBoonAbility_Str", "EpicBoonAbility_Dex", "EpicBoonAbility_Con", "EpicBoonAbility_Int", "EpicBoonAbility_Wis", "EpicBoonAbility_Cha" }
local ABILITY_INDEX = { Strength = 2, Dexterity = 3, Constitution = 4, Intelligence = 5, Wisdom = 6, Charisma = 7 }

local function has(c, passive) return Osi.HasPassive(c, passive) == 1 end

local resourceUUIDs = {}
local function resourceUUID(name)
    if resourceUUIDs[name] == nil then
        resourceUUIDs[name] = false
        for _, u in pairs(Ext.StaticData.GetAll("ActionResource")) do
            local r = Ext.StaticData.Get(u, "ActionResource")
            if r and r.Name == name then resourceUUIDs[name] = u break end
        end
    end
    return resourceUUIDs[name] or nil
end

-- entries of a resource on a character, keyed by resource level (0 for non-slot resources)
local function resourceEntries(c, name)
    local u, e = resourceUUID(name), Ext.Entity.Get(c)
    if not (u and e and e.ActionResources) then return nil, e end
    return e.ActionResources.Resources[u], e
end

local function useCosts(spell)
    local s = Ext.Stats.Get(spell)
    return s and tostring(s.UseCosts) or "", s
end

-- ---------------------------------------------------------------- Blink Steps + Spell Recall
function EB.OnCast(caster, spell)
    local costs, stat = useCosts(spell)
    if has(caster, "EpicBoon_DimensionalTravel") and costs:find("ActionPoint:") and not costs:find("BonusActionPoint:")
        and spell ~= "Target_EpicBoon_BlinkStep" then
        Osi.ApplyStatus(caster, "EPIC_BLINK_STEPS", 6.0, 1)
    end
    local recall = has(caster, "EpicBoon_SpellRecall_Int") or has(caster, "EpicBoon_SpellRecall_Wis") or has(caster, "EpicBoon_SpellRecall_Cha")
    local level = stat and tonumber(stat.Level) or 0
    if recall and level >= 1 and level <= 4 and costs:find("SpellSlot") then
        local roll = Ext.Math.Random(1, 4)
        if roll ~= level then return end
        for _, pool in ipairs({ "SpellSlot", "WarlockSpellSlot" }) do
            local entries, e = resourceEntries(caster, pool)
            for _, x in ipairs(entries or {}) do
                if x.ResourceId == level and x.Amount < x.MaxAmount then
                    x.Amount = x.Amount + 1
                    e:Replicate("ActionResources")
                    Log.Info(string.format("Spell Recall: %s rolled %d on a level %d %s - slot kept", tostring(caster), roll, level, spell))
                    return
                end
            end
        end
    end
end

-- ---------------------------------------------------------------- Energy Redirection + Overwhelming Strike
local lastDamageType = {}

-- Osi.UseSpell queues casts with IgnoreSpellRolls, so the target's saving throw would never be rolled (found
-- 2026-10-01). Strip that option from our own request when it reaches the server's cast queue.
local pendingRolled = {}
local rolledSub
local function castWithRolls(caster, spell, target)
    table.insert(pendingRolled, { spell = spell, ticks = 0 })
    if not rolledSub then
        rolledSub = Ext.Events.Tick:Subscribe(function()
            if #pendingRolled == 0 then return end
            for _, r in ipairs(Ext.System.ServerCastRequest.OsirisCastRequests) do
                for i, p in ipairs(pendingRolled) do
                    if r.Spell.OriginatorPrototype == p.spell then
                        local keep = {}
                        for _, o in ipairs(r.CastOptions) do if o ~= "IgnoreSpellRolls" then keep[#keep + 1] = o end end
                        r.CastOptions = keep
                        table.remove(pendingRolled, i)
                        break
                    end
                end
            end
            for i = #pendingRolled, 1, -1 do
                pendingRolled[i].ticks = pendingRolled[i].ticks + 1
                if pendingRolled[i].ticks > 60 then table.remove(pendingRolled, i) end
            end
        end)
    end
    Osi.UseSpell(caster, spell, target)
end

function EB.OnAttacked(defender, attacker, damageType, amount)
    if attacker and defender then lastDamageType[attacker .. "|" .. defender] = damageType end
    if not (amount and amount > 0 and attacker and attacker ~= defender and has(defender, "EpicBoon_EnergyResistance")) then return end
    if Osi.HasActiveStatus(defender, "EPIC_ENERGY_RES_" .. string.upper(tostring(damageType))) ~= 1 then return end
    if Osi.IsDead(attacker) == 1 or Osi.IsDead(defender) == 1 then return end
    local entries, e = resourceEntries(defender, "ReactionActionPoint")
    local r = entries and entries[1]
    if not r or r.Amount < 1 then return end
    r.Amount = r.Amount - 1
    e:Replicate("ActionResources")
    castWithRolls(defender, "Target_EpicBoon_EnergyRedirection_" .. tostring(damageType), attacker)  -- Dex save rolled
    Log.Info(string.format("Energy Redirection: %s redirects %s damage at %s", tostring(defender), tostring(damageType), tostring(attacker)))
end

function EB.OnCritical(attacker, target)
    for passive, ability in pairs(VARIANT_ABILITY) do
        if passive:find("IrresistibleOffense") and has(attacker, passive) then
            local e = Ext.Entity.Get(attacker)
            local score = e and e.Stats and e.Stats.Abilities[ABILITY_INDEX[ability]] or 0
            local dtype = lastDamageType[attacker .. "|" .. target] or "Bludgeoning"
            Osi.ApplyDamage(target, score, dtype, attacker)
            Log.Info(string.format("Overwhelming Strike: %s deals %d %s (%s score)", tostring(attacker), score, dtype, ability))
            return
        end
    end
end

-- ---------------------------------------------------------------- Last Stand, Fate, ability pick
function EB.OnStatus(object, status, causee)
    if status == "EPIC_LAST_STAND_DOWNED" then
        Ext.Timer.WaitFor(300, function()
            local mx = Osi.GetMaxHitpoints(object)
            Osi.SetHitpoints(object, math.min(mx, 1 + math.floor(mx / 2)))
            Log.Info("Last Stand: " .. tostring(object) .. " stays up with half their Hit Points")
        end)
    elseif status == "EPIC_OVERWHELMING_MARK" and causee then
        EB.OnCritical(causee, object)
    end
end

function EB.OnEnteredCombat(object)
    if not has(object, "EpicBoon_Fate") then return end
    local entries, e = resourceEntries(object, "EpicBoonFate")
    if entries and entries[1] and entries[1].Amount < entries[1].MaxAmount then
        entries[1].Amount = entries[1].MaxAmount
        e:Replicate("ActionResources")
    end
end

-- A restricted boon already contains its +1; a second +1 from the ability pick is removed.
function EB.Validate(c)
    local restricted = nil
    for passive in pairs(VARIANT_ABILITY) do if has(c, passive) then restricted = passive end end
    if restricted then
        for _, pick in ipairs(ABILITY_PICKS) do
            if has(c, pick) then
                Osi.RemovePassive(c, pick)
                Log.Warn(string.format("Epic Boon: %s already includes its ability increase; removed the extra %s", restricted, pick))
            end
        end
    elseif has(c, "EpicBoonAbility_InBoon") then
        Log.Warn("Epic Boon: 'increase included in my boon' was picked with a boon that doesn't include one - no +1 was gained")
    end
    -- passives gained at level-up don't run OnCreate: apply their standing statuses now
    if has(c, "EpicBoon_Recovery") and Osi.HasActiveStatus(c, "EPIC_LAST_STAND") ~= 1 and Osi.GetLevel(c) == 19 then
        Osi.ApplyStatus(c, "EPIC_LAST_STAND", -1, 1)
    end
    if has(c, "EpicBoon_Truesight") and Osi.HasActiveStatus(c, "TRUESIGHT") ~= 1 then
        Osi.ApplyStatus(c, "TRUESIGHT", -1, 1)
    end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("EpicBoons " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(caster, spell) EB.OnCast(caster, spell) end))
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, attackerOwner, _, damageType, amount)
    EB.OnAttacked(defender, attackerOwner, damageType, amount)
end))
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(object, status, causee) EB.OnStatus(object, status, causee) end))
Ext.Osiris.RegisterListener("EnteredCombat", 2, "after", guard("EnteredCombat", function(object) EB.OnEnteredCombat(object) end))
Ext.Osiris.RegisterListener("LeveledUp", 1, "after", guard("LeveledUp", function(c) EB.Validate(c) end))

Apotheosis = Apotheosis or {}
Apotheosis.EpicBoons = EB
return EB
