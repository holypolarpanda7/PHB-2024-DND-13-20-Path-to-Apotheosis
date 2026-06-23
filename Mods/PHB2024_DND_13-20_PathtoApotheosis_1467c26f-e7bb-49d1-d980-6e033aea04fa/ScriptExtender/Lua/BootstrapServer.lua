-- =====================================================================
-- Path to Apotheosis - Server bootstrap (Script Extender)
-- =====================================================================
-- Diviner feature "Greater Portent" (PHB 2024, Wizard subclass, level 14):
-- you roll a THIRD Portent d20 each long rest (the base feature rolls two).
--
-- How the base game works (verified via Norbyte's Osiris dump):
--   The script GLO_Spells_PostEA reacts to LongRestFinished(), clears the old
--   Portent statuses and applies two fresh PORTENT_<value> statuses, where each
--   <value> (1..20) is the rolled die face. The count of dice is fixed at 2 and
--   is NOT exposed through any stat, action resource or progression, so a third
--   die cannot be added through Stats/Lsx data alone.
--
-- Our approach:
--   For any character that owns the marker passive Diviner_14_GreaterPortent,
--   we apply one ADDITIONAL random PORTENT_<value> shortly after the long rest
--   completes. The base game has already cleared + reapplied its two dice by
--   then, so there is no accumulation across rests.
-- =====================================================================

local GREATER_PORTENT_PASSIVE = "Diviner_14_GreaterPortent"

-- Delay so the base-game Portent reroll (clear + apply 2 dice) finishes first.
local APPLY_DELAY_MS = 1500

--- Roll a single d20. Prefer the Script Extender RNG (engine-seeded); fall back
--- to Lua's math.random if unavailable.
local function rollD20()
    if Ext.Random then
        return Ext.Random(1, 20)
    end
    return math.random(1, 20)
end

--- Grant one extra Portent die to a character that has Greater Portent.
local function grantExtraPortentDie(character)
    if not character then return end
    if Osi.HasPassive(character, GREATER_PORTENT_PASSIVE) == 1 then
        local value = rollD20()
        -- ApplyStatus(target, statusId, duration, force, source); -1 = permanent.
        Osi.ApplyStatus(character, "PORTENT_" .. value, -1.0, 1, character)
    end
end

Ext.Osiris.RegisterListener("LongRestFinished", 0, "after", function()
    Ext.Timer.WaitFor(APPLY_DELAY_MS, function()
        local players = Osi.DB_Players:Get(nil)
        if not players then return end
        for _, row in pairs(players) do
            local ok, err = pcall(grantExtraPortentDie, row[1])
            if not ok then
                Ext.Utils.PrintError("[Apotheosis] Greater Portent error: " .. tostring(err))
            end
        end
    end)
end)

-- =====================================================================
-- Enchanter feature "Alter Memories" - Modify Memory aura (PHB 2024,
-- Wizard subclass, level 14).
--
-- The spell Shout_Apotheosis_ModifyMemory applies MODIFY_MEMORY_AURA to the
-- caster: a 6m following, concentration aura that tags every valid enemy in
-- range with the technical marker MODIFY_MEMORY_MARK (applied/removed by the
-- engine as creatures enter/leave the radius).
--
-- BG3 auras have no native "max targets" field, so we enforce a TARGET CAP with
-- a FIFO queue here:
--   * cap = 1 normally, 2 if the caster owns Enchanter_14_AlterMemories.
--   * The first 'cap' enemies to enter are "active": each is locked down by an
--     even 50/50 split of MM_HOLD (Paralyzed) or MM_SLOW (Slowed).
--   * Extra enemies wait in a FIFO queue. When an active victim leaves the aura,
--     dies, or the aura ends (its mark is removed), the next queued enemy is
--     promoted in arrival order.
-- =====================================================================

local MM_PASSIVE   = "Enchanter_14_AlterMemories"
local MM_AURA      = "MODIFY_MEMORY_AURA"
local MM_MARK      = "MODIFY_MEMORY_MARK"
local MM_HOLD      = "MM_HOLD"
local MM_SLOW      = "MM_SLOW"

-- mmState[casterGuid] = { active = { [victimGuid] = effectStatus }, activeCount = N, queue = { victimGuid, ... } }
local mmState = {}

--- Target cap for a given caster: 2 with the feature, otherwise 1.
local function mmCap(caster)
    if Osi.HasPassive(caster, MM_PASSIVE) == 1 then
        return 2
    end
    return 1
end

local function mmGetState(caster)
    local st = mmState[caster]
    if not st then
        st = { active = {}, activeCount = 0, queue = {} }
        mmState[caster] = st
    end
    return st
end

--- Coin flip: true ~50% of the time (engine RNG preferred).
local function mmCoinFlip()
    if Ext.Random then
        return Ext.Random(0, 1) == 0
    end
    return math.random(0, 1) == 0
end

--- Lock a victim down with one of the two effects, recording which was applied.
local function mmActivate(caster, victim)
    local st = mmGetState(caster)
    if st.active[victim] then return end
    local status = mmCoinFlip() and MM_HOLD or MM_SLOW
    -- ApplyStatus(target, statusId, duration, force, source); -1 = SE-managed.
    Osi.ApplyStatus(victim, status, -1.0, 1, caster)
    st.active[victim] = status
    st.activeCount = st.activeCount + 1
end

--- Promote queued enemies into free slots, FIFO, skipping any that have since
--- left the aura or died.
local function mmPromote(caster)
    local st = mmState[caster]
    if not st then return end
    local cap = mmCap(caster)
    while st.activeCount < cap and #st.queue > 0 do
        local victim = table.remove(st.queue, 1)
        if Osi.HasActiveStatus(victim, MM_MARK) == 1 and Osi.IsDead(victim) == 0 then
            mmActivate(caster, victim)
        end
    end
end

--- Remove a victim's active effect (if any) and free its slot.
local function mmDeactivate(caster, victim)
    local st = mmState[caster]
    if not st then return end
    local effect = st.active[victim]
    if effect then
        Osi.RemoveStatus(victim, effect)
        st.active[victim] = nil
        st.activeCount = st.activeCount - 1
    end
end

--- An enemy entered the aura: activate immediately if a slot is free, else queue.
local function mmOnMarkApplied(victim, caster)
    if not caster or caster == "" then return end
    -- Only act for a genuine aura owner (filters out any unrelated causee).
    if Osi.HasActiveStatus(caster, MM_AURA) ~= 1 then return end
    local st = mmGetState(caster)
    if st.active[victim] then return end
    for _, v in ipairs(st.queue) do
        if v == victim then return end
    end
    if st.activeCount < mmCap(caster) then
        mmActivate(caster, victim)
    else
        st.queue[#st.queue + 1] = victim
    end
end

--- An enemy left the aura (or the aura ended): free its slot/queue position and
--- promote the next enemy in line.
local function mmOnMarkRemoved(victim, caster)
    local st = caster and caster ~= "" and mmState[caster] or nil
    if not st then return end
    if st.active[victim] then
        mmDeactivate(caster, victim)
        mmPromote(caster)
    else
        for i, v in ipairs(st.queue) do
            if v == victim then
                table.remove(st.queue, i)
                break
            end
        end
    end
end

--- The aura ended on the caster: clear every active effect and reset state.
local function mmOnAuraRemoved(caster)
    local st = mmState[caster]
    if not st then return end
    for victim, effect in pairs(st.active) do
        Osi.RemoveStatus(victim, effect)
    end
    mmState[caster] = nil
end

-- StatusApplied(object, status, causee, storyActionID): causee is the aura owner.
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(object, status, causee, _)
    if status ~= MM_MARK then return end
    local ok, err = pcall(mmOnMarkApplied, object, causee)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Modify Memory (apply) error: " .. tostring(err))
    end
end)

-- StatusRemoved(object, status, causee, applyStoryActionID).
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", function(object, status, causee, _)
    if status == MM_MARK then
        local ok, err = pcall(mmOnMarkRemoved, object, causee)
        if not ok then
            Ext.Utils.PrintError("[Apotheosis] Modify Memory (remove) error: " .. tostring(err))
        end
    elseif status == MM_AURA then
        local ok, err = pcall(mmOnAuraRemoved, object)
        if not ok then
            Ext.Utils.PrintError("[Apotheosis] Modify Memory (aura end) error: " .. tostring(err))
        end
    end
end)

