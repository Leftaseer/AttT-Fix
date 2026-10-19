#!/usr/bin/env python3
"""Register inputs of every function from the machine code: registers read on some path from the entry before
being written.  Saves of callee-saved registers (push ebx/esi/edi/ebp) and 'push ecx' that only reserves stack
space in the prologue are not reads; a call reads the register inputs of its callee (and clobbers EAX/ECX/EDX),
a tail jump those of its target, so the analysis repeats until nothing changes.  Detects MSVC /LTCG custom
conventions (a function that passes EAX on to a callee takes EAX too).
usage: regparams.py EXE BINFEAT.json OUT.tsv [STACKPARAMS.tsv FUNCTIONS.tsv]   ->  ADDR <tab> regs (e.g. ECX,EAX) <tab> ret-pop-bytes"""
import sys, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone import x86_const as X
p = PE(sys.argv[1]); bf = {int(k, 16): v for k, v in json.load(open(sys.argv[2])).items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
FULL = {}
for full, subs in {'EAX': ('eax', 'ax', 'al', 'ah'), 'ECX': ('ecx', 'cx', 'cl', 'ch'), 'EDX': ('edx', 'dx', 'dl', 'dh'),
                   'EBX': ('ebx', 'bx', 'bl', 'bh'), 'ESI': ('esi', 'si'), 'EDI': ('edi', 'di'), 'EBP': ('ebp', 'bp')}.items():
    for s in subs: FULL[s] = full
BIT = {'EAX': 1, 'ECX': 2, 'EDX': 4, 'EBX': 8, 'ESI': 16, 'EDI': 32, 'EBP': 64}
def regs(i, names):
    return set(FULL[i.reg_name(r)] for r in names if i.reg_name(r) in FULL)
callee_in = {}       # function -> register input bits (previous pass)
slots, pops = {}, {}  # stack parameter slots (stackparams.py) and ret pops of the callees, when given
if len(sys.argv) > 5:
    for l in open(sys.argv[4]):
        q = l.rstrip('\n').split('\t')
        if l[0] != '#': slots[int(q[0], 16)] = int(q[1])
    for l in open(sys.argv[5]):
        q = l.rstrip('\n').split('\t')
        if l[0] != '#': pops[int(q[0], 16)] = 0 if q[3] == '?' else int(q[3] or 0)
SAVED = {'EBX', 'ESI', 'EDI', 'EBP'}


TEXT = p.text_range()


def own(t, start):
    """a jump target outside the known size that still belongs to this function (no function starts there)"""
    return t not in bf and TEXT[0] <= t < TEXT[1] and abs(t - start) <= 0x20000


def analyse(start):
    size = bf[start]['size']; end = start + size
    code = p.read(start, size)
    if not code: return 0, set()
    ins = {}
    for i in md.disasm(code, start): ins[i.address] = i
    # callee-saved registers the function overwrites somewhere: pushes of those are saves
    clobbers = set()
    for i in ins.values():
        if i.mnemonic == 'pop':
            continue
        try:
            clobbers |= regs(i, i.regs_access()[1]) & SAVED
        except Exception:
            pass
    inputs = 0; retpop = set(); pending = []; entry_run = True
    seen = set(); work = [(start, 0)]; steps = 0
    while work and steps < 20000:
        a, w = work.pop()
        pending = []; bound = 0
        while True:
            steps += 1
            if (a, w) in seen: break
            if a not in ins:
                # code past the size of the function (its body is not contiguous): follow it until another function
                if a in bf or not (TEXT[0] <= a < TEXT[1]) or abs(a - start) > 0x20000: break
                got = list(md.disasm(p.read(a, 16), a, 1))
                if not got: break
                ins[a] = got[0]
            seen.add((a, w)); i = ins[a]
            m = i.mnemonic
            try:
                rd, wr = i.regs_access()
            except Exception:
                break
            r = regs(i, rd); wrr = regs(i, wr)
            if m != 'push':
                entry_run = False
            if m == 'push':
                # a pushed register is read only if the slot goes to a call as an argument (decided at the call);
                # otherwise it is a save or reserves stack space
                o = i.operands[0]
                pr = FULL.get(i.reg_name(o.reg)) if o.type == X.X86_OP_REG else None
                # pushes that open the function are saves
                pending.append(pr if pr and not w & BIT[pr] and not entry_run and pr not in clobbers else None)
                r = set() if o.type == X.X86_OP_REG else r
            elif m == 'pop':
                if pending: pending.pop()
                bound = min(bound, len(pending))
            elif m in ('test', 'cmp') or m.startswith('j'):
                bound = len(pending)
            elif m in ('add', 'sub') and i.op_str.startswith('esp, ') and i.operands[1].type == X.X86_OP_IMM:
                k = i.operands[1].imm // 4
                if m == 'add': pending = pending[:max(0, len(pending) - k)]; bound = min(bound, len(pending))
                else: pending.extend([None] * min(k, 64))
            if m == 'pop': r = set()
            if m in ('xor', 'sub', 'sbb') and len(i.operands) == 2 and i.operands[0].type == X.X86_OP_REG and i.operands[1].type == X.X86_OP_REG and i.operands[0].reg == i.operands[1].reg:
                r = set() if m != 'sbb' else r
            if m == 'call':
                o = i.operands[0]
                ci = callee_in.get(o.imm, 0) if o.type == X.X86_OP_IMM else 0
                r = set(n for n, b in BIT.items() if ci & b)
                # an indirect call takes the pushes since the last test or branch (saves come before those)
                k = slots.get(o.imm, len(pending) - bound) if o.type == X.X86_OP_IMM else len(pending) - bound
                for x in pending[len(pending) - k:] if k else []:
                    if x and (o.type == X.X86_OP_IMM or x in ('EAX', 'ECX', 'EDX')):
                        r.add(x)      # before an indirect call a pushed EBX/ESI/EDI/EBP is far more often a save
                if o.type == X.X86_OP_IMM and pops.get(o.imm):
                    pending = pending[:max(0, len(pending) - pops[o.imm] // 4)]
                bound = min(bound, len(pending))
            # alignment padding: lea r,[r] / mov r,r
            if (m == 'lea' and i.op_str.split(',')[0].strip() == i.op_str.split('[')[-1].rstrip(']').strip()) or \
                    (m == 'mov' and len(i.operands) == 2 and i.operands[0].type == X.X86_OP_REG and
                     i.operands[1].type == X.X86_OP_REG and i.operands[0].reg == i.operands[1].reg):
                a = a + i.size
                continue
            # or r,-1 / and r,0 set the register without depending on it
            if m in ('or', 'and') and len(i.operands) == 2 and i.operands[0].type == X.X86_OP_REG and \
                    i.operands[1].type == X.X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == (0xFFFFFFFF if m == 'or' else 0):
                r = set()
            for x in r:
                if not w & BIT[x]: inputs |= BIT[x]
            for x in wrr:
                w |= BIT[x]
                # a register written after being pushed was saved there, not passed
                pending = [None if y == x else y for y in pending] if m != 'call' else pending
            if m == 'call': w |= BIT['EAX'] | BIT['ECX'] | BIT['EDX']
            if m in ('ret', 'retf'):
                retpop.add(i.operands[0].imm if i.operands else 0); break
            if m == 'int3' or m == 'hlt': break
            if m == 'jmp':
                o = i.operands[0]
                if o.type == X.X86_OP_IMM and (start <= o.imm < end or own(o.imm, start)): a = o.imm; continue
                if o.type == X.X86_OP_IMM:     # tail call: the target's register inputs
                    for n, b in BIT.items():
                        if callee_in.get(o.imm, 0) & b and not w & b: inputs |= b
                break  # tail call or switch: stop
            if m.startswith('j') or m.startswith('loop'):
                o = i.operands[0]
                if o.type == X.X86_OP_IMM and (start <= o.imm < end or own(o.imm, start)): work.append((o.imm, w))
            a = a + i.size
    return inputs, retpop


for rnd in range(8):
    res = {start: analyse(start) for start in sorted(bf)}
    changed = sum(1 for a, (inp, _) in res.items() if callee_in.get(a, 0) != inp)
    callee_in = {a: inp for a, (inp, _) in res.items()}
    print('pass %d: %d functions changed' % (rnd + 1, changed), file=sys.stderr)
    if not changed:
        break
with open(sys.argv[3], 'w') as out:
    for start in sorted(res):
        inputs, retpop = res[start]
        names = [n for n, b in BIT.items() if inputs & b]
        out.write('%08X\t%s\t%s\n' % (start, ','.join(names), ','.join(str(x) for x in sorted(retpop))))
