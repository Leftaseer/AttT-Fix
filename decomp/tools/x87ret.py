#!/usr/bin/env python3
"""Which functions return a float in ST0, from the machine code: follows the depth of the x87 register stack
through each function (loads push, fstp/faddp/fcompp ... pop, calls add what the callee leaves) and looks at the
depth at every ret.  A function that leaves one value there returns a float; the decompiler often types such a
function 'float10' with a hidden pointer to the result (Ghidra cannot put 10 bytes in ST0) or int, and every
caller then mixes float and integer bits ('extraout_ST0').  ghidra/FloatReturns.java gives them a float or
double result.

The width of the value is that of its last load ('fld dword' -> float, 'fld qword' or a constant -> double,
arithmetic -> the x87's 80 bits, written double).  Calls whose callee is unknown (indirect, or not followed yet)
leave nothing, unless the caller's next x87 instruction uses ST0 on an empty stack: then they returned one.
Iterates until the results of the callees settle.

usage: x87ret.py EXE symbols/GAME_functions.tsv OUT.tsv
OUT: address, float/double/x87 (80-bit arithmetic: use double); functions whose rets disagree are left out (and
counted)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86
from stackfx import switch_targets
from crtfuncs import ftol_kind

pe = PE(sys.argv[1])
funcs, sizes = set(), {}
for l in open(sys.argv[2]):
    if l[0] != '#':
        q = l.split('\t')
        funcs.add(int(q[0], 16))
        sizes[int(q[0], 16)] = int(q[1])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
lo, hi = pe.text_range()
cache = {}


def insn(a):
    if a not in cache:
        b = pe.read(a, 16) if lo <= a < hi else None
        i = next(md.disasm(b, a), None) if b else None
        cache[a] = i
    return cache[a]


PUSH = {'fld', 'fild', 'fbld', 'fldz', 'fld1', 'fldpi', 'fldl2e', 'fldl2t', 'fldlg2', 'fldln2',
        'fsincos', 'fptan', 'fxtract'}
# (capstone spells fcomip and fucomip 'fcompi' and 'fucompi')
POP1 = {'fstp', 'fistp', 'fisttp', 'fbstp', 'fcomp', 'ficomp', 'fucomp', 'fcomip', 'fucomip', 'fcompi', 'fucompi', 'faddp', 'fsubp',
        'fsubrp', 'fmulp', 'fdivp', 'fdivrp', 'fpatan', 'fyl2x', 'fyl2xp1', 'ffreep'}
POP2 = {'fcompp', 'fucompp'}
CONTROL = {'fldcw', 'fnstcw', 'fstcw', 'fnstsw', 'fstsw', 'fnclex', 'fclex', 'fwait', 'wait', 'fnsave', 'fsave',
           'frstor', 'fnstenv', 'fstenv', 'fldenv', 'ffree', 'fincstp', 'fdecstp', 'fnop', 'fninit', 'finit'}
# imports with x87 arguments (MSVC intrinsics) and ones that return a double in ST0
FPU_ARGS = {'_CIsin': 1, '_CIcos': 1, '_CItan': 1, '_CIsqrt': 1, '_CIatan': 1, '_CIasin': 1, '_CIacos': 1,
            '_CIexp': 1, '_CIlog': 1, '_CIlog10': 1, '_CIsinh': 1, '_CIcosh': 1, '_CItanh': 1,
            '_CIpow': 2, '_CIatan2': 2, '_CIfmod': 2}
DOUBLE_IMPORTS = {'floor', 'ceil', 'atof', 'strtod', 'wcstod', 'modf', 'ldexp', 'frexp', 'fabs', 'sqrt', 'pow',
                  'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'exp', 'log', 'log10', 'fmod', 'sinh',
                  'cosh', 'tanh', '_hypot', '_copysign', '_chgsign', '_logb', '_nextafter', '_scalb', 'difftime',
                  '_atof_l', '_strtod_l', '_wtof',
                  '_AIL_digital_master_volume_level@4'}     # (Miles: F32 in ST0; 0x4C13D0 hands it on)


def import_at(a):
    """name of the import a call goes to: 'call [IAT]', or a 'jmp [IAT]' thunk"""
    i = insn(a)
    if i and i.mnemonic == 'jmp' and i.operands and i.operands[0].type == x86.X86_OP_MEM and \
            i.operands[0].mem.base == 0 and i.operands[0].mem.index == 0:
        return pe.imports.get(i.operands[0].mem.disp, (None, None))[1]
    return None


def width(i):
    """bits the value pushed by a load has: 4 float, 8 double, 10 x87"""
    m = i.mnemonic
    if m == 'fld' and i.operands and i.operands[0].type == x86.X86_OP_MEM:
        return {4: 4, 8: 8}.get(i.operands[0].size, 10)
    if m in ('fild', 'fldz', 'fld1'):
        return 8
    return 10


ftol = {a for a in funcs if ftol_kind(pe.read(a, 32))}
result = {}       # function -> (depth at its rets 0/1, width)


def call_effect(i):
    """(x87 values the call leaves, width, callee or None, known)"""
    op = i.operands[0]
    if op.type == x86.X86_OP_IMM:
        t = op.imm
        name = import_at(t)
    elif op.type == x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
        t, name = None, pe.imports.get(op.mem.disp, (None, None))[1]
    else:
        return 0, 10, None, False
    if name in FPU_ARGS:
        return 1 - FPU_ARGS[name], 10, None, True
    if t is not None and t in ftol:
        return -1, 10, None, True      # _ftol2(_sse): takes ST0, returns an integer (0x463E20 ends in a jump to it)
    if name in DOUBLE_IMPORTS:
        return 1, 8, None, True
    if name is not None:
        return 0, 10, None, True
    if t in result:
        d, w = result[t]
        return d, w, t, True
    return 0, 10, t, False


def analyze(f):
    """depths and widths at the rets of f; None if they cannot be followed; also notes callers' uses"""
    seen = {}
    work = [(f, 0, 10, None)]
    rets = []
    while work:
        a, d, w, pend = work.pop()
        while True:
            if a in seen:
                if seen[a] != d:
                    return None
                break
            seen[a] = d
            i = insn(a)
            if i is None:
                return None
            m = i.mnemonic
            nxt = a + i.size
            if m.startswith('f') and m not in CONTROL:
                if m not in PUSH and d == 0 and pend is not None:
                    # the call before returned a value in ST0 the analysis did not know of
                    d, w = 1, 10
                if m in PUSH:
                    d += 1
                    w = width(i)
                    if m in ('fsincos', 'fptan', 'fxtract'):
                        w = 10
                elif m in POP1:
                    d -= 1
                    w = 10
                elif m in POP2:
                    d -= 2
                elif m in ('fninit', 'finit'):
                    d = 0
                else:
                    w = 10 if m not in ('fst', 'fist', 'fcom', 'fucom', 'fcomi', 'fucomi', 'ftst', 'fxam', 'fxch') else w
                if d < 0:
                    return None
                pend = None
            elif m == 'call':
                e, cw, t, known = call_effect(i)
                d += e
                if e > 0:
                    w = cw
                if d < 0:
                    return None
                pend = (t or 0) if not known or e == 0 else None
                if known and e == 0 and t is None:
                    pend = None
            elif m.startswith('ret'):
                rets.append((d, w))
                break
            elif m == 'jmp':
                op = i.operands[0]
                if op.type != x86.X86_OP_IMM:
                    if import_at(a) or (op.type == x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0):
                        e, cw, t, known = call_effect(i)
                        rets.append((d + e, cw if e > 0 else w))
                    for t in switch_targets(i, pe.u32, f, f + sizes.get(f, 0)):
                        work.append((t, d, w, pend))   # the cases of a switch
                    break
                t = op.imm
                if t in funcs and t != f:
                    e, cw, _, known = call_effect(i)
                    rets.append((d + e, cw if e > 0 else w))   # tail call
                    break
                a = t
                continue
            elif m.startswith('j') or m.startswith('loop'):
                op = i.operands[0]
                if op.type == x86.X86_OP_IMM:
                    work.append((op.imm, d, w, pend))
            elif m in ('int3', 'hlt', 'ud2'):
                break
            a = nxt
    return rets


for it in range(12):
    new, bad = {}, 0
    for f in sorted(funcs):
        r = analyze(f)
        if not r:
            continue
        ds = {d for d, _ in r}
        if len(ds) != 1 or ds - {0, 1}:
            bad += 1
            continue
        d = ds.pop()
        new[f] = (d, max(w for _, w in r) if d else 10)
    changed = sum(1 for f in new if result.get(f) != new[f])
    result = new
    print('pass %d: %d functions followed, %d with rets disagreeing, %d changed' % (it, len(new), bad, changed))
    if not changed:
        break

with open(sys.argv[3], 'w') as o:
    o.write('# address\tresult in ST0 (tools/x87ret.py)\n')
    n = 0
    for f in sorted(result):
        d, w = result[f]
        if d:
            n += 1
            o.write('%08X\t%s\n' % (f, {4: 'float', 8: 'double'}.get(w, 'x87')))
print('%d functions return a float in ST0' % n)
