#!/usr/bin/env python3
"""Make a test-only Lua overlay to load a save identically in original and rebuilt engines.

The original GUIScenes bytecode is retained under an alias. Only the test driver is new;
the resulting PAK contains game data and must stay in the local test workspace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def read_entry(path, wanted):
    with path.open('rb') as stream:
        if stream.read(8) != b'GRES' + struct.pack('<I', 100):
            raise ValueError('expected GRES 100 archive')
        count, = struct.unpack('<I', stream.read(4))
        for _ in range(count):
            name = stream.read(128).split(b'\0')[0].decode('cp1251')
            offset, size = struct.unpack('<II', stream.read(8))
            if name.lower() == wanted:
                stream.seek(offset)
                result = stream.read(size)
                if len(result) != size:
                    raise ValueError('truncated archive entry')
                return result
    raise ValueError('entry not found: ' + wanted)


def write_pak(path, entries):
    if path.exists():
        raise ValueError('output already exists')
    offset = 12 + 136 * len(entries)
    table, data = bytearray(), bytearray()
    for name, blob in sorted(entries.items()):
        table += name.encode('ascii').ljust(128, b'\0') + struct.pack('<II', offset + len(data), len(blob))
        data += blob
    path.write_bytes(b'GRES' + struct.pack('<II', 100, len(entries)) + table + data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resource0', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--save', default='game0')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--roundtrip', action='store_true', help='save, perturb gold, reload, assert gold/army restoration, save evidence')
    mode.add_argument('--continent2', action='store_true', help='use the original story Move Object route to continent 2 and save evidence there')
    mode.add_argument('--spellbook', action='store_true', help='open the world spellbook with the loaded hero’s spells')
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_]+', args.save):
        parser.error('save name must use letters, digits or underscores')
    original = read_entry(args.resource0, 'guiscenes.lua')
    driver = '''DoFile("scenario_original_guiscenes")
local menuUpdate = GUIScene.MainMenu.Update
local loadUpdate = GUIScene.Load.Update
local opened, selected = false, false
function GUIScene.MainMenu:Update(...)
  if not opened then opened = true; self:_Load() end
  if menuUpdate then return menuUpdate(self, ...) end
end
function GUIScene.Load:Update(...)
  if loadUpdate then loadUpdate(self, ...) end
  if not selected and self.scene and self._SlotNames then
    for i, name in ipairs(self._SlotNames) do
      if name == "SAVE_NAME" then
        selected = true
        self._CurrentSlotNum = i - (self._FirstSlotNum or 1) + 1
        self:StrongLoad()
        break
      end
    end
  end
end
'''.replace('SAVE_NAME', args.save).encode('ascii')
    if args.roundtrip:
        driver += b'''
local worldLoad = GUIScene.WorldLevel.Load
local roundtripStarted = false
local function armySignature()
  local result = {}
  for i, troop in ipairs(HeroArmy.Troops) do result[i] = tostring(troop.Unit)..":"..tostring(troop.Qn) end
  return table.concat(result, "|")
end
function GUIScene.WorldLevel:Load(...)
  worldLoad(self, ...)
  if not roundtripStarted then
    roundtripStarted = true
    WorldLevel.SaveLoad = function()
      local gold, army = Hero.Inventory.Gold, armySignature()
      Serializator:Save("scenario_saved")
      Hero.Inventory.Gold = gold + 137
      Serializator:Load("scenario_saved")
      assert(Hero.Inventory.Gold == gold, "roundtrip gold not restored")
      assert(armySignature() == army, "roundtrip army not restored")
      Serializator:Save("scenario_reloaded")
    end
  end
end
'''
    if args.continent2:
        driver += b'''
local worldLoad = GUIScene.WorldLevel.Load
function GUIScene.WorldLevel:Load(...)
  worldLoad(self, ...)
  if WorldLevel.curContinent == 1 then
    WorldLevel.SaveLoad = function()
      Actions:DoAction("Move Object", "Hero", "continent2", 5185, 6110, 83, false)
    end
  elseif WorldLevel.curContinent == 2 then
    WorldLevel.SaveLoad = function()
      assert(WorldLevel.curContinent == 2, "wrong destination continent")
      Serializator:Save("scenario_continent2")
    end
  end
end
'''
    if args.spellbook:
        driver += b'''
local worldLoad = GUIScene.WorldLevel.Load
local openedSpellbook = false
function GUIScene.WorldLevel:Load(...)
  worldLoad(self, ...)
  if not openedSpellbook then
    openedSpellbook = true
    WorldLevel.SaveLoad = function()
      assert(#Unit.Hero.BattleParams.Magic > 0, "spellbook fixture requires known spells")
      self:OnSpellBook()
    end
  end
end
'''
    write_pak(args.output, {'guiscenes.lua': driver, 'scenario_original_guiscenes.lua': original})
    manifest = {'source': str(args.resource0.resolve()), 'original_script_sha256': hashlib.sha256(original).hexdigest(),
                'driver_sha256': hashlib.sha256(driver).hexdigest(), 'overlay_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                'save': args.save, 'roundtrip': args.roundtrip, 'continent2': args.continent2, 'spellbook': args.spellbook,
                'scope': 'shared test asset; original EXE is not patched'}
    args.output.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
