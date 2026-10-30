# Game tests

The scenarios `run_tests.sh` runs on a build of auto-decompiled code (`run_tests.sh attt_vNN` builds
`auto/attt_vNN` twice, plain and with `-D DECOMP_TEST_INPUT -D DECOMP_DEBUG_LOG`). They expect the work folder
`/opt/re` (the game, the Wine prefix, the saves `saves_*`, the reference pictures `ref*.png`) and run one game at a
time: two at once share the Wine prefix and break each other.

Each save test skips the videos, loads its save as soon as the main menu is up and plays a fixed time after the
loading (`tools/gametest_save.sh`); a run stops as soon as the game exits or writes its error log.

| test | what passes |
|---|---|
| world (x3) | the village save loads (no loading parchment 40 s after) |
| battle | the battle save plays 100 s without an engine error |
| battles | from the village save the hero attacks an army the way the player does (`Actions['Fight With Army']`: the save screen, the save, the battle), the enemy fights some turns, the battle is won (the tactic scene's `VictoryCurrentBattle`), the victory window closes and the world goes on (`ti_after_battles.txt`: a small state machine in Lua run every 5 s) |
| extras | the walk-on characters of save 212 are there (picture) |
| message | three gold messages at once go without an error |
| exit | after the battle save, the game menu's and main menu's exits end the game (exit 0) |
| vis | the main menu at 90 s looks like the original's |
| long | 2 minutes from the start without an engine error |
| trees | the trees of save 215 are there (picture) |
| army | the army window shows its text (picture) |
| ogantar | Ogantar's trees (save 241, a player's) stand where the original puts them (picture `ref_ogantar.png`, made with every replacement switched off in a `--toggle` build) |
| wall | a wall stops the hero (save 243, a player's: forward held with the test input's `hold`; picture `ref_wall.png` made with every replacement switched off) |
| spellbook | the spell book (`GUIScene.WorldLevel:OnSpellBook`) looks as with every replacement switched off (picture `ref_spellbook.png` from a `--toggle` build; the first one, from a build with 0x45E830's misplaced village trees behind the book, was wrong) |

The whole set takes about 20 minutes.

## Coverage

`run_cov.sh attt_vNN` runs the same scenarios (vis aside) on a coverage build (`build.py --coverage`, with test
input and the debug log): every function of the new code marks itself the first time it runs and each run of the
game leaves `decomp_coverage_*.bin` next to it. The files are gathered in `out/cov_attt_vNN/` and
`tools/coverage.py` reports how many of the replaced functions ran (hand-written in `src/fixed`, generated, engine)
and lists them in `out/cov_attt_vNN_run.tsv` / `_notrun.tsv`. Any other play with that build (a player's own game
too) adds its files the same way: `coverage.py BUILD.map *.bin`.
