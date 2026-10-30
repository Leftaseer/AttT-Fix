#!/bin/bash
# pass if Ogantar's trees (save 241) stand where the original puts them: the middle of the picture 20 s after the
# loading against ref_ogantar.png (made with every replacement switched off), grey thumbnail RMSE < 0.12
# (0x45E830's label flag left 0 put them at height 0: 0.25; two runs of the same build differ by about 0.04)
T=/home/user/AttT-Fix/decomp
GT_NAME=ogantar GT_WAIT=20 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_241 bash $T/tools/gametest_save.sh "$1" || exit 1
m=$(compare -metric RMSE <(convert /opt/re/shots/ogantar_end.png -crop 400x350+200+50 -resize 100x88 -colorspace gray png:-) \
    <(convert /opt/re/ref_ogantar.png -crop 400x350+200+50 -resize 100x88 -colorspace gray png:-) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 $m" >> /opt/re/out/gbis/ogantar.log
python3 -c "import sys; sys.exit(0 if $m < 0.12 else 1)"
