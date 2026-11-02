# Current verification checkpoint — 2026-11-02

Active checkout: `/home/attt-dev/work/AttT-Fix`, branch `decomp/continue`.
Builds, generated sources, manifests and logs stay under `/home/attt-dev`.
Windows is for user-facing playtest packages; the agent does not launch the game.

## Binary identities

Build numbers were reused. Identify binaries by SHA-256, not by `build79` or compile timestamps.

| Binary | SHA-256 |
|---|---|
| Inherited plain baseline | `a73b8d70b03223ba3296aaee855659324a3b4a9bdb5368b6b1c67c59dc52b75a` |
| Current plain checkpoint | `ab4eff34c0d842d349a458832a25209cf3b0d4b6d239024e9f46d2c923d6e17d` |

Current binary: `/home/attt-dev/re/checkpoint-20261102/frame/ATThrone.exe`.
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
- Differential suite: **17 tests, zero failures**. New cases exercise valid virtual calls, bounded angular
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

Current full sweep: `/home/attt-dev/work/checkpoint-20261102/sweep`, started fresh against the current binary.
Its `manifest.json` pins binary, map, generated-source and tool hashes, Unicorn/Python versions and parameters.
Parameters: 30 cases, seed 1, FPCW `0x27f`, 5,000,000 instructions, 24 shards, 30-second function limit.
It is still in progress; no clean-sweep claim is made. Keep `lowcov`, `unsupported` and `crashed` as explicit
gaps. A 30-second kill is a runner result, not proof of a game hang. The game uses FPCW `0x7f`; focused angular
and frame tests exercise both precision settings, while the broad sweep retains `0x27f` for comparison.

The targeted inherited-baseline checks reconfirmed all ten faultdiff entries and remaining sorting, allocation,
float-sum and prototype-related differences. Random-pointer sort cases timed out, whereas bounded array tests
returned and matched. These results need classification, not blanket suppression of NaNs or fault differences.
Raw evidence: `/home/attt-dev/work/checkpoint-20261102`.

## Reproduce and resume

```sh
source /home/attt-dev/env.sh
cd /home/attt-dev/work/AttT-Fix
python3 -I decomp/tools/difftest.py \
  /home/attt-dev/work/attt/bin/attt.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.map

# Only resume a stopped run; a lock rejects concurrent writers.
python3 -I decomp/tools/verify_sweep.py \
  /home/attt-dev/work/attt/bin/attt.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.exe \
  /home/attt-dev/re/checkpoint-20261102/frame/ATThrone.map \
  /home/attt-dev/work/attty_test/auto_fix4 \
  /home/attt-dev/re/checkpoint-20261102/frame/work_attt \
  /home/attt-dev/work/checkpoint-20261102/sweep \
  --jobs 24 --shards 24 --n 30 --fn-timeout 30 --resume
```

The runner rejects changed inputs/settings on resume. Its initial-run, resume-without-duplicate-rows and
changed-seed rejection paths were exercised with two focused functions. A completed runner means all shards
finished, not that all functions were verified; inspect `summary.json` verdicts.

Next: finish the sweep, compare its discrepancy lists with verify76, triage remaining differences with valid
fixtures, then prepare plain/debug v55 for the user's playtest. The BSS-size reduction follows stabilization.
