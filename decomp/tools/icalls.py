#!/usr/bin/env python3
"""Facts about every indirect call (virtual calls, function pointers) from the machine code, for
ghidra/ICallOverride.java: the decompiler gives such a call its default prototype and loses the object passed in
ECX ('(**(code **)*p)(1)' for 'mov ecx, esi; call [eax+4]' with this = esi), and it guesses how many of the
values on the stack are its arguments.

For each 'call reg' / 'call [mem]' (not an import slot) inside a function:
  ecx      1 if ECX may hold a value set for the call: on some path to it (through the jumps), written after the last
           call, or the function's own ECX input; 0 if every path has a call after the last write
  cleanup  N of an 'add esp, N' after the call (a caller-pop callee; a few instructions that leave ESP alone may
           come between), -1 if there is none
  pushes   pushes right before the call with only moves between them (its arguments when nothing is nested)
  pop      bytes the callee removes, from the balance of ESP: the depth before the call is followed from the entry,
           the path after it to a ret through known pushes, pops and calls, and at the ret ESP must be back at the
           return address; -1 when no such path exists (an EBP frame restores ESP, an unknown call is in the way).
           'push 0x31; push file; push b; push a; push obj; call [ecx+0xFC]; push eax; call check; add esp, 0xC'
           has five pushes but the callee takes three: the other two are the check's.

usage: icalls.py EXE symbols/GAME_functions.tsv OUT.tsv [AUTO.jsonl.protos (conventions of imports)]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86
from stackfx import cleanup_after

pe = PE(sys.argv[1])
funcs = []
pops = {}           # function -> bytes its ret pops (None: unknown)
for l in open(sys.argv[2]):
    if l[0] == '#':
        continue
    q = l.rstrip('\n').split('\t')
    funcs.append((int(q[0], 16), int(q[1]), 'ECX' in q[2].split(',')))
    pops[int(q[0], 16)] = None if q[3] == '?' else int(q[3] or 0)
imports = {}        # IAT slot -> bytes the imported function pops
if len(sys.argv) > 4:
    W8 = {'double', 'longlong', 'ulonglong', 'undefined8', 'qword'}
    for l in open(sys.argv[4], encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) > 6 and q[6] == 'import':
            ps = [x.strip().rsplit(' ', 1)[0] for x in q[4].split(',') if x.strip()] if q[4] else []
            if q[1] == '__thiscall':
                ps = ps[1:]
            imports[int(q[0], 16)] = sum(8 if t in W8 else 4 for t in ps) \
                if q[1] in ('__stdcall', '__thiscall') and q[5] != 'true' else 0
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
slots = set(pe.imports)
ECXS = {x86.X86_REG_ECX, x86.X86_REG_CX, x86.X86_REG_CL, x86.X86_REG_CH}
MOVES = ('mov', 'lea', 'fld', 'fst', 'fild', 'fistp', 'movs', 'movz')
ESP = x86.X86_REG_ESP
STOP = object()


def is_icall(i):
    if i.mnemonic != 'call':
        return False
    op = i.operands[0]
    if op.type == x86.X86_OP_IMM:
        return False
    return not (op.type == x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in slots)


def effect(i, code, known):
    """ESP change of one instruction (bytes), or STOP when it is unknown or ESP is set from elsewhere"""
    m, ops = i.mnemonic, i.operands
    if m == 'push':
        return -4
    if m == 'pop':
        return 4
    if m in ('pushfd', 'pushal'):
        return -4 if m == 'pushfd' else -32
    if m in ('popfd', 'popal'):
        return 4 if m == 'popfd' else 32
    if m in ('sub', 'add') and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP:
        if ops[1].type != x86.X86_OP_IMM:
            return STOP
        return -ops[1].imm if m == 'sub' else ops[1].imm
    if m == 'leave' or (ops and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP and m in ('mov', 'lea', 'and')):
        return STOP
    if m == 'call':
        op = ops[0]
        if op.type == x86.X86_OP_IMM:
            p = pops.get(op.imm)
            return STOP if p is None else p
        if op.type == x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in slots:
            p = imports.get(op.mem.disp)
            return STOP if p is None else p
        p = known.get(i.address)
        return STOP if p is None else p
    return 0


def depths(code, start, known, check=None):
    """depth (bytes below the return address, negative) at each instruction reachable from the entry; with check (a
    list), a disagreement where paths meet or a ret away from the return address is appended to it"""
    d = {}
    todo = [(start, 0)]
    while todo:
        p, dep = todo.pop()
        while p in code:
            if p in d:
                if check is not None and d[p] != dep:
                    check.append(p)
                break
            d[p] = dep
            i = code[p]
            if i.mnemonic.startswith('ret'):
                if check is not None and dep != 0:
                    check.append(p)
                break
            if i.mnemonic in ('int3', 'hlt'):
                break
            e = effect(i, code, known)
            if e is STOP:
                break
            dep += e
            if i.mnemonic == 'jmp':
                op = i.operands[0]
                if op.type == x86.X86_OP_IMM and op.imm in code:
                    p = op.imm
                    continue
                break
            if i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                if i.operands[0].type == x86.X86_OP_IMM:
                    todo.append((i.operands[0].imm, dep))
            p = i.address + i.size
    return d


def to_ret(code, start, known, limit=400):
    """ESP changes from start to every ret reachable without anything unknown: the set of totals, or None"""
    totals, seen, n = set(), set(), 0
    todo = [(start, 0)]
    while todo:
        p, dep = todo.pop()
        while p in code:
            if (p, dep) in seen or n > limit:
                break
            seen.add((p, dep))
            n += 1
            i = code[p]
            if i.mnemonic.startswith('ret'):
                totals.add(dep)
                break
            if i.mnemonic in ('int3', 'hlt'):
                break
            e = effect(i, code, known)
            if e is STOP:
                return None
            dep += e
            if i.mnemonic == 'jmp':
                op = i.operands[0]
                if op.type == x86.X86_OP_IMM and op.imm in code:
                    p = op.imm
                    continue
                return None                      # tail jump or table: the stack after it is not followed
            if i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                if i.operands[0].type == x86.X86_OP_IMM:
                    todo.append((i.operands[0].imm, dep))
            p = i.address + i.size
    return totals or None


def predecessors(ins, code):
    """the instructions control comes from: the one before unless it is a jmp or ret, and every jump to it"""
    preds = {}
    for k, i in enumerate(ins):
        m = i.mnemonic
        if k + 1 < len(ins) and m != 'jmp' and not m.startswith('ret'):
            preds.setdefault(ins[k + 1].address, []).append(i.address)
        if (m.startswith('j') or m.startswith('loop')) and i.operands[0].type == x86.X86_OP_IMM and i.operands[0].imm in code:
            preds.setdefault(i.operands[0].imm, []).append(i.address)
    return preds


def ecx_set(a, preds, code, start, ecx_in, limit=200):
    """1 if on some path to the call ECX is written after the last call (or is the function's own ECX input):
    a __thiscall callee needs it; for a __stdcall one a value in ECX does no harm"""
    todo, seen = list(preds.get(a, [])), set()
    while todo and len(seen) < limit:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        i = code[p]
        if i.mnemonic == 'call':
            continue
        try:
            w = i.regs_access()[1]
        except Exception:
            w = []
        if any(r in ECXS for r in w):
            return 1
        if p == start:
            if ecx_in:
                return 1
            continue
        todo.extend(preds.get(p, []))
    return 1 if (a == start or not preds.get(a)) and ecx_in else 0


def callee_pops(code, start, calls, cleanup):
    """bytes popped by each callee-pop indirect call, from the ESP balance (resolved in rounds: one call's pop can
    be needed to follow the stack to the next one)"""
    known = {a: 0 for a in calls if cleanup[a] >= 0}
    for _ in range(4):
        d = depths(code, start, known)
        new = False
        for a in calls:
            if a in known or a not in d:
                continue
            i = code[a]
            t = to_ret(code, a + i.size, known)
            if not t or len(t) != 1:
                continue
            p = -(d[a] + t.pop())
            if 0 <= p <= -d[a] and p % 4 == 0 and p <= 64:
                known[a] = p
                new = True
        if not new:
            break
    # the rest (chains of indirect calls): each callee taken to pop what brings ESP back to the frame depth (the
    # commonest depth in the function, where statements start), accepted only if the whole function then agrees:
    # every ret at the return address, the same depth wherever paths meet, every instruction reached
    rest = [a for a in calls if a not in known]
    if rest:
        d = depths(code, start, known)
        if d:
            vals = list(d.values())
            frame = max(set(vals), key=vals.count)
            guess = dict(known)
            for _ in range(len(rest) + 1):
                d = depths(code, start, guess)
                for a in rest:
                    if a in d and a not in guess:
                        guess[a] = frame - d[a]
            bad = []
            d = depths(code, start, guess, bad)
            if not bad and all(a in guess and guess[a] >= 0 and guess[a] % 4 == 0 for a in rest) and \
                    len(d) == len(code) - sum(1 for i in code.values() if i.mnemonic in ('int3', 'nop')):
                known = guess
    return known


with open(sys.argv[3], 'w') as f:
    f.write('# call address\tfunction\tecx set (1/0)\tadd esp after (-1: none)\tpushes right before'
            '\tbytes the callee pops (ESP balance, -1: unknown)\n')
    n = solved = 0
    for start, size, ecx_in in funcs:
        try:
            ins = list(md.disasm(pe.read(start, size), start))
        except Exception:
            continue
        code = {i.address: i for i in ins}
        preds = predecessors(ins, code)
        rows, cleanup = [], {}
        for k, i in enumerate(ins):
            if not is_icall(i):
                continue
            ecx = ecx_set(i.address, preds, code, start, ecx_in)
            cl = cleanup_after(code.get, i.address + i.size)
            pushes = 0
            for j in range(k - 1, -1, -1):
                m = ins[j].mnemonic
                if m == 'push':
                    pushes += 1
                elif not m.startswith(MOVES):
                    break
            cleanup[i.address] = cl
            rows.append((i.address, ecx, cl, pushes))
        if not rows:
            continue
        known = callee_pops(code, start, [r[0] for r in rows], cleanup)
        for a, ecx, cl, pushes in rows:
            pop = known.get(a, -1) if cl < 0 else 0
            solved += pop >= 0 and cl < 0
            f.write('%08X\t%08X\t%d\t%d\t%d\t%d\n' % (a, start, ecx, cl, pushes, pop))
            n += 1
print('%d indirect calls, the pop of %d callee-pop ones from the ESP balance' % (n, solved))
