#!/bin/bash
# pass (exit 0) if a build made with -D DECOMP_TEST_INPUT loads a save game and plays on for a while without an
# engine error.  The build skips the start-up videos and loads the save as soon as the main menu is up
# (testinput.txt 'skipintro', 'loadsave NAME'); it says when the world is there ('autoload: loaded at'), and the
# run goes on GT_WAIT seconds from then.  It stops at once when the game exits or writes its error log.
#   SAVES       a folder with one gameNN.sav (and its .bmp), loaded
#   TI_AFTER    lines run after the loading, 'L+MS lua CODE' (MS milliseconds after it), optional
#   GT_WAIT     seconds of play after the loading (default 40); GT_LOAD: the longest the loading may take (150)
#   GT_NAME     the run's name (game/NAME, shots/NAME_end.png; default save); GT_LOG: a file the end of each run's
#               output is appended to; DXVK, WINEPREFIX as tools/rungame.py takes them
# The screenshot at the end is $WORK/shots/NAME_end.png.
name=$(basename "$(ls "$SAVES"/*.sav | head -1)" .sav)
ti=$(mktemp)
{ echo "0 skipintro"; echo "0 loadsave $name"; [ -n "$TI_AFTER" ] && cat "$TI_AFTER"; } > "$ti"
out=$(LOGOS=1 NOWM=1 WINDOWED=1 RES=800x600 TESTINPUT="$ti" timeout $(( ${GT_WAIT:-40} + ${GT_LOAD:-150} + 60 )) \
      python3 "$(dirname "$0")/rungame.py" "$1" "${GT_NAME:-save}" \
      "wait 2; focus; until autoload:_loaded ${GT_LOAD:-150}; wait ${GT_WAIT:-40}; shot end" 2>&1)
rm -f "$ti"
[ -n "$GT_LOG" ] && { echo "== $(date +%T) $1"; echo "$out" | grep -v "^window" | tail -6; } >> "$GT_LOG"
echo "$out" | grep -q "until autoload:_loaded: seen" && echo "$out" | grep -q "running at the end" &&
    ! echo "$out" | grep -q "Failed with error\|error log"
