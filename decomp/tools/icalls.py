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

usage: icalls.py EXE symbols/GAME_functions.tsv OUT.tsv [AUTO.jsonl.protos (conventions of imports)]
                 [symbols/GAME.sym (vftables: the pop of a virtual call the balance leaves open)]
                 [symbols/GAME_icall_pops.tsv (pops measured in the running game, rebuild/src/engine/icalltrace.cpp)]"""
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


def is_ijmp(i):
    """a tail call through a pointer: 'jmp reg' or 'jmp [reg+off]' (not a switch table, not an import slot)"""
    if i.mnemonic != 'jmp' or not i.operands:
        return False
    op = i.operands[0]
    if op.type == x86.X86_OP_REG:
        return True
    return op.type == x86.X86_OP_MEM and op.mem.base != 0 and op.mem.index == 0


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


# virtual calls whose callee pop the balance leaves open: the functions at that offset of every vftable of the game
# (symbols/GAME.sym), when their ret pops all agree.  Only for calls with ECX set (a method of the game's classes:
# COM objects such as Direct3D's pass this on the stack and have no vftable in the symbols) and no more arguments
# than the pushes before the call.
vt_pops = {}
if len(sys.argv) > 5:
    vts = []
    for l in open(sys.argv[5], encoding='utf-8'):
        q = l.split('#')[0].split(None, 2)
        if len(q) == 3 and q[1] == 'd' and 'vftable' in q[2]:
            vts.append(int(q[0], 16))
    lens = {}
    for v in vts:              # a vftable: the function pointers up to the first dword that is none
        n = 0
        while n < 256 and pe.u32(v + 4 * n) in pops:
            n += 1
        lens[v] = n
    for off in range(0, 0x400, 4):
        seen = set()
        for v in vts:
            if off // 4 < lens[v]:
                seen.add(pops[pe.u32(v + off)])
        if len(seen) == 1 and None not in seen:
            vt_pops[off] = seen.pop()


measured = {}       # call address -> bytes popped, measured (icalltrace.cpp) where the code alone does not tell
if len(sys.argv) > 6:
    for l in open(sys.argv[6]):
        q = l.split()
        if l[0] != '#' and len(q) >= 2:
            measured[int(q[0], 16)] = int(q[1])


def com_call(ins, k):
    """a COM method call: the last push before the call is the object whose vftable the call reads ('mov ecx, [eax];
    push eax; call [ecx+0x108]' of Direct3D): this goes on the stack, ECX only holds the vftable"""
    last = None
    for j in range(k - 1, max(-1, k - 8), -1):
        m = ins[j].mnemonic
        if m == 'push':
            last = ins[j]
            break
        if not m.startswith(MOVES):
            return False
    if last is None or last.operands[0].type != x86.X86_OP_REG:
        return False
    r = last.operands[0].reg
    ecx_written = False
    for j in range(k - 1, max(-1, k - 10), -1):
        i = ins[j]
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[1].type == x86.X86_OP_MEM and \
                i.operands[1].mem.base == r and i.operands[1].mem.disp == 0 and i.operands[1].mem.index == 0:
            # the vftable load: COM if it went into ECX, or nothing else set ECX on the way (a method of the game
            # may also be given its object as an argument: 'mov ecx, esi; push esi; call [eax+4]' is thiscall)
            dst = i.operands[0].reg if i.operands[0].type == x86.X86_OP_REG else None
            return dst in ECXS or not ecx_written
        if i.mnemonic.startswith(('call', 'j', 'ret')):
            return False
        try:
            if any(x in ECXS for x in i.regs_access()[1]):
                ecx_written = True
        except Exception:
            ecx_written = True
    return False


def vslot(ins, k):
    """vftable offset of the indirect call ins[k]: call [reg+off], or call reg after mov reg, [x+off]"""
    op = ins[k].operands[0]
    if op.type == x86.X86_OP_MEM and op.mem.base not in (0, ESP, x86.X86_REG_EBP) and op.mem.index == 0:
        return op.mem.disp
    if op.type == x86.X86_OP_REG:
        for j in range(k - 1, max(-1, k - 7), -1):
            p = ins[j]
            if p.mnemonic == 'mov' and p.operands[0].type == x86.X86_OP_REG and p.operands[0].reg == op.reg:
                m = p.operands[1]
                if m.type == x86.X86_OP_MEM and m.mem.base not in (0, ESP, x86.X86_REG_EBP) and m.mem.index == 0:
                    return m.mem.disp
                return None
            if p.mnemonic.startswith(('call', 'j', 'ret')):
                return None
    return None


with open(sys.argv[3], 'w') as f:
    f.write('# call address\tfunction\tecx set (1/0)\tadd esp after (-1: none)\tpushes right before'
            '\tbytes the callee pops (ESP balance, -1: unknown)\n')
    n = solved = byvt = ntail = bym = 0
    tails = []
    for start, size, ecx_in in funcs:
        try:
            ins = list(md.disasm(pe.read(start, size), start))
        except Exception:
            continue
        code = {i.address: i for i in ins}
        preds = predecessors(ins, code)
        rows, cleanup = [], {}
        for k, i in enumerate(ins):
            if is_ijmp(i):
                # a tail call (ghidra/TailCalls.java makes the decompiler see one): ESP is back at the return
                # address, the callee pops what this function's own ret would; unknown, a vftable slot may tell
                ecx = ecx_set(i.address, preds, code, start, ecx_in)
                pop = pops.get(start)
                off = vslot(ins, k)
                if pop is None and ecx == 1 and off in vt_pops:
                    pop = vt_pops[off]
                tails.append((i.address, ecx, -1 if pop is None else pop))
                continue
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
            com = com_call(ins, k)
            if com:
                ecx = 0             # stdcall with this on the stack
            rows.append((i.address, ecx, cl, pushes, None if com else vslot(ins, k)))
        for a, ecx, pop in tails:
            f.write('%08X\t%08X\t%d\t-1\t0\t%d\n' % (a, start, ecx, pop))
            n += 1
            ntail += 1
        tails.clear()
        if not rows:
            continue
        known = callee_pops(code, start, [r[0] for r in rows], cleanup)
        for a, ecx, cl, pushes, off in rows:
            pop = known.get(a, -1) if cl < 0 else 0
            # the balance fixes only the sum of the pops between two known depths: a callee 'popping nothing' after
            # pushes is as likely another call taking them (0x5B52A0: two COM calls in a row, the second given 0
            # once the first was known; it pops its four arguments)
            if cl < 0 and pop == 0 and pushes > 0:
                pop = -1
            solved += pop >= 0 and cl < 0
            if pop < 0 and cl < 0 and ecx == 1 and off in vt_pops and vt_pops[off] // 4 <= pushes:
                pop = vt_pops[off]
                byvt += 1
            # a measured 0 may be a caller-pop callee whose arguments are cleaned up later, after another call: only
            # without pushes before the call
            if pop < 0 and cl < 0 and a in measured and (measured[a] > 0 or pushes == 0):
                pop = measured[a]
                bym += 1
            f.write('%08X\t%08X\t%d\t%d\t%d\t%d\n' % (a, start, ecx, cl, pushes, pop))
            n += 1
print('%d indirect calls (%d of them tail jumps), the pop of %d callee-pop ones from the ESP balance, %d from the '
      'vftables (%d offsets agree), %d measured' % (n, ntail, solved, byvt, len(vt_pops), bym))
