#!/bin/bash
# pass if the trees of the user's save 215 are there: the spot looks more like the original's picture (ref215.png)
# than like one without them (ref215_empty.png, v14)
T=/home/user/AttT-Fix/decomp
GT_NAME=gtrees GT_WAIT=70 DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_u215 bash $T/tools/gametest_save.sh "$1" ||
    { echo "$(date +%T) not running" >> /opt/re/out/gbis/trees.log; exit 1; }
cr() { convert $1 -crop 200x220+390+50 -colorspace gray -resize '20x22!' png:-; }
full=$(compare -metric RMSE <(cr /opt/re/shots/gtrees_end.png) <(cr /opt/re/ref215.png) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
empty=$(compare -metric RMSE <(cr /opt/re/shots/gtrees_end.png) <(cr /opt/re/ref215_empty.png) null: 2>&1 | sed 's/.*(\(.*\))/\1/')
echo "$(date +%T) $1 with $full without $empty" >> /opt/re/out/gbis/trees.log
python3 -c "import sys; sys.exit(0 if float('$full') < float('$empty') else 1)"
