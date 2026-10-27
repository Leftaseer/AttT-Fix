#!/bin/bash
# pass (exit 0) if the game runs GT_WAIT (60) s from start without writing an engine error log (DXVK, 800x600, no logos)
out=$(DXVK=/opt/re/dxvk/dxvk-2.4/x32 RES=800x600 WINEPREFIX=/opt/re/gameprefix2 timeout $(( ${GT_WAIT:-60} + 140 )) python3 /home/user/AttT-Fix/decomp/tools/rungame.py "$1" bis "wait ${GT_WAIT:-60}; shot end" 2>&1)
echo "$out" | grep -q "running at the end" && ! echo "$out" | grep -q -- "---"
