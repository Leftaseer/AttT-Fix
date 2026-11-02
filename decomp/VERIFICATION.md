# Current verification checkpoint — 2026-11-02

Active checkout: `/home/attt-dev/work/AttT-Fix`, branch `decomp/continue`.
Builds, generated sources, manifests and logs stay under `/home/attt-dev`.
Windows is for user-facing playtest packages. The user explicitly authorized running anything within the
home directory; game tests now run from private WSL copies under `/home/attt-dev/work`.

## Initial WSL Wine game smoke tests

The original, v57 plain and v57 debug EXEs each survived a 35-second developer world start (`-nologo`) with
identical assets/settings under WineD3D at 800x600. No game error files appeared. Screenshots show the opening
world/dialogue scene; debug also displays its menu and logs initialization. Evidence, identities and the
retained incomplete debug attempt are in `/home/attt-dev/work/wine-tests/world-start-v57-20261102.json` and
[WINE_TESTING.md](WINE_TESTING.md). These are not normal-menu, save/load, combat or AttTFix activation tests.
The runner now defaults to normal startup and records explicit developer mode. All 35 tooling tests pass;
game binaries are unchanged.

## WSL Wine environment prepared

See [WINE_TESTING.md](WINE_TESTING.md). A private WineHQ 11.0 runtime/prefix with Xvfb, software graphics,
native D3DX9_29 and null audio is installed in WSL. A standalone synthetic PE32 probe passed VC80 loads,
D3D9 render/readback, native shader-effect compilation and DirectSound8 initialization. The tooling suite
now passes 35 tests, including six Wine-runner isolation/conversion/cleanup controls. No game code or v57
binary changed. At this setup checkpoint, automatic approval review rejected the original EXE launch.
After the user's explicit home-directory authorization, the approved smoke runs above supersede that pending
status. Probe evidence is `/home/attt-dev/work/wine-probes/probe-rui6xcff/`.

## Verification milestone — tools commit e7afd4a, unchanged v57 binaries

The user confirmed the v57 AttTFix activation and debug-barracks fixes in-game. The next work is verification;
no executable, shipped package, Steam file or mod configuration was changed for this milestone.
Transferred `/home/attt-dev/AttT-decomp` material was reviewed; see [ARTIFACTS_REVIEW.md](ARTIFACTS_REVIEW.md).

Verifier changes:

- Synthetic linked x86 programs provide a positive control and deliberately wrong return values, missing
  memory writes, callee-saved register corruption, incorrect stack cleanup and wrong float results. The real
  differential harness detects these defects. A boolean control permits unused upper return-register bits;
  the existing instruction-cache negative control is retained.
- `autoverify --only` must select active generated replacements from this exact build. Native reservations
  are rejected instead of allowing an original/original comparison. Every selected entry must have its
  replacement jump. An actual `--only 0044A9C0` run is rejected before writing a verdict file.
- NaN/Infinity bit filtering is now conditional on explicit `AV_NONAN` triage mode. Previously the random
  object path called the filter unconditionally. Typed float generation includes nonfinite and boundary
  values. Sweep manifests now pin `AV_NONAN`; resuming with a changed float policy was tested and rejected.
- Coverage used for a `verified` verdict now comes only from original calls that return normally. All-call
  coverage remains diagnostic `coverage_all`. A synthetic branching fixture proves fault-only blocks cannot
  increase the normal-return coverage used by the verdict.
- The sweep supervisor records termination metadata. A wall-clock limit is `timeout`, SIGSEGV/SIGABRT of
  the worker is `emulator_crash`, and an unexplained prior stop is `interrupted`. They are not conflated with
  emulated game faults or normal successful calls.
- `difftest.py ... --report FILE.json` records per-function comparisons/normal returns/faults, test names and
  input/test hashes. It explicitly identifies the comparison scope: only the entry is restored; callees are
  shared. `verification_inventory.py ORIGINAL REBUILT MAP AUTO WORK OUTPUT --report FILE.json` validates
  the input identities before attaching evidence. A report for a different binary was tested and rejected.

