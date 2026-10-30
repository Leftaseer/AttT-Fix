#!/bin/bash
# pass if the wall in front of the hero (save 243, a player's: Ogantar) stops him: forward (W) held 5 s after the
# loading, the picture 12 s after it against ref_wall.png (made with every replacement switched off), grey
# thumbnail of the middle RMSE < 0.04 (walking through: 0.09; two runs of the same build: 0.01)
# (GT_NAME, TOGGLE: another run name, replacements switched off in a --toggle build)
T=/home/user/AttT-Fix/decomp
GT_NAME=${GT_NAME:-wall} GT_WAIT=12 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_243 TI_AFTER=/opt/re/ti_after_wall.txt bash $T/tools/gametest_save.sh "$1" || exit 1
[ -n "$NOCHECK" ] && exit 0
m=$(compare -metric RMSE <(convert /opt/re/shots/${GT_NAME:-wall}_end.png -crop 400x350+200+100 -resize 100x88 -colorspace gray png:-) \
    <(convert /opt/re/ref_wall.png -crop 400x350+200+100 -resize 100x88 -colorspace gray png:-) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 $m" >> /opt/re/out/gbis/wall.log
python3 -c "import sys; sys.exit(0 if $m < 0.04 else 1)"
