#!/bin/bash
# pass if the spell book (village save, WorldLevel:OnSpellBook; set up by 0x4C8B70) looks as with the original's
# set-up: the screen against ref_spellbook.png
T=/home/user/AttT-Fix/decomp
GT_NAME=spellbook GT_WAIT=25 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_world TI_AFTER=/opt/re/ti_after_spellbook.txt bash $T/tools/gametest_save.sh "$1" || exit 1
m=$(convert /opt/re/shots/spellbook_end.png -resize 640x480 -colorspace gray png:- | compare -metric RMSE /opt/re/ref_spellbook.png - null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 $m" >> /opt/re/out/gbis/spellbook.log
python3 -c "import sys; sys.exit(0 if $m < 0.03 else 1)"