Both v57 binaries now pass **32 differential tests** (599 normal-return comparison pairs across 32 function
addresses). **29 tooling tests** pass. The added direction-delta contract tests axis changes, crossing -pi/pi,
large finite vectors and signed zero at x87 control words `0x27F` and `0x7F`, with an independent shortest-turn
range/expected-angle check. All 20 addresses in the focused cohort have normal-return contract fixtures.
Several dependencies in these fixtures are mocked; this is not an end-to-end equivalence claim.

The exact-build inventory finds **10,167 active replacements**, of which **9,661 addresses** are associated
with generated sources and eligible for autoverify, including hand overrides. Direct fixtures exercise 32
addresses, 20 of them in that generated-source group; 9,641 eligible addresses have no direct fixture yet.
These are evidence counts, not branch coverage or a count of all functions verified by other methods.

A fresh hash-pinned 20-function run on v57 plain completed with `--n 30 --seed 1 --fpcw 0x27F`, a 20-second
function limit and default nonfinite input policy: **7 verified, 8 faultdiff, 3 timeout, 1 lowcov, 1 differs**.
It is a focused run, not a new full sweep:

- Verified: `0043F260`, `004402A0`, `00440390`, `004CC8D0`, `004F6B30`, `00558520`, `005B15B0`.
- Timeout: `00458380`, `0048C980`, `0048CC40`; their bounded normal-state fixtures pass. A separate three-address
  interruption audit also confirmed wall-clock timeouts rather than worker crashes.
- `004FCCB0`: zero normal fuzz returns, normal-return coverage 0.00 versus all-call coverage 1.00. It remains
  lowcov; its 16 bounded normal comparison pairs pass. This illustrates why fault-only coverage is insufficient.
- The eight raw fault differences and the allocation mismatch at `0055B850` remain visible. Normal-state
  contracts pass; this run does not close or reclassify those raw discrepancies as universally safe.

Evidence: `/home/attt-dev/work/verification-v57-20261102/`: exact-build inventory, plain/debug differential
reports, tooling logs, `targeted20-final/` manifest/results, interruption audit, rejection controls, a tool-source
snapshot and `checkpoint.json`. Earlier runs in this directory are retained with their own tool identities;
the final cohort above is the authoritative 20-row result. No historical full-sweep totals were updated.

Next: expand valid world/combat/object-lifetime fixtures and compare complete call chains against an unmodified
original image. The WSL Wine runtime/prefix has since been installed and probed; game integration using the
transferred assets/saves remains pending as described above.

## v57 AttTFix compatibility / barracks candidate — source commit c9d773e

Package: `/mnt/e/Programs/Qoder_plays/AttT-Fix/AttT_decomp_exe_v57/`.
Staging: `/home/attt-dev/work/playtest-packages/AttT_decomp_exe_v57/`.
All seven files were delivered and checked by SHA-256 against staging; earlier packages are preserved.
Both binaries use the new `--attfix-compat` build preset: **10,167 replacements**, with 10,100 switchable
functions in debug. This supersedes v56's compatibility assessment and barracks implementation. The user's
v56 logs show AttTFix 2.1.2 loaded successfully but rejected Frame, DoFile and most optimization hooks;
the barracks success message accompanied an ordinary army screen. Preserved addresses/timestamp alone
were insufficient evidence of functional mod compatibility.

The preset reserves 110 complete native functions referenced by the supplied mod DLL and local mod source,
including interior patch sites. Of those, 99 were replaced in v56. The profile records individual references,
source hashes and DLL SHA-256 `202caa2282681878e84022dab6d72f3d72fea619981f3a68c592392ab29b5a79` in
`decomp/rebuild/attfix_compat.json`. Lua's API remains replaced as a complete library. Default builds without
the preset retain the original replacement set. Generation/audit commands:

```sh
python3 -I decomp/tools/attfix_compat.py generate ORIGINAL_EXE MOD_DLL PROFILE_JSON --source-dir src
python3 -I decomp/tools/attfix_compat.py check ORIGINAL_EXE REBUILT_EXE decomp/rebuild/attfix_compat.json
```

Native function-import operands also retain their original addresses. **540 old function IAT slots** tail-jump
through the canonical new IAT, so the DLL's byte guards match and direct reads such as its qsort slot remain
callable. Later canonical IAT hooks affect these native callers too. Data imports are still relocated normally.
`verify_relink.py --keep-function-iat` verifies every forwarder's import identity before allowing that slot to
differ. This does not disable the DLL's byte checks. A linked synthetic-PE regression proves that an unchanged
native import call reaches two successive replacements installed in its canonical IAT.

