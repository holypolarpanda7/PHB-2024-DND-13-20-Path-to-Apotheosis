-- Subclass features at levels 13-20 (Scripts/gen_subclass_features.py) that need a script.
--  * Shadow Sorcery 18 Umbral Form: at 0 HP, a real Charisma save (DC 5 + half the damage); success -> 3 x Sorcerer level HP.
--  * Hollow Warden 15 Persistent Hunt: at 0 HP in Wrath of the Wild, spend a level 4+ slot -> 5 x its level HP.
--  * Hexblade 14 Masterful Hex: Infectious Hex (1d6 Necrotic to another creature within 30 ft of the cursed target)
--    and Resilient Hex (APO_RESILIENT_HEX only while you concentrate on Hex).
--  * College of Spirits 14 Mystical Connection: a second Spirits from Beyond roll, offered as a free switch.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local SF = {}
local NULL = "NULL_00000000-0000-0000-0000-000000000000"
local ABILITY = { Strength = 2, Dexterity = 3, Constitution = 4, Intelligence = 5, Wisdom = 6, Charisma = 7 }

local function short(g) return g and string.sub(g, -36) or nil end
local function has(c, p) return Osi.HasPassive(c, p) == 1 end

local function abilityMod(c, ability)
    local m = 0
    pcall(function() m = math.floor((Ext.Entity.Get(c).Stats.Abilities[ABILITY[ability]] - 10) / 2) end)
    return m
end

local function profBonus(c)
    local pb = 2
    pcall(function() pb = Ext.Entity.Get(c).Stats.ProficiencyBonus end)
    return pb
end

local function classLevel(c, class)
    local lvl = 0
    pcall(function()
        for _, cl in ipairs(Ext.Entity.Get(c).Classes.Classes) do
            local d = Ext.StaticData.Get(cl.ClassUUID, "ClassDescription")
            if d and d.Name == class then lvl = cl.Level end
        end
    end)
    return lvl
end

-- ---------------------------------------------------------------- 0 HP: Umbral Form, Persistent Hunt
local lastDamage = {}

function SF.OnAttacked(defender, amount)
    lastDamage[short(defender)] = amount
end

local function dropToZero(c)  -- the replacement downed status left c at 1 HP: go down for real
    Osi.ApplyDamage(c, math.max(1, Osi.GetHitpoints(c)), "None", NULL)
end

local function dcGuid(value)  -- a DifficultyClass with this DC (the game ships Legacy_<n> ones)
    local best
    for _, g in ipairs(Ext.StaticData.GetAll("DifficultyClass")) do
        local d = Ext.StaticData.Get(g, "DifficultyClass")
        if d and d.Difficulties and d.Difficulties[1] == value then
            if tostring(d.Name):find("Legacy_", 1, true) == 1 then return g end
            best = best or g
        end
    end
    return best
end

local pendingGrave = {}

-- A real engine Charisma save (proficiency, Bless, Aura of Protection... apply) against DC 5 + half the damage;
-- RollResult decides.
function SF.UmbralGrave(c)
    local dc = math.min(30, 5 + math.floor((lastDamage[c] or 0) / 2))
    local g = dcGuid(dc)
    if not g then
        Log.Warn("Umbral Form: no DifficultyClass " .. dc)
        return
    end
    pendingGrave[c] = dc
    Osi.RequestPassiveRoll(c, NULL, "SavingThrow", "Charisma", g, 0, "APO_UMBRAL_GRAVE_" .. c)
end

function SF.UmbralGraveResult(c, success)
    local dc = pendingGrave[c]
    pendingGrave[c] = nil
    Log.Info(string.format("Umbral Form: Strength of the Grave Charisma save vs DC %d -> %s", dc or -1, success and "success" or "failure"))
    if success then
        Osi.SetHitpoints(c, math.max(1, math.min(Osi.GetMaxHitpoints(c), 3 * classLevel(c, "Sorcerer"))))
    else
        Osi.RemoveStatus(c, "APO_UMBRAL_FORM")  -- 0 HP ends the form (Incapacitated) and its protection
        dropToZero(c)
    end
end

function SF.PersistentHunt(c)
    Ext.Timer.WaitFor(200, function()
        local spent
        pcall(function()
            local best
            for u, entries in pairs(Ext.Entity.Get(c).ActionResources.Resources) do
                local def = Ext.StaticData.Get(u, "ActionResource")
                if def and def.Name == "SpellSlot" then
                    for _, en in ipairs(entries) do
                        if en.Level and en.Level >= 4 and en.Amount >= 1 and (not best or en.Level < best.Level) then best = en end
                    end
                end
            end
            if best then
                best.Amount = best.Amount - 1
                Ext.Entity.Get(c):Replicate("ActionResources")
                spent = best.Level
            end
        end)
        if spent then
            Osi.SetHitpoints(c, math.min(Osi.GetMaxHitpoints(c), 5 * spent))
            Log.Info(string.format("Persistent Hunt: %s spends a level %d slot and stays up with %d HP", c, spent, 5 * spent))
        else
            Osi.ApplyStatus(c, "APO_PERSISTENT_HUNT_SPENT", 6, 1, c)
            Log.Info("Persistent Hunt: no level 4+ slot left")
            Ext.Timer.WaitFor(100, function() dropToZero(c) end)
        end
    end)
