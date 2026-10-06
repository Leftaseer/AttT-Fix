#!/bin/sh
# Build AttTFix (proxy dinput8.dll, 32-bit) with mingw-w64.
#   Linux / WSL:  sudo apt install g++-mingw-w64-i686 python3 lua5.1   ->  sh build.sh
#   MSYS2:        pacman -S mingw-w64-i686-gcc python  (MINGW32 shell) ->  CXX=g++ sh build.sh
# attfix.lua is UTF-8 and is embedded into the DLL in cp1251 (the game's encoding) as attfix_lua.h.
set -e
cd "$(dirname "$0")"
CXX="${CXX:-i686-w64-mingw32-g++}"
PYTHON="${PYTHON:-python3}"
LUAC="${LUAC:-luac5.1}"
if command -v "$LUAC" >/dev/null 2>&1; then "$LUAC" -p attfix.lua; else echo "note: $LUAC not found, skipping Lua syntax check"; fi
"$PYTHON" - <<'PY'
lua = open('attfix.lua', encoding='utf-8').read()
def esc(line):
    out = ''
    for ch in line:
        b = ch.encode('cp1251')
        if ch == '\\': out += '\\\\'
        elif ch == '"': out += '\\"'
        elif b[0] >= 128: out += '\\%03o' % b[0]
        else: out += ch
    return out
open('attfix_lua.h', 'w').write(''.join('"' + esc(l) + '\\n"\n' for l in lua.split('\n')))
PY
"$CXX" -O2 -msse2 -mfpmath=sse -Wall -shared -static -static-libgcc -static-libstdc++ -Wl,--kill-at \
    -o dinput8.dll attfix.cpp -lwinmm
# symbols for the built-in profiler (AttTFix.sym next to the dll; optional)
NM="${NM:-i686-w64-mingw32-nm}"
if command -v "$NM" >/dev/null 2>&1; then
    "$NM" --defined-only dinput8.dll | "$PYTHON" -c "
import sys
import struct
d = open('dinput8.dll', 'rb').read()
pe = struct.unpack_from('<I', d, 0x3C)[0]
base = struct.unpack_from('<I', d, pe + 0x34)[0]
rows = []
for l in sys.stdin:
    p = l.split()
    if len(p) == 3 and p[1] in 'tT' and not p[2].startswith('.'):
        n = p[2].lstrip('_@')
        import re
        m = re.match(r'ZN?L?(\\d+)', n)
        if m: k = int(m.group(1)); n = n[m.end():m.end() + k]
        rows.append((int(p[0], 16), n.split('@')[0]))
import subprocess
rows.sort()
open('AttTFix.sym', 'w').write(''.join('%x %s\\n' % (a - base, n) for a, n in rows))
"
fi
echo "built: $(pwd)/dinput8.dll"
