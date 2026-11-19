# C translation status — ATThrone 1.11.128 (v0.3, 2026-11-19)

This report states how much of the AttT engine has been translated into compilable C, how that is
verified, and what remains. Method and tooling are described in [README.md](README.md); historical
verification records are in [VERIFICATION.md](VERIFICATION.md).

## 1. Snapshot

| Item | Value |
|---|---|
| Binary | ATThrone 1.11.128, TimeDateStamp `0x475EABAF` (MSVC 2005, `/O2 /LTCG`) |
| Branch / tag | `decomp/continue` / `v0.3` |
| Rebuilt executable | **4,603,228 bytes and 86,513 pointers checked, 0 mismatches** |
| Replaced functions | **10,460** (11,766 original symbols used) |
| Differential suite | **1,020 tests, 0 failed** |
| Hand-written fixed sources | **967** files in `rebuild/src/fixed/f_*.c` |

The only intentional build skip is `0042EEF0` (*registers the prototype does not take*).

## 2. Method, in one paragraph

Both executables carry complete relocation tables, so the original is converted to a relocatable
object (`tools/exe2obj.py`) and linked again together with new code; the original `.text`, `.rdata`
and `.data` keep their addresses, and new code lands in appended sections (`.ntext`, `.nrdata`,
`build.py`). Each replaced function keeps its first five bytes rewritten to `E9 ->` a compiled body;
the build then verifies every untouched byte and all 86,513 pointers (hence "0 mismatches"). Every
hand translation is additionally validated against the original function in a Unicorn emulator from
an identical machine state (`tools/difftest.py`): registers (including the ones the original leaves
alone), ESP/EBX/ESI/EDI/EBP, x87, and all written memory are compared, and stubbed callees log their
arguments so behavior is asserted explicitly. A batch is complete only when the relink reports zero
mismatches, the focused test passes and the full suite reports zero failures.

## 3. Coverage

The automatic pipeline works on **11,174** candidate functions (the Lua 5.1 range and library code
are deliberately outside it):

| | functions | share |
|---|---|---|
| compiled by the auto pipeline into C and linked | 9,734 | 87.1 % |
| rejected by it, **since translated by hand** | 659 | 5.9 % |
| **still without a source translation** | **73** | **0.65 %** |
| auto compile-error rows | 1 (+1 intentional skip) | — |

By code volume the 73 remaining rejects are **82,738 bytes ≈ 4.5 %** of the 1,830,609 bytes of
function code in the corpus. Of the 18,583 entries in `symbols/attt_functions.tsv`, 10,460 are
replaced; the rest is dominated by the 6,801 SEH funclets (`Unwind@`), the external Lua 5.1 sources
and library/CRT code the pipeline does not target.

## 4. What remains (73 rejects)

By the auto decompiler's rejection reason:

```text
20 unaffected register             19 extra output register
 9 indirect call without prototype  8 decompiler warning
 7 stack outside the frame          4 catches exceptions
 2 register input                   1 callee reads the caller's EBP
 1 return address as a value        1 float/integer bits mixed (copy)
 1 float/integer bits mixed (piece)
```

By size: 43 functions are larger than 512 bytes, 11 are 129-512 bytes, 15 are 33-128 bytes and 5 are
32 bytes or smaller. The largest are SEH-wrapped game logic:

```text
0050C3C0  7,952 B   indirect call without a prototype
004662A0  5,520 B   return address as a value (stack depth lost)
0054D5B0  5,216 B   extra output register
005E23D7  4,697 B   unaffected register
00545400  4,624 B   extra output register
0053F020  3,232 B   extra output register
00544848  3,000 B   extra output register
005310E0  2,592 B   indirect call without a prototype
```

The small end is CRT glue: `__chkstk` (0x005E4080), CPUID/SSE2 probes (0x005E49DC, 0x005E498C),
`__ftol2` fast path (0x005E3FA0), the /GS cookie check (0x005E47CF) and similar fragments.

One additional auto compile-error row remains, 0x005E37A0 (22 bytes): an `atexit`-style registration
of the thunk 0x005E3790 whose inlined CRT callee the decompiler named `_AIL_shutdown`, so the
generated source does not compile. It is not part of the reject screen.

## 5. What blocks the rest

The remaining functions are blocked by tooling, not by unknown logic:

- **SEH.** `difftest.py` does not model SEH chains, so the large `try/catch` functions (4 classified
  as *catches exceptions* and many of the *extra output register* / *stack outside the frame* ones
  with `__finally` blocks) cannot be verified entry-by-entry. The auto pipeline already filters
  functions whose SEH frame only runs destructors; anything more needs harness support.
- **Naked code.** CPU feature probes and stack helpers use `pushfd`/`popfd`, `cpuid`, `movapd` or
  raw `call`/`ret` frame juggling that plain C cannot express without inline assembly, which the
  fixed-source build deliberately avoids.
- **Register-preserving tail calls.** 0x005E47CF (the /GS check) compares ECX with the process cookie
  at 0x006C8630 and, on mismatch, **tail-jumps** into 0x005E4CAC, which stores the caller's live
  EAX/ECX/EDX/EBX/ESI/EDI (0x8D1698..0x8D1684) before reporting. A C call cannot keep those values.
  The build's shim for referencing 0x005E4CAC is also broken: `shim_asm` computes
  `nstack = nparams - len(regs)` and emits `addl $-24, %esp` for a zero-parameter prototype against a
  six-register input list, corrupting the stack. Translating 0x005E47CF faithfully therefore needs
  either a narrow build.py fix plus a naked replacement, or to leave it as a reject (current state).
- **Unknown call targets.** The nine *indirect call without a prototype* functions need the callee
  target types recovered per call site (devirtualization); none of them can be replaced before that.

## 6. Reproduce

```bash
# relink (0 mismatches at the end)
python3 decomp/rebuild/build.py --exe ATThrone.exe --auto auto/attt --out build/ATThrone.exe

# one function
python3 decomp/tools/difftest.py ATThrone.exe build/ATThrone.exe build/ATThrone.map \
    decomp/rebuild/tests/test_005E218A_005E4A80_crt_helpers.py

# everything
python3 decomp/tools/difftest.py ATThrone.exe build/ATThrone.exe build/ATThrone.map \
    decomp/rebuild/tests/*.py
```

For a runnable game build add `--attfix-compat` (keeps the 110 functions AttTFix patches) or
`-D DECOMP_DEBUG_LOG` for engine-error logging; see README.md.

## 7. Milestones

| Tag | Contents |
|---|---|
| `v0.1` | first published translation checkpoint (projectile path sampling). |
| `v0.2` | second published checkpoint (mouse ray unprojection); included the previous session's batch work. |
| `v0.3` | this status report; 10,460 replacements, 73 rejects left, 1,020 passing differential tests. |
