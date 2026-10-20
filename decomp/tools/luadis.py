#!/usr/bin/env python3
"""Disassembler of the game's compiled Lua 5.1 scripts (in Resource*.pak): 4-byte size_t and float lua_Number,
which the standard luac cannot read.  Prints every function with its constants and instructions, with the
constant operands written out (GETGLOBAL Config, SELF ... "Load", ...).

usage: luadis.py FILE.lua [FUNCTION_NAME_SUBSTRING]"""
import struct, sys

OPS = ('MOVE LOADK LOADBOOL LOADNIL GETUPVAL GETGLOBAL GETTABLE SETGLOBAL SETUPVAL SETTABLE NEWTABLE SELF ADD SUB MUL '
       'DIV MOD POW UNM NOT LEN CONCAT JMP EQ LT LE TEST TESTSET CALL TAILCALL RETURN FORLOOP FORPREP TFORLOOP SETLIST '
       'CLOSE CLOSURE VARARG').split()


class R:
    def __init__(s, d):
        s.d, s.p = d, 0

    def take(s, n):
        b = s.d[s.p:s.p + n]
        s.p += n
        return b

    def u8(s): return s.take(1)[0]
    def i32(s): return struct.unpack('<i', s.take(4))[0]
    def u32(s): return struct.unpack('<I', s.take(4))[0]

    def string(s):
        n = s.u32()
        return s.take(n)[:-1].decode('cp1251', 'replace') if n else None


def function(r):
    f = {'source': r.string(), 'line': r.i32(), 'lastline': r.i32()}
    f['nups'], f['nparams'], f['vararg'], f['stack'] = r.u8(), r.u8(), r.u8(), r.u8()
    f['code'] = [r.u32() for _ in range(r.u32())]
    ks = []
    for _ in range(r.u32()):
        t = r.u8()
        ks.append(None if t == 0 else bool(r.u8()) if t == 1 else struct.unpack('<f', r.take(4))[0] if t == 3
                  else r.string())
    f['k'] = ks
    f['protos'] = [function(r) for _ in range(r.u32())]
    r.take(4 * r.u32())                                # line info
    f['locals'] = []
    for _ in range(r.u32()):
        f['locals'].append(r.string()); r.i32(); r.i32()
    f['upnames'] = [r.string() for _ in range(r.u32())]
    return f


def rk(f, x):
    return repr(f['k'][x - 256]) if x >= 256 else 'r%d' % x


def show(f, path, want, out):
    if want is None or want in path:
        out.append('function %s (line %d, %d params)' % (path, f['line'], f['nparams']))
        for pc, i in enumerate(f['code']):
            op = OPS[i & 63]
            a, c, b = (i >> 6) & 255, (i >> 14) & 511, (i >> 23) & 511
            bx = i >> 14
            sbx = bx - 131071
            if op in ('LOADK', 'GETGLOBAL', 'SETGLOBAL'):
                arg = 'r%d %r' % (a, f['k'][bx])
            elif op == 'CLOSURE':
                arg = 'r%d proto %d' % (a, bx)
            elif op in ('JMP', 'FORLOOP', 'FORPREP'):
                arg = 'r%d -> %d' % (a, pc + 1 + sbx)
            elif op in ('GETTABLE', 'SELF'):
                arg = 'r%d r%d %s' % (a, b, rk(f, c))
            elif op in ('SETTABLE', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW', 'EQ', 'LT', 'LE'):
                arg = 'r%d %s %s' % (a, rk(f, b), rk(f, c))
            else:
                arg = 'r%d %d %d' % (a, b, c)
            out.append('  %4d %-9s %s' % (pc, op, arg))
    for n, p in enumerate(f['protos']):
        # the name a closure is stored under: the SETTABLE / SETGLOBAL right after its CLOSURE
        name = str(n)
        for pc, i in enumerate(f['code']):
            if OPS[i & 63] == 'CLOSURE' and i >> 14 == n and pc + 1 < len(f['code']):
                j = f['code'][pc + 1]
                if OPS[j & 63] == 'SETTABLE' and (j >> 23) & 511 >= 256:
                    name = str(f['k'][((j >> 23) & 511) - 256])
                elif OPS[j & 63] == 'SETGLOBAL':
                    name = str(f['k'][j >> 14])
        show(p, path + '/' + name, want, out)


d = open(sys.argv[1], 'rb').read()
assert d[:4] == b'\x1bLua' and d[4] == 0x51, 'not Lua 5.1 bytecode'
r = R(d)
r.take(12)
out = []
show(function(r), 'main', sys.argv[2] if len(sys.argv) > 2 else None, out)
print('\n'.join(out))