-- =====================================================================
-- Celestial feature "Searing Vengeance" (PHB 2024, Warlock subclass,
-- level 14) - heal to HALF YOUR HIT POINT MAXIMUM.
--
-- The stat side (SEARING_VENGEANCE_DOWNED) guarantees survival with a 1 HP
-- floor and fires the radiant burst. The engine's RegainHitPoints functor
-- can't express "half of max HP", so once the custom downed status lands we
-- top the warlock up to half their maximum here. We only ever RAISE current
-- HP, so the 1 HP floor is never undone if half-max happens to be lower.
-- =====================================================================

local SEARING_DOWNED = "SEARING_VENGEANCE_DOWNED"

local function searingHealHalf(character)
    local entity = Ext.Entity.Get(character)
    if not entity or not entity.Health then return end
    local health = entity.Health
    local maxHp = health.MaxHp or 0
    if maxHp <= 0 then return end
    local half = math.floor(maxHp / 2)
    if health.Hp < half then
        health.Hp = half
        entity:Replicate("Health")
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(object, status, _, _)
    if status ~= SEARING_DOWNED then return end
    local ok, err = pcall(searingHealHalf, object)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Searing Vengeance error: " .. tostring(err))
    end
end)

-- =====================================================================
-- Archfey feature "Bewitching Magic" (PHB 2024, Warlock subclass, level
-- 14) - add your CHARISMA MODIFIER to your spell save DC.
--
-- SpellSaveDC stat boosts only accept a literal integer, so we size the
-- bonus to the caster's Charisma here. The BEWITCHING_MAGIC status (applied
-- by the passive whenever an Enchantment/Illusion spell is cast) drives the
-- 2-turn lifetime: we add a SpellSaveDC boost when it lands and strip it
-- again when it ends. Refreshing the status never stacks the boost.
-- =====================================================================

