-- =====================================================================
-- Path to Apotheosis - Server bootstrap (Script Extender)
-- =====================================================================

-- =====================================================================
-- Centralised logging  (see CLAUDE.md "In-game debug feedback loop").
-- Output goes to the SE console (CreateConsole) AND the SE log file
-- (EnableLogging -> %LOCALAPPDATA%\...\Extender Logs\). Every line is
-- tagged [Apotheosis] so it is greppable in the log. Flip Apotheosis.DEBUG
-- to false to silence the verbose Debug() traces.
-- =====================================================================
local TAG = "[Apotheosis]"
Apotheosis = Apotheosis or {}
Apotheosis.DEBUG = true

local Log = {}
function Log.Info(...)  Ext.Utils.Print(TAG, ...) end
function Log.Warn(...)  Ext.Utils.PrintWarning(TAG, ...) end
function Log.Error(...) Ext.Utils.PrintError(TAG, ...) end
function Log.Debug(...) if Apotheosis.DEBUG then Ext.Utils.Print(TAG, "[dbg]", ...) end end
Apotheosis.Log = Log

Log.Info("BootstrapServer.lua loading - server context")

-- Heartbeat: confirm the mod actually reached a running session. If this line
-- never prints to the console, the mod is not being loaded (check deployment).
Ext.Events.SessionLoaded:Subscribe(function()
    local ok, err = pcall(function()
        Log.Info("SessionLoaded - Apotheosis server scripts active")
    end)
    if not ok then Log.Error("SessionLoaded heartbeat error: " .. tostring(err)) end
end)

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

-- =====================================================================
-- Druid feature "Beast Spells" (PHB 2024, level 18) - LIMITED adaptation.
--
-- The literal feature ("cast your druid spells while in Wild Shape") can't be
-- expressed in Stats data: a shapeshifted druid is polymorphed into a beast
-- that owns no spellbook and no spell slots. As a pragmatic stand-in we grant a
-- curated set of SUPPORT spells (offense is already covered by the beast's own
-- attacks) plus a small pool of temporary spell slots to fuel them, whenever a
-- druid that owns the marker passive Druid_BeastSpells enters Wild Shape, and
-- strip everything again on revert.
--
-- WILDSHAPE_TECHNICAL is the engine's own marker status and lives on the SAME
-- entity GUID while shapeshifted, so StatusApplied / StatusRemoved give clean
-- transform / revert hooks. The engine restores the druid's pre-transform
-- resources on revert, so the temporary slots never leak into normal play; we
-- still revoke our grants explicitly for safety and to cover partial reverts.
-- =====================================================================

local BEAST_SPELLS_PASSIVE = "Druid_BeastSpells"
local BEAST_SPELLS_MARK    = "WILDSHAPE_TECHNICAL"

-- Curated support spells granted while in beast form.
local BEAST_SPELLS_GRANTED = {
    "Target_HealingWord",
    "Target_CureWounds",
    "Target_LesserRestoration",
    "Target_FaerieFire",
    "Target_Moonbeam",
}

-- Temporary slots to fuel the curated list: 2x level 1, 1x level 2.
local BEAST_SPELLS_SLOTS = "ActionResource(SpellSlot,2,1);ActionResource(SpellSlot,1,2)"

-- beastSpellsActive[charGuid] = true while spells/slots are granted to it.
local beastSpellsActive = {}

local function beastSpellsGrant(character)
    if beastSpellsActive[character] then return end -- already granted; don't stack
    if Osi.HasPassive(character, BEAST_SPELLS_PASSIVE) ~= 1 then return end
    for _, spell in ipairs(BEAST_SPELLS_GRANTED) do
        Osi.AddSpell(character, spell, 0, 0)
    end
    -- AddBoosts(object, boosts, sourceType, cause); cause/source = the marker status.
    Osi.AddBoosts(character, BEAST_SPELLS_SLOTS, BEAST_SPELLS_MARK, character)
    beastSpellsActive[character] = true
end

local function beastSpellsRevoke(character)
    if not beastSpellsActive[character] then return end
    for _, spell in ipairs(BEAST_SPELLS_GRANTED) do
        Osi.RemoveSpell(character, spell, 0)
    end
    -- RemoveBoosts(object, boosts, removeAll, sourceType, cause).
    Osi.RemoveBoosts(character, BEAST_SPELLS_SLOTS, 0, BEAST_SPELLS_MARK, character)
    beastSpellsActive[character] = nil
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(object, status, _, _)
    if status ~= BEAST_SPELLS_MARK then return end
    local ok, err = pcall(beastSpellsGrant, object)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Beast Spells (grant) error: " .. tostring(err))
    end
