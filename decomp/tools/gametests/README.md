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
| extras | the walk-on characters of save 212 are there (picture) |
| message | three gold messages at once go without an error |
| exit | after the battle save, the game menu's and main menu's exits end the game (exit 0) |
| vis | the main menu at 90 s looks like the original's |
| long | 2 minutes from the start without an engine error |
| trees | the trees of save 215 are there (picture) |
| army | the army window shows its text (picture) |

The whole set takes about 15 minutes.