local BEWITCH_STATUS = "BEWITCHING_MAGIC"
-- bewitchBoost[charGuid] = the exact boost string currently applied to it.
local bewitchBoost = {}

--- Charisma modifier of a character. Stats.Abilities is 1-indexed with [1]=None,
--- so Charisma (the 6th ability) is the 7th entry. Returns nil if unreadable.
local function charismaModifier(character)
    local entity = Ext.Entity.Get(character)
    if entity and entity.Stats and entity.Stats.Abilities then
        local score = entity.Stats.Abilities[7]
        if score then
            return math.floor((score - 10) / 2)
        end
    end
    return nil
end

local function bewitchApply(character)
    if bewitchBoost[character] then return end -- already boosted; don't stack on refresh
    local mod = charismaModifier(character)
    if not mod or mod <= 0 then return end
    local boost = "SpellSaveDC(" .. mod .. ")"
    -- AddBoosts(object, boosts, sourceType, cause).
    Osi.AddBoosts(character, boost, BEWITCH_STATUS, character)
    bewitchBoost[character] = boost
end

local function bewitchRemove(character)
    local boost = bewitchBoost[character]
    if not boost then return end
    -- RemoveBoosts(object, boosts, removeAll, sourceType, cause).
    Osi.RemoveBoosts(character, boost, 0, BEWITCH_STATUS, character)
    bewitchBoost[character] = nil
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(object, status, _, _)
    if status ~= BEWITCH_STATUS then return end
    local ok, err = pcall(bewitchApply, object)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Bewitching Magic (apply) error: " .. tostring(err))
    end
end)

Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", function(object, status, _, _)
    if status ~= BEWITCH_STATUS then return end
    local ok, err = pcall(bewitchRemove, object)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Bewitching Magic (remove) error: " .. tostring(err))
    end
end)

-- =====================================================================
-- Genie Sorcery feature "Elemental Rebuke" (Sorcerer subclass, level 15):
-- when a creature damages you with an attack, a burst of elemental energy
-- automatically strikes it.
--
-- Why Script Extender: the stat engine has no reactive "when hit, damage the
-- attacker" functor for a passive (interrupts aside). We listen to the Osiris
-- AttackedBy event (arity 7: defender, attackerOwner, attacker, damageType,
-- damageAmount, damageCause, storyActionID) and, if the defender owns the marker
-- passive, apply ELEMENTAL_REBUKE_HIT to the attacker. That status's
-- OnApplyFunctors deal the retaliation damage; StackType Overwrite lets it
-- re-trigger on every incoming hit.
-- =====================================================================

local ELEMENTAL_REBUKE_PASSIVE = "NobleGenies_15_ElementalRebuke"
local ELEMENTAL_REBUKE_HIT = "ELEMENTAL_REBUKE_HIT"

Ext.Osiris.RegisterListener("AttackedBy", 7, "after", function(defender, attackerOwner, attacker, damageType, damageAmount, damageCause, storyActionID)
    local ok, err = pcall(function()
        if not defender or not attacker or attacker == "" then return end
        if attacker == defender then return end
        if (tonumber(damageAmount) or 0) <= 0 then return end
        if Osi.HasPassive(defender, ELEMENTAL_REBUKE_PASSIVE) ~= 1 then return end
        if Osi.IsDead(defender) == 1 then return end
        -- Lash back: ELEMENTAL_REBUKE_HIT deals the damage on apply to the bearer.
        -- duration 6.0s = 1 turn; force = 1; source = the rebuking sorcerer.
        Osi.ApplyStatus(attacker, ELEMENTAL_REBUKE_HIT, 6.0, 1, defender)
    end)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Elemental Rebuke error: " .. tostring(err))
    end
end)
