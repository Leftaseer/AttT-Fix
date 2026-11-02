#!/usr/bin/env python3
"""Exercise the debug menu's compiled handlers and float Lua 5.1.2 VM without launching the game.

Usage: python3 check_debugmenu.py ORIGINAL_EXE DEBUG_EXE DEBUG_MAP
Scene/world objects and Win32 calls are mocked; real graphics and desktop focus need a playtest.
"""
import pathlib
import re
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from difftest import Harness
from unicorn import UC_HOOK_CODE


class MenuHarness(Harness):
    def __init__(self, orig, rebuilt, mapfile):
        super().__init__(orig, rebuilt, mapfile)
        self.symbols = dict((m[1], int(m[2], 16)) for m in re.finditer(
            r'^\s+\w+:\w+\s+(\S+)\s+([0-9a-fA-F]{16})\s+', pathlib.Path(mapfile).read_text(), re.M))
        self.windows = []
        debuglog = self.symbol('DebugLog')
        self.uc.hook_add(UC_HOOK_CODE, lambda *args: self._ret(), begin=debuglog, end=debuglog)

    def symbol(self, name):
        matches = [a for n, a in self.symbols.items() if n == '_' + name or n.startswith('?' + name + '@@')]
        if len(matches) != 1:
            raise AssertionError((name, matches))
        return matches[0]

    def checked_call(self, entry, args=()):
        result = self.call(entry, args=args)
        assert result['fault'] is None, result
        return result['eax']

    def crt_strtod(self):
        p, end = self._arg(0), self._arg(1)
        match = re.match(rb'\s*[+-]?(?:0[xX][0-9a-fA-F]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)', self._cstr(p))
        text = match[0] if match else b''
        if end:
            self.uc.mem_write(end, struct.pack('<I', p + len(text)))
        value = float(int(text, 16)) if b'x' in text.lower() else float(text or b'0')
        self._ret(st0=value)

    def crt_sprintf(self):
        dst, fmt = self._arg(0), self._cstr(self._arg(1)).decode('ascii')
        slot = 2

        def replace(match):
            nonlocal slot
            spec = match[0]
            if spec == '%%':
                return '%'
            if spec.endswith('g'):
                value = struct.unpack('<d', struct.pack('<II', self._arg(slot), self._arg(slot + 1)))[0]
                slot += 2
            else:
                value = self._cstr(self._arg(slot)).decode('ascii')
                slot += 1
            return spec % value

        out = re.sub(r'%%|%s|%\.14g', replace, fmt).encode('ascii')
        self.uc.mem_write(dst, out + b'\0')
        self._ret(len(out))

    def crt_lstrcpynA(self):
        dst, src, count = (self._arg(i) for i in range(3))
        self.uc.mem_write(dst, self._cstr(src)[:count - 1] + b'\0')
        self._ret(dst, 12)

    def crt_ShowWindow(self):
        self.windows.append(('show', self._arg(0), self._arg(1)))
        self._ret(1, 8)

    def crt_SetWindowPos(self):
        self.windows.append(('position', self._arg(0), self._arg(6)))
        self._ret(1, 28)

    def crt_SetForegroundWindow(self):
        self.windows.append(('foreground', self._arg(0)))
        self._ret(1, 4)

    def crt_SetActiveWindow(self):
        self.windows.append(('active', self._arg(0)))
        self._ret(1, 4)

    def crt_SendMessageW(self):
        assert self._arg(1) == 0x188, 'expected LB_GETCURSEL'
        self._ret(self.selection, 16)

    def lua_init(self):
        self.L = self.checked_call(0x402870)
        for name in ('luaopen_base', 'luaopen_table', 'luaopen_string'):
            self.checked_call(self.symbol(name), [self.L])
            self.checked_call(0x402A70, [self.L, 0])

    def lua(self, source):
        source = source.encode('ascii')
        buf = self.alloc(len(source) + 1, source + b'\0')
        name = self.alloc(6, b'=test\0')
        assert self.checked_call(0x4026F0, [self.L, buf, len(source), name]) == 0, 'Lua syntax error'
        assert self.checked_call(0x403860, [self.L, 0, 0, 0]) == 0, 'Lua runtime error'

    def command(self, command):
        self.checked_call(self.symbol('MenuProc'), [1, 0x111, command, 0])

    def queued(self):
        address = self.symbol('g_testLua')
        chunk = self._cstr(address).decode('ascii')
        assert chunk and len(chunk) < 2048
        self.uc.mem_write(address, b'\0')
        return chunk


