#!/bin/bash
# pass if the walk-on characters (static animated objects) of the user's village save 212 are there: their spot
# looks more like the original's picture (ref212.png) than like one without them (ref212_empty.png)
T=/home/user/AttT-Fix/decomp
GT_NAME=gextras GT_WAIT=50 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_u212 bash $T/tools/gametest_save.sh "$1" ||
    { echo "$(date +%T) not running" >> /opt/re/out/gbis/extras.log; exit 1; }
cr() { convert $1 -crop 260x150+420+210 -colorspace gray -resize '26x15!' png:-; }
full=$(compare -metric RMSE <(cr /opt/re/shots/gextras_end.png) <(cr /opt/re/ref212.png) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
empty=$(compare -metric RMSE <(cr /opt/re/shots/gextras_end.png) <(cr /opt/re/ref212_empty.png) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 with $full without $empty" >> /opt/re/out/gbis/extras.log
python3 -c "import sys; sys.exit(0 if float('$full') < float('$empty') else 1)"
