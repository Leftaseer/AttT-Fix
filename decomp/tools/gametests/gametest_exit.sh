#!/bin/bash
# pass if the game, after a battle save, the game menu's exit and the main menu's exit, ends by itself (exit 0)
# (a build with -D DECOMP_TEST_INPUT)
T=/home/user/AttT-Fix/decomp
rm -f /opt/re/game/gexit/decomp_debug.log
ti=$(mktemp); { echo "0 skipintro"; echo "0 loadsave game00"; cat /opt/re/ti_after_exit.txt; } > $ti
out=$(LOGOS=1 NOWM=1 WINDOWED=1 RES=800x600 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_user \
      TESTINPUT=$ti timeout 400 python3 $T/tools/rungame.py "$1" gexit "wait 2; focus; until autoload:_loaded 150; wait 150" 2>&1)
rm -f $ti
echo "$(date +%T) $(echo "$out" | grep -v '^window' | tail -1)" >> /opt/re/out/gbis/exit.log
echo "$out" | grep -q "exited with 0"