def main():
    h = MenuHarness(*sys.argv[1:])
    h.lua_init()
    h.lua("""
        Dbg = {}
        function DecompDbg(s) Dbg[#Dbg + 1] = s end
        function Clock_GetHours() return 123 end
        WorldLevel = {Armys = {}}
        Unit = {}
        GUIScene = {WorldLevel = {scene = {OnArmyIcon = function(self)
            GUIScene.ArmyScreen = {scene = {ChooseScene = function(self, name, info)
                Opened = {name = name, info = info, owner = self}
            end}}
        end}}}
    """)
    # The compiled C++ formatter/queue must handle every selection, including the longest ID.
    ids = re.findall(r'"(u\w+)"', pathlib.Path(__file__).resolve().parents[1].joinpath(
        'rebuild/src/engine/debugmenu.cpp').read_text().split('static const char *kUnitIds[] = {')[1].split('};')[0])
    for index, unit in enumerate(ids):
        h.lua("Unit['%s'] = {BattleParams = {}}" % unit)
        h.selection = index
        h.command(1004)
        h.lua(h.queued())
        h.lua("""
            assert(Opened.name == 'Barrack')
            assert(Opened.owner == GUIScene.ArmyScreen.scene)
            assert(Opened.info[2] == '%s' and Opened.info[3] == 100)
            assert(Opened.info.curCount == 100 and Opened.info.lastTime == 123)
            assert(Dbg[#Dbg] == 'barracks: 100 x %s (10 troops x 10)')
        """ % (unit, unit))
    print('ok: barracks actions for %d unit selections (world scene has no ChooseScene)' % len(ids))

    h.lua("""
        Army, ArmyPos, Actions = {}, {}, {}
        WorldHero = {GetPos = function() return 10, 20 end}
        WorldArmy = {new = function(self, name)
            local a = {delete = function(self) Deleted = (Deleted or 0) + 1 end}
            WorldLevel.Armys[name] = a
            return a
        end}
        Actions['Fight With Army'] = function(self, name, selfHero, noSave)
            assert(selfHero == false and noSave == true)
            local a, b = WorldLevel.Armys[name], Unit.uDragon.BattleParams
            Result = {Health = b.Health, Speed = b.Speed}
            for k, v in pairs(a.ChangeParam) do Result[k] = Result[k] + v end
            assert(Army[name].TroopList[1].Unit == 'uDragon')
            assert(Army[name].TroopList[1].Quantity == 1)
            assert(ArmyPos[name].x == 260 and ArmyPos[name].z == 270)
        end
    """)
    for speed in (6, 1, 9):
        h.lua('Unit.uDragon.BattleParams = {Health = 836, Speed = %d}' % speed)
        h.command(1005)
        h.lua(h.queued())
        h.lua("""
            assert(Result.Health == 100836 and Result.Speed == 1)
            assert(Unit.uDragon.BattleParams.Health == 836 and Unit.uDragon.BattleParams.Speed == %d)
            assert(Dbg[#Dbg] == 'battle: 1 x uDragon, 100836 HP, unit Speed 1')
        """ % speed)
    h.lua('assert(Deleted == 2)')
    print('ok: dragon Speed 1, +100000 health, repeated battles, no-save arguments, unchanged unit definitions')

    menu = 0x1234
    game = 0x5678
    h.uc.mem_write(h.symbol('g_menu'), struct.pack('<I', menu))
    h.uc.mem_write(h.to_rebuilt(0x6C889C), struct.pack('<I', game))
    h.uc.mem_write(h.to_rebuilt(0x6BF6E0), b'\1')
    for _ in range(3):
        h.windows.clear()
        h.checked_call(h.symbol('MenuProc'), [menu, 0x312, 0x4D01, 0])
        assert ('show', menu, 5) in h.windows and ('show', menu, 0) not in h.windows
        assert ('foreground', menu) in h.windows and ('active', menu) in h.windows
    for message, wp in ((0x111, 1006), (0x10, 0)):
        h.windows.clear()
        h.checked_call(h.symbol('MenuProc'), [menu, message, wp, 0])
        assert ('show', menu, 0) in h.windows
        assert ('foreground', game) in h.windows
    print('ok: repeated Ctrl+Alt+D shows/focuses; Close and X hide (Win32 calls mocked)')


if __name__ == '__main__':
    main()
