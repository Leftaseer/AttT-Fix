# Tactical health and Fireball verification

The original and v57 plain deal 250 displayed damage with Fireball in the same gladiator encounter.
Both victory screens report one gladiator slain, zero troop losses, 244 gold and 610 experience.
The two victory saves are byte-identical with SHA-256
`dafb7b185e82a3b15c478ba79b27457273c8a473d49b29a98bf9989122de4f2b`.

## Live combat fixtures

The shared `--fireball --save game00` overlay loads the copied battle save and opens the tactical
spellbook on the hero’s turn. Recorded relative mouse input selects Fireball and targets the gladiator.
The fixture writes `Saves/scenario_fireball_victory.sav` from the real victory screen callback.
The runner requires that fresh output. Aim deltas were adjusted by inspection because the two runs
had different camera positions. The test covers this cast, damage display, enemy death and victory rewards.

| Engine | Run directory under `/home/attt-dev/work/wine-tests/` |
|---|---|
| Original | `original-fireball-qr02i86y` |
| v57 plain | `v57-fireball-k3beb4w1` |

Each run includes `selected.png`, `target.png`, `cast.png`, `victory.png`, `control.jsonl` and `result.json`.
The earlier input exploration in `original-cast-input-03u515hi` reached Fireball targeting and ended at its
time limit before a cast. The final pair uses byte-identical overlays with SHA-256
`134d4ddac265cee6810b85969961b19e1bdb377c8d2416afb8abe12aa88e3adf`.

The `--health --save game00` fixture independently tests the native tactical health API. It checks a
single live hero in slot 1, applies `SubHealth(7)` and `SubHealth(-7)`, and measures health after each
operation with `FactHealth(1)`. Both engines pass the exact loss and restoration assertions. Each run
produces a fresh `scenario_health_checked.sav` after the assertions. The saved evidence differs in seven
camera coordinates and rotations. The raw field differences are preserved in `health-comparison.json`.

| Engine | Health run directory |
|---|---|
| Original | `original-health-s4aey54d` |
| v57 plain | `v57-health-l9lupg2c` |

## Numeric health contract

`rebuild/tests/test_tactical_health.py` drives the `SubHealth` Lua binding at `005640F0` with a numeric Lua
stack value and a tactical creature whose script table is absent. Its 12 normal comparisons cover
fractional truncation, damage, healing and clamps at zero and maximum health across two x87 control words.
The test checks the health ratio, death flag, cleared pending damage fields, return value, stack cleanup
and preserved x87 mode. As with the existing differential suite, the two entry executions share callees.
The live fixture supplies additional coverage with initialized game objects and their script tables.

Both v57 builds pass **33 differential tests and 611 normal comparison pairs**. All **42 tooling tests**
pass. Reports and fixture hashes are in `/home/attt-dev/work/combat-verification/`.

## Relative mouse input

`wine_control.py RUN move-relative DX DY` sends relative XTEST motion. `click-relative DX DY` moves and
clicks, and a zero delta clicks at the current game cursor. This path drives the game’s DirectInput
cursor in the private Wine display. Choose coordinates from a live capture because the game applies its
own sensitivity and the camera can shift. The controller records the applied deltas in `control.jsonl`.

## Normal menu loading and reload after movement

The original (`original-mouse-load-9r2s401m`) and v57 plain (`v57-mouse-load-kc01i2za`) load the copied
`game0` through the normal menus with relative mouse input and standard game assets. In each run, F5
writes a private quicksave. The hero moves and the pause menu loads that quicksave. A second F5 save
confirms the exact saved hero position and rotation were restored. Decoding both pairs shows differences
only in clock fields. The initial original F9 probe left the hero at the moved position. The recorded
reload check uses the pause menu in both engines. Evidence is in `ui-reload-comparison.json` and each
run’s captures, `control.jsonl`, `before-ui-reload.sav` and `after-ui-reload.sav`.
