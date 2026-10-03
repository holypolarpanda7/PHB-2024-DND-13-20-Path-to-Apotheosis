-- Feature effects stats can't express (VISION principle 4: Script Extender when stats can't).
--   WildMagic_SurgeOfUndeath_Passive  when a creature with this passive dies, a zombie rises where it fell
--                                     (stats have no death context; the passive's old OnDeath never fired)
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local FR = {}

local ZOMBIE = "c2a2c269-ede8-4887-99f1-e0c044cc0c75"

function FR.OnDied(character)
    if Osi.HasPassive(character, "WildMagic_SurgeOfUndeath_Passive") ~= 1 then return end
    local x, y, z = Osi.GetPosition(character)
    local g = Osi.CreateAt(ZOMBIE, x, y, z, 0, 1, "")
    Log.Info("Surge of Undeath: a zombie rises from " .. tostring(character) .. " (" .. tostring(g) .. ")")
end

Ext.Osiris.RegisterListener("Died", 1, "after", function(character)
    local ok, err = pcall(FR.OnDied, character)
    if not ok then Log.Error("FeatureRiders Died: " .. tostring(err)) end
end)

Apotheosis = Apotheosis or {}
Apotheosis.FeatureRiders = FR
return FR
