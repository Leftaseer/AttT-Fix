# Extended save and continent checks — 2026-11-03

Checkpoint: `/home/attt-dev/work/wine-cohorts/extended-checkpoint-20261103.json`.
This extends [the shared integration milestone](WINE_SHARED_RESULTS.md) with **ten successful runs**, plus
two cases that failed required-output checks because their save name was unavailable in the load list.
All **42 tooling tests** pass. v57 EXEs and supplied assets/saves remain unchanged; no Windows installation
was touched. Generated overlays, outputs and exact tool snapshots stay in WSL.

## More world saves

`/home/attt-dev/work/wine-cohorts/world-roundtrips-j3o_enr_/` contains the eight-case supervisor logs,
fixture manifests, `results.json`, structured `comparison.json` and the exact `b0c8daa` tool sources/hashes.
Each case uses copied saves, an identical original/rebuilt Lua overlay, 800x600 WineD3D, normal startup,
Escape at 5/12 seconds and a 60-second limit. Roundtrip work and assertions follow the previous milestone:
save, add 137 gold, reload, assert gold/army restoration, then write a fresh second evidence save.

| Save | Original | v57 plain | Decoded before/after in each engine | Cross-engine differences |
|---|---|---|---|---|
| `game1` | pass | pass | zero | `Time.msec` only |
| `game209` | pass | pass | zero | `Time.msec` only |
| `game210` | pass | pass | zero | `Time.min`, `Time.sec`, `Time.msec` only |
| `g_log` | required outputs absent | required outputs absent | not exercised | name unavailable in both load lists |

All runs remain alive without game error files. The `g_log` case stays on the Load screen because no matching
slot is available; the fixture never calls its load method. It is retained as an unmet selection precondition,
not reported as a game regression or a passing roundtrip. It is a parseable saved-state file, but this test
does not establish whether directly loading it through a different API would work.

Together with the previous game0 pair, **four regular world saves** now have exact decoded roundtrip state
in both engines. These supplied saves are all continent 1; the battle autosave `game00` is covered separately
by the previous tactical sequence. Save inputs still match their recorded SHA-256 identities.

## Native clock control

`original-game210-clock-control-k5f03jo0` repeats the original game210 test with the same EXE, fixture and
input schedule. It passes and has zero own roundtrip differences. Its comparison with the first original
run changes only `Time.min/sec/msec`:

- First original snapshot: minute 15, second 52, millisecond 386.
- Original repeat: minute 16, second 6, millisecond 629.
- v57 snapshot: minute 16, second 6, millisecond 990.

All other decoded fields match. Raw differences are retained in
`/home/attt-dev/work/wine-tests/native-game210-clock-control.json`. This demonstrates native snapshot timing
variation under these unsynchronized runs. It does not prove the rewritten timing contract equivalent;
fixed-step clock tests remain a separate verification need. No clock fields were filtered from comparison.

## Real continent transition, including AttTFix

`/home/attt-dev/work/wine-cohorts/continent2-ohw7akaw/` contains supervisor logs, `results.json`, comparisons
and `checkpoint.json`. All three 120-second runs pass:

| Build | Run directory under `/home/attt-dev/work/wine-tests/` |
|---|---|
| Original | `original-continent2-gul4ncf4` |
| v57 plain | `v57-continent2-3ktmoilj` |
| v57 plain + supplied AttTFix 2.1.2 | `v57-attfix-continent2-q9ddkn0t` |

The shared overlay first loads copied game0, then queues the game's normal `Move Object` action through
`WorldLevel.SaveLoad`. It uses the original story route from the transferred English
`continent1conversations.lua:28255`: hero to continent2, x=5185, z=6110, rotation=83, outside town. This is a
controlled hero transition; it does not execute the full dialogue/quest prerequisites or accompanying NPC move.

On arrival it asserts `WorldLevel.curContinent == 2` and creates `scenario_continent2.sav`. Each run requires
that output to be new/nonempty; independent decoding also confirms continent 2. The original and v57 plain
destination saves differ only in `Time.msec` (519 versus 681); original versus mod-enabled v57 differs only
in `Time.msec` (519 versus 23). All other decoded fields match, with no field filtering.

Normal world logic subsequently enters a tactical encounter in all three runs. Captures show turn 1 with
the same army layout; animation poses/lighting differ with timing and mod settings. The mod log records
continent2 script/resource loading and smoothing object-table clears on scene changes; the process remains
alive through the full interval without game error files. This is a bounded load/transition/encounter check,
not proof of every campaign transition or combat outcome. Software-rendered duration/FPS is not a native
Windows performance comparison.

`tools/make_wine_fixture.py --continent2` now reproduces the tested overlay byte-for-byte. Its SHA-256 is
`7bb966d4b1f000d4c4ab270954e755badb056b37389fe6849ccdf40eeebce8da`. It is mutually exclusive with
`--roundtrip`. Run it with the original or rebuilt EXE using `--overlay`, copied `--saves`, normal startup,
Escape at 5/12 seconds and `--require-file Saves/scenario_continent2.sav`; use the prior explicit test mod
DLL/INI for the mod case. The original GUIScenes bytecode is still retained unchanged under an alias.

## Limits and next work

These checks exercise real native/rebuilt call chains with shared test assets, not mocks. They do not
increase the count of generated functions verified by direct emulation fixtures or replace the existing
fuzz discrepancy inventory. Physical mouse automation, fixed-step timing, continent 3, attacks/spells/victory,
longer repeated mod-enabled transitions and independent valid-state fixtures remain open. The next useful
step is to turn observed world/combat states into smaller deterministic contracts and add attack/spell cases.