Native Frame/Render remain available to the mod. The debug main loop detects a Step that advances frameCount
and calls `DecompTestFrameEnd` afterward, preserving frame-end Lua execution even when Frame is owned by the
DLL. Emulation verifies that rebuilt Step reaches the native Frame entry, and that the queue executes once
through native CLua::RunBuffer. Compatibility builds do not use the replaced Frame/Render's synthetic key
injection or automatic screenshot hooks; manual debug actions and Alt debug keys remain available.

Barracks now supplies the Barrack template and selected-unit Load arguments during the native child creation
call, restoring the army template and original Load function immediately afterward, including on failure.
The v56 approach queued ChooseScene before activation; native GUI activation `00583D20` clears that pending
scene name. The action fixture now models template loading/activation and verifies the actual chosen template,
stock and restored normal army screen, rather than only accepting a mocked ChooseScene call.

| Binary | Bytes | SHA-256 |
|---|---:|---|
| `ATThrone.exe` | 4,828,672 | `d06a3d610fa8fae842962bd45d5f885097d75ce82e9658ed21365d8896a5b18d` |
| `ATThrone_debug.exe` | 5,270,528 | `755576eed4c71b99315c29fbfb1967bd3004dbe0aa7bd27ce30140ff8911e78c` |

Both pass **31 differential tests**, relink with **zero mismatches** (4,603,348 bytes / 86,595 pointers),
and the profile audit: **110 reserved functions / 51,968 native bytes exactly match the original**. Ten tooling
tests pass. Debug action checks cover 115 unit selections, restored army definitions, Speed 1 / +100000 Health,
repeat battles, no-save arguments, menu recall/Close and native-frame queue integration. Scene objects and
Win32 remain mocked. Timestamp `0x475EABAF` and image base `0x400000` are unchanged.

**End-to-end mod behavior and real barracks rendering remain user playtest steps.** This is a candidate tied
to the recorded DLL hash, not a blanket compatibility claim for future mod versions. No full sweep was rerun;
earlier unsupported/low-coverage/interrupted cases and classified fault differences remain unclosed.
The agent has not launched the game or changed its Steam installation or mod configuration.

Evidence: `/home/attt-dev/re/v57-20261102/{plain,debug}/` and `/home/attt-dev/work/debugmenu-v57/`
(action/tooling/audit logs, supplied feedback logs, expected v56 audit failure, source/payload manifest).

## v56 debug-menu playtest package — source commit cbab162

Package: `/mnt/e/Programs/Qoder_plays/AttT-Fix/AttT_decomp_exe_v56/`.
WSL staging: `/home/attt-dev/work/playtest-packages/AttT_decomp_exe_v56/`.
All seven files were delivered and checked by SHA-256 against staging; older packages are preserved.
The plain executable and its map are copied byte-for-byte from v55. Only the debug build changes:

- Barracks opens through `WorldLevel.scene:OnArmyIcon()` and the resulting
  `GUIScene.ArmyScreen.scene:ChooseScene('Barrack', info)`. The native world object has no `ChooseScene`
  method, matching the supplied log's repeated error. Native `0053E040` creates the GUI container and
  loads ArmyScreen synchronously; `00583D70` then schedules the barracks in that container. Stock is 100.
- `WorldArmy:BeginBattle` adds each `ChangeParam` field to cloned unit stats. The test dragon now receives
  `Speed = 1 - Unit.uDragon.BattleParams.Speed` alongside `Health = 100000`, producing unit Speed 1.
  No global unit definition changes. Status reports the dynamic HP total; the stale 100201 label is removed.
- Ctrl+Alt+D always shows and focuses the menu, including after an action returns focus to the game.
  Close and the title-bar X hide it. Frame-end action execution and activation-based pausing are retained.

| Binary | Bytes | SHA-256 |
|---|---:|---|
| `ATThrone.exe` (unchanged v55) | 4,875,264 | `33eaf4e22b3c55b33a9cde12c429c9542c32715a160288378282dd342d344630` |
| `ATThrone_debug.exe` | 5,319,680 | `a7ba61ef0dd305e580d7b783c4f32c35ec13cf8b9338752290819c75bab87a81` |

