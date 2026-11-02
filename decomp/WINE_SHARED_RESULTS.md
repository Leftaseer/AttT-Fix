# Shared original/rebuilt integration fixtures — 2026-11-02

Evidence: `/home/attt-dev/work/wine-tests/shared-integration-v57-20261102.json`.
Seven completed smoke runs pass. v57 binaries, supplied archives/saves and the Windows installation are
unchanged. All **42 tooling tests** pass; log: `/home/attt-dev/work/wine-runtime/tooling-tests-shared-final.log`.

## Shared fixture and input limits

X11 synthetic clicks did not move the original game's DirectInput cursor or activate Load. A separate
Win32 `mouse_event` helper also failed to activate it. These are retained input diagnostics, not passing UI
load tests. `original-ui-load-corf8ltm` was closed with requested Alt+F4, exit 0; its generic survival verdict
is failed because the process exited. `original-win32-input-f3415upt` survived until controller completion.
Neither supplies evidence about a successful mouse click or save loading.

`tools/make_wine_fixture.py` instead creates a **test-only Resource2.pak**, copying the original GUIScenes
bytecode unchanged under an alias and adding a small Lua driver around its menu/load callbacks. The driver
opens the load scene, selects the named save and calls its normal `StrongLoad` method. The original and plain
EXEs use the identical generated overlay and copied saves; there are no native engine hooks/mocks or debug
test-input injection in these comparisons. These are controlled asset fixtures, not unmodified mouse UI tests.
Generated PAKs contain game bytecode and stay under `/home/attt-dev/work/wine-scenarios/`, outside Git.

Original GUIScenes bytecode SHA-256: `13ef56de137ebcdee3656cbcc9b033625ae74359f28543685a1d8a501c7356cf`.
Each generated fixture has a JSON manifest with original-script, driver and overlay hashes.

| Scenario | Original run | v57 plain run | Evidence |
|---|---|---|---|
| Load game0 | `original-shared-load-b73v5ham` | `v57-plain-shared-load-adi5ei55` | Same loaded world visible; original pause menu dismissed for its world capture |
| Save/perturb/reload game0 | `original-roundtrip-eqqkbmbh` | `v57-plain-roundtrip-idi4hfu7` | Both fresh required evidence saves present; assertions pass; decoded roundtrip states equal |
| game00, N/E/N combat keys | `original-combat-keys-_xcsj0hs` | `v57-plain-combat-repeat-1zbh61lg` | Both progress from turn 2 to turn-3 enemy/defeat screen, no game error files |

All run directories are under the evidence root `/home/attt-dev/work/wine-tests/`, with result manifests,
screenshots, copied game data and logs. Normal startup uses Escape at 5/12 seconds (the first original load
also used Escape at 20 seconds, which paused the loaded world). Combat adds N at 40, E at 55 and N at 70 seconds,
with a 90-second limit. The captures named `before-keys` were taken after the first N and before E; do not
interpret the filename as a pre-input checkpoint. The common defeat outcome after skipping/waiting is not a
crash. This bounded sequence does not prove damage rules, all spells/units, battle victory or each key's effect.

One earlier rebuilt combat run, `v57-plain-combat-keys-hnn5m16c`, ended with runner status 143 before reporting.
Its cause is unknown; it is retained as incomplete and excluded from passes. The attached-terminal repeat
completed. The runner now records SIGTERM/SIGHUP as interruption errors and clears active-session metadata
when finalization runs; an uncatchable termination can still leave an incomplete directory.

## Save/reload assertions and structured comparison

The roundtrip fixture schedules work through the game's `WorldLevel.SaveLoad` callback. It saves to
`scenario_saved`, adds 137 gold in memory, reloads that save, asserts restoration of gold and ordered army
unit/quantity composition, then saves to `scenario_reloaded`. The runner requires both output `.sav` files
to be nonempty and rejects required outputs that existed before launch. This catches a no-op load rather
than accepting a surviving process. Saves are written only in the private run directory.

`tools/save_state.py` decodes the game's float32/size_t32 Lua save constructors without executing Lua. It
accepts only data-construction instructions and the `Serialize` global; other instructions, closures and
incompatible headers fail. It preserves string versus numeric keys and reports scalar changes, including
signed zero. Canonical comparison ignores bytecode construction order and debug/source metadata, while
keeping every serialized data field. Negative controls detect changed gold and executable instructions.

Results in `roundtrip-state-comparison.json`:

- Original saved versus reloaded: **zero decoded differences**.
- v57 saved versus reloaded: **zero decoded differences**.
- Original versus v57 before reload: **two differences**, `Serialize.Time.sec` (2 versus 3) and
  `Serialize.Time.msec` (940 versus 30). The same two differences remain after reload.
- All other decoded fields match. Clock differences are retained explicitly; no fields were filtered out.

This is one saved state and one roundtrip in each engine, not a whole-game equivalence claim.

## AttTFix 2.1.2 activation and runtime evidence

Run `v57-plain-attfix-g9zaax8f` uses the supplied 2.1.2 DLL, SHA-256
`202caa2282681878e84022dab6d72f3d72fea619981f3a68c592392ab29b5a79`, with native Wine override
`dinput8=n,b`, the shared game0 fixture and explicit test INI. The run survives 60 seconds and displays the
loaded world without game error files. `attfix-activation-check.json`, `AttTFix.log` and `AttTFix_perf.log`
provide installation and execution evidence:

- Frame/render replacement, object/particle smoothing, forest batching, radix sort, asynchronous sound and
  lazy effect-state save/restore install successfully.
- Runtime skin optimization counters are active; a sample reports 300 validation comparisons, maximum
  error `9.2e-07`, `bad=0`. Mipmap counters show effects/textures processed with zero reported failures.
- WineD3D-specific unsupported optimizations remain disabled by the mod as logged. Widescreen and MSAA are
  configured off; DXVK is not used. The INI is retained in the run and its input hash is in the manifest.

This confirms more than DLL loading, but does not benchmark native Windows performance or verify every
mod setting. The current mod source identifies as 2.1.0; this test used the verified supplied 2.1.2 binary.

## Reproduction

From the active checkout, create an overlay with `tools/make_wine_fixture.py RESOURCE0 OUTPUT --save game0`
(add `--roundtrip` for its assertion/evidence saves). Run `tools/wine_game_test.py` with the original or v57
plain EXE, `--overlay OUTPUT`, copied `--saves`, normal startup and `--key-at 5:Escape --key-at 12:Escape`.
For roundtrip checks, require `Saves/scenario_saved.sav` and `Saves/scenario_reloaded.sav` via repeated
`--require-file`. For the mod, also pass `--mod-dll` and `--mod-ini`; neither is installed globally.

`tools/wine_control.py RUN capture LABEL`, `key KEY`, `click X Y` and `finish` operate on the private live
display and record actions in `control.jsonl`. Click coordinates are relative to the selected window, but a
successful X11 call does not establish game consumption. Capture names cannot overwrite existing artifacts.
The controller refuses sessions finalized as inactive. `finish` ends a surviving smoke after its final capture.

Next: more continents/saves and state contracts; controlled movement/attack/spell and battle-win scenarios;
longer mod-enabled save/load and continent transitions; DXVK as separate backend evidence. Physical mouse UI
automation remains unresolved in this Wine environment.
