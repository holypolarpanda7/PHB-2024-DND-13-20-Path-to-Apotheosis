-- Illrigger 13-20 (issue #7): the scripted parts of Scripts/gen_illrigger.py's features.
--  * Last Word (13th-level boon): dropping to 0 with seals left expends up to three for an explosion
--    (ILLRIGGER_LAST_WORD_<n>: CreateExplosion + RegainHitPoints, which also gets you back up).
--  * Soul's Doom (13th-level boon): a doomed creature takes extra damage equal to the Illrigger's
--    Proficiency Bonus whenever it takes damage.
--  * Hell Mage (Architect of Ruin 18): a successful save against an enemy seals that enemy.
--  * Sanguine Gift (Sanguine Knight 13, toggle): healing within 30 feet costs a seal for +Illrigger level.
--  * Haemal Exchange (Sanguine Knight 15): the d8 goes to the nearest ally; it ends after their next save.
--  * Quid Pro Quo (Hellspeaker 15): a devil (a Merregon - BG3 has no horned devil) stands in for the banished.
--  * Dark Malediction (Shadowmaster 18): interdicted creatures radiate darkness.
--  * Seal placement boons: Flash of Brimstone (any seal), Dis's Onslaught, Soul's Doom and By the Throat (the
--    Bonus Action seal).
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local IL = {}

local function has(c, p) return Osi.HasPassive(c, p) == 1 end
local function short(g) return g and string.sub(g, -36) or nil end

local function seals(c)
    local n = 0
    pcall(function()
        for u, entries in pairs(Ext.Entity.Get(c).ActionResources.Resources) do
            local def = Ext.StaticData.Get(u, "ActionResource")
            if def and def.Name == "Seal" then n = entries[1].Amount end
        end
    end)
    return n
end

local function spendSeals(c, n)
    local e = Ext.Entity.Get(c)
    for u, entries in pairs(e.ActionResources.Resources) do
        local def = Ext.StaticData.Get(u, "ActionResource")
        if def and def.Name == "Seal" then entries[1].Amount = math.max(0, entries[1].Amount - n) end
    end
    e:Replicate("ActionResources")
end

-- ---------------------------------------------------------------- Last Word
function IL.OnDowned(c)
    if not has(c, "InterdictBoons_13_LastWord") then return end
    local n = math.min(3, math.floor(seals(c)))
    if n < 1 then return end
    spendSeals(c, n)
    Osi.ApplyStatus(c, "ILLRIGGER_LAST_WORD_" .. n, 0, 1, c)
    Log.Info(string.format("Last Word: %s expends %d seal(s) and explodes", c, n))
end

-- ---------------------------------------------------------------- Soul's Doom
local doomedBy = {}   -- target -> Illrigger
local recent = {}     -- target -> time of our own extra damage (it raises AttackedBy too)

function IL.OnStatusApplied(target, status, causee)
    if status == "ILLRIGGER_SOULS_DOOM" and causee then doomedBy[short(target)] = short(causee) end
end

function IL.OnStatusRemoved(target, status)
    if status == "ILLRIGGER_SOULS_DOOM" then doomedBy[short(target)] = nil end
end

function IL.OnAttackedBy(defender, attacker, damageAmount)
    local t = short(defender)
    local il = doomedBy[t]
    if not il or (damageAmount or 0) <= 0 then return end
    if Osi.HasActiveStatus(t, "ILLRIGGER_SOULS_DOOM") ~= 1 then doomedBy[t] = nil return end
    local now = Ext.Utils.MonotonicTime()
    if recent[t] and now - recent[t] < 250 then return end
    recent[t] = now
    local pb = Ext.Entity.Get(il).Stats.ProficiencyBonus
    Osi.ApplyDamage(t, pb, "Necrotic", il)
    Log.Info(string.format("Soul's Doom: %s takes %d extra damage", t, pb))
end

-- ---------------------------------------------------------------- helpers for the subclass features
local ILLRIGGER = "33bd368d-2ff4-4add-8692-66d87372053a"
local MERREGON = "9bbee0e3-4141-4561-9543-15d3a21000f4"

local function classLevel(c, classUuid)
    local ok, lvl = pcall(function()
        for _, cl in pairs(Ext.Entity.Get(c).Classes.Classes) do
            if tostring(cl.ClassUUID) == classUuid then return cl.Level end
        end
        return 0
    end)
    return ok and lvl or 0
end

local function within(a, b, m)
    local ok, d = pcall(Osi.GetDistanceTo, a, b)
    return ok and d and d <= m
end

local function partyAndNearby(c, radius)
    local out = {}
    pcall(function()
        for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
            local g = e.Uuid and e.Uuid.EntityUuid
            if g and Osi.IsDead(g) == 0 and within(c, g, radius) then out[#out + 1] = g end
        end
    end)
    return out
end

-- ---------------------------------------------------------------- Sanguine Gift
function IL.OnHealed(target)
    for _, sk in ipairs(partyAndNearby(target, 9)) do
        if Osi.HasActiveStatus(sk, "ILLRIGGER_SANGUINE_GIFT") == 1 and has(sk, "SanguineKnight_13_SanguineGift")
            and (sk == target or Osi.IsAlly(sk, target) == 1) and seals(sk) >= 1 and Osi.CanSee(sk, target) == 1 then
            spendSeals(sk, 1)
            local lvl = classLevel(sk, ILLRIGGER)
            Osi.SetHitpoints(target, math.min(Osi.GetMaxHitpoints(target), Osi.GetHitpoints(target) + lvl))
            Log.Info(string.format("Sanguine Gift: %s regains %d more", target, lvl))
            return
        end
    end
end

-- ---------------------------------------------------------------- Haemal Exchange
local empowered = {}
function IL.OnHaemalPending(sk)
    Osi.RemoveStatus(sk, "ILLRIGGER_HAEMAL_PENDING")
    local best, bestD
    for _, g in ipairs(partyAndNearby(sk, 9)) do
        if g ~= sk and Osi.IsAlly(sk, g) == 1 then
            local d = Osi.GetDistanceTo(sk, g)
            if not bestD or d < bestD then best, bestD = g, d end
        end
    end
    if best then
        Osi.ApplyStatus(best, "ILLRIGGER_HAEMAL_EMPOWER", 10 * 6.0, 1, sk)
        empowered[best] = true
        Log.Info("Haemal Exchange: " .. best .. " gains 1d8 on its next roll")
    end
end

-- ---------------------------------------------------------------- Quid Pro Quo
local devils = {}  -- banished guid -> devil guid
function IL.OnBanished(target, causee)
    local x, y, z = Osi.GetPosition(target)
    local devil = Osi.CreateAt(MERREGON, x, y, z, 0, 1, "")
    if not devil then return end
    devil = short(devil)
    pcall(Osi.SetFaction, devil, Osi.GetFaction(causee))
    pcall(Osi.AddPartyFollower, devil, causee)
    devils[short(target)] = devil
    Log.Info("Quid Pro Quo: a devil takes the place of " .. short(target))
end

function IL.OnBanishEnded(target)
    local devil = devils[short(target)]
    if devil then
        pcall(Osi.RemovePartyFollower, devil, Osi.GetHostCharacter())
        pcall(Osi.RequestDelete, devil)
        devils[short(target)] = nil
    end
end

-- ---------------------------------------------------------------- Hell Mage (any successful save vs an enemy)
local seenRolls = {}
Ext.Entity.OnCreate("SavingThrowRolledEvent", function(_, _, c)
    local ok, err = pcall(function()
        local cr = c.ConditionRoll
        local key = tostring(cr.RollUuid)
        if seenRolls[key] then return end
        seenRolls[key] = true
        local function g(h) local ok2, v = pcall(function() return h.Uuid.EntityUuid end) return ok2 and v or nil end
        local saver, source = g(c.Target), g(c.Source)
        local sc = tostring(c.SpellCastUuid)
        if sc ~= "00000000-0000-0000-0000-000000000000" and sc ~= "nil" then saver, source = source, saver end
        if cr.SwappedSourceAndTarget then saver, source = source, saver end
        if not saver or not source then return end
        if empowered[saver] then  -- Haemal Exchange's d8 is spent on this save
            empowered[saver] = nil
            Ext.Timer.WaitFor(500, function() Osi.RemoveStatus(saver, "ILLRIGGER_HAEMAL_EMPOWER") end)
        end
        if cr.Roll.Result.Total < cr.Difficulty then return end
        for _, aor in ipairs(partyAndNearby(saver, 9)) do
            if has(aor, "ArchitectOfRuin_18_HellMage") and (aor == saver or Osi.IsAlly(aor, saver) == 1) and Osi.IsEnemy(aor, source) == 1 then
                Osi.ApplyStatus(source, "INTERDICTED", -1, 1, aor)
                Log.Info("Hell Mage: " .. source .. " is sealed after a successful save")
                return
            end
        end
    end)
    if not ok then Log.Error("Illrigger SavingThrowRolledEvent: " .. tostring(err)) end
end)

-- ---------------------------------------------------------------- seal placement boons
-- dnd55e's Bonus Action seal is Target_Seal; seals from weapon hits come from Baleful Interdict. A placement is
-- seen as INTERDICTED applied with the Illrigger as cause; it was the Bonus Action one if Target_Seal just went
-- out at that creature.
local sealCasts = {}  -- Illrigger -> { target, time }
local pendingRolled, rolledSub = {}, nil

local function castWithRolls(caster, spell, target)  -- Osi.UseSpell, but the save is rolled for real (as EpicBoons.lua)
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

function IL.OnSealCast(caster, target)
    sealCasts[short(caster)] = { target = short(target), time = Ext.Utils.MonotonicTime() }
end

function IL.OnSealPlaced(target, il)
    local t = short(target)
    local cast = sealCasts[il]
    local bonusAction = cast and cast.target == t and Ext.Utils.MonotonicTime() - cast.time < 5000
    if bonusAction then sealCasts[il] = nil end
    if has(il, "InterdictBoons_13_FlashOfBrimstone") then Osi.ApplyStatus(il, "ILLRIGGER_FLASH_READY", 6.0, 1, il) end
    if not bonusAction then return end
    if has(il, "InterdictBoons_13_DissOnslaught") then Osi.ApplyStatus(il, "ILLRIGGER_DISS_ONSLAUGHT", 6.0, 1, il) end
    if has(il, "InterdictBoons_13_SoulsDoom") then Osi.ApplyStatus(t, "ILLRIGGER_SOULS_DOOM", 60.0, 1, il) end
    if has(il, "Painkiller_13_ByTheThroat") then castWithRolls(il, "Target_Illrigger_ByTheThroat", t) end
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("Illrigger " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(t, s, c)
    if s == "DOWNED" then IL.OnDowned(short(t))
    elseif s == "HEAL" then IL.OnHealed(short(t))
    elseif s == "ILLRIGGER_HAEMAL_PENDING" then IL.OnHaemalPending(short(t))
    elseif s == "ILLRIGGER_QUID_PRO_QUO" and c then IL.OnBanished(t, short(c))
    elseif s == "INTERDICTED" and c then
        IL.OnSealPlaced(t, short(c))
        if has(short(c), "Shadowmaster_18_DarkMalediction") then Osi.ApplyStatus(t, "ILLRIGGER_DARK_MALEDICTION", -1, 1, short(c)) end
    end
    IL.OnStatusApplied(t, s, c)
end))
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("StatusRemoved", function(t, s)
    if s == "INTERDICTED" then Osi.RemoveStatus(t, "ILLRIGGER_DARK_MALEDICTION")
    elseif s == "ILLRIGGER_QUID_PRO_QUO" then IL.OnBanishEnded(t)
    elseif s == "ILLRIGGER_HAEMAL_EMPOWER" then empowered[short(t)] = nil
    end
    IL.OnStatusRemoved(t, s)
end))
Ext.Osiris.RegisterListener("UsingSpellOnTarget", 6, "after", guard("UsingSpellOnTarget", function(caster, target, spell)
    if spell == "Target_Seal" then IL.OnSealCast(caster, target) end
end))
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, attackerOwner, attacker2, damageType, damageAmount)
    IL.OnAttackedBy(defender, attackerOwner, damageAmount)
end))

return IL
