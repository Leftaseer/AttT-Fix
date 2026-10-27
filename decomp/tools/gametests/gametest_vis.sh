#!/bin/bash
# pass if the game runs 90 s without an engine error and the picture at 90 s looks like the original's
# (16x12 grey thumbnails, RMSE < 0.2; two runs of the original differ by about 0.13)
out=$(DXVK=/opt/re/dxvk/dxvk-2.4/x32 RES=800x600 WINEPREFIX=/opt/re/gameprefix2 timeout 260 python3 /home/user/AttT-Fix/decomp/tools/rungame.py "$1" bis "wait 90; shot end" 2>&1)
echo "$out" | grep -q "running at the end" && ! echo "$out" | grep -q -- "---" || exit 1
d=$(compare -metric RMSE <(convert /opt/re/shots/bis_end.png -colorspace gray -resize '16x12!' png:-) \
    <(convert /opt/re/ref90.png -colorspace gray -resize '16x12!' png:-) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "thumb $d" >> /opt/re/out/gbis/vis.log
python3 -c "import sys; sys.exit(0 if float('$d') < 0.2 else 1)"