The updated debug build passes **31 differential tests**; **nine tooling tests** pass. Relink checks
4,604,704 bytes / 86,576 pointers with zero mismatches. Both payloads preserve PE timestamp `0x475EABAF`
and image base `0x400000`. Replacement/toggle counts remain 10,266 / 10,194.
`decomp/tools/check_debugmenu.py ORIGINAL_EXE DEBUG_EXE DEBUG_MAP` executes the compiled menu handlers and
the rebuilt float Lua 5.1.2 VM in Unicorn. It checks all 115 unit selections, stock/scene arguments, dragon
stats at base speeds 6/1/9, repeated-battle cleanup, unchanged base stats, no-save fight arguments, repeated
hotkey activation and both close controls. Scene/world objects and Win32 calls are mocked: this does not
verify real scene rendering, desktop focus or cursor behavior. Those require the user's next playtest.
No full sweep was rerun; the retained limits in v55 below still apply. The plain binary inherits its v55 checks.

Build and differential log: `/home/attt-dev/re/v56-20261102/debug/`.
Action/tooling logs, supplied playtest log and source manifest: `/home/attt-dev/work/debugmenu-v56/`.
The package contains English playtest steps, matching maps, toggle list and payload hashes.

## v55 playtest package — source commit 37b6280

Delivered to `/mnt/e/Programs/Qoder_plays/AttT-Fix/AttT_decomp_exe_v55/`.
WSL staging copy: `/home/attt-dev/work/playtest-packages/AttT_decomp_exe_v55/`.
All seven delivered files were checked by SHA-256 against the WSL copies. Existing packages and the Steam
installation were preserved. `README_EN.txt` explains installation, checks and limitations; `manifest.json`
records the source revision and every delivered payload hash. No game was launched by the agent.

| Binary | Bytes | SHA-256 |
|---|---:|---|
| `ATThrone.exe` | 4,875,264 | `33eaf4e22b3c55b33a9cde12c429c9542c32715a160288378282dd342d344630` |
| `ATThrone_debug.exe` | 5,319,680 | `fe88c4ff9460b42ed96478e65e01dacd8abd4ebddb362fea782493b08ba6f184` |

Both pass **31 differential tests**, keep 10,266 replacements, and pass relink verification (4,604,704 bytes,
86,576 pointers, zero mismatches). All **nine tooling tests** pass. The debug build has toggle/log/test-input
and debug-menu support; its 10,194-entry toggle list is included. Maps match the delivered binaries.
Builds remain in `/home/attt-dev/re/v55-20261102/{plain,debug}/`.

The eleven historical fault differences were triaged after the four-function work below. Three more
translation defects were fixed, with failing-before/passing-after fixtures:

- `004402A0`, `00440390`: the original stores/reloads coordinate differences, radius sums, squared distance
  and squared radius as floats. The translation omitted the final stores. With finite inputs `x=1e30`,
  `radius=1e29`, the original compares two infinities and continues; the translation compared wide finite
  squares and rejected the object. Explicit float stores restore the original boundary behavior. The original
  ordered comparison itself already handles NaNs correctly; this was not a comparison-negation bug.
- `00458380`: restore the original y/x/z/w sum order and the `fcomip; ja` condition. A NaN dot product is not
  an ordered positive plane hit; it must stay in the vertex scan. Bounded frustum tests cover inside/outside,
  mixed vertices, empty buffers and NaNs.

All three now verify on their original seed-1, 30-case fuzz inputs: circle 12 normal / 18 matching faults,
shape 11 / 19, frustum 7 / 23. The three earlier fixes, allocator control, and generator primitive are below.

### v55 recheck of the 15 previously flagged addresses

A hash-pinned targeted run on the final plain binary completed all 15 addresses (`--n 30 --seed 1`, FPCW
`0x27f`, 45-second function limit): **5 verified, 1 lowcov, 1 differs, 8 faultdiff**.
Verified: `004402A0`, `00440390`, `00458380`, `00558520`, `005B15B0`.
Grid lookup `004FCCB0` remains lowcov (1 normal / 29 matching faults); its bounded conversion fixtures pass.
`0055B850` retains the diagnosed allocator-padding discrepancy in the raw harness.

The eight retained fault differences have normal-input contract fixtures. They were not suppressed or claimed
bit-equivalent on invalid inputs:

