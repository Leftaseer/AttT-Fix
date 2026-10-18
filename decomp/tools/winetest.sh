#!/usr/bin/env bash
# Smoke test of a rebuilt exe without the game: run the original and the rebuilt ATThrone.exe under Wine
# (Xvfb, null sound device) in empty folders and compare what they leave behind (error log, Saves, graphic.cfg).
# Without game data both stop at the first missing .pak, so this checks start-up, the CRT, the window, the
# engine construction and everything the rebuilt code replaces on that path.
# usage: winetest.sh ORIG.exe REBUILT.exe [workdir]   (AttT also needs stub mss32.dll/binkw32.dll in workdir/stubs)
set -u
orig=$1; rb=$2; w=${3:-/tmp/attt-winetest}
export WINEPREFIX=${WINEPREFIX:-$w/prefix} WINEDEBUG=-all
mkdir -p "$w"
[ -f ~/.asoundrc ] || printf 'pcm.!default { type null }\n' > ~/.asoundrc
for d in orig rb; do
  rm -rf "$w/$d"; mkdir -p "$w/$d"
  [ "$d" = orig ] && cp "$orig" "$w/$d/ATThrone.exe" || cp "$rb" "$w/$d/ATThrone.exe"
  cp "$w"/stubs/*.dll "$w/$d/" 2>/dev/null
  (cd "$w/$d" && timeout 60 xvfb-run -a wine ATThrone.exe > wine.out 2>&1)
done
status=0
for f in $(cd "$w/orig" && ls | grep -v -e wine.out -e ATThrone.exe -e '\.dll$'); do
  if [ -d "$w/orig/$f" ]; then [ -d "$w/rb/$f" ] || { echo "missing folder $f"; status=1; }; continue; fi
  # the error log starts with the time of day
  if ! diff <(tail -n +2 "$w/orig/$f") <(tail -n +2 "$w/rb/$f" 2>/dev/null) > /dev/null; then echo "differs: $f"; status=1; fi
done
[ $status = 0 ] && echo "same behaviour: $(cd "$w/orig" && ls | grep -v -e wine.out -e '\.exe$' -e '\.dll$' | tr '\n' ' ')"
exit $status
