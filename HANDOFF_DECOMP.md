# AttT decomp — handoff / full project context

Updated 2026-11-04. Read `decomp/VERIFICATION.md` for the current, hash-identified checkpoint and verification
limits, then `decomp/README.md` for pipeline internals. Older sections below preserve investigation history;
their status statements and test counts are superseded by the latest checkpoint.

For a new full sweep, start with `--native-coverage --jobs 16 --shards 96 --fn-timeout 30`.
Keep the first pass and any selected 120-second retries in separate output directories. The v57
first pass covered all 9,661 addresses in 29 minutes 9 seconds, with 488 timeouts. See
`decomp/VERIFICATION.md` for the complete command and the comparison with the earlier run.

**Current work: sound and geometry candidate.** Seven further translations have bounded
regressions, including Sound3D volume and terrain transform translation. The plain and debug
builds pass 43 differential tests and 795 normal comparison pairs. The plain build passes a
Wine save roundtrip with AttTFix 2.1.2. The 21-address rerun retains four raw differences and
six fault differences with separate diagnostic and valid-input evidence. The full plain
candidate sweep reconciles all 9,661 addresses in 33 minutes 34 seconds, with those same
10 raw mismatches and no new mismatch addresses. All 14 previously verified addresses
that timed out on the first pass verify at 120 seconds. Build hashes and evidence are in
`decomp/VERIFICATION.md`.

**Previous work: full v57 plain sweep and float edge fixes.** The 9,661-address baseline sweep is under
`/home/attt-dev/work/v57-full-sweep-20261104/`. The inventory tool can attach its completed verdicts
after reconciling all shards against the exact build. Seven confirmed mismatches in integer coordinate
bounds and mesh position setters are corrected in the local candidate, with the raw v57 results preserved.
All seven pass the targeted rerun. The plain candidate passes a Wine save roundtrip with active
AttTFix 2.1.2. The sound volume setter's NaN discrepancy has a mock DirectSound reproduction and
remains open. Build paths, hashes and evidence are in `decomp/VERIFICATION.md`.

**Previous work: grid lookup and debug action verification.** Both v57 builds match the original on 77,000
structured grid queries each and pass 34 differential tests with 653 normal comparison pairs. The raw
allocator byte difference reproduces in v57 plain; the diagnostic constructor-input control matches 30/30.
In Wine the debug menu opens the Barrack scene and starts a battle with one dragon at speed 1 and 100,836
HP, checked from the live unit. A Win32 probe confirms focus and cursor restoration with Ctrl+Alt+D and
both Close controls, despite stale X11 captures. See `decomp/VERIFICATION.md` for the exact-build evidence.

**Previous work: tactical damage and normal input verification.** Original and v57 plain produce identical
victory saves after casting Fireball for 250 displayed damage. Both also pass exact seven-point damage
and healing assertions in a live battle. The emulated numeric health cases bring both v57 suites to 33
tests and 611 normal comparison pairs. Relative XTEST motion drives the game’s DirectInput cursor.
Both engines load the copied quicksave from the menus and restore its position and heading after
movement. See `decomp/WINE_COMBAT_RESULTS.md` and `/home/attt-dev/work/combat-verification/`.

**Previous work: fixed-step clock and spellbook verification.** Both v57 builds pass all 24 clock cases in
independent original/rebuilt PE mappings, including fractional updates and calendar rollover. A deliberately
broken minute carry fails 12 cases. The original and v57 plain also render matching learned-spell pages
with the shared world spellbook fixture. Reports live in `/home/attt-dev/work/clock-verification/`.
See `decomp/VERIFICATION.md` for scope and reproduction. All 42 tooling tests pass.

**Previous work: expanded world-save and continent-transition verification**, v57 EXEs unchanged. See
`decomp/WINE_EXTENDED_RESULTS.md`; checkpoint `/home/attt-dev/work/wine-cohorts/extended-checkpoint-20261103.json`.
Ten more runs pass: original/plain roundtrips of game1/game209/game210 (zero own decoded-state differences),
original/plain/mod-enabled v57 transitions to continent 2 (fresh destination saves independently decoded),
and a repeated original game210 timing control. Cross-engine differences remain only serialized clock
fields; the native repeat also varies only in those fields. This is timing variation evidence, not a fixed-step
equivalence verdict. Both g_log attempts stay in the Load list because the name is unavailable; required
outputs correctly fail, with no game errors. All supplied regular world saves are continent 1; the shared
Move Object fixture covers actual continent-2 loading and a subsequent tactical encounter. Mod logs show
smoothing cache clears on scene changes; all three transition runs survive 120 seconds. The fixture builder's
new `--continent2` mode reproduces the tested PAK exactly. 42 tooling tests pass. Evidence cohorts are
`world-roundtrips-j3o_enr_` and `continent2-ohw7akaw`; old tool sources/hashes are retained. Next: deterministic
world/combat contracts, attack/spell/victory cases, fixed-step clocks and repeated mod-enabled transitions.

**Previous work: shared original/v57 integration milestone**, v57 binaries unchanged. See
`decomp/WINE_SHARED_RESULTS.md`; evidence `/home/attt-dev/work/wine-tests/shared-integration-v57-20261102.json`.
Seven completed smokes compare original/plain with identical Lua overlays (not native engine hooks): game0
load/world rendering, save/perturb/reload and a game00 N/E/N battle sequence. Both own roundtrip states match
exactly; original versus v57 differs only at serialized Time.sec/msec (retained, not filtered). Both tactical
runs reach turn-3 enemy/defeat without errors. AttTFix 2.1.2 installs real hooks in v57 plain and records active
skin/mipmap counters (sample skin verify=300, bad=0). Widescreen/MSAA/DXVK are outside that mod test.
42 tooling tests pass, including new fail-closed save-decoder controls. X11/Win32 mouse automation did not
activate the original Load UI; shared resource fixtures provide the comparison instead. One combat runner
143 is incomplete, repeated successfully in an attached terminal. New tools: `make_wine_fixture.py`,
`save_state.py`, `wine_control.py`; runner supports fresh required outputs, per-run mod/INI, overlays and
interruption records. Source/asset bytes are unchanged; generated PAKs contain original bytecode and stay
outside Git. Next: expand states/continents, movement/attack/spell/victory scenarios and longer mod transitions.

**Previous work: WSL Wine normal startup/menu and save-loading milestone**, v57 binaries unchanged. Original
and plain play intro videos (60 s runs) and reach visually matching main menus with external Escape keys at
5/12/20 s (35 s runs). Debug loads copies of `game0` and `game00` (60 s each), with load selection and a required
`scenario: world-scene 1` marker; captures show the loaded world/pause menu and tactical "Your turn" screen.
No game error files. One no-key debug attempt failed its required marker because native reserved Init bypasses
the old `skipintro` test hook; retained as failed, not a game crash. Input handling now records timed X11 keys,
save hashes and test-input hashes. All 37 tooling tests pass. Evidence:
`/home/attt-dev/work/wine-tests/menu-load-v57-20261102.json`; reproducible debug scenarios are in
`decomp/tools/scenarios/`, details/limits in `decomp/WINE_TESTING.md`. Next: original/plain save UI baseline,
write-save/reload, bounded combat/world actions and actual AttTFix activation; no mod was installed here.

**Previous work: initial WSL Wine world-start checks passed**, shipped v57 binaries are unchanged. The user
explicitly authorized running anything within the home directory. The original, v57 plain and v57 debug each
survived 35 seconds of developer world start (`-nologo`) with identical assets/settings; screenshots show the
opening world/dialogue scene, and debug also displays its menu and logs initialization. No game error files.
Evidence: `/home/attt-dev/work/wine-tests/world-start-v57-20261102.json`. One earlier debug run was interrupted
before reporting (143, cause unknown); it is retained as incomplete and was repeated successfully. These are
not menu, save/load, combat or mod-activation checks. The runner now makes developer launch explicit and
defaults to normal startup. All 35 tooling tests pass. See `decomp/WINE_TESTING.md` for the next scenarios.

**Previous work: isolated WSL Wine environment ready**, shipped v57 binaries are unchanged. See
`decomp/WINE_TESTING.md`. WineHQ 11.0 and a private prefix/display/null-audio device are installed under
`/home/attt-dev/work/wine-runtime`. A synthetic PE32 probe passed VC80 loads, native D3DX shader compilation,
D3D9 render/readback and DirectSound8 initialization. The tooling suite passes 35 tests. A game runner is
prepared with fresh copies/reflinks of inputs, private saves/configuration, logs, hashes and screenshots.
At setup time, automatic approval review rejected the original EXE launch, citing an existing Windows/Wine
game-launch restriction. The later explicit user authorization and approved runs are recorded above.

