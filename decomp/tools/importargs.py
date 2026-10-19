#!/usr/bin/env python3
"""Argument bytes of caller-pop imported functions, from the machine code: after 'call dword ptr [IAT slot]' the
caller removes the arguments with 'add esp, N'.  The decompiler's prototype of an import can miss an argument
(std::operator+(const string &, const char *) returning by value takes three: the result, the string and the
C string), and code calling it then loses that argument.

usage: importargs.py EXE OUT.tsv      OUT: IAT slot, commonest non-zero N, number of calls"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86

pe = PE(sys.argv[1])
lo, hi = pe.text_range()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
code = pe.read(lo, hi - lo)
slots = set(pe.imports)
seen = {}
prev = None
# linear sweep with resynchronisation: good enough for MSVC code, where calls are not hidden in data
def sweep():
    off = 0
    while off < len(code):
        last = None
        for i in md.disasm(code[off:], lo + off):
            last = i
            yield i
        off = (last.address + last.size - lo) if last else off + 1
        if last is None or off < len(code):
            off += 0 if last is None else 1     # capstone stopped at undecodable bytes: skip one


pushes = {}         # IAT slot -> pushes right before each call (its arguments, for imports that pop them)
run = 0
for i in sweep():
    m = i.mnemonic
    if m == 'push':
        run += 1
    elif m in ('call', 'ret', 'jmp') or (m in ('add', 'sub') and i.op_str.startswith('esp,')) or 'fs:' in i.op_str \
            or m.startswith('j'):
        pass                # handled below / ends a run
    if prev is not None:
        if i.mnemonic == 'add' and i.op_str.startswith('esp, ') and i.operands[1].type == x86.X86_OP_IMM:
            n = i.operands[1].imm
        else:
            n = 0
        seen.setdefault(prev, []).append(n)
        prev = None
    if i.mnemonic == 'call' and i.operands[0].type == x86.X86_OP_MEM and i.operands[0].mem.base == 0 and \
            i.operands[0].mem.index == 0 and i.operands[0].mem.disp in slots:
        prev = i.operands[0].mem.disp
        pushes.setdefault(prev, []).append(run)
    if m != 'push' and not (m.startswith('mov') or m == 'lea' or m.startswith('fst') or m.startswith('fld')):
        run = 0             # arguments are pushed with only movs and leas between them
with open(sys.argv[2], 'w') as f:
    # the commonest non-zero cleanup: the compiler sometimes removes the arguments of two calls with one add
    f.write('# IAT slot\tcommonest add esp after a call (argument bytes of a caller-pop import)\tcalls'
            '\tcommonest number of pushes right before a call\n')
    for a in sorted(seen):
        nz = [n for n in seen[a] if n]
        mode = max(set(nz), key=nz.count) if nz else 0
        ps = pushes.get(a, [0])
        pm = max(set(ps), key=ps.count)
        f.write('%08X\t%d\t%d\t%d\n' % (a, mode, len(seen[a]), pm))
print('%d imports called' % len(seen))