| Addresses | Retained difference | Normal-input evidence |
|---|---|---|
| `00477E00`, `004783C0` | Fuzz calls an invalid synthetic device/vtable target | Both constructors match with valid mock devices, first acquisition and shared-declaration reuse |
| `004E0E50`, `004E0E90` | Original unsigned division by a zero-sized selection range traps; C modulo-zero is undefined | Nonempty ranges of 1, 2, 8 entries return matching members |
| `00555E80` | Original integer reciprocal traps when its computed denominator is zero; C division-zero is undefined | Defined integer powers and nonzero reciprocal denominators match |
| `0047BF50` | Original pointer-chain preload occurs before the count guard; the compiler can sink/elide it | Valid headers for counts 0, 1, 2 match, including getter/setter virtual paths |
| `0051DB90` | Original loads each unit before calling a bare-ret helper; the generated prototype loses that load | Valid unit arrays match with the current no-op helper; per-unit ECX/prototype reconstruction remains technical debt before changing that helper |
| `00553260` | Original empty loop exceeds the emulator instruction limit on an oversized synthetic range; C removes it | Bounded 0/3/16-element ranges match coordinate writes; unrelated update/logging is stubbed |

These fixtures support playtesting; they do not prove all invalid states safe. No full 9,734-address sweep has
been run on v55, and low coverage, unsupported imports and interrupted runs in the earlier sweep remain gaps.
The old aggregate counts remain historical and are not recomputed by mixing targeted results into them.
The next required validation is the user's in-game playtest: existing saves, movement/forests/effects,
battle Wait, level-up animation, save/load, and the debug-menu cursor/spell workflow.

Evidence: `/home/attt-dev/work/fault-triage-20261102/` (disassemblies, geometry before/after tests, normal-input
contracts, final plain/debug logs, targeted manifest/results, `v55-source-manifest.json`).

## Earlier math triage checkpoint — source commit 22e4a17

The four `differs` from the recovered sweep have now been investigated. Three translation defects have hand
overrides and failing-before/passing-after regression fixtures. The fourth is an allocator-padding artifact
with a controlled reproduction; it remains visible in the unmodified fuzz harness.

| Function | Change/evidence | Targeted seed-1 result |
|---|---|---|
| `00558520` | Restore rounded coordinate differences and `(dx² + dy²) + dz²` order | verified, 5 normal / 25 matching faults |
| `005B15B0` | Preserve the two `fcomi; ja` unordered/equal partition paths with `!(a > b)` | verified, 28 normal / 2 matching faults |
| `004FCCB0` | Use signed 32-bit `_ftol2_sse` conversion before unsigned storage; preserve float stores | lowcov, 1 normal / 29 matching faults |
| `0055B850` | Trace uninitialized empty-allocator byte during lazy filesystem creation | raw differs; initialized-byte control verifies 30/30 |

Distance and partition functions also verify on seeds 2 and 8 (`--n 30`, FPCW `0x27f`), and seed 1 with the game's
FPCW `0x7f`. Grid lookup remains lowcov on those runs, with 1–2 normal returns and matching faults otherwise.
Bounded grid fixtures return normally at both precisions for normal coordinates and explicit overflow/NaN
conversion cases. These are targeted checks; **the 9,734-row sweep below has not been rerun on this binary**.

The distance regression uses finite coordinates `(1, 1, 4096)` at single precision: the original key is
`0x4B800001`, while the reordered translation produced `0x4B800000`. It also checks actor-radius selection,
callback/count changes, and empty/small/large buffers (0, 1, 4, 17 entries) at both precisions. The partition test
compares returned bounds and payload moves on bounded finite, tied and NaN arrays. All three new defect
fixtures fail on the previous candidate and pass after the fixes.

The grid function's actual stack ABI is `(out_cell, float x, float z)` plus `this` in ECX. Its typed declaration
now reflects that ABI, keeping the same three stack dwords. `GH_FTOL32` models the CRT's SSE2-enabled branch:
store double, then signed `cvttsd2si`, including integer-indefinite `0x80000000` on overflow or NaN. Recognized
32-bit helper calls emitted by `autodecomp.py` now use this primitive; 64-bit helpers retain their width.
Two tooling tests compile generated macros to x86 and emulate ordinary/negative/out-of-range/NaN values and
a 64-bit conversion. The existing generated directory was not regenerated. Inlined Ghidra casts still require
machine-code review; the generator does not blindly rewrite casts.