**Previous work: verification milestone**, tools commit `e7afd4a`; shipped v57 binaries are unchanged.
The user confirmed both v57 fixes (AttTFix activation and debug barracks) in-game. The transferred
`/home/attt-dev/AttT-decomp` archive was reviewed without replacing current code; see
`decomp/ARTIFACTS_REVIEW.md`. It supplies real resource archives, six saves, original Lua and a 2.1.2 DLL
matching the v57 profile. The older source checkouts identify as 2.1.0. Wine/prefix/display tools were absent
at the archive review; the later Wine setup is described above.
New verifier controls reject deliberately broken replacements, native/native selections and mismatched report
identities; nonfinite filtering is explicit, normal-return coverage determines verification, and sweep timeouts
are distinguished from emulator crashes. Both v57 binaries pass 32 differential tests (599 normal comparison
pairs / 32 addresses); 29 tooling tests pass. All 20 focused addresses have normal-state fixtures. The current
20-address fuzz run is 7 verified / 8 faultdiff / 3 timeout / 1 lowcov / 1 differs; no full sweep was rerun.
Inventory: 10,167 active replacements, 9,661 autoverify-eligible generated-source addresses; 20 have direct
normal fixtures. Evidence: `/home/attt-dev/work/verification-v57-20261102/`. Next: expand valid state/lifetime
fixtures, add original-image call-chain comparisons, and prepare isolated WSL Wine integration tests.

**Current checkpoint: v57 AttTFix compatibility / barracks candidate**, source commit `c9d773e`, package
`E:\Programs\Qoder_plays\AttT-Fix\AttT_decomp_exe_v57`. Both binaries use `--attfix-compat`, reserving 110
native functions and forwarding 540 original function IAT slots through the new import table. This leaves
10,167 replacements (99 fewer than v56); debug has 10,100 switchable functions. The supplied AttTFix 2.1.2
DLL loaded in v56, but its engine hooks failed byte checks: preserving addresses/timestamp was insufficient.
The new profile audit proves all 110 reserved functions / 51,968 bytes match the original. Both binaries pass
31 differential tests and relink with zero mismatches; ten tooling tests pass. Debug frame-end Lua works
through the native/mod-owned Frame, checked in emulation. Barracks now initializes its template directly;
the previous pre-activation ChooseScene was cleared by native GUI activation. All 115 selections pass the
updated action fixture, and normal army definitions are restored afterward. The user has since confirmed
mod activation and the barracks action; broader gameplay and visual coverage remain separate validation work.
No game has been launched by the agent. Evidence is under `/home/attt-dev/re/v57-20261102/` and
`/home/attt-dev/work/debugmenu-v57/`. See `decomp/VERIFICATION.md` for hashes, build details and limits.

Previous candidate: v56 debug-menu fixes, source commit `cbab162`, package
`E:\Programs\Qoder_plays\AttT-Fix\AttT_decomp_exe_v56`. Barracks now opens through the world's army-screen
GUI container; the tough dragon has unit Speed 1 (an additive correction against its base Speed);
Ctrl+Alt+D always shows/focuses the menu, while Close/X hide it. The updated debug binary passes 31
differential tests and relink with zero mismatches; nine tooling tests pass. Additional compiled-handler /
Lua VM checks cover 115 unit selections, battle stats and menu recall with scene/Win32 mocks. The plain
binary and map are identical to v55. **Next: user playtest of barracks, dragon stats, focus and cursor.**
Builds/logs are under `/home/attt-dev/re/v56-20261102/` and `/home/attt-dev/work/debugmenu-v56/`.
The user's next playtest found the barracks and mod hook failures described above; v57 supersedes this candidate.

Previous checkpoint: the level-up animation and battle Wait bugs were confirmed fixed in-game. v55 was delivered at
`E:\Programs\Qoder_plays\AttT-Fix\AttT_decomp_exe_v55`, source commit `37b6280`, with English instructions,
plain/debug exes, matching maps, toggle list and hashes. Both binaries pass 31/31 differential tests plus nine
tooling tests; relink has zero mismatches. Six additional translation defects are fixed (distance sums, NaN
partitioning, signed grid conversion, two collision guards and the frustum guard). The 15-address recheck is
5 verified / 1 lowcov / 1 allocator-padding differs / 8 classified faultdiff. These retained diagnostics and
older full-sweep coverage gaps are documented, not hidden. **Next: the user's in-game playtest.** The agent
has not launched the game or changed its Steam installation. The historical 9,734-row sweep belongs to an
older binary; do not claim it was rerun on v55/v56 or update its counts with targeted results.

---

## 1. Goal

Decompile the engine of *Ascension to the Throne* (AttT, Steam 1.1.128, MSVC 2005 /O2 /LTCG) into C,
rebuild a runnable `ATThrone.exe` from the original bytes plus the rewritten functions, verify it, and hand
the user playtest builds so subsystems can be modernised and modded later.

Full replacement preset: **10,266 of 18,591 functions replaced**. The shipped v57 AttTFix compatibility preset
has **10,167 replacements**, reserving the mod's native hook boundaries. Everything else is original bytes.
The exe is relinked, not recompiled: original
sections keep their addresses, new code goes to `.ntext`/`.nrdata`/`.ndata`, PE TimeDateStamp is preserved so
AttTFix (dinput8.dll) keeps working.

## 2. Hard rules (from the user, still in force)

- Work only in: WSL distro **AttT-Dev** (user `attt-dev`) and `E:\Programs\Qoder_plays\AttT-Fix`.
  Never touch the user's own Ubuntu distro, never write anywhere else on Windows.
- Reading `E:\SteamLibrary\steamapps\common\AttT` is allowed; writing there only via the user's playtests.
- **Never launch the game on Windows yourself** — the user playtests. On 2026-11-02 the user supplied prior
  artifacts and suggested Wine testing in WSL. Investigate an isolated WSL setup using fresh run directories;
  no Wine runtime or prefix is currently installed. The historical Wine scripts need path/dependency and
  artifact-preservation fixes before use. Keep the Windows installation and transferred originals untouched.
- Do not delete test files / builds / playtest packages without explicit consent.
- Valkyrie (the second game in this engine family) is **out of scope** for now.
- Reply and write new documentation in **English**, including package instructions (confirmed 2026-11-02).
- Work primarily in `/home/attt-dev`; put only user-facing deliverables in the Windows folder.
- Push completed checkpoints periodically to `decomp/continue` (authorized 2026-11-02).

## 3. Environment

Current shell: WSL **AttT-Dev**, user `attt-dev`. Active source checkout:
`/home/attt-dev/work/AttT-Fix`, branch `decomp/continue`. Builds, logs, manifests and scratch work stay in WSL.
The Windows checkout retains the previous session's files; do not assume its HEAD matches the active checkout.

Windows-side paths (historical context and playtest delivery):

- Repo: `E:\Programs\Qoder_plays\AttT-Fix` (git, branch `decomp/continue`, origin
  `https://github.com/Leftaseer/AttT-Fix.git`).
- Game: `E:\SteamLibrary\steamapps\common\AttT\ATThrone.exe` (+ `ATThrone.exe.noLAA.bak`), saves in
  `...\AttT\Saves\` (`game0.sav` = quick save, `game00.sav`, `game1.sav`, …), `decomp_debug.log` and
  `decomp_toggle.log` are written next to the exe.
- `E:\Programs\Qoder_plays\AttT-Fix\.att_tmp\` = scratch (gitignored): disassemblies, one-off scripts, build
  scripts. Contains the current investigation artifacts (see section 9).

From an external Windows shell, WSL can be invoked through a script file:

```
MSYS_NO_PATHCONV=1 wsl.exe -d AttT-Dev -- bash /mnt/e/Programs/Qoder_plays/AttT-Fix/.att_tmp/<script>.sh
```

- `source /home/attt-dev/env.sh` (clang, lld-link, llvm-*, python via `$HOME/pyenv/bin/python3`, Ghidra at
  `$GHIDRA`, `$MINGW_INCLUDE`, `$PYTHONPATH`).
- Game copy for builds: `/home/attt-dev/work/attt/bin/attt.exe`; work dir `/home/attt-dev/work/attt`.
- Auto-decompiled C: `/home/attt-dev/work/attty_test/auto_fix4` (`auto_*.c`, `functions.tsv`, `convs.tsv`,
  `rets.tsv`, `protos/`). ~9 734 generated functions live here, not in git.
- Build outputs: `/home/attt-dev/re/buildNN/` (`ATThrone_*.exe` + `.map` + `work_attt/`).
- AttT-Dev sudo password: kept in the session notes, never in this repo (needed only to install packages; avoid).

## 4. How to build

```
cd /mnt/e/Programs/Qoder_plays/AttT-Fix/decomp/rebuild
python3 -I build.py --exe /home/attt-dev/work/attt/bin/attt.exe --auto /home/attt-dev/work/attty_test/auto_fix4 \
    [--toggle] [-D DECOMP_DEBUG_LOG] [-D DECOMP_TEST_INPUT] [-D DECOMP_DEBUG_MENU] \
    [--fixed-exclude FILE] [--auto-exclude FILE] [--coverage] \
    --out /home/attt-dev/re/buildNN/ATThrone_xxx.exe
