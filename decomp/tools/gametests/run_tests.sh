#!/bin/bash
# build auto/$1 and run the game tests: village save x3, battle save, a battle from the village and back, extras, messages, exit after a battle,
# main menu picture, 2 minutes from the start, trees, army window
cd /opt/re
T=/home/user/AttT-Fix/decomp; D=${1:-attt_n}
t0=$(date +%s)
python3 $T/rebuild/build.py --exe bin/attt.exe --out rb/t_$D/ATThrone.exe --auto auto/$D --laa 2>&1 | tail -1
python3 $T/rebuild/build.py --exe bin/attt.exe --out rb/t_${D}_ti/ATThrone.exe --auto auto/$D -D DECOMP_TEST_INPUT -D DECOMP_DEBUG_LOG 2>&1 | tail -1
TI=/opt/re/rb/t_${D}_ti/ATThrone.exe
for i in 1 2 3; do bash gametest_world.sh $TI; echo world rc=$?; done
bash gametest_battle.sh $TI; echo battle rc=$?
bash gametest_battles.sh $TI; echo battles rc=$?
convert shots/save_end.png -resize 300x225 /tmp/claude-0/-home-user-AttT-Fix/e5484138-d72a-5972-a73b-6b3ae20a7092/scratchpad/battle_$D.png
bash gametest_extras.sh $TI; echo extras rc=$?; tail -1 out/gbis/extras.log
bash gametest_message.sh $TI; echo message rc=$?
bash gametest_exit.sh $TI; echo exit rc=$?; cat game/gexit/decomp_debug.log | head -5
bash gametest_vis.sh /opt/re/rb/t_$D/ATThrone.exe; echo vis rc=$?; tail -1 out/gbis/vis.log
GT_WAIT=120 bash gametest.sh /opt/re/rb/t_$D/ATThrone.exe; echo long rc=$?
bash gametest_trees.sh $TI; echo trees rc=$?; tail -1 out/gbis/trees.log
bash gametest_army.sh $TI; echo army rc=$?; tail -1 out/gbis/army.log
echo "suite: $(( ($(date +%s) - t0) / 60 )) min"