For `0055B850`, the write trace identifies the same nested `00451430` allocator-copy instruction in both runs.
`CFileSystem` construction (`00451E00`) passes an uninitialized local byte: the original/rebuilt loader stack
layouts yield `08` and `E8`, copied to heap address `2035FEB0`. A separate diagnostic initializes only that
allocator input byte before the two container constructors (`00451430`, `00489710`); the original seed-1
30-case comparison then verifies (coverage 0.58, 30 normal returns). **No byte masking or suppression was added
to the production verifier.** A bounded forest-loader fixture with an already initialized filesystem also
matches, covering 0/2 file entries and both file-state branches using emulated file-access stubs.

Current plain: `/home/attt-dev/re/triage-20261102/final-plain/ATThrone.exe`, 4,875,264 bytes,
SHA-256 `16f94ba0007d41e91e322a98eb67a0e38ad239fe54e9b2d600c07d66b1a9219c`.
Current debug: `/home/attt-dev/re/triage-20261102/final-debug/ATThrone_debug.exe`, 5,319,680 bytes,
SHA-256 `4fde90f16b53c974c83b28d1c06caae9839f55bd596c858ea1436d5c2547aced`.
Both pass relink verification (4,604,704 bytes / 86,576 pointers, zero mismatches), keep 10,266 replacements,
and pass **22 differential tests each**. All **nine tooling tests** pass.

Raw evidence and commands: `/home/attt-dev/work/triage-20261102/` (before/after logs, targeted run manifests,
`allocator-final-raw/zero` logs/TSVs, `source-manifest.json`). Builds and scratch remain in WSL.
Next: triage the eleven historical fault differences and remaining coverage gaps, then prepare v55 playtests.
The old aggregate verdict counts below describe the older sweep binary and must not be silently updated with
these targeted results or the diagnostic allocator control.

## Earlier binary identities and recovered sweep

Build numbers were reused. Identify binaries by SHA-256, not by `build79` or compile timestamps.

| Binary | SHA-256 |
|---|---|
| Inherited plain baseline | `a73b8d70b03223ba3296aaee855659324a3b4a9bdb5368b6b1c67c59dc52b75a` |
| Corrected plain binary used by the full sweep | `ab4eff34c0d842d349a458832a25209cf3b0d4b6d239024e9f46d2c923d6e17d` |
| Smaller plain candidate (BSS split) | `70abad38d0db5f0b644b0a035e89325ef7c93ae3c944a93b8dcc55043c58b288` |
| Smaller debug candidate (BSS split) | `0ef29b8f548f7e65d49d3c42c5a9351b2845095b9156899907278d78ae015ed0` |

Full-sweep binary: `/home/attt-dev/re/checkpoint-20261102/frame/ATThrone.exe`.
Original input: `/home/attt-dev/work/attt/bin/attt.exe`.
Generated sources: `/home/attt-dev/work/attty_test/auto_fix4` (not committed).
Build: plain `--auto`, no exclusions or debug defines. Replacements remain **10,266 of 18,591 functions**.
Autoverify selects **9,734 generated-function addresses**, including their hand overrides; it does not test all
10,266 replacements. The manual suite covers selected engine and Lua behavior, not every remaining function.

## Confirmed changes and checks

- Preserved the five pending hand fixes for `0043F260`, `0048C980`, `0048CC40`, `004CC8D0`, `004F6B30`.
- Found a real ABI bug in the inherited `004CC8D0` fix: its inline assembly jumped without placing `this` in
  ECX. A bounded object with a valid thiscall target failed on the inherited binary. The corrected naked
  boundary sets ECX, keeps the virtual target in EDX, reuses the argument slot and tail-jumps; the test passes.
- Root-caused the residual `004F6B30` seed-11 discrepancy: clang changed `numerator / -normal + offset` into
  `offset - numerator / normal`. The original uses `fchs`, division, then addition. A volatile float denominator
  preserves that order and removes the NaN sign difference. Reproduction: `--only 004F6B30 --seed 11 --n 64
  --fpcw 0x27f`; before: differs at case 55; after: verified, coverage 1.00, 7 normal returns / 57 both faulted.