```

- `--fixed-exclude FILE`: one `004B2720`-style address per line; keeps the original code at those entries
  (used to keep 0x004B2720 original in the "working" v45 builds). `--auto-exclude` does the same for the
  generated set.
- `--toggle`: adds `toggle.c` + `decomp_toggle.txt` support (runtime bisection, see section 7).
- `-D DECOMP_DEBUG_LOG`: `decomp_debug.log` (crash handler + engine errors + custom probes).
- `-D DECOMP_TEST_INPUT`: `testinput.txt` (`skipintro`, `fastcam`, `loadsave NAME`, `MS lua CODE`, …) and the
  debug hotkeys **Alt+1..4** (1 = +100000 experience → level up, 2 = +100000 gold, 3 = +12 h, 4 = +7 days).
- `-D DECOMP_DEBUG_MENU`: the Win32 debug menu of v52 (`src/engine/debugmenu.cpp`; requires
  `DECOMP_TEST_INPUT`, enforced by `#error`): Ctrl+Alt+D window with all spells, +100000 gold, a barracks with
  any of 115 unit ids, and a 1×uDragon battle at +100000 health. See section 13.
- `--coverage`: per-function coverage counters.
- Hand sources in `decomp/rebuild/src/fixed/f_*.c` override generated ones; header `/* @conv ECX 8 */` must
  match `convs.tsv`. Engine sources in `src/engine/`, Lua 5.1.2 in `src/lua51/`.
- Gotcha: build.py caches per-file objects in `~/.cache/decomp_build`, so `__DATE__/__TIME__` in the log line
  "---- start … build …" is stale — it does **not** identify the exe. Compare hashes instead.

## 5. Verification (do both before every delivery)

```
python3 decomp/tools/difftest.py /home/attt-dev/work/attt/bin/attt.exe <exe> <map>   # expects 12/12
# verify_relink runs inside build.py and prints the numbers:
#   sections .text,.rdata,.data,.ndata,.ntext, 4604704 bytes and 86576 pointers checked, 0 mismatches
```

Difftest emulates original vs replacement functions (Unicorn) on the Lua/engine test suite in
`decomp/rebuild/tests`. `autoverify.py` (random inputs) was run over all 9 734 generated functions on
2026-10-31: 3 613 verified / 4 918 lowcov / 936 unsupported / 267 crashed / 0 differs, 0 faultdiff —
**but that sweep was vacuous, see §5.1; it is being re-run as verify76.**

### 5.1 Unicorn TB cache bug in the harness (found 2026-11-02, fixed)

`Harness.call()` runs the original bytes at the entry, then writes the replacement head (`E9` jmp or the
function bytes) and runs again. Unicorn 2.1.4 does **not** invalidate the cached translation block on that
`mem_write` when the `until` (STOP) address is a mapped page — which it is (0x0FFF0000). The second run
therefore silently re-executed the cached *original* body, so every comparison compared the original with
itself. Minimal reproductions: with STOP unmapped and `until = entry+3` the write invalidates; with STOP
mapped it never does, for any write size. Proof against a real build: deleting the fix makes
`test_0050B9A0_wait.py` pass on build75 (the buggy build), keeping it makes build75 fail.

Fix: `uc.ctl_remove_cache(entry, entry + 16)` before every `emu_start` in `Harness.call()`
(`decomp/tools/difftest.py`). `FastHarness.run_case()` (autoverify) goes through the same `call()`, so
both tools are fixed. **All difftest/autoverify numbers produced before 2026-11-02 are invalid** and must
be re-established with the fixed harness.

## 6. Playtest packages (gitignored folders in the repo root)

`AttT_decomp_exe_v42 … v53`, each with a Russian `README_RU.txt` (+ `maps/`). History:

- v42/v43/v44 — auto / auto_debug / coverage / hand + `toggle_bisect.bat|ps1` + `toggle_list.txt`.
  v42 was the save-load crash (fixed in 635a126: the ABI adapter must forward every stack dword the original
  popped, 0x48C240). v44 fixed a missing third argument in a hand function.
- **v45 — the last known-good package**: `ATThrone_auto.exe` (damage-preview fix d256947 included; 0x004B2720
  kept original via `--fixed-exclude`), plus auto_debug / coverage / hand and `ATThrone_probe.exe`.
- v46 — probe2 only (instrumented 0x004B2720, *old/buggy* string reader).
- v47 — `ATThrone_ctrl.exe` (replacement in, **no** logging) + `ATThrone_probe3.exe` (replacement in + fixed
  string reader). Both reproduce the animation bug → logging is not the cause.
- **v48** — `ATThrone_auto_debug.exe` (== probe3 binary) + `toggle_list.txt` (10 212 switches) +
  `toggle_list_suspects.txt` (26 direct callees of the constructor) + `toggle_only4b2720.txt` +
  `toggle_bisect.ps1/.bat` with **004B2720 forced on** + Russian README with the bisection procedure.
- v49 — same engine + the v48 harness bugs fixed (see §7.1). One exe `ATThrone_auto_debug.exe`,
  `toggle_list.txt` (10 194 switchable generated functions, **sorted by address**), `toggle_bisect.ps1` with a
  baseline step, Russian README. Superseded v48: the user's first v48 step switched off our own engine code.
  Its bisection produced 14 "no" answers in a row and "found" 004205D0, which is byte-identical to the
  original — the answers were not reliable (see §7.2).
- **v50** — `ATThrone_auto_debug.exe` (sha256 1a1e4d73…) = the same build plus engine-side
  diagnostics (scene-change log, `rankchange: built/current scene` frames, back-buffer shots `rc_NN`/`rs_NN`),
  automatic level-up through `testinput.txt` (`L4000 lua …`), `toggle_bisect.ps1` v50 with A/B controls, a
  per-run engine verdict, a "no scene built → repeat the step" guard, a confirmation run, and a
  `bisect_version.txt` tag that sets v49 results aside instead of trusting them.
- **v51** — the level-up animation fix (section 8) confirmed in-game. `ATThrone.exe` (build73, plain
  `--auto`, 7,008,256 B, sha256 fba42f4d…) + `ATThrone_debug.exe` (build72, `--toggle -D DECOMP_TEST_INPUT
  -D DECOMP_DEBUG_LOG`), maps, `toggle_list.txt`, generic `toggle_bisect.bat|ps1` + `bisect_scenario.txt`,
  Russian README.
- **v52** — same plain exe as v51 (build75 was byte-identical to v51 plain; its 0x0050B9A0 contains the
  wait bug of §14) + `ATThrone_debug.exe` (build74, adds `-D DECOMP_DEBUG_MENU`; 7,451,136 B, sha256
  ac980534…), maps, toggle_list, Russian README with the menu instructions. Builds: 0 mismatches / 11
  difftest tests each (comparisons were vacuous, §5.1). Not yet played: the menu was verified statically
  (symbols, imports, embedded chunks) only.
- **v53** — the battle Wait fix (§14). Plain `ATThrone.exe` = build76 (`--auto`, 7,008,256 B,
  sha256 33a4999c…) + `ATThrone_debug.exe` = build77 (toggle + debug log + debug menu; 7,451,136 B,
  sha256 c47a02a1…), maps, `toggle_list.txt`, Russian README. 0 relink mismatches, 10 266 replaced
  functions, difftest 12/12 on both **with the fixed harness**.
