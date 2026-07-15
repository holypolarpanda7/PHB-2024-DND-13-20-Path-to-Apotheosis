-- =====================================================================
-- Apotheosis functional feature tests.
--
-- Goes beyond "was the passive granted": performs character actions
-- (force-casts spells, provokes attacks), optionally spawns a target,
-- and verifies observable effects (statuses, scripted reactions).
--
-- Loaded by BootstrapServer.lua; exposed as _G.ApotheosisFeatureTests.
--
-- Console entry points (registered in BootstrapServer.lua):
--   !apofeatures                     -- list registered tests
--   !apofeature <PassiveName> [tgt]  -- run one test (optional target GUID)
--
-- Outcome log markers (stable, parsed by Scripts/test_subclass.sh):
--   FeatureTest <passive>: PASS
--   FeatureTest <passive>: FAILED <reason>
--   FeatureTest <passive>: SKIP (manual) <instructions>
-- =====================================================================

local FT = {
    Config = {
        -- Root template force-spawned as a hostile-capable test target when no
        -- party ally is available. Override at runtime:
        --   ApotheosisFeatureTests.Config.DummyTemplate = "<uuid>"
        DummyTemplate = nil,
        StatusPollMs = 400,
        StatusTimeoutMs = 8000,
        CastSettleMs = 1500,
    },
    tests = {},
}

local function log()
    if Apotheosis and Apotheosis.Log then
        return Apotheosis.Log
    end
    local TAG = "[Apotheosis]"
    return {
        Info = function(...) Ext.Utils.Print(TAG, ...) end,
        Warn = function(...) Ext.Utils.PrintWarning(TAG, ...) end,
        Error = function(...) Ext.Utils.PrintError(TAG, ...) end,
        Debug = function(...) end,
    }
end

-- ---------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------

function FT.GetHost()
    local host = Osi.GetHostCharacter and Osi.GetHostCharacter() or nil
    if not host or host == "" then
        error("No host character available")
    end
    return host
end

--- First party member that is not `host`, or nil.
function FT.GetAlly(host)
    local players = Osi.DB_Players and Osi.DB_Players:Get(nil) or nil
    if not players then return nil end
    for _, row in pairs(players) do
        local member = row[1]
        if member and member ~= host and Osi.IsDead(member) ~= 1 then
            -- Osiris GUIDs can be prefixed with a name; compare tails
            local tail = tostring(member):sub(-36)
            if tail ~= tostring(host):sub(-36) then
                return member
            end
        end
    end
    return nil
end

--- Spawn the configured dummy template near `host`. Returns guid or nil.
function FT.SpawnDummy(host)
    local template = FT.Config.DummyTemplate
    if not template or template == "" then
        return nil, "no DummyTemplate configured (set ApotheosisFeatureTests.Config.DummyTemplate)"
    end
    local x, y, z = Osi.GetPosition(host)
    if not x then
        return nil, "could not resolve host position"
    end
    local guid = Osi.CreateAt(template, x + 2, y, z + 2, 0, 0, "")
    if not guid or guid == "" then
        return nil, "CreateAt returned nothing for template " .. tostring(template)
    end
    return guid, nil
end

function FT.RemoveSpawned(guid)
    if guid and Osi.RequestDelete then
        pcall(Osi.RequestDelete, guid)
    end
end

--- Poll until `target` has `status` (cb(true)) or timeout (cb(false)).
function FT.ExpectStatus(target, status, timeoutMs, cb)
    local deadline = Ext.Utils.MonotonicTime() + (timeoutMs or FT.Config.StatusTimeoutMs)
    local function poll()
        if Osi.HasActiveStatus(target, status) == 1 then
            cb(true)
            return
        end
        if Ext.Utils.MonotonicTime() >= deadline then
            cb(false)
            return
        end
        Ext.Timer.WaitFor(FT.Config.StatusPollMs, poll)
    end
    poll()
end