- Relink: **4,604,704 bytes and 86,576 pointers checked, zero mismatches**.
- Differential suite: **18 tests, zero failures**. New cases exercise valid virtual calls, bounded angular
  sorting with ties and NaNs, finite/NaN terrain frames, and the verifier's instruction-cache invalidation.
- Negative control: disabling cache invalidation makes the new verifier regression return `(1, 1)` rather
  than `(1, 2)`, so the test detects the old original-versus-original failure.

The old plain baseline was rebuilt in WSL and reproduced byte-for-byte before these changes.
The v54 debug-menu changes still need the user's in-game check. No new package has been delivered yet.

## Corrected sweeps and their limits

All difftest/autoverify passing claims made before the 2026-11-02 cache fix are invalid. The historical
`rebuild/autoverify_findings.tsv` retains useful diagnosis notes, but its old passing statuses are not evidence.

Saved verify76: 9,734 rows: 3,708 verified, 4,797 lowcov, 947 unsupported, 263 crashed, 10 faultdiff, 9 differs.
Saved verify79: 393 rows; it is incomplete and refers to the inherited binary, not the current checkpoint.

All 263 verify76 crashed entries were rerun separately against the inherited plain baseline with seed 1,
8 cases, 300,000 instructions per call and a 30-second function limit. Every process completed:
**31 verified, 232 lowcov, no differs/faultdiff**. Different case counts change generated inputs; this is triage,
not a replacement for the original 30-case sweep and not verification of those functions on all valid inputs.

Initial sweep: `/home/attt-dev/work/checkpoint-20261102/sweep`, started fresh against the current binary.
Its `manifest.json` pins binary, map, generated-source and tool hashes, Unicorn/Python versions and parameters.
Parameters: 30 cases, seed 1, FPCW `0x27f`, 5,000,000 instructions, 24 shards, 30-second function limit.
The initial runner stopped incomplete at 9,070/9,734 rows: shards 3, 10 and 17 exited on a Python
`OverflowError` in the x87-to-binary64 decoder (`004658E0`, `004C1100`, `00549B00`). Finite x87 values can exceed
the binary64 exponent range. The decoder now returns signed infinity on narrowing overflow; ordinary finite,
zero, NaN and infinity handling is unchanged. Four new tooling tests cover overflow, representable limits and special values, and pass with the
fix (seven tooling tests total, including the three linker tests). Fix commit: `ab36293`.

### Recovered results

All **9,734 unique expected addresses** now have a result. The initial 9,070 rows are preserved unchanged.
Only the 664 missing addresses were processed in `sweep-completion/`, with the same binary, generated inputs,
seed, case count and limits, under a separate manifest pinning the corrected decoder. All 24 completion shards
exited successfully. This is an aggregate of two recorded tool versions, not a fresh uniform sweep of all
addresses with the new decoder. Completed earlier calls never reached the decoder exception.

| Verdict | Functions |
|---|---:|
| verified | 3,557 |
| lowcov | 4,478 |
| unsupported | 969 |
| crashed (interrupted verifier run) | 715 |
| differs | 4 |
| faultdiff | 11 |
| Total processed | 9,734 |

`verified` meets the verifier's sampled coverage and normal-return thresholds; it is not a proof for all inputs.
Keep `lowcov`, `unsupported` and `crashed` as gaps. The 30-second function limit differs from verify76's
120-second limit, so interruption counts are not directly comparable or evidence of 715 gameplay crashes.
The game uses FPCW `0x7f`; focused angular and frame tests exercise both precision settings, while the broad
sweep retains `0x27f` for comparison.

The comparison with verify76 is:

- Former `differs` at `0043F260`, `004CC8D0`, `004F6B30` are now `verified`.
- `0048C980` and `0048CC40` changed from `differs` to interrupted runs. Their bounded-array tests pass, but
  the random-input cases are unresolved gaps and must not be counted as verified fixes.
- Four `differs` remain: `004FCCB0`, `00558520`, `0055B850`, `005B15B0`.
- All ten former `faultdiff` entries remain, plus a newly observed `00477E00` fault difference. Its fuzz case
  reaches an invalid graphics-device target (`01030002`). A bounded constructor test using a valid synthetic
  device covers both first acquisition and shared-declaration reuse, matches the original and returns normally.
  The fuzz discrepancy is retained; this does not establish or rule out a gameplay defect.