- **v54 — current**: debug-menu usability only, plain exe unchanged. Cursor fix (game clears it with
  `SetCursor(NULL)` every step and `ShowCursor(0)` on `-nologo`; the menu now shows/unwinds the display count
  on pause/resume and answers `WM_SETCURSOR` at `HTCLIENT`) and two-stage spell learning (first click = the
  25 working spells — 24 with a `SpellAct` implementation + `spA07_Portal`; second click = all 40, unfinished
  included). Plain `ATThrone.exe` = build79 (`--auto`, 7,008,256 B, sha256 33a4999c… = v53) + debug
  `ATThrone_debug.exe` = build78 (7,452,160 B, sha256 74049765…), maps, `toggle_list.txt`, Russian README.
  0 relink mismatches, 10 266 replaced, difftest 12/12 on both; the new `kSpells` chunk also validated in a
  real Lua 5.1 VM (fengari): 40-spell table → 25 on the first click → 40 on the second, FireWall only on the
  second. The v53 Wait fix was confirmed in-game on 2026-11-02 and `decomp/continue` was pushed then (v54 is
  included in that push; the v54 menu changes are debug-build only and still await a playtest).

## 7. Runtime bisection (`--toggle`)

`toggle.c` reads `decomp_toggle.txt` next to the exe before the C runtime starts. All replacements are on
first; rules apply in order:

```
- 00000000-FFFFFFFF     # switch everything off
+ 004B2720              # switch one on
+ 004B0000-004C0000     # switch a range on
```

`decomp_toggle.log` reports `N of 10266 replaced functions on`. 75 replacements can never be switched off
(build.py `ALWAYS_ON`): the 54 Lua-library entries and the 17+4 hand-written engine functions (src/engine:
window, main loop, frame, input; plus CEngine::Init 0x44F2E0 kept in src/fixed, listed in `HARNESS_EXTRA`).
Switching a function off copies the original entry's first instructions into the slot and jumps back — no code
is written to .text.

### 7.1 Why the first v48 bisection step broke the test (fixed in v49)

Symptoms the user reported: intro not skipped, save not autoloaded. Causes:

1. The step's rules (`- 00000000-FFFFFFFF`, `+ 00449F80-004E1C60`, `+ 004B2720`) also switched off our own
   engine: `CEngine::Init` (0x44F2E0, whose vtable slot then ran the *original* Init → intros), `GameMain`,
   `WinMain`, etc. The test harness lives in that code. v49 keeps every hand-written replacement on.
2. `toggle_list.txt` was in source order, not address order, while the script enables "`list[0]`–`list[mid-1]`"
   as a numeric range → the halves were not halves. v49 writes the list sorted (build.py does it).
3. The autoload Lua only acted when `GUIScene.Load.scene` was *already* up; nothing ever opened the load
   screen. v49 opens it like the Load button (`GUIScene.MainMenu.scene:ChooseScene('Load')`), finds the name in
   `GUIScene.Load._SlotNames`, sets `_CurrentSlotNum` (page-relative: `idx - _FirstSlotNum + 1`) and calls
   `StrongLoad()`. Every stage logs to `decomp_debug.log` (`skipintro: on`, `testinput: opened`,
   `autoload: opening the load screen`, `autoload: <name>`, `autoload: loaded at N ms`).
4. `testinput.txt` was opened CWD-only; v49 falls back to the directory of the exe (`TestInputFile()`).

The bisect script now runs a **baseline step** first (no generated function on). If the animation is missing
there, the culprit is hand-written code (most likely 0x004B2720 itself) and the search stops with that message.

`toggle_bisect.ps1` (v49) loads a save, has the user press Alt+1, asks y/n, and binary-searches
`toggle_list.txt`, always re-enabling `004B2720` at the end of the rule list. State in `bisect_state.txt`,
permanent exclusions in `bisect_exclude.txt`, baseline flag in `bisect_baseline.txt`.

### 7.2 Why the v49 answers were unreliable, and what v50 changes

The user ran 14 steps and answered "n" every time; the search converged on 004205D0. That cannot be right:
at k=1 exactly one function is on (004205D0), and `src/fixed/f_004205D0.c` is a `@raw` thunk that is
byte-identical to the original and is also on in the working v45 build. So at least that "n" was not about
the function the step had switched on. Nothing in v49 could detect that: a step counted as "n" even when the
hero never levelled up (no Alt+1, wrong save), and the stale `bisect_state.txt` ("0 1274") /
`bisect_exclude.txt` ("004205D0") from a v49 run would have been read as this search's own progress.

The game folder itself is fine (checked 2026-11-01): AttTFix logs `Enabled=0`, Resource2.pak present, the
harness worked in all 20 logged launches (`skipintro`/`testinput`/`autoload game0`), and 0x004B2720 built the
scene in every one of them. The failure was in the protocol, not in the folder.

v50 (all in `src/engine/engine.cpp`, `DECOMP_TEST_INPUT`, plus `toggle_bisect.ps1`):

