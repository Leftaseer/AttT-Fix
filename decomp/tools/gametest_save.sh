#!/bin/bash
# pass (exit 0) if a build made with -D DECOMP_TEST_INPUT loads a save game and plays on for a while without an
# engine error: the startup videos are skipped with Escape, testinput.txt opens the load screen and loads the
# save (SAVES=folder with gameNN.sav, TESTINPUT=script, see ti_load.txt below), GT_WAIT seconds after that.
#   45000 lua for k,v in pairs(GUIScene) do if type(v)=='table' and rawget(v,'_ChooseHero') and v.scene then v:_Load() end end
#   55000 lua GUIScene.Load:StrongLoad()
# env: DXVK, WINEPREFIX, SAVES, TESTINPUT, GT_WAIT (default 75)
out=$(LOGOS=1 NOWM=1 WINDOWED=1 RES=800x600 timeout $(( ${GT_WAIT:-75} + 250 )) python3 "$(dirname "$0")/rungame.py" "$1" save \
      "wait 15; focus; key Escape; wait 5; key Escape; wait 5; key Escape; wait 45; wait ${GT_WAIT:-75}; shot end" 2>&1)
echo "$out" | grep -q "running at the end" && ! echo "$out" | grep -q "Failed with error"