end)

Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", function(object, status, _, _)
    if status ~= BEAST_SPELLS_MARK then return end
    local ok, err = pcall(beastSpellsRevoke, object)
    if not ok then
        Ext.Utils.PrintError("[Apotheosis] Beast Spells (revoke) error: " .. tostring(err))
    end
end)

-- =====================================================================
-- Manual smoke driver.
--
-- Intended loop:
--   1. Start a fresh game / finish character creation.
--   2. Load into the world.
--   3. Open the Script Extender console and run: server
--   4. Trigger a smoke command such as: Apotheosis.Smoke.RunLevelSweep()
--
-- This is intentionally MANUAL-triggered, not auto-run. The driver can move
-- the host character through level checkpoints and run non-destructive checks.
-- Encounter-specific enemy/status orchestration is the next layer to add per
-- class/subclass plan.
-- =====================================================================

local function stringifyValue(value)
    if type(value) ~= "table" then
        return tostring(value)
    end

    local parts = {}
    for key, item in pairs(value) do
        parts[#parts + 1] = tostring(key) .. "=" .. stringifyValue(item)
    end
    table.sort(parts)
    return "{" .. table.concat(parts, ", ") .. "}"
end

local function getHostCharacterHandle()
    if Osi.GetHostCharacter then
        local host = Osi.GetHostCharacter()
        if host and host ~= "" then
            return host
        end
    end

    local players = Osi.DB_Players:Get(nil)
    if players then
        for _, row in pairs(players) do
            if row and row[1] and row[1] ~= "" then
                return row[1]
            end
        end
    end

    return nil
end

local Smoke = Apotheosis.Smoke or {}
Apotheosis.Smoke = Smoke

Smoke.Wizard = Smoke.Wizard or {}

Smoke.DEFAULT_START_LEVEL = 12
Smoke.DEFAULT_END_LEVEL = 20
Smoke.LEVEL_SETTLE_MS = 1200
Smoke.POST_RESTORE_SETTLE_MS = 600
Smoke.MARKER_PASSIVES = {
    "Barbarian_BrutalStrike_Improved",
    "Diviner_14_GreaterPortent",
    "Druid_BeastSpells",
    "Enchanter_14_AlterMemories",
    "NobleGenies_15_ElementalRebuke",
    "Rogue_SlipperyMind",
}

local smokeState = {
    running = false,
    lastHost = nil,
}

local function smokeDetectMarkers(character)
    local found = {}
    for _, passive in ipairs(Smoke.MARKER_PASSIVES) do
        if Osi.HasPassive(character, passive) == 1 then
            found[#found + 1] = passive
        end
    end
    return found
end

local function smokeGetHost()
    local host = getHostCharacterHandle()
    if not host then
        error("Smoke could not resolve a host character; load fully into the world first")
    end
    smokeState.lastHost = host
    return host
end

local function smokeRestore(character)
    if Osi.PROC_CharacterFullRestore then
        Osi.PROC_CharacterFullRestore(character)
    end
    if Osi.RemoveHarmfulStatuses then
        Osi.RemoveHarmfulStatuses(character)
    end
    if Osi.SetHitpointsPercentage then
        Osi.SetHitpointsPercentage(character, 100)
    end
end

local function smokeSetLevel(character, level)
    if not Osi.SetLevel then
        error("Osi.SetLevel is unavailable in this runtime")
    end
    Osi.SetLevel(character, level)
end

local function smokeRunTimedLevelSequence(character, startAt, endAt, perLevel, onComplete)
    local function step(level)
        if level > endAt then
            if onComplete then
                onComplete()
            end
            return
        end

        smokeSetLevel(character, level)
        Log.Info("Smoke queued level " .. tostring(level) .. " - waiting for progression state to settle")

        Ext.Timer.WaitFor(Smoke.LEVEL_SETTLE_MS, function()
            smokeRestore(character)
            Ext.Timer.WaitFor(Smoke.POST_RESTORE_SETTLE_MS, function()
                perLevel(level)
                step(level + 1)
            end)
        end)
    end

    step(startAt)
end

local function smokeHasPassive(character, passive)
    return Osi.HasPassive(character, passive) == 1
end

local function smokeHasSpell(character, spell)
    if not Osi.HasSpell then
        return false
    end
    return Osi.HasSpell(character, spell, 0) == 1
end

local function smokeDescribeBuild(character)
    local tags = Osi.CharacterGetTags(character)
    local markers = smokeDetectMarkers(character)
    Log.Info("Smoke host = " .. tostring(character))
    Log.Info("Smoke tags = " .. stringifyValue(tags))
    if #markers > 0 then
        Log.Info("Smoke tracked markers = " .. table.concat(markers, ", "))
    else
        Log.Info("Smoke tracked markers = <none>")
    end
end

local function smokeRunPassiveChecks(character, level)
    local markers = smokeDetectMarkers(character)
    Log.Info("Smoke level " .. tostring(level) .. " marker scan")
    if #markers == 0 then
        Log.Warn("Smoke level " .. tostring(level) .. ": no tracked marker passives found on host")
        return
    end

    for _, passive in ipairs(markers) do
        if Osi.HasPassive(character, passive) == 1 then
            Log.Info("Smoke PASS L" .. tostring(level) .. ": HasPassive(" .. passive .. ")")
        else
            Log.Error("Smoke FAIL L" .. tostring(level) .. ": missing passive " .. passive)
        end
    end
end

function Smoke.CaptureBuild()
    local ok, err = pcall(function()
        local host = smokeGetHost()
        smokeDescribeBuild(host)
    end)
    if not ok then
        Log.Error("Smoke.CaptureBuild error: " .. tostring(err))
    end
end

function Smoke.SetLevel(level)
    local ok, err = pcall(function()
        local host = smokeGetHost()
        smokeSetLevel(host, tonumber(level) or level)
        smokeRestore(host)
        Log.Info("Smoke moved host to level " .. tostring(level))
        smokeDescribeBuild(host)
    end)
    if not ok then
        Log.Error("Smoke.SetLevel error: " .. tostring(err))
    end
end

function Smoke.RunLevelSweep(startLevel, endLevel)
    local ok, err = pcall(function()
        if smokeState.running then
            error("Smoke run already in progress")
        end

        smokeState.running = true
        local host = smokeGetHost()
        local startAt = tonumber(startLevel) or Smoke.DEFAULT_START_LEVEL
        local endAt = tonumber(endLevel) or Smoke.DEFAULT_END_LEVEL

        Log.Info("Smoke level sweep starting: " .. tostring(startAt) .. " -> " .. tostring(endAt))
        smokeDescribeBuild(host)

        smokeRunTimedLevelSequence(host, startAt, endAt, function(level)
            Log.Info("Smoke reached level " .. tostring(level))
            smokeRunPassiveChecks(host, level)
        end, function()
            Log.Info("Smoke level sweep complete")
            Log.Info("Next step: add class/subclass-specific encounter hooks to Apotheosis.Smoke plans")
            smokeState.running = false
        end)
    end)
    if not ok then
        smokeState.running = false
        Log.Error("Smoke.RunLevelSweep error: " .. tostring(err))
    end
end

local WIZARD_LEVEL_EXPECTATIONS = {
    [12] = {
        absentPassives = { "SpellMastery", "Wizard_SignatureSpells" },
    },
    [13] = {
        passives = { "UnlockedSpellSlotLevel7" },
    },
    [15] = {
        passives = { "UnlockedSpellSlotLevel8" },
    },
    [17] = {
        passives = { "UnlockedSpellSlotLevel9" },
    },
    [18] = {
        passives = { "SpellMastery" },
        spells = { "Shout_SpellMastery" },
    },
    [20] = {
        passives = { "Wizard_SignatureSpells" },
    },
}

local WIZARD_SUBCLASS_EXPECTATIONS = {
    {
        passive = "Abjurer_14_SpellResistance",
        label = "AbjurationSchool",
    },
    {
        passive = "Diviner_14_GreaterPortent",
        label = "DivinationSchool",
        custom = function(character)
            grantExtraPortentDie(character)
            Log.Info("Wizard smoke invoked Greater Portent grant helper")
        end,
    },
    {
        passive = "Evoker_14_Overchannel",
        label = "EvocationSchool",
    },
    {
        passive = "Illusionist_14_IllusoryReality",
        label = "IllusionSchool",
    },
    {
        passive = "SongVictory",
        label = "Bladesinger",
    },
    {
        passive = "Conjurer_14_SplinteredSummons",
        label = "ConjurationSchool",
    },
    {
        passive = "SplitEnchantment",
        label = "EnchantmentSchool",
    },
    {
        passive = "Enchanter_14_AlterMemories",
        label = "EnchantmentSchool",
        spells = { "Shout_Apotheosis_ModifyMemory" },
    },
    {
        passive = "Necromancer_14_DeathsMaster",
        label = "NecromancySchool",
        spells = { "Shout_Apotheosis_BolsterUndead" },
    },
    {
        passive = "Transmuter_14_MasterTransmuter",
        label = "TransmutationSchool",
        spells = { "Target_Apotheosis_Panacea" },
    },
}

local function smokeAssertPresent(character, level, kind, value)
    if kind == "passive" then
        if smokeHasPassive(character, value) then
            Log.Info("Wizard PASS L" .. tostring(level) .. ": HasPassive(" .. value .. ")")
        else
            Log.Error("Wizard FAIL L" .. tostring(level) .. ": missing passive " .. value)
        end
    elseif kind == "spell" then
        if smokeHasSpell(character, value) then
            Log.Info("Wizard PASS L" .. tostring(level) .. ": HasSpell(" .. value .. ")")
        else
            Log.Error("Wizard FAIL L" .. tostring(level) .. ": missing spell " .. value)
        end
    end
end

local function smokeAssertAbsent(character, level, kind, value)
    if kind == "passive" then
        if smokeHasPassive(character, value) then
            Log.Error("Wizard FAIL L" .. tostring(level) .. ": unexpected passive " .. value)
        else
            Log.Info("Wizard PASS L" .. tostring(level) .. ": passive absent as expected (" .. value .. ")")
        end
    end
end

local function smokeRunWizardLevelChecks(character, level)
    local expectation = WIZARD_LEVEL_EXPECTATIONS[level]
    if not expectation then
        Log.Info("Wizard smoke L" .. tostring(level) .. ": no generic level assertion registered")
        return
    end

    if expectation.passives then
        for _, passive in ipairs(expectation.passives) do
            smokeAssertPresent(character, level, "passive", passive)
        end
    end

    if expectation.spells then
        for _, spell in ipairs(expectation.spells) do
            smokeAssertPresent(character, level, "spell", spell)
        end
    end

    if expectation.absentPassives then
        for _, passive in ipairs(expectation.absentPassives) do
            smokeAssertAbsent(character, level, "passive", passive)
        end
    end
end

local function smokeRunWizardSubclassChecks(character, level)
    if level < 14 then
        return
    end

    local matched = false
    for _, subclass in ipairs(WIZARD_SUBCLASS_EXPECTATIONS) do
        if smokeHasPassive(character, subclass.passive) then
            matched = true
            Log.Info("Wizard subclass smoke detected = " .. subclass.label)
            smokeAssertPresent(character, level, "passive", subclass.passive)
            if subclass.spells then
                for _, spell in ipairs(subclass.spells) do
                    smokeAssertPresent(character, level, "spell", spell)
                end
            end
            if subclass.custom then
                local ok, err = pcall(subclass.custom, character)
                if not ok then
                    Log.Error("Wizard FAIL L" .. tostring(level) .. ": subclass hook error for " .. subclass.passive .. ": " .. tostring(err))
                end
            end
        end
    end

    if not matched then
        Log.Warn("Wizard smoke L" .. tostring(level) .. ": no known level-14 wizard subclass passive detected")
    end
end

function Smoke.Wizard.RunSweep(startLevel, endLevel)
    local ok, err = pcall(function()
        if smokeState.running then
            error("Smoke run already in progress")
        end

        smokeState.running = true
        local host = smokeGetHost()
        local startAt = tonumber(startLevel) or Smoke.DEFAULT_START_LEVEL
        local endAt = tonumber(endLevel) or Smoke.DEFAULT_END_LEVEL

        Log.Info("Wizard smoke sweep starting: " .. tostring(startAt) .. " -> " .. tostring(endAt))
        smokeDescribeBuild(host)

        smokeRunTimedLevelSequence(host, startAt, endAt, function(level)
            Log.Info("Wizard smoke reached level " .. tostring(level))
            smokeRunWizardLevelChecks(host, level)
            smokeRunWizardSubclassChecks(host, level)
        end, function()
            Log.Info("Wizard smoke sweep complete")
            smokeState.running = false
        end)
    end)
    if not ok then
        smokeState.running = false
        Log.Error("Smoke.Wizard.RunSweep error: " .. tostring(err))
    end
end

function Smoke.Wizard.Help()
    Log.Info("Wizard smoke commands:")
    Log.Info("  Apotheosis.Smoke.Wizard.RunSweep()")
    Log.Info("  Apotheosis.Smoke.Wizard.RunSweep(12, 20)")
    Log.Info("  timing: " .. tostring(Smoke.LEVEL_SETTLE_MS) .. "ms after SetLevel, " .. tostring(Smoke.POST_RESTORE_SETTLE_MS) .. "ms after restore")
end

function Smoke.Help()
    Log.Info("Smoke commands:")
    Log.Info("  Apotheosis.Smoke.CaptureBuild()")
    Log.Info("  Apotheosis.Smoke.SetLevel(12)")
    Log.Info("  Apotheosis.Smoke.RunLevelSweep()")
    Log.Info("  Apotheosis.Smoke.RunLevelSweep(12, 20)")
    Log.Info("  Apotheosis.Smoke.Wizard.Help()")
    Log.Info("  Apotheosis.Smoke.Wizard.RunSweep()")
end

Ext.Events.SessionLoaded:Subscribe(function()
    local ok, err = pcall(function()
        Log.Info("Smoke API ready - enter 'server' then Apotheosis.Smoke.Help() in the SE console")
    end)
    if not ok then
        Log.Error("Smoke API readiness error: " .. tostring(err))
    end
end)
