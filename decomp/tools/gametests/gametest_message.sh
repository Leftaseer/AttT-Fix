#!/bin/bash
# pass if on-screen messages (gold given in the village: CMessage, its text animation) go without an error
T=/home/user/AttT-Fix/decomp
GT_NAME=gmsg GT_WAIT=40 GT_LOG=/opt/re/out/gbis/msg.log DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_world TI_AFTER=/opt/re/ti_after_msg.txt bash $T/tools/gametest_save.sh "$1"
