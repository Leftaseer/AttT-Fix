#!/bin/bash
# pass if the army window (village save, WorldLevel:OnArmy) shows its text: the right page against ref_army.png
# (the original's; 0x587D30 once placed the text off screen)
T=/home/user/AttT-Fix/decomp
GT_WAIT=25 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_world TI_AFTER=/opt/re/ti_after_army.txt bash $T/tools/gametest_save.sh "$1" || exit 1
m=$(convert /opt/re/shots/save_end.png -resize 640x480 -crop 180x170+360+115 -colorspace gray png:- | compare -metric RMSE /opt/re/ref_army.png - null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 $m" >> /opt/re/out/gbis/army.log
python3 -c "import sys; sys.exit(0 if $m < 0.03 else 1)"