- `src/fixed/f_004B2720.c` publishes the scene it builds (`g_rankSceneMade`); `CEngine::Frame` logs every
  scene change and the frame the scene was built / became current; `CEngine::Render` saves the back buffer as
  a 400x300 24-bit BMP (`rc_NN` = +20/50/80/110/140/170 frames after the build, `rs_NN` = +10/40/70/100 while
  it is current). The script copies them to `bisect_shots\<step>\`.
- The level-up is automatic: `testinput.txt` gets `L4000 lua pcall(function() Actions:Expirience(100000) end)`
  (`L` = ms after the save has loaded), so no Alt+1 timing is involved (Alt+1 still works as a fallback).
- Two controls run before the search: A = everything on (bug must reproduce), B = everything off except
  004B2720 (animation must play). A failing control stops the search and says what to send.
- A run with no `rankchange: built` line (or a crash) is not accepted as y/n — the script asks to repeat it.
- The result gets a confirmation run (`+ 00000000-FFFFFFFF`, `- <culprit>`); only "y" there confirms it.
- Every run's `decomp_toggle.log` count is printed and compared with the expected number (control B calibrates the
  75 always-on entries; a range that contains 004B2720 or an excluded address is corrected for), so "the rules were
  not applied" cannot silently pass as an answer.
- `bisect_version.txt` = `v50`; files of an older search are moved to `bisect_old_<stamp>\`.

Script logic was tested end-to-end with a stubbed `Start-Process`/`Read-Host` (16-run search, the confirmed and
the not-confirmed paths, resume from `bisect_state.txt`, no-scene-built guard, toggle-count accounting) in
`.att_tmp/test50.ps1` / `test50b.ps1` plus the parser check `check50.ps1`; it has never launched the real game
from this side.

### 7.3 Generic bisection script (v51+, `AttT_decomp_exe_v51\toggle_bisect.*`)

The v50 script was hard-wired to the animation (level-up trigger, `rankchange:` evidence, 0x004B2720 forced).
v51 ships a generic one for any bug; its example scenario is the animation bug, now fixed, so Control A on it is
expected to say "the bug did not appear":

- `bisect_scenario.txt`: `[note]` (printed before each run), `[input]` (testinput.txt lines; `0 skipintro`
  and `0 fastcam` are always prepended), `[force]` (generated addresses kept on in every step).
- The only question is "is the bug present?" (y/n/r/q), so the same search works for any bug.
- Controls: A = `+ all` must answer y; B = `- all` must answer n (hand-written code is always on). B answering
  y means the cause is hand-written code (engine, src/fixed, harness) — the search stops and says so.
- Search rules `- all`, `+ prefix`, `- exclusions`, `+ force`; the found function is appended to
  `bisect_exclude.txt`; the confirmation run is `+ all`, `- exclusions`, `- culprit`.
- Evidence per step: toggle count from `decomp_toggle.log` (with an expected-count warning), the last 30 new
  lines of `decomp_debug.log`, every new `*.bmp`, plus `decomp_toggle.txt`, `testinput.txt` and `step.txt` in
  `bisect_shots\<step>\`. The v51 exe still writes BMPs only for the rank-change scene, so generic steps usually
  have none - the log tail is the evidence.
- `bisect_version.txt` is a SHA256 signature (scenario + toggle_list + exe); when any of them changes,
  `bisect_state/exclude/ctrl_*` move to `bisect_old_<stamp>\` and are never read as the new search's results.
  A search resumes through `bisect_state.txt`.
- `testinput.txt` is rewritten per step and removed by the finally block (Ctrl+C leaves it behind - delete it
  by hand so the next launch does not replay the scenario).
- Default exe: `ATThrone_auto_debug.exe`, then `ATThrone_debug.exe`; `-Exe` overrides. `-Check` parses the
  scenario and exits without starting the game.
- Tested with the same stubbed harness (`.att_tmp/test_bisect.ps1`): find, stop+resume, confirm, both control
  failures, `[force]`, scenario-change archiving. Never launched the real game from this side.

## 8. Level-up animation investigation — fixed in v51

**Symptom**: with our 0x004B2720 in the build the rank-change animation does not play (user's words: "нет
анимации"). With the original 0x004B2720 (`--fixed-exclude nofix_4b2720.txt`, i.e. v45 auto) it works.

**Proof it is not the logging**: v47 `ATThrone_ctrl.exe` was built with the replacement compiled in and
`-D DECOMP_TEST_INPUT` only (no `DECOMP_DEBUG_LOG`) — the animation was still missing. Also
`decomp_toggle.log` of that run said `10266 of 10266` on, so nothing was silently switched off.

**Code**: `decomp/rebuild/src/fixed/f_004B2720.c` (hand). A `/* @conv ECX 8 */` thiscall: ECX = scene,
2 stack args (`self_of_caller`, `*(that+0x388)` kept at scene+0x80), `ret 8`, returns the scene.

What it does (matches the original, audited twice):
base ctor 0x4B20D0(arg1) → scene+0x80 = arg2 → vtables 0x6109BC (this) / 0x61099C (+4) → +0x74 = 0;
hero 0x425F60, skins/anim/glow tables via 0x4323E0/0x45C740/0x4648E0/0x464970/0x4B2690/0x4B2670/0x4B2670/
0x44D030/0x4369F0/0x45BB70/0x4B2670 → model string → 0x57AC90(anim,2/5) = frame range → `new(0x204)` +
0x42A0D0/0x42A530 (`&name` whose +0x1c/+0x20 are the range) → `new(0x1cc)` +
0x4B2430 (animation player at +0x7C) → model fields 0x58..0xA4, 0x1E4=1, vf+0x18 → `new(0x324)` + 0x4EC6F0
(shadow at +0x78) → Lua loop over RankChangeGlow: `new(0x690)` + 0x550420 + 0x54EA10 + 0x54FE30 + place
callback at ps+0x2f4 → teardown, `return this`.

Downstream (all auto-generated, unchanged): caller 0x53FCC0 (`new(0x84)`, `sub_004B2720(scene,this,*(this+
0x388))`, `sub_005079E0(this+0x44, scene)`, `sub_004B2260(scene)` → `*(scene+0x7c)` → `sub_004EF750(
G_006C8C3C, player, 0, 0)`, `*(byte*)(this+1000)=1`). Scene Update override 0x4B25B0 calls base 0x4B1D10(dt)
and tears the scene down when `model->byte[0x1dc] != 0`.

**Runtime log from probe3 (2026-11-01 20:06, correct after the string fix)** — all values plausible:
```
hero 'Warrior'/7/15, skin 'W02_Sergeant'/12/15, tables 0x607cc4 with registry refs 72/48/43,
model 'W02_Sergeant.skm;5;W05_LieutenantColonelRankChan'/54/63, model vtbl 0x00608424, player vtbl 0x00610a14,
built model=0x36cdf798 player=0x339f3e90 shadow=0x…, 4 effects RankChangeColumn/Magic/ExplodeSparks/Smoke,
counts 0/40/125/145, heights 0/10/8/0; no crash, function ran to the end.
```

**Ruled out** (each verified concretely, do not redo blindly):
- std::string layout misunderstanding (the earlier "garbage names" were the probe's own bug — see 9).
- argument order/count of every callee of 0x4B2720; call-target sets of original vs our compiled function
  match exactly except the three glue thunks (0x45BB70, 0x463AD0, 0x57AFB0 are *not* replaced, so the
  compiler calls `glue.obj` cdecl→thiscall adapters 0xb0c59c / 0xb0c6d9 / 0xb0d2f4; bodies verified).
- scene vtable pointers, +0x80 list add, +0x74/0x78/0x7C stores, teardown order, `ret 8`.
- logging side effects (ctrl exe, section 8 paragraph 2) and toggle state.

**ROOT CAUSE (found 2026-11-01, fixed in v51)** — the model's frame range lives in the caller's frame.
0x0042A530 takes `&name` (a pointer to the MSVC8 std::string member of a larger struct) and reads the
animation's first and last frame from `*(int*)(&name+0x1c)` and `*(int*)(&name+0x20)`; it stores them as
model+0x1D0 (first) and model+0x1D4 (last), and 0x42A7A0 advances model+0x1CC only while +0x1DC==0. The
original 0x4B2720 computes those two ints itself, right before building the model:
`sub_0057AC90(&anim, 2)` → first, `sub_0057AC90(&anim, 5)` → last, each truncated to int by
`fnstcw/fldcw 0xC00/fistpll` (disasm 0x4b2afe–0x4b2b67; name string sits at S+0xB0, the ints at S+0xCC and
S+0xD0 = name+0x1c/+0x20). Our ctor called both functions and threw the results away, so 0x42A530 picked up
stack garbage as the frame range: the model loaded at the wrong frame and never advanced. Camera zoom and
particles still ran, which is exactly what the ctrl_off shots show (camera close, hero frozen in idle).

Log proof: `4b2720 anim25 a=0x00000000 b=0x43750000` → anim[2] = 0.0f, anim[5] = 245.0f.

Why bisection could never find it: 0x42A530, 0x4B25B0, 0x4B1D10, 0x4B2430, 0x53FCC0 are all *generated* and
were original in control B; the only code wrong was our 0x4B2720, which is always on in a toggle build.

**Fix** (`src/fixed/f_004B2720.c`): the model name now lives in `Name_4B2720 { Str_4B2720 name; int first,
last; }` with `_Static_assert(sizeof(Str_4B2720)==0x1c)` and `__builtin_offsetof(first)==0x1c`,
`offsetof(last)==0x20`; `first = (int)sub_0057AC90(&anim,2); last = (int)sub_0057AC90(&anim,5);` and
`&nm.name` is what goes to 0x42A0D0/0x42A530. Verified in the built exe (build73, `_f_004B2720` at
0xa44b90): `or $0xc00/fldcw/fistpl` then stores to 0x104/0x108(%esp), `lea 0xf0(%esp),%ebx` = &name = E1+0xE8,
`push $1; push %eax; push %ebx; call 0x42a530`.

Verification for v51: build73 (plain `--auto`) and build72 (`--toggle -D DECOMP_TEST_INPUT -D
DECOMP_DEBUG_LOG`) — both `4604704 bytes and 86576 pointers checked, 0 mismatches`, both difftest 11/11.
User confirmed in-game on 2026-11-02 ("анимация теперь работает"); fix pushed to `decomp/continue`
(commits 2029335 harness, 7e5976c fix).

## 9. Hard-won technical facts

- **MSVC8 std::string = 28 bytes**: allocator +0, `_Bx` +4 (16-byte inline buffer while `_Myres` < 16,
  otherwise the heap pointer at +4), `_Mysize` +0x14, `_Myres` +0x18. Short-string inline storage is why a
  probe that reads `*(char**)s` prints garbage. Confirmed by 0x42A0D0 itself (`mov 0x14(%edi),%esi; cmp $5`)
  and by every `sub $0x1c` by-value push. Project convention: `typedef struct { unsigned int w[7]; }`.
- **glue.obj**: every original function that is *not* replaced gets a thin adapter in `.ntext` so that
  C-ABI calls with (reg-params, stack) reach the original ABI. Pattern: push ebx/esi/edi/ebp, push the last
  (out) stack param, `mov 0x18(%esp),%ecx`, `mov 0x1c(%esp),%ebx`, call original, pop, `ret` (cdecl cleanup
  by the caller). If a call target points into 0xb0xxxx, it is one of these, not a bug.
- **0x42A0D0** is **cdecl**, 3 args, arg1 = the std::string (reads size at +0x14), returns a 0x248- or
  0x1dc-byte object. Our `sub_0042A0D0(&name, &c, 1)` is right.
- **0x463AD0** is thiscall with ONE stack arg (`ret 4`), out pointer returned in EAX.
- Level-up flow and scene fields: see section 8.
- **0x42A530 reads the animation frame range from the caller's frame**, not from the mesh: it takes `&name`
  and uses `*(int*)(&name+0x1c)` / `*(int*)(&name+0x20)` as first/last frame (model +0x1D0/+0x1D4); 0x42A7A0
  advances +0x1CC up to +0x1D4 and sets +0x1DC. Any ctor calling it must place those two ints directly after
  its name std::string. Same pattern to check in every other 0x42A530 call site (0x4B2x, 0x42Bxxx users).
- Every 0x004B27xx scene class writes `+0x74` model, `+0x78` shadow, `+0x7C` animation player, `+0x80` list.
- Model flags at +0x1DC / +0x1E4 look like "animation finished" markers (written in 0x42A65B/0x42A67A,
  0x42A7CC, 0x42B0C0, 0x42B1AE). Nothing confirmed yet.

## 10. Scratch artifacts for this bug (`.att_tmp/`)

- `orig_4B2720.dis` — original 0x4B2720 (0x4B2720–0x4B2FFD, 585 insns, 84 calls).
- `new67_4B2720.dis` — our compiled version in build67 (0xADD830–0xADDF21, 480 insns, 77 calls). Careful:
  the dump continues past the function into the next one; the function ends at the `ret $0x8` at 0xADDF21.
- `dis_42a0d0.txt` — 0x42A0D0 disassembly (the string/length proof).
- `glue463ad0.txt` — glue thunk bodies (0x463AD0, 0x463B40, 0x46AA00).
- `cmp4b27d.py` — call+argument-push comparison of the two disassemblies (fixed ranges inside).
- Build scripts: `build62_66.sh` (v45 set), `build67.sh` (probe2), `build68_69.sh` (v47 ctrl+probe3),
  `dt67.sh` / `dt68_69.sh` (difftest), `pack48.sh` / `pack48b.sh` / `pack48c.sh` (v48 assembly).
- `nofix_4b2720.txt` — one line, `004B2720`, for `--fixed-exclude`.
- `build71.sh` / `copy71.sh` / `dt71.sh` — the v50 diagnostic build, its packaging and difftest.
- `build72_73.sh` / `dt73.sh` / `pack51.sh` — the v51 fix: build72 = toggle+log, build73 = plain auto,
  difftest of both (11/11 each), packaging.
- `build_v52.sh` / `build_v52_log.sh` / `build_v52_plain.sh` / `difftest_v52*.sh` / `pack52.sh` — v52 debug
  menu build (build74) and its byte-identical plain rebuild (build75), difftests and packaging.
- `difftest_v53.sh` / `pack53.sh` / `sweep76.sh` — v53: full difftest of build76/77, packaging, and the
  corrected full autoverify sweep (24 shards → `/home/attt-dev/work/verify76`).
- `build78.sh` / `build79.sh` / `pack54.sh` — v54: build78 = toggle+log+menu with the cursor and two-stage
  spell changes, build79 = plain auto (sha256 = build76), packaging. `spelltest.js` (+ `node_modules`:
  `fengari`, `luaparse`) extracts the `kSpells` chunk from `debugmenu.cpp` and exercises it in a real Lua 5.1
  VM; `spellmap.py`, `spellact.py`, `spell_ids.sh`, `spell_school.sh`, `spellcfg.sh`, `cast_search.sh` and
  the other `spell*` / `lua*` scripts produced the working-spell list (`SpellAct` implementations + Portal).
- Cursor diagnosis (v54): `showcursor_ctx.sh`, `objdump_cursor*.sh`, `iat_cursor.sh`, `setcursor_ctx.sh`,
  `cursor_search.sh`, `mouse_search.sh`, `strings44f.sh` — located `ShowCursor(0)` at 0x44F7BB (inside
  0x44F2E0, `-nologo` only) and the saved-cursor `SetCursor(NULL)` pattern at 0x443C00 / 0x443E80.
- `nofix_proof*.sh` — proof that the old harness was vacuous: the wait test passes on build75 when
  `ctl_remove_cache` is removed. `probe_*.py/.sh`, `uc_bisect*.py`, `uc_inval*.py`, `uc_flush_*.py` — the
  Unicorn cache-invalidation experiments behind §5.1. `orig_50B9A0.dis` / `new77_50B9A0.dis` — the two
  disassemblies of the Wait fix.
- Diagnosis scripts for the root cause: `callers_4b2720.sh`, `caller_ctx.sh`, `reg_ctx.sh`, `anim_ctx.sh`,
  `reg2.sh`, `model_args.sh`, `check_ctor_asm.sh`, `check_ctor_asm2.sh`.
- `test50.ps1` / `test50b.ps1` / `check50.ps1` — stubbed end-to-end test of the v50 bisect script (search,
  resume, no-scene guard) and its parser check; `bisect_test\` is their sandbox.

## 11. Task board state

Done: toolchain, staging, baseline rebuild/relink/difftest, full Ghidra export, autoverify sweep, autodecomp
fixes, float-return fixes, damage preview (0x50E2D0), Alt+1..4 keys + intro skip, save-load crash fix,
packages v44 / v45 / v46 + v47 + v48 + v49 + v50 + v51, the level-up animation fix of #13 (confirmed
in-game 2026-11-02), the v52 debug menu (built + packaged), the v53 battle Wait fix (built + packaged;
confirmed in-game 2026-11-02), and v54's debug-menu cursor + two-stage spell learning (built + packaged).
Open: playtest the v54 menu (pushed with v53's confirmation; debug-build only); the corrected autoverify sweep
(verify76) must confirm or replace the old "0 differs" claim; shrink the exe (the original .data BSS tail is
written as zeros — see below); wider differential testing.
Session 2026-11-02 (see §15): 0x004F6B30 x87/NaN fix landed in build79 (verified on 4 seeds, relink 0
mismatches, difftest 12/12); the build79 sweep is 393/10266 rows and must be resumed; verify76's backlog is
10 faultdiff + 9 differs (one already fixed, two are prototype/return artifacts) + 263 "crashed" rows that
still need individual re-runs. Nothing was packaged or pushed for this fix yet.

### Exe size (measured 2026-11-02)

| file | size | .text | .rdata | .data raw | .data virtual |
|---|---|---|---|---|---|
| original attt.exe | 3,145,728 | 2,118,663 | 749,779 | 40,960 | 2,173,136 |
| v51 ATThrone.exe | 7,008,256 | 2,119,188 | 750,152 | 2,173,440 | 2,173,136 |
| v51 debug | 7,442,432 | 2,119,188 | 750,152 | 2,173,440 | 2,173,136 |

The 3.86 MB delta: +2.13 MB because `exe2obj.py` copies each section's *virtual* size as initialized COFF
data, so the original's 2.13 MB uninitialized `.data` tail is written as zeros (fixable: emit the tail as a
BSS section, exe would drop to ~4.9 MB); +1.65 MB `.ntext` = our 10,266 functions + 5-byte jmp stubs (~51 KB)
+ glue adapters; +39 KB `.reloc`, +28 KB `.nrdata`, +22 KB `.zidata`; original `.text`/`.rdata` stay because
the image layout (and thus every absolute address) is preserved, including the dead bodies of replaced
functions. The debug build adds ~300 KB more code (log calls), 123 KB `.ndata` (log buffers) and 90 KB relocs.

## 12. Definition of done for the open bug

Our 0x004B2720 compiled into a plain `--auto` build (no excludes, no logging), verify_relink 0 mismatches,
difftest 11/11 (those runs predate the harness fix of §5.1; the suite is now 12/12 on v53), user confirms the
animation in-game, then commit the cause + fix, push `decomp/continue`, and
ship the final package whose README says which exe to play. v51 meets the build/verify half:
`AttT_decomp_exe_v51\ATThrone.exe` (plain) + `ATThrone_debug.exe`, maps, toggle_list, `README_RU.txt`.

## 13. Debug menu (v52, `-D DECOMP_DEBUG_MENU`; extended in v54)

`src/engine/debugmenu.cpp` (hand engine source, `#ifdef DECOMP_DEBUG_MENU`, `#error` unless
`DECOMP_TEST_INPUT`). `main.cpp` calls `DecompDebugMenuInit()` after `g_engine->ApplyGamma()`; the main loop
treats `DecompDebugMenuPaused()` like an inactive app (`no Step`). `engine.cpp` registers `DecompDebugMenuLua`
as `DecompDbg` in `TestLua` and exposes `DecompQueueLua(chunk)` (fills `g_testLua` only if the previous chunk
has run), so every button action runs in the game's own Lua state at the end of a frame. New USER32 imports
(`LoadCursorA`, `SetWindowTextW`, `SendMessageW`, `RegisterHotKey`) are in `rebuild/imports_extra.txt`.

