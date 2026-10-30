#!/bin/bash
# coverage of the game tests: a coverage build (build.py --coverage, test input and debug log) of auto/$1 runs the
# tests of run_tests.sh; the decomp_coverage_*.bin files the runs leave go to out/cov_$1/ and tools/coverage.py
# reports which replaced functions ran (out/cov_$1_run.tsv / _notrun.tsv)
cd /opt/re
T=/home/user/AttT-Fix/decomp; D=${1:-attt_v67}
t0=$(date +%s)
python3 $T/rebuild/build.py --exe bin/attt.exe --out rb/cov_$D/ATThrone.exe --auto auto/$D --coverage -D DECOMP_TEST_INPUT -D DECOMP_DEBUG_LOG 2>&1 | tail -1
E=/opt/re/rb/cov_$D/ATThrone.exe
rm -f game/*/decomp_coverage_*.bin
for i in 1 2 3; do bash gametest_world.sh $E; echo world rc=$?; done
bash gametest_battle.sh $E; echo battle rc=$?
bash gametest_battles.sh $E; echo battles rc=$?
bash gametest_extras.sh $E; echo extras rc=$?
bash gametest_message.sh $E; echo message rc=$?
bash gametest_exit.sh $E; echo exit rc=$?
GT_WAIT=120 bash gametest.sh $E; echo long rc=$?
bash gametest_trees.sh $E; echo trees rc=$?
bash gametest_army.sh $E; echo army rc=$?
bash gametest_spellbook.sh $E; echo spellbook rc=$?
bash gametest_ogantar.sh $E; echo ogantar rc=$?
mkdir -p out/cov_$D; rm -f out/cov_$D/*.bin
for f in game/*/decomp_coverage_*.bin; do cp $f out/cov_$D/$(basename $(dirname $f))_$(basename $f); done
ls out/cov_$D | wc -l
python3 $T/tools/coverage.py rb/cov_$D/ATThrone.map out/cov_$D/*.bin --out out/cov_$D
echo "coverage suite: $(( ($(date +%s) - t0) / 60 )) min"
