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
echo "built: $(pwd)/dinput8.dll"
