#!/usr/bin/env python3
"""Bytes popped by functions that end in a tail jump: such a function has no ret of its own, so regparams.py
finds no ret N, but its callers' stack is cleaned by the function it jumps to (thiscall wrappers like
'mov ecx, [ecx+1C4]; jmp Method').  Follows jmp chains to a function with a known ret and writes the pop into
column 4 of functions.tsv (in place).

usage: tailpop.py EXE REGPARAMS.tsv symbols/GAME_functions.tsv [AUTO.jsonl.protos (import conventions)]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
from stackfx import table_import_pops
import capstone
from capstone import x86

pe = PE(sys.argv[1])
known = {}          # addr -> pop, for functions with a ret
for l in open(sys.argv[2]):
    q = l.rstrip('\n').split('\t')
    if len(q) > 2 and q[2]:
        known[int(q[0], 16)] = int(q[2].split(',')[0])
rows, sizes = [], {}
for l in open(sys.argv[3]):
    rows.append(l)
    if l[0] != '#':
        q = l.split('\t')
        sizes[int(q[0], 16)] = int(q[1])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
# import thunks (jmp [IAT]): the import's own convention, from AutoExport's .protos when given
imp_pop = {}
forced = set()      # thunks whose pop comes from the import table (the row may hold regparams' 0 for a jmp)
if len(sys.argv) > 4:
    W8 = {'double', 'longlong', 'ulonglong', 'undefined8', 'qword'}
    for l in open(sys.argv[4], encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) > 6 and q[6] == 'import':
            ps = [x.strip().rsplit(' ', 1)[0] for x in q[4].split(',') if x.strip()] if q[4] else []
            if q[1] == '__thiscall':
                ps = ps[1:]
            n = sum(8 if t in W8 else 4 for t in ps)
            imp_pop[int(q[0], 16)] = n if q[1] in ('__stdcall', '__thiscall') and q[5] != 'true' else 0
imp_pop.update(table_import_pops(pe))     # symbols/import_protos.tsv: D3DX9, MSVCP80 with hidden parameters
# C++ imports by their decorated names (symbols/GAME_cxximports.tsv of cxximports.py, next to functions.tsv)
cxx = os.path.join(os.path.dirname(os.path.abspath(sys.argv[3])), os.path.basename(sys.argv[3]).replace('_functions', '_cxximports'))
if os.path.exists(cxx):
    slot_of = {n: a for a, (dll, n) in pe.imports.items()}
    for l in open(cxx):
        q = l.rstrip('\n').split('\t')
        if l[0] != '#' and len(q) > 2 and q[0] in slot_of and slot_of[q[0]] not in imp_pop:
            imp_pop[slot_of[q[0]]] = int(q[2]) if q[1] in ('__thiscall', '__stdcall') else 0
for a, size in sizes.items():
    if a in known:
        continue
    try:
        i = next(md.disasm(pe.read(a, 8), a, 1))
    except (StopIteration, Exception):
        continue
    if i.mnemonic == 'jmp' and i.operands[0].type == x86.X86_OP_MEM and i.operands[0].mem.base == 0 and \
            i.operands[0].mem.disp in imp_pop:
        known[a] = imp_pop[i.operands[0].mem.disp]
        forced.add(a)
tails = {}          # function without a ret -> set of functions it tail-jumps to
for a, size in sizes.items():
    if a in known:
        continue
    t = set()
    try:
        moves_esp = False
        for i in md.disasm(pe.read(a, size), a):
            if i.mnemonic == 'jmp' and i.operands[0].type == x86.X86_OP_IMM:
                d = i.operands[0].imm
                if d in sizes and not (a <= d < a + size):
                    t.add(d)
            # a jump on to an import after a few instructions ('mov [ecx], vftable; jmp [~exception]', 0x420600),
            # nothing pushed or popped before it
            elif i.mnemonic == 'jmp' and i.operands[0].type == x86.X86_OP_MEM and i.operands[0].mem.base == 0 and \
                    i.operands[0].mem.index == 0 and i.operands[0].mem.disp in imp_pop and not moves_esp:
                known[('imp', i.operands[0].mem.disp)] = imp_pop[i.operands[0].mem.disp]
                t.add(('imp', i.operands[0].mem.disp))
            if i.mnemonic in ('push', 'pop', 'call', 'leave') or 'esp' in i.op_str.split(',')[0]:
                moves_esp = True
    except Exception:
        pass
    if t:
        tails[a] = t


def pop_of(a, depth=0):
    if a in known:
        return known[a]
    if depth > 8 or a not in tails:
        return None
    ps = set(pop_of(d, depth + 1) for d in tails[a])
    return ps.pop() if len(ps) == 1 else None


fixed = 0
with open(sys.argv[3], 'w') as f:
    for l in rows:
        if l[0] != '#':
            q = l.rstrip('\n').split('\t')
            a = int(q[0], 16)
            if a in known and (q[3] == '?' or a in forced and q[3] != str(known[a])):
                q[3] = str(known[a]); fixed += 1
                l = '\t'.join(q) + '\n'
            elif a not in known and a in tails:
                p = pop_of(a)
                if p is not None and str(p) != q[3]:
                    q[3] = str(p)
                    fixed += 1
                    l = '\t'.join(q) + '\n'
        f.write(l)
print('ret pop taken from the tail-jump target for %d functions' % fixed)