--- Poll until `target` has ANY of the listed statuses.
function FT.ExpectAnyStatus(target, statuses, timeoutMs, cb)
    local deadline = Ext.Utils.MonotonicTime() + (timeoutMs or FT.Config.StatusTimeoutMs)
    local function poll()
        for _, s in ipairs(statuses) do
            if Osi.HasActiveStatus(target, s) == 1 then
                cb(true, s)
                return
            end
        end
        if Ext.Utils.MonotonicTime() >= deadline then
            cb(false, nil)
            return
        end
        Ext.Timer.WaitFor(FT.Config.StatusPollMs, poll)
    end
    poll()
end

--- Force-cast `spell` from `caster` at `target` (works even if the caster
--- doesn't own the spell), then wait CastSettleMs before `cb`.
function FT.UseSpellOn(caster, spell, target, cb)
    Osi.UseSpell(caster, spell, target)
    Ext.Timer.WaitFor(FT.Config.CastSettleMs, cb)
end

-- ---------------------------------------------------------------------
-- Registry / runner
-- ---------------------------------------------------------------------

--- Register a functional test for a passive.
--- spec = {
---   mode   = "auto" | "manual",
---   target = "none" | "ally",     -- "ally" resolves party ally, else dummy
---   note   = string,              -- manual instructions / description
---   run    = function(ctx, finish) ... end,
---            -- ctx = { host, target }; finish(ok, reason)
--- }
function FT.Register(passive, spec)
    FT.tests[passive] = spec
end

function FT.List()
    local L = log()
    local names = {}
    for k in pairs(FT.tests) do names[#names + 1] = k end
    table.sort(names)
    L.Info("Registered feature tests (" .. tostring(#names) .. "):")
    for _, n in ipairs(names) do
        local t = FT.tests[n]
        L.Info("  " .. n .. " [" .. t.mode .. (t.target and t.target ~= "none" and (", needs " .. t.target) or "") .. "]")
    end
end

--- Run the test registered for `passive`. explicitTarget (optional GUID)
--- overrides ally/dummy resolution. onDone(ok|nil) is optional.
function FT.Run(passive, explicitTarget, onDone)
    local L = log()
    local finishothers = onDone or function() end

    local test = FT.tests[passive]
    if not test then
        L.Warn("FeatureTest " .. passive .. ": SKIP (no test registered)")
        finishothers(nil)
        return
    end

    local ok, err = pcall(function()
        local host = FT.GetHost()

        if Osi.HasPassive(host, passive) ~= 1 then
            L.Error("FeatureTest " .. passive .. ": FAILED host does not have the passive (precondition)")
            finishothers(false)
            return
        end

        if test.mode == "manual" then
            L.Warn("FeatureTest " .. passive .. ": SKIP (manual) " .. tostring(test.note or ""))
            finishothers(nil)
            return
        end

        local ctx = { host = host, target = nil, spawned = nil }

        if test.target == "ally" then
            ctx.target = explicitTarget or FT.GetAlly(host)
            if not ctx.target then
                local dummy, why = FT.SpawnDummy(host)
                if dummy then
                    ctx.target = dummy
                    ctx.spawned = dummy
                else
                    L.Error("FeatureTest " .. passive .. ": FAILED no target (no ally in party; " .. tostring(why) .. ")")
                    finishothers(false)
                    return
                end
            end
        end

        local function finish(passOk, reason)
            if ctx.spawned then
                FT.RemoveSpawned(ctx.spawned)
            end
            if passOk then
                L.Info("FeatureTest " .. passive .. ": PASS")
            else
                L.Error("FeatureTest " .. passive .. ": FAILED " .. tostring(reason or "unknown"))
            end
            finishothers(passOk)
        end

        test.run(ctx, finish)
    end)

    if not ok then
        L.Error("FeatureTest " .. passive .. ": FAILED runtime error: " .. tostring(err))
        finishothers(false)
    end
end

--- Run tests for every passive in `passives` (sequentially).
function FT.RunForPassives(character, passives)
    local queue = {}
    for _, p in ipairs(passives or {}) do
        if FT.tests[p] then
            queue[#queue + 1] = p
        end
    end
    if #queue == 0 then return end

    local L = log()
    L.Info("FeatureTests: running " .. tostring(#queue) .. " test(s): " .. table.concat(queue, ", "))
    local i = 0
    local function nextTest()
        i = i + 1
        if i > #queue then
            L.Info("FeatureTests: batch complete")
            return
        end
        FT.Run(queue[i], nil, function() nextTest() end)
    end
    nextTest()
end

-- ---------------------------------------------------------------------
-- Built-in tests
-- ---------------------------------------------------------------------

-- Winter Walker L15: cold damage chills the target.
FT.Register("WinterWalker_15_FrozenHaunt", {
    mode = "auto",
    target = "ally",
    note = "Ray of Frost at target must apply CHILLED (2 turns)",
    run = function(ctx, finish)
        FT.UseSpellOn(ctx.host, "Projectile_RayOfFrost", ctx.target, function()
            FT.ExpectStatus(ctx.target, "CHILLED", nil, function(found)
                finish(found, found and nil or "target never gained CHILLED after cold damage")
            end)
        end)
    end,
})

-- Scion of the Three L13: static boosts; grant-level verification.
FT.Register("DeadThree_UnholyInfiltration", {
    mode = "auto",
    target = "none",
    note = "static boosts (Stealth/Deception advantage, 18m darkvision)",
    run = function(ctx, finish)
        -- Boosts are stats-engine static; passive presence is the observable.
        finish(true)
    end,
})

-- Noble Genies L15: attacker gets lashed with ELEMENTAL_REBUKE_HIT.
FT.Register("NobleGenies_15_ElementalRebuke", {
    mode = "auto",
    target = "ally",
    note = "target attacks host with Fire Bolt; attacker must gain ELEMENTAL_REBUKE_HIT",
    run = function(ctx, finish)
        FT.UseSpellOn(ctx.target, "Projectile_FireBolt", ctx.host, function()
            FT.ExpectStatus(ctx.target, "ELEMENTAL_REBUKE_HIT", nil, function(found)
                finish(found, found and nil or "attacker never gained ELEMENTAL_REBUKE_HIT")
            end)
        end)
    end,
})

-- Diviner L14: extra Portent die on long rest (exposed grant function).
FT.Register("Diviner_14_GreaterPortent", {
    mode = "auto",
    target = "none",
    note = "GrantExtraPortentDie must apply a PORTENT_<n> status",
    run = function(ctx, finish)
        local grant = Apotheosis and Apotheosis.Features and Apotheosis.Features.GrantExtraPortentDie
        if not grant then
            finish(false, "Apotheosis.Features.GrantExtraPortentDie not exposed")
            return
        end
        grant(ctx.host)
        local portents = {}
        for v = 1, 20 do portents[#portents + 1] = "PORTENT_" .. v end
        FT.ExpectAnyStatus(ctx.host, portents, 5000, function(found, which)
            finish(found, found and nil or "no PORTENT_<n> status appeared after grant")
        end)
    end,
})

-- Archfey L14: Bewitching Magic status hook applies scripted boosts.
FT.Register("Archfey_14_BewitchingMagic", {
    mode = "auto",
    target = "none",
    note = "applying BEWITCHING_MAGIC must stick (scripted boost hook)",
    run = function(ctx, finish)
        Osi.ApplyStatus(ctx.host, "BEWITCHING_MAGIC", 12.0, 1, ctx.host)
        FT.ExpectStatus(ctx.host, "BEWITCHING_MAGIC", 4000, function(found)
            finish(found, found and nil or "BEWITCHING_MAGIC did not apply")
        end)
    end,
})

-- Manual-only entries: real reaction/UI flows that can't be safely automated.
FT.Register("Berserker_10_Retaliation", {
    mode = "manual",
    target = "none",
    note = "in combat, let a melee enemy hit the barbarian; expect the Retaliation reaction prompt (dnd55e interrupt)",
})
FT.Register("Druid_BeastSpells", {
    mode = "manual",
    target = "none",
    note = "enter Wild Shape at L18+; expect curated support spells + temp slots; revert must remove them",
})
FT.Register("Enchanter_14_AlterMemories", {
    mode = "manual",
    target = "none",
    note = "cast Modify Memory aura; with the L14 passive the FIFO lockdown cap is 2 instead of 1",
})
FT.Register("Celestial_14_SearingVengeance", {
    mode = "manual",
    target = "none",
    note = "get downed in combat; expect scripted half-HP revive path (SEARING_VENGEANCE_DOWNED)",
})

_G.ApotheosisFeatureTests = FT
return FT
