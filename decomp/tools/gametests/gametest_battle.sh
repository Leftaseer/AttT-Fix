#!/bin/bash
# pass if the battle save (the user's game00) loads and the battle goes on 100 s without an engine error
T=/home/user/AttT-Fix/decomp
GT_WAIT=100 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_user bash $T/tools/gametest_save.sh "$1"
