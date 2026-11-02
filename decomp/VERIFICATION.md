# Current verification checkpoint — 2026-11-02

Active checkout: `/home/attt-dev/work/AttT-Fix`, branch `decomp/continue`.
Builds, generated sources, manifests and logs stay under `/home/attt-dev`.
Windows is for user-facing playtest packages; the agent does not launch the game.

## Latest triage checkpoint — source commit 22e4a17

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
