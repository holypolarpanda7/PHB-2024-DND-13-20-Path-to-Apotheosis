-- Spell Mastery (Wizard 18, PHB 2024, issue #18): choose a level 1 and a level 2 Wizard spell with a casting time
-- of an action; cast them at their lowest level without a slot. Whenever you finish a Long Rest you can replace
-- ONE of them. Stats side: Shout_SpellMastery -> SPELL_MASTERY_SELECTION (pick resources + picker shouts)
-- -> a pick applies SM_UNLOCK_<SPELL> (the free-cast copy). This module does what stats can't express:
--   - a pick replaces the earlier pick of the same level
--   - the selection closes after both picks the first time (SPELL_MASTERY_CHOSEN), after ONE pick later
--   - SPELL_MASTERY_BLOCK keeps the selection closed until the next Long Rest
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local SM = {}

-- picker shout -> { spell level, unlock status }
SM.PICKS = {
    Shout_SM_BurningHands = { 1, "SM_UNLOCK_BURNINGHANDS" },
    Shout_SM_CharmPerson = { 1, "SM_UNLOCK_CHARMPERSON" },
    Shout_SM_ChromaticOrb = { 1, "SM_UNLOCK_CHROMATICORB" },
    Shout_SM_ColorSpray = { 1, "SM_UNLOCK_COLORSPRAY" },
    Shout_SM_DisguiseSelf = { 1, "SM_UNLOCK_DISGUISESELF" },
    Shout_SM_FalseLife = { 1, "SM_UNLOCK_FALSELIFE" },
    Shout_SM_FogCloud = { 1, "SM_UNLOCK_FOGCLOUD" },
    Shout_SM_Grease = { 1, "SM_UNLOCK_GREASE" },
    Shout_SM_HideousLaughter = { 1, "SM_UNLOCK_HIDEOUSLAUGHTER" },
    Shout_SM_Longstrider = { 1, "SM_UNLOCK_LONGSTRIDER" },
    Shout_SM_MageArmor = { 1, "SM_UNLOCK_MAGEARMOR" },
    Shout_SM_MagicMissile = { 1, "SM_UNLOCK_MAGICMISSILE" },
    Shout_SM_ProtectionFromEvilAndGood = { 1, "SM_UNLOCK_PROTECTIONFROMEVILANDGOOD" },
    Shout_SM_RayOfSickness = { 1, "SM_UNLOCK_RAYOFSICKNESS" },
    Shout_SM_Sleep = { 1, "SM_UNLOCK_SLEEP" },
    Shout_SM_Thunderwave = { 1, "SM_UNLOCK_THUNDERWAVE" },
    Shout_SM_WitchBolt = { 1, "SM_UNLOCK_WITCHBOLT" },
    Shout_SM_AcidArrow = { 2, "SM_UNLOCK_ACIDARROW" },
    Shout_SM_Blindness = { 2, "SM_UNLOCK_BLINDNESS" },
    Shout_SM_CloudOfDaggers = { 2, "SM_UNLOCK_CLOUDOFDAGGERS" },
    Shout_SM_CrownOfMadness = { 2, "SM_UNLOCK_CROWNOFMADNESS" },
    Shout_SM_Blur = { 2, "SM_UNLOCK_BLUR" },
    Shout_SM_Darkness = { 2, "SM_UNLOCK_DARKNESS" },
    Shout_SM_Darkvision = { 2, "SM_UNLOCK_DARKVISION" },
    Shout_SM_DetectThoughts = { 2, "SM_UNLOCK_DETECTTHOUGHTS" },
    Shout_SM_EnlargeReduce = { 2, "SM_UNLOCK_ENLARGEREDUCE" },
    Shout_SM_FlamingSphere = { 2, "SM_UNLOCK_FLAMINGSPHERE" },
    Shout_SM_HoldPerson = { 2, "SM_UNLOCK_HOLDPERSON" },
    Shout_SM_Invisibility = { 2, "SM_UNLOCK_INVISIBILITY" },
    Shout_SM_MirrorImage = { 2, "SM_UNLOCK_MIRRORIMAGE" },
    Shout_SM_PhantasmalForce = { 2, "SM_UNLOCK_PHANTASMALFORCE" },
    Shout_SM_RayOfEnfeeblement = { 2, "SM_UNLOCK_RAYOFENFEEBLEMENT" },
    Shout_SM_ScorchingRay = { 2, "SM_UNLOCK_SCORCHINGRAY" },
    Shout_SM_Shatter = { 2, "SM_UNLOCK_SHATTER" },
    Shout_SM_Web = { 2, "SM_UNLOCK_WEB" },
}

local function has(c, status) return Osi.HasActiveStatus(c, status) == 1 end

function SM.OnPick(caster, spell)
    local pick = SM.PICKS[spell]
    if not pick then return end
    local level, unlock = pick[1], pick[2]
    for _, v in pairs(SM.PICKS) do
        if v[1] == level and v[2] ~= unlock and has(caster, v[2]) then
            Osi.RemoveStatus(caster, v[2])
            Log.Info("Spell Mastery: " .. v[2] .. " replaced by " .. unlock)
        end
    end
    local swap = has(caster, "SPELL_MASTERY_CHOSEN")
    local picked = { false, false }
    for _, v in pairs(SM.PICKS) do if has(caster, v[2]) or v[2] == unlock then picked[v[1]] = true end end
    if swap or (picked[1] and picked[2]) then
        Osi.RemoveStatus(caster, "SPELL_MASTERY_SELECTION")
        Osi.ApplyStatus(caster, "SPELL_MASTERY_BLOCK", -1, 1, caster)
        Osi.ApplyStatus(caster, "SPELL_MASTERY_CHOSEN", -1, 1, caster)
        Log.Info("Spell Mastery: selection closed for " .. tostring(caster) .. (swap and " (one swap per Long Rest)" or ""))
    end
end

function SM.OnLongRest()
    for _, row in pairs(Osi.DB_Players:Get(nil) or {}) do
        local c = row[1]
        if Osi.HasPassive(c, "SpellMastery") == 1 and has(c, "SPELL_MASTERY_BLOCK") then
            Osi.RemoveStatus(c, "SPELL_MASTERY_BLOCK")
        end
    end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("SpellMastery " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(caster, spell) SM.OnPick(caster, spell) end))
Ext.Osiris.RegisterListener("LongRestFinished", 0, "after", guard("LongRestFinished", SM.OnLongRest))

Apotheosis = Apotheosis or {}
Apotheosis.SpellMastery = SM
return SM
