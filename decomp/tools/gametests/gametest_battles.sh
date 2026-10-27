#!/bin/bash
# pass if, from a village save, a battle goes the way the player's do: the hero attacks an army (Actions 'Fight
# With Army': the save screen, the save game00, the battle), the enemy fights some turns (the tactic scene's
# OnNextTroop), the battle is won (VictoryCurrentBattle), the victory window is closed, back in the world
T=/home/user/AttT-Fix/decomp
GT_NAME=gbattles GT_WAIT=280 TI_AFTER=/opt/re/ti_after_battles.txt DXVK=/opt/re/dxvk/dxvk-2.4/x32 WINEPREFIX=/opt/re/gameprefix2 SAVES=/opt/re/saves_world bash $T/tools/gametest_save.sh "$1"