The three formerly decoder-blocked entries now have explicit outcomes: `004658E0` interrupted, `004C1100`
unsupported (MSVCP80 string `swap`), `00549B00` lowcov. None stopped the completion shards.
Aggregate evidence: `/home/attt-dev/work/checkpoint-20261102/sweep-recovered/summary.json` and `all.tsv`.
`combine_sweep.py` validates cohort input identities, tool differences, disjoint address sets, expected address
coverage and binary hashes before producing the report. Both source manifests and raw logs remain intact.

The targeted inherited-baseline checks reconfirmed all ten faultdiff entries and remaining sorting, allocation,
float-sum and prototype-related differences. Random-pointer sort cases timed out, whereas bounded array tests
returned and matched. These results need classification, not blanket suppression of NaNs or fault differences.
Raw evidence: `/home/attt-dev/work/checkpoint-20261102`. The narrower historical checks above are separate from
the recovered results and must not be added to their counts.

## Reproduce and resume

```sh
source /home/attt-dev/env.sh
cd /home/attt-dev/work/AttT-Fix
python3 -I decomp/tools/difftest.py \
  /home/attt-dev/work/attt/bin/attt.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.map

# The original sweep manifest pins the old decoder and intentionally rejects
# resuming with the changed harness. Recheck/resume only the completion cohort:
python3 - <<'PY'
import json
import subprocess
with open('/home/attt-dev/work/checkpoint-20261102/completion-command.json') as f:
    command = json.load(f)
subprocess.run(command + ['--resume'], check=True)
PY
```

The runner rejects changed inputs/settings on resume. Its initial-run, resume-without-duplicate-rows and
changed-seed rejection paths were exercised with two focused functions. A completed runner means all shards
finished, not that all functions were verified; inspect `summary.json` verdicts.

## BSS size reduction (separate candidates)

`exe2obj.py` now splits the original `.data` at its PE `SizeOfRawData` boundary and emits the virtual tail as
uninitialized COFF `.bss`, merged back into `.data` by the existing linker option. Symbols and relocations into
the tail use that section. Its alignment is one byte to avoid adding a gap after non-page-aligned prefixes.
The writer rejects nonzero bytes or relocations in an uninitialized section rather than silently dropping them.

Plain candidate: `/home/attt-dev/re/checkpoint-20261102/bss/ATThrone.exe`.
Size: **7,007,744 -> 4,875,264 bytes** (2,132,480 bytes removed, approximately 30%).
`.data` raw size: 2,173,440 -> 40,960 bytes; virtual size stays 2,173,136 bytes.
All 18 differential tests pass, and relink verification reports zero mismatches.

The synthetic linker test uses a 0x600-byte initialized prefix, an uninitialized tail and a relocation targeting
a symbol deep in that tail. It checks address continuity, loader-visible zero fill and the reduced raw size.
Two guard tests reject nonzero tail data and tail relocations. All three pass:

```sh
python3 -I -m unittest discover -s decomp/tools/tests -v
```

Compared with the full-sweep binary, section virtual addresses, sizes, memory permissions, entry point, timestamp
and import/directory layout are unchanged. Mapped section bytes match except for 16 bytes within unused partial
instructions immediately following replacement jumps (entry+5 through entry+8, already ignored by relink
verification). All new-code/data sections match byte-for-byte. Evidence: `bss-equivalence.json` in the checkpoint
directory. This is a structural comparison, not a new full autoverify sweep of the smaller binary.

Debug candidate: `/home/attt-dev/re/checkpoint-20261102/debug-bss/ATThrone_debug.exe`, 5,319,680 bytes.
Flags: `--toggle -D DECOMP_TEST_INPUT -D DECOMP_DEBUG_LOG -D DECOMP_DEBUG_MENU`.
Relink verification and all **18 differential tests** pass on the debug candidate as well. Neither candidate
has been played or delivered. The broad sweep keeps its original binary and manifest unchanged.

This earlier checkpoint waited for triage of the four differences and eleven fault differences. See the
latest section above for the completed four-function triage and current candidates. The smaller candidates are prepared locally.
Delivery waits for verification triage; in-game validation will then be the user's step.
