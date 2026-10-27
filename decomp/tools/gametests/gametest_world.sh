#!/bin/bash
# pass if the village save loads (no loading-screen parchment left of the picture 40 s after the loading)
T=/home/user/AttT-Fix/decomp
GT_WAIT=40 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_world bash $T/tools/gametest_save.sh "$1" || exit 1
m=$(convert /opt/re/shots/save_end.png -resize '400x300!' -crop 20x100+48+100 -colorspace gray -format "%[fx:mean]" info:)
echo "world $m" >> /opt/re/out/gbis/world.log
python3 -c "import sys; sys.exit(0 if $m < 0.33 else 1)"