- Window: `AttTDecompDebugMenu`, `WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU`, `WS_EX_TOPMOST|WS_EX_TOOLWINDOW`,
  436×660 at game rect +24/+48 clamped to the screen; shown at start with `SW_SHOWNOACTIVATE`; Ctrl+Alt+D
  (`RegisterHotKey`, `MOD_CONTROL|MOD_ALT|MOD_NOREPEAT`) toggles it. Status = last 4 `DecompDbg` lines in a
  static + `decomp_debug.log`.
- Focus: both windows share the process, so no `WM_ACTIVATEAPP`; `WM_ACTIVATE` calls `PauseGame()`
  (`CEngine::SetActive(false)`, `ClipCursor(nullptr)`) and `ResumeGame()` (`SetActive(true)`, `CInput::Reset()`,
  `ClipCursor(game rect)`) — mirrors the game's own inactive-window handling. Buttons return the focus to the
  game window after queueing.
- Cursor (v54): the game hides the OS cursor two ways — `SetCursor(NULL)` from the saved-cursor RAII pattern at
  0x443C00 / 0x443E80 (runs every step, stores the old handle at +0x280) and `ShowCursor(0)` at 0x44F7BB
  (inside 0x44F2E0, only with `-nologo` + config byte +0x40 == 0), so the display count can sit at -1. The
  menu now loops `ShowCursor(TRUE)` on pause until the count is >= 0 (remembered in `g_cursorShows`), sets
  `g_arrow`, and unwinds the exact count with `ShowCursor(FALSE)` on resume, leaving the game's state as
  found. `WM_SETCURSOR` at `HTCLIENT` returns the arrow (both windows belong to the process, so the menu would
  otherwise inherit the game's NULL).
- Actions (all Lua chunks, `pcall`, errors go to the status):
  - `kSpells` (v54: two-stage): working set = the 24 spells implemented in `SpellAct` (union over the global
    table at run time, so mods are picked up) plus `spA07_Portal` (works, but opens `ChooseScene('Portal')`
    instead of going through `SpellAct`). If any working spells are missing from `Unit.Hero.BattleParams.Magic`,
    the click appends only those (`learned N (working only; click again for all)`); otherwise it appends every
    remaining string key of `Spell` (`learned N (ALL, unfinished too)`). The 15 unfinished spells (e.g.
    `spF02_FireWall`) have no `SpellAct` implementation and crash the game when cast — v52 learned them on the
    first click. Chunk validated with fengari (real Lua 5.1 VM), see §10.
  - `kGold`: `Hero.Inventory.Gold += 100000`.
  - `OpenBarracks(unit)`: `GUIScene.WorldLevel.scene:ChooseScene('Barrack', {[2]=unit,[3]=100,curCount=100,
    lastTime=Clock_GetHours()})` → 100 units = 10 troops × `HeroArmy.MaxQnUnitInTroop` (10).
  - `kTough`: `ArmyPos['DecompTough']`/`Army['DecompTough']` (1×uDragon, 250 units from `WorldHero:GetPos()`),
    `WorldArmy:new` + `a.ChangeParam={Health=100000}` (WorldArmy:BeginBattle *adds* it → 201+100000), then
    `Actions['Fight With Army'](Actions,'DecompTough',false,true)` (selfHero=false → normal troop battle;
    flag=true → no game00 autosave). The game's `RequestBeforeBattle` confirmation starts the fight; AttT has
    no speed setting, so "speed 1" is the normal 1x.
- Units list: 115 ids (`uValkyr1` … `uTest`, default selection `uDragon`).
- Static verification (no game launch): map symbols `_DecompDebugMenuLua/_DecompDebugMenuPaused/
  _DecompDebugMenuInit/_DecompQueueLua/?MenuProc?/?OpenBarracks?`, the four USER32 imports, embedded wide
  strings and Lua chunks; build74 verify_relink 0 mismatches, difftest 11/11 (vacuous, §5.1); build75 (plain)
  is byte-identical to v51 plain. Caveat: an exclusive-fullscreen swap chain may cover the topmost window —
  README says to use windowed/borderless if the menu is not visible.

## 14. Battle Wait acted like Skip (0x0050B9A0, fixed in v53, 2026-11-02)

**Report**: in battle the Wait button did not move the unit's turn to the end of the round; it behaved like
the Skip button. The user bisected it to 0x0050B9A0 (`bisect_exclude.txt` / `decomp_toggle.log` /
`bisect_shots\confirm_0050B9A0`).

**Original semantics** (disassembly in `.att_tmp/orig_50B9A0.dis`): after the victory/death checks, a
two-pass search over the `{troop, state}` array at `this+0x270` selects the next troop:
`cmp dword ptr [edi + 4], ebp` — pass 0 selects state 0 (has not acted), pass 1 selects state 1 (waited;
0x0050C280 sets it). If both passes find nothing, all states are reset, `++[this+0x1c4]` (new round),
SetNumTurn (0x613908) and the round listeners run, and the search restarts. The found entry gets state 2,
`[+0x27c]`, `_IsWaitMove` (0x613914) = (pass == 1), the current troop `[+0x64]`, the caption, the troop
script hook, then AI / wait / reach marking.

**Bug**: our hand function searched `state == 0` on *both* passes (`e->state == 0` was a literal
comparison). A troop that had waited (state 1) was never selected, so the second pass always fell through
to "start a new round" — visually a skipped turn. 0x0050C280 was already correct.

**Fix**: `f_0050B9A0.c` — `if (e->state == pass && sub_0051DAA0(e->troop) > 0)` and `_IsWaitMove` gets
`pass == 1`. Build75 (v52 plain) has `cmp dword ptr [edi + 4], 0`; build76/77 have
`cmp dword ptr [edi + 4], ebp` (verified in `.att_tmp/new77_50B9A0.dis`, `00AE9B9B`).

**Test**: `decomp/rebuild/tests/test_0050B9A0_wait.py` stubs the callees, builds a 2-troop battle fixture
and compares original vs rebuild for (current, waited) states (2,1), (0,1), (2,2), then runs the new code
and asserts the waited troop is selected with `_IsWaitMove=1` and the round is not advanced. It fails on
build75 with exactly the reported symptom (waited B not selected, A selected, round 2) and passes on
build76/77. It only detects this because of the harness fix in §5.1.

**Still true from the original**: a waited troop is only found on the second pass; if every remaining troop
has already waited, the round rolls over normally. Wait availability as a UI action is decided elsewhere
(0x0050C280), not here.

## 15. 0x004F6B30 (three-point frame builder) — x87 precision + NaN branch fix

**Status at session end (2026-11-02)**: fixed in build79
`sha256 a73b8d70b03223ba3296aaee855659324a3b4a9bdb5368b6b1c67c59dc52b75a`, relink 0 mismatches, difftest
12/12, 004F6B30 verified on 4 seeds (one documented NaN tail case). Not packaged, not pushed. The full
autoverify sweep of this build was started and stopped on request at 393/10266 rows.

### 15.1 What the original does (disassembly facts)

The rebuilt body lives at 0xA4C9xx..0xA4CFxx in `.ntext`, reached by the 5-byte jmp at 0x4F6B30.

* **Branch selection** — three `fcomip`+`jbe` at 0x4F6C67, 0x4F6C7F, 0x4F6E3E, all against the double 0.5 at
  0x00607CE0 (`GV_00607CE0_8`). `jbe` is *taken when unordered*, i.e. on NaN; a C `a <= b` is false on NaN,
  so the generated branch picked a different edge whenever the frame contained NaN (that was the old seed-1
  case-6 divergence: all components NaN, original took body1, ours another body, then a later store wrote
  through a garbage pointer -> `mem 00000005`). Structure: CMP-1 (0x4F6C67) is `if (A <= B)` -> inner CMP-3
  (0x4F6E3E) `if (C <= D)`, else CMP-2 (0x4F6C7F) `else if (E <= F)`. Bodies: fall-through 0x4F6C89 = body4,
  0x4F6D56 = body3, 0x4F6E48 = body2 (`param_1[9] - *param_1`), 0x4F6F1D = body1.
* **Cross products** — first cross (C's `fVar2`/`fStack_84`/`fVar5`) stored as floats to `[esp+0xb8/0xbc/0xc0]`
  (0x4F703C/0x4F7059/0x4F7068); second cross (`fVar6`/`fVar11`/`fVar3`) to `[esp+0x10/0x14/0x18]`
  (0x4F7089/0x4F70A3/0x4F70AF); the axis cross is computed from those float slots and stored to
  0x94/0x98/0x9c (float).
* **Dot** — 0x4F7148-0x4F7156: three `fmul`/`faddp` in extended precision, `fstps 0x1c` (rounds the *sum* to
  float), `flds`, `fstps 0x60`. The individual products are NOT rounded: the old C
  `fVar4 = fVar11 * fStack_84;` rounded one product and gave `acos(0.999999881) = 0.00048828125` where the
  original had `acos(1) = 0` (seed-1 case 4).
* **First length** — 0x4F7164-0x4F7178: sum of squares in extended from the cross components, `fstps 0x1c`
  (sum rounded to float), `flds`, `call 0x5E406A` (CIsqrt), then `fstps 0x1c; flds 0x1c` — the **sqrt result
  is rounded to float** — and `fstps 0x5c`.
* **Second length** — 0x4F7189-0x4F71AA: reloads the first-cross components as doubles (`fldl 0x20/0xa4/0x38`,
  the `fstl` spills), sums squares in extended, rounds sum to float, sqrt, rounds the result to float.
* **Final** — `fmuls 0x5c` (l1*l2, extended, **not** rounded to float), `fdivrs 0x60` (dot / l1*l2 in
  extended), `fstps 0x1c; flds`, `call 0x5E4238` (CIacos).

### 15.2 Current source state (`decomp/rebuild/src/fixed/f_004F6B30.c`)

```c
  if (!((local_dc[1] + fStack_c0) * GV_00607CE0_8 >
        (local_dc[4] + fStack_b4) * GV_00607CE0_8)) {
    if (!(fStack_60 > local_7c[1])) { ... } else { ... }
  }
  else if (!(fStack_54 > local_7c[4])) { ... } else { ... }
```
```c
  fVar9 = (float10)GH_FROUND(sub_005E406A((float10)GH_FROUND(
      (fVar3 * fVar3 + fVar6 * fVar6 + fVar11 * fVar11))));
  fVar10 = (float10)GH_FROUND(sub_005E406A((float10)GH_FROUND(
      (fVar5 * fVar5 + fStack_84 * fStack_84 + fVar2 * fVar2))));
  fDot = fVar5 * fVar3 + fVar2 * fVar6 + fVar11 * fStack_84;
  fVar9 = sub_005E4238((float10)GH_FROUND(
      (fDot / ((float)fVar10 * (float)fVar9))));
```

Rules for anyone editing this function again:
* keep `fDot` as one extended expression stored into `volatile float fDot` (no intermediate float variable);
* round the sqrt *results* to float, but do **not** wrap `((float)fVar10 * (float)fVar9)` in `GH_FROUND`
  (the original divides before the product is ever rounded);
* all three `fcomip` comparisons need the `!(a > b)` form or branch order changes on NaN.

### 15.3 Verification numbers (build79)

* build.py: `4604704 bytes and 86576 pointers checked, 0 mismatches`; 10266 replaced functions.
* difftest: `12 tests, 0 failed`.
* autoverify `--only 004F6B30`:
  * seed 1, n=64: verified, cov 1.00, 13 ok / 51 both faulted
  * seed 2, n=64: verified, cov 0.97, 9 ok / 55 both faulted
  * seed 8, n=64: verified, cov 0.97, 16 ok / 48 both faulted
  * seed 11, n=64: differs, cov 1.00, case 55 (see 15.4)
  * seeds 3-7, n=16: lowcov (0-2 ok, the rest fault in *both* runs) — no divergence seen, but weak evidence
* The random case sequence depends on `--n` (case 55 at n=64 is not case 55 at n=58), so always reproduce a
  reported case with the same `--n` and `--seed`.
* "both faulted" = the original and the rebuilt faulted identically; it counts as agreement.

### 15.4 Known residual (seed 11, case 55 — degenerate NaN input)

**Resolved by the current checkpoint:** clang moved a negation through division/addition. Preserving the
original `fchs / fdiv / fadd` order removes the discrepancy; see `decomp/VERIFICATION.md`. The following is
historical investigation evidence.

All cross components are NaN (`[esp+0x10]=0x14=0x18=0xbc=0xc0=0xFFFFFFFF`, `[0xb8]=0`). After the branch fix
both builds take the same path, but one heap byte still differs deterministically (3/3 runs):
`mem 203F6913: 7f10f03d20465645 / ff10f03d20465645` — the sign bit of a float ~1.9e38 stored in a heap
object. Not root-caused; the epilogue `/ -fVar11` (0x4F7225 area) or a NaN/±0 sign difference is the
suspicion. Gameplay data never feeds NaN here; treated as a documented tail risk.

Probe: `.att_tmp/av_probe_stack2.py` (hooks 0x4F7148 / 0x4F7164 / 0x4F7189 in the *original* run and prints
raw `(m,e)` of st0..st7 plus the float slots; case counter increments on each original entry, 0-based) and
`.att_tmp/probe4f6s11.sh`. Note `h._fpu_st(i)` decodes 80-bit registers to 53 bits, so equal-to-float values
prove a value was rounded to float.

### 15.5 Sweep state

* `.att_tmp/sweep79.sh` (24 shards, `--n 30 --shard k/24 --resume --fn-timeout 120`) writes
  `/home/attt-dev/work/verify79/av_*.tsv`; **393 of 10266 rows done**, all 24 shard files exist.
* Resume: `cd /mnt/e/Programs/Qoder_plays/AttT-Fix && setsid nohup bash .att_tmp/sweep79.sh >/dev/null 2>&1 </dev/null &`
  (`--resume` continues from the TSVs; `.cur` records the in-flight function). To stop: `pkill -9 -f sweep79.sh`
  **first**, then `pkill -9 -f autoverify.py` — otherwise the shard loop respawns the workers.
* Previous full sweep (build76), `/home/attt-dev/work/verify76`: 9734 rows = 3708 verified, 4797 lowcov,
  947 unsupported, 263 crashed, 10 faultdiff, 9 differs.
  * faultdiff (original faults, ours does not): 004E0E50, 004E0E90, 0047BF50, 004402A0, 0051DB90, 00440390,
    00553260, 00555E80, 004783C0, 00458380.
  * differs: 005B15B0, 0055B850, 00558520, 0048C980, 0048CC40 (heap mem), 0043F260 (st0 low bits),
    004FCCB0 (new faults at 0x9A3DC5), 004F6B30 (fixed in build79), 004CC8D0 (new fault at 0x2).
  * `crashed` rows have cov 0.00 = the process was killed (segfault/hang) and resume recorded it; they are
    **not** proven code differences and need an individual re-run.

### 15.6 Triage notes already established

* **Uncommitted hand fixes** — `git status` shows five untracked files in `decomp/rebuild/src/fixed/`:
  `f_0043F260.c`, `f_0048C980.c`, `f_0048CC40.c`, `f_004CC8D0.c`, `f_004F6B30.c`. They are compiled into
  build79 (build.py picks up `src/fixed/`) and each header explains the original semantics (float rounding of
  every atan2 step; `fcomi; ja` / `fcomip; jbe` guards treating NaN as equal / scan-left; the vtable tail
  call). So **6 of the 9 verify76 `differs` rows are probably already fixed by build79** and only need a
  re-run (`--only 0043F260,0048C980,0048CC40,004CC8D0` etc.). They are still uncommitted — commit them
  together with the next package.
* **004CC8D0** — already has a hand fix (writes the vtable tail call as a jmp; see the header comment in
  `f_004CC8D0.c`). The verify76 row predates it; re-check on build79.
* **004FCCB0** (`auto_038.c`) — the analysis prototype is wrong (`int param_1, float param_2, int *param_3`)
  while the real call is `(this, unsigned int *cell, float x, float z)`. The code survives because the float
  comes in through `BITCAST(float, (param_3))` and the pointer through `*(int *)param_1`. With verifier-random
  arguments the computed cell index `iVar6` becomes huge and the new code faults on `*pfVar5`; the original's
  index stays in range. Not a runtime bug; fixing the prototype in the analysis would silence it.
* **0043F260** — hand fix exists; the diff is `st0 -3.1385693550109863 / -3.1385693009360693`, i.e. a double
  vs rounded-float return. Check whether the `st0` return needs `GH_FROUND` (same class as the §5 return
  rounding rule).

### 15.7 Previous session's next steps (superseded by decomp/VERIFICATION.md)

1. Finish the verify79 sweep and diff its verdict lists against verify76's; every new `differs` needs a look.
2. Re-check the 263 `crashed` rows individually (`--only <addr> --n 8` into a separate TSV) to separate
   harness kills from real hangs.
3. Triage the 10 `faultdiff` (usually a load the compiler dropped — a real behaviour change, so look at each).
4. Package v55 (plain + debug) with `README_RU.txt` once the sweep is clean; v54's debug menu is still waiting
   for an in-game check (visible cursor, second spell click learns all 40).
5. Still open: task #21 — emit the original `.data` BSS tail as uninitialized (~2.1 MB smaller exe, see §11).