end

-- ---------------------------------------------------------------- Masterful Hex
function SF.InfectiousHex(target, warlock)
    local best, bestD
    local tx, ty, tz = Osi.GetPosition(target)
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local ok, g = pcall(function() return e.Uuid.EntityUuid end)
        if ok and g and g ~= target and g ~= warlock and Osi.IsDead(g) == 0 and Osi.IsEnemy(warlock, g) == 1 then
            local x, y, z = Osi.GetPosition(g)
            local d = x and math.sqrt((x - tx) ^ 2 + (y - ty) ^ 2 + (z - tz) ^ 2) or math.huge
            if d <= 9 and (not bestD or d < bestD) then best, bestD = g, d end
        end
    end
    if best then
        Osi.ApplyStatus(best, "APO_INFECTIOUS_HEX_DAMAGE", 0, 1, warlock)
        Log.Info("Infectious Hex: 1d6 Necrotic to " .. best)
    end
end

function SF.OnCasted(caster, spell)
    if not has(caster, "Hexblade_14_MasterfulHex") then return end
    if spell:sub(1, 10) == "Target_Hex" then
        Osi.ApplyStatus(caster, "APO_RESILIENT_HEX", -1, 1, caster)
    else
        local ok, conc = pcall(function() return Ext.Stats.Get(spell).SpellFlags end)
        local isConc = false
        if ok and conc then for _, f in ipairs(conc) do if f == "IsConcentration" then isConc = true end end end
        if isConc then Osi.RemoveStatus(caster, "APO_RESILIENT_HEX") end  -- a new Concentration spell ends Hex
    end
end

function SF.OnTurnStarted(c)
    if Osi.HasActiveStatus(c, "APO_RESILIENT_HEX") == 1 then
        local conc
        pcall(function() conc = Ext.Entity.Get(c).Concentration.SpellId.OriginatorPrototype end)
        if not conc or tostring(conc):sub(1, 10) ~= "Target_Hex" then Osi.RemoveStatus(c, "APO_RESILIENT_HEX") end
    end
end

-- ---------------------------------------------------------------- Mystical Connection
local switching = {}

function SF.SpiritRolled(bard, idx)
    if not has(bard, "Spirits_14_MysticalConnection") or switching[bard] then return end
    local die = 10  -- dnd55e's die: d6 / d8 (Font of Inspiration) / d10 (Magical Secrets) - always d10 by level 14
    if Osi.HasPassive(bard, "Bard_10_MagicalSecrets") ~= 1 then die = Osi.HasPassive(bard, "FontOfInspiration") == 1 and 8 or 6 end
    local second = math.random(0, die - 1)
    if second == idx then return end  -- the same spirit: nothing to choose
    Osi.ApplyStatus(bard, "APO_MYSTICAL_CONNECTION_" .. second, -1, 1, bard)
    Log.Info(string.format("Mystical Connection: rolled spirit %d, second roll %d offered", idx, second))
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("SubclassFeatures " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, _, _, _, amount)
    SF.OnAttacked(defender, amount)
end))

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(target, status, causee)
    target = short(target)
    if status == "APO_UMBRAL_GRAVE_DOWNED" then
        SF.UmbralGrave(target)
    elseif status == "APO_PERSISTENT_HUNT_DOWNED" then
        SF.PersistentHunt(target)
    elseif status == "APO_INFECTIOUS_HEX" and causee then
        SF.InfectiousHex(target, short(causee))
    elseif status:match("^SPIRITS_FROM_BEYOND_%d$") then
        SF.SpiritRolled(target, tonumber(status:match("(%d)$")))
    end
end))

Ext.Osiris.RegisterListener("UsingSpell", 5, "before", guard("UsingSpell", function(c, spell)
    c = short(c)
    if spell:match("^Shout_ApoMysticalConnection_") then  -- the switch applies a spirit: don't offer another
        switching[c] = true
        Ext.Timer.WaitFor(1500, function() switching[c] = nil end)
    end
end))

Ext.Osiris.RegisterListener("RollResult", 6, "after", guard("RollResult", function(ev, roller, _, result)
    if type(ev) == "string" and ev:sub(1, 17) == "APO_UMBRAL_GRAVE_" then
        SF.UmbralGraveResult(ev:sub(18), result == 1)
    end
end))

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(c, spell) SF.OnCasted(short(c), spell) end))
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c) SF.OnTurnStarted(short(c)) end))

return SF
