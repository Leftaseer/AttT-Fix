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
                 [symbols/GAME_icall_pops.tsv (pops measured in the running game, rebuild/src/engine/icalltrace.cpp)]
                 [out/GAME_rtti.json (rtti.py: classes and their vftables, for virtual calls on this)]
Also gives functions without a ret of their own their pop from their callers (column 4 of functions.tsv, in place).
Where the balance leaves several pops open, guesses checked against the whole function: each callee pops what
brings ESP back to the frame depth, or what was pushed since the call before it; exception-state writes tell the
depth after a call.  Checked against the pops measured in the game (symbols/GAME_icall_pops.tsv, left out): 784 of
them found, none wrong."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86
from stackfx import table_import_pops, cleanup_after, prologue_end

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
imports.update(table_import_pops(pe))
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
    if m == 'lea' and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP and ops[1].mem.base == ESP and \
            ops[1].mem.index == 0:
        return ops[1].mem.disp                  # 'lea esp, [esp+0]': an alignment nop (0x4212D8)
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
    todo = [(start, 0, None)]
    while todo:
        p, dep, ebp = todo.pop()
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
            # an EBP frame: 'mov ebp, esp' remembers the depth, 'mov esp, ebp' and 'leave' go back to it (the
            # epilogue is reached, so the frame-depth check below can accept the function)
            if i.mnemonic == 'mov' and i.op_str == 'ebp, esp':
                ebp = dep
            elif i.mnemonic == 'mov' and i.op_str == 'esp, ebp' and ebp is not None:
                dep = ebp
                p = i.address + i.size
                continue
            elif i.mnemonic == 'leave' and ebp is not None:
                dep = ebp + 4
                ebp = None
                p = i.address + i.size
                continue
            elif i.mnemonic == 'pop' and i.op_str == 'ebp':
                ebp = None
            elif i.mnemonic == 'and' and i.op_str.startswith('esp, ') and ebp is not None:
                # 'and esp, -8' aligning an EBP frame: what follows is counted from the aligned ESP, the epilogue's
                # 'mov esp, ebp' goes back (0x428090)
                p = i.address + i.size
                continue
            elif ebp is not None and i.operands and i.operands[0].type == x86.X86_OP_REG and \
                    i.operands[0].reg == x86.X86_REG_EBP and i.mnemonic not in ('push', 'cmp', 'test'):
                ebp = None                      # EBP written otherwise
            e = effect(i, code, known)
            if e is STOP:
                break
            dep += e
            if i.mnemonic == 'jmp':
                op = i.operands[0]
                if op.type == x86.X86_OP_IMM and op.imm in code:
                    p = op.imm
                    continue
                # a tail call leaves like a ret: ESP back at the return address (0x47BF50 ends in 'jmp edx' after
                # a call that pops two float arguments made room for with 'sub esp, 8')
                if check is not None and tail_jump(i, code) and dep != 0:
                    check.append(p)
                break
            if i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                if i.operands[0].type == x86.X86_OP_IMM:
                    todo.append((i.operands[0].imm, dep, ebp))
            p = i.address + i.size
    return d


def tail_jump(i, code):
    """a jmp that leaves the function as a call would: to another function, through a register, a pointer or an
    import slot (not a switch table: those have an index register)"""
    op = i.operands[0]
    if op.type == x86.X86_OP_IMM:
        return op.imm not in code
    return op.type == x86.X86_OP_REG or (op.type == x86.X86_OP_MEM and op.mem.index == 0)


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
                if tail_jump(i, code):           # a tail call: ESP must be where a ret would leave it
                    totals.add(dep)
                    break
                return None                      # a switch table: the stack after it is not followed
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


def register_saves(ins):
    """pushes of EBX/EBP/ESI/EDI not written before them in the function: saves of the caller's values, also in the
    middle of a function (0x477197's 'push ebx' before the code that uses EBX), no arguments"""
    written, saves = set(), set()
    for i in ins:
        if i.mnemonic == 'push' and i.op_str in ('ebx', 'ebp', 'esi', 'edi') and i.op_str not in written:
            saves.add(i.address)
        elif i.operands and i.operands[0].type == x86.X86_OP_REG and i.mnemonic not in ('push', 'pop', 'cmp', 'test'):
            written.add(i.reg_name(i.operands[0].reg))
    return saves


def pushes_since_call(ins, k, preds, saves=()):
    """dwords pushed (or made room for with sub esp) between the last call (or jump, ret, join of paths) and the
    call at ins[k], whatever else lies between (x87 code between the pushes of the arguments: 0x4E17FA); None when
    the walk reaches the function's start (its own pushes are saves) or ESP changes otherwise"""
    n = 0
    for j in range(k - 1, -1, -1):
        i = ins[j]
        m = i.mnemonic
        if m == 'push':
            n += i.address not in saves
        elif m == 'call':
            # a call on an object on the stack ('mov ecx, esp', 'lea ecx, [esp+N]' before it) may build an argument
            # of this one in place: 0x48BA70 takes a std::string by value, copy-constructed at ESP
            # (not a local deeper in the frame: 0x4C8CB6 sets a string at [esp+0xbc])
            for b in ins[max(0, j - 4):j]:
                if (b.mnemonic == 'mov' and b.op_str == 'ecx, esp') or \
                        (b.mnemonic == 'lea' and b.op_str.startswith('ecx, [esp') and b.operands[1].mem.disp < 0x40):
                    return None
            return n
        elif m in ('pop', 'leave') or m.startswith(('ret', 'j', 'loop')):
            return n
        elif m == 'sub' and i.operands[0].type == x86.X86_OP_REG and i.operands[0].reg == ESP and \
                i.operands[1].type == x86.X86_OP_IMM:
            n += i.operands[1].imm // 4          # room for arguments stored with mov/fstp (0x42BC0D: two floats)
        elif i.operands and i.operands[0].type == x86.X86_OP_REG and i.operands[0].reg == ESP:
            return None
        if len(preds.get(i.address, [])) > 1 or (j and ins[j - 1].address not in preds.get(i.address, [])):
            return n
    return None


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


def reg_import(ins, k):
    """the IAT slot a 'call reg' calls through: the register's last write before it is 'mov reg, [slot]' (MSVC
    keeps an import used several times in a register: 0x4323E0 calls std::operator+ twice as 'call esi' and
    removes both argument lists with one 'add esp, 0x18' after the second)"""
    op = ins[k].operands[0]
    if op.type != x86.X86_OP_REG:
        return None
    for j in range(k - 1, -1, -1):
        i = ins[j]
        try:
            written = i.regs_access()[1]
        except Exception:
            return None
        if op.reg in written:
            m = i.operands[1] if i.mnemonic == 'mov' and len(i.operands) == 2 else None
            if m is not None and m.type == x86.X86_OP_MEM and m.mem.base == 0 and m.mem.index == 0 and \
                    m.mem.disp in imports:
                return m.mem.disp
            return None
    return None


def padding(i):
    """alignment filler the code jumps over: int3, nop, 'lea r, [r+0]', 'mov r, r' (0x4212D8 'lea esp, [esp]')"""
    if i.mnemonic in ('int3', 'nop'):
        return True
    ops = i.operands
    if i.mnemonic == 'lea' and ops[0].type == x86.X86_OP_REG and ops[1].mem.base == ops[0].reg and \
            ops[1].mem.index == 0 and ops[1].mem.disp == 0:
        return True
    return i.mnemonic == 'mov' and len(ops) == 2 and ops[0].type == x86.X86_OP_REG and \
        ops[1].type == x86.X86_OP_REG and ops[0].reg == ops[1].reg


exact = set()       # the calls callee_pops solved from a single path to a ret (not the frame-depth guess)


def seh_frame(code, start):
    """the prologue of MSVC's exception frame on ESP: push -1; push HANDLER; mov eax, fs:[0]"""
    i = code.get(start)
    if not i or i.mnemonic != 'push' or i.operands[0].type != x86.X86_OP_IMM or i.operands[0].imm & 0xFFFFFFFF != 0xFFFFFFFF:
        return False
    j = code.get(start + i.size)
    if not j or j.mnemonic != 'push' or j.operands[0].type != x86.X86_OP_IMM:
        return False
    k = code.get(j.address + j.size)
    return bool(k) and k.mnemonic == 'mov' and 'fs:[0]' in k.op_str


def seh_state(code, start):
    """the depth of the exception state slot: the frame on ESP at the entry (-4), or after an aligned EBP frame
    ('push ebp; mov ebp, esp; and esp, -8; push -1; push HANDLER; mov eax, fs:[0]': -8, 0x4C8B70); else None"""
    if seh_frame(code, start):
        return -4
    p, ins = start, []
    for _ in range(3):
        i = code.get(p)
        if not i:
            return None
        ins.append(i)
        p += i.size
    if [x.mnemonic for x in ins] == ['push', 'mov', 'and'] and ins[0].op_str == 'ebp' and \
            ins[1].op_str == 'ebp, esp' and ins[2].op_str.startswith('esp, ') and seh_frame(code, p):
        return -8
    return None


STATE = [-4]        # the state slot's depth in the function being solved (seh_state)
CONSTS = {}         # registers holding one constant all through the function being solved (const_regs)


def const_regs(code):
    """EBX/EBP/ESI/EDI that every write in the function sets to the same constant ('or ebp, 0xffffffff' kept for
    the exception state's -1: 0x4C8B70 writes 'mov [esp+0x344], ebp')"""
    vals = {}
    for i in code.values():
        if not i.operands or i.operands[0].type != x86.X86_OP_REG or i.mnemonic in ('push', 'cmp', 'test'):
            continue
        r = i.operands[0].reg
        if r not in (x86.X86_REG_EBX, x86.X86_REG_EBP, x86.X86_REG_ESI, x86.X86_REG_EDI):
            continue
        if i.mnemonic == 'pop' or (i.mnemonic == 'mov' and i.op_str == 'ebp, esp'):    # (restores, the frame)
            continue
        if i.mnemonic == 'or' and i.operands[1].type == x86.X86_OP_IMM and i.operands[1].imm & 0xFFFFFFFF == 0xFFFFFFFF:
            v = 0xFFFFFFFF
        elif i.mnemonic == 'mov' and i.operands[1].type == x86.X86_OP_IMM:
            v = i.operands[1].imm & 0xFFFFFFFF
        elif i.mnemonic == 'xor' and i.operands[1].type == x86.X86_OP_REG and i.operands[1].reg == r:
            v = 0
        else:
            v = None
        vals.setdefault(r, set()).add(v)
    return {r: v.pop() for r, v in vals.items() if len(v) == 1 and None not in v}


ORDER = []          # the addresses of the function being solved, in order (for reg_const)


def reg_const(i):
    """the constant a callee-saved register holds at i: its last write before i, within 80 instructions, is
    'or r, -1', 'mov r, imm' or 'xor r, r' (0x4C8B70 keeps the state's -1 in EBP for a while: 'or ebp, 0xffffffff'
    ... 'mov [esp+0x344], ebp' after two calls)"""
    import bisect
    r = i.operands[1].reg
    if r not in (x86.X86_REG_EBX, x86.X86_REG_EBP, x86.X86_REG_ESI, x86.X86_REG_EDI) or not ORDER:
        return None
    k = bisect.bisect_left(ORDER[0], i.address)
    code = ORDER[1]
    for j in range(k - 1, max(-1, k - 80), -1):
        w = code[ORDER[0][j]]
        if not w.operands or w.operands[0].type != x86.X86_OP_REG or w.operands[0].reg != r or \
                w.mnemonic in ('push', 'cmp', 'test'):
            continue
        if w.mnemonic == 'or' and w.operands[1].type == x86.X86_OP_IMM and w.operands[1].imm & 0xFFFFFFFF == 0xFFFFFFFF:
            return 0xFFFFFFFF
        if w.mnemonic == 'mov' and w.operands[1].type == x86.X86_OP_IMM:
            return w.operands[1].imm & 0xFFFFFFFF
        if w.mnemonic == 'xor' and w.operands[1].type == x86.X86_OP_REG and w.operands[1].reg == r:
            return 0
        return None
    return None


def store_value(i):
    """the value 'mov [esp+N], x' stores: an immediate or a constant register (CONSTS, reg_const), else None"""
    o = i.operands[1]
    if o.type == x86.X86_OP_IMM:
        return o.imm & 0xFFFFFFFF
    if o.type == x86.X86_OP_REG and o.reg in CONSTS:
        return CONSTS[o.reg]
    if o.type == x86.X86_OP_REG:
        return reg_const(i)
    return None


def state_store(i):
    """N of 'mov byte/dword ptr [esp+N], imm' with a value an exception state can have, else None"""
    if i.mnemonic != 'mov' or len(i.operands) != 2 or i.operands[0].type != x86.X86_OP_MEM or \
            store_value(i) is None:
        return None
    m = i.operands[0].mem
    if m.base != ESP or m.index != 0 or i.operands[0].size not in (1, 4):
        return None
    v = store_value(i)
    if i.operands[0].size == 4 and not (v < 0x100 or v == 0xFFFFFFFF):
        return None
    return m.disp


def state_write_depth(code, p, known, limit=60, local=None, passed=None):
    """depth right after a call at p from the first exception-state write on the straight path from it (ESP
    changes on the way all known), None when there is none before a branch target is left or something unknown.
    With local (call -> its local guess) the path may go through calls not known yet, taken to pop that; they go
    into passed"""
    acc = 0
    for _ in range(limit):
        i = code.get(p)
        if i is None or i.mnemonic.startswith('ret') or i.mnemonic in ('int3', 'hlt'):
            return None
        n = state_store(i)
        if n is not None:
            return STATE[0] - n - acc
        if i.mnemonic == 'mov' and i.op_str == 'ebp, esp':
            return None
        e = effect(i, code, known)
        if e is STOP and local and i.address in local and passed is not None and len(passed) < 3:
            e = local[i.address]
            passed.append(i.address)
        if e is STOP:
            return None
        acc += e
        if i.mnemonic == 'jmp':
            if i.operands[0].type == x86.X86_OP_IMM and i.operands[0].imm in code:
                p = i.operands[0].imm
                continue
            return None
        p = i.address + i.size
    return None


def state_ok(code, d, a):
    """a dword write of -1 to [esp+N] (leaving every try block: the state's commonest write) lands on the state, and
    nothing takes the state's address: 'lea edx, [esp+0x44]' there was the function's own parameter, reused for a
    result, and the write after it into the same slot no state (0x4CAA48 pops 28, not 20)"""
    i = code[a]
    if i.mnemonic == 'lea' and i.operands[1].mem.base == ESP and i.operands[1].mem.index == 0:
        return d[a] + i.operands[1].mem.disp != STATE[0]
    n = state_store(i)
    return n is None or i.operands[0].size != 4 or store_value(i) != 0xFFFFFFFF or d[a] + n == STATE[0]


def deferred_cleanup(code):
    """a call to a caller-pop function with pushes since the call before it and no 'add esp' after it: MSVC cleans
    several calls up with one 'add esp' later (0x46C53B's five arguments): statements do not start at one depth"""
    pushed = False
    for a in sorted(code):
        i = code[a]
        if i.mnemonic == 'push':
            pushed = True
        elif i.mnemonic == 'call':
            if pushed and i.operands[0].type == x86.X86_OP_IMM and pops.get(i.operands[0].imm) == 0 and \
                    cleanup_after(code.get, a + i.size) < 0 and not noreturn_after(code, a + i.size):
                return True
            pushed = False
        elif i.mnemonic.startswith(('j', 'ret')):
            pushed = False
    return False


def noreturn_after(code, p):
    """the call does not come back: int3 padding or another function right after it"""
    i = code.get(p)
    return i is None or i.mnemonic == 'int3'


def prologue_frame(code, start, limit=24):
    """depth after the prologue: the straight code from the entry to the first call or branch, its pushes of
    EBX/EBP/ESI/EDI not written yet (saves: the caller's values), a first 'push ecx' (room for a local) and 'sub esp,
    N'; None if anything else changes ESP"""
    dep, frame, written, p = 0, 0, set(), start
    for n in range(limit):
        i = code.get(p)
        if i is None or i.mnemonic == 'call' or i.mnemonic.startswith(('j', 'ret', 'loop')):
            break
        m, ops = i.mnemonic, i.operands
        if m == 'push':
            dep -= 4
            r = i.op_str
            if r in ('ebx', 'ebp', 'esi', 'edi') and r not in written or (r == 'ecx' and n == 0) or \
                    (ops[0].type == x86.X86_OP_IMM and n < 2 and seh_frame(code, start)) or \
                    (r == 'eax' and seh_frame(code, start) and n == 3):
                frame = dep
        elif m == 'sub' and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP and ops[1].type == x86.X86_OP_IMM:
            dep -= ops[1].imm
            frame = dep
        elif ops and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP and not (m == 'mov' and 'fs:' in i.op_str):
            return None
        elif m == 'mov' and i.op_str.startswith('dword ptr fs:'):
            pass
        if ops and ops[0].type == x86.X86_OP_REG and m not in ('push', 'cmp', 'test'):
            written.add(i.reg_name(ops[0].reg))
        p = i.address + i.size
    return frame


def callee_pops(code, start, calls, cleanup, fixed=None, local=None):
    """bytes popped by each callee-pop indirect call, from the ESP balance (resolved in rounds: one call's pop can
    be needed to follow the stack to the next one); fixed: pops already known (imports called through a register)"""
    known = {a: 0 for a in calls if cleanup[a] >= 0}
    known.update(fixed or {})
    exact.clear()
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
                exact.add(a)
                new = True
        if not new:
            break
    # chains of indirect calls in a function with an exception frame on ESP ('push -1; push handler; mov eax, fs:[0]'):
    # its state variable sits right below the return address (depth -4), and the code writes it after every object
    # built or destroyed ('mov byte/dword ptr [esp+N], state'): the first such write after a call, with only known
    # ESP changes between, tells the depth after the call (0x424330: five virtual calls in a row, the prologue's
    # 'push edi' among the pushes before the first).  Kept only if the whole function then agrees.
    if seh_state(code, start) is not None:
        STATE[0] = seh_state(code, start)
        CONSTS.clear()
        CONSTS.update(const_regs(code))
        ORDER[:] = [sorted(code), code]
        anch = dict(known)
        for _ in range(8):
            d = depths(code, start, anch)
            new = False
            for a in calls:
                if a in anch or a not in d:
                    continue
                passed = []
                after = state_write_depth(code, a + code[a].size, anch, local=local, passed=passed)
                if after is None:
                    continue
                p = after - d[a]
                # (through calls not known yet only if their local guesses and this one's give the anchor's depth
                # exactly: 0x4C8D1F's two floats and 0x4C8D34's one argument before the state write after both)
                if passed and (a not in local or p != local[a]):
                    continue
                if 0 <= p <= 64 and p % 4 == 0:
                    anch[a] = p
                    anch.update({c: local[c] for c in passed})
                    new = True
            if not new:
                break
        if DEBUG == start:
            print('anchors', {'%X' % k: v for k, v in anch.items() if k not in known}, 'known', {'%X' % k: v for k, v in known.items()})
        if len(anch) > len(known):
            bad = []
            d = depths(code, start, anch, bad)
            # (code past calls still unknown is not reached yet: the frame depth below may solve those)
            if not bad and all(state_ok(code, d, a) for a in d):
                known = anch
            elif DEBUG == start:
                print("anchors rejected: bad %s state %s" % (["%X" % b for b in bad], ["%X" % a for a in d if not state_ok(code, d, a)]))
    # the rest (chains of indirect calls): each callee taken to pop what brings ESP back to the frame depth (where
    # statements start), accepted only if the whole function then agrees: every ret at the return address, the same
    # depth wherever paths meet, every instruction reached.  The frame depth: the prologue's (its saves of registers
    # not written yet, also after other instructions: 0x425620's 'push edi' after 'mov esi, ecx; mov eax, [esi]'),
    # else the commonest depth in the function
    # Where MSVC cleans up after several calls at once (deferred_cleanup) statements start at other depths: there
    # each callee is first taken to pop what was pushed since the call before it (0x46C556 pops 16, not the 36 down
    # to the frame depth that also hold 0x46C53B's arguments), elsewhere that comes last (an argument that is a call's
    # result has the arguments after it pushed before that call)
    # Not where the epilogue takes ESP back from EBP ('mov esp, ebp', 'leave'): the balance proves nothing there
    # (0x405E90 never cleans up after its caller-pop calls)
    rest = [a for a in calls if a not in known]
    if rest and not any(i.mnemonic == 'leave' or (i.mnemonic == 'mov' and i.op_str == 'esp, ebp') for i in code.values()):
        d = depths(code, start, known)
        if d:
            vals = list(d.values())
            frames = [prologue_frame(code, start)]
            frames += [f for f in [max(set(vals), key=vals.count)] if f not in frames]
            frames = [f for f in frames if f is not None] + ['local']
            defer = deferred_cleanup(code)
            if defer:
                frames = frames[:1] + ['local'] if frames[0] != 'local' else frames
                frames.reverse()
            bad, guess, ok = ['ceiling'], {}, []
            for frame in frames:
                guess = dict(known)
                if frame == 'local':
                    guess.update({a: local[a] for a in rest if local and a in local})
                # (the local guess takes the frame depth where it has nothing: the first call, pushes since the
                # entry being saves)
                fill = frame if frame != 'local' else prologue_frame(code, start)
                for _ in range(len(rest) + 1):
                    if fill is None:
                        break
                    d = depths(code, start, guess)
                    for a in rest:
                        if a in d and a not in guess:
                            guess[a] = fill - d[a]
                # ESP never above the frame depth after a call (the saved registers are there): a known callee
                # taking more than was pushed since the guessed one before it took the rest from what that one was
                # given (0x4EE6DC pops nothing: the 'push eax' before it is 0x4C2E10's second argument), so that one
                # pops less
                fr = frame if frame != 'local' else prologue_frame(code, start)
                if fr is not None:
                    for _ in range(len(rest) + 2):
                        d = depths(code, start, guess)
                        over = next(((a, d[a] + effect(code[a], code, guess) - fr) for a in sorted(d)
                                     if code[a].mnemonic == 'call' and effect(code[a], code, guess) is not STOP and
                                     d[a] + effect(code[a], code, guess) > fr), None)
                        if not over:
                            break
                        prev = max((c for c in rest if c < over[0] and c in guess), default=None)
                        if prev is None or guess[prev] < over[1] or any(
                                code[b].mnemonic == 'call' and b not in guess and
                                code[b].operands[0].type != x86.X86_OP_IMM for b in d if prev < b < over[0]):
                            guess = None
                            break
                        guess[prev] -= over[1]
                    else:
                        guess = None
                    if guess is None:
                        bad, guess = ['ceiling'], {}
                        continue
                bad = []
                d = depths(code, start, guess, bad)
                if DEBUG == start:
                    print('frame %s guess %s bad %s unreached %s' % (frame, {'%X' % k: v for k, v in guess.items()},
                          ['%X' % b for b in bad], ['%X' % a_ for a_, i in code.items() if a_ not in d and not padding(i)][:10]))
                if not bad and all(a in guess and guess[a] >= 0 and guess[a] % 4 == 0 for a in rest) and \
                        all(a_ in d or padding(i) for a_, i in code.items()):
                    ok.append((frame, guess))
            # each guess can be wrong where the other is right and still balance (a register saved in the middle,
            # 0x474B1A's 'push ebx' before a loop, misleads the frame depth; a call's result pushed for the next one
            # the pushes since the call before): a callee's pop is kept where the guesses that balance agree
            # (a frame depth guess alone is not taken where calls are cleaned up later)
            if ok and (len(ok) > 1 or (POLICY == 'agree1' and not (defer and ok[0][0] != 'local'))):
                known = dict(known)
                known.update({a: ok[0][1][a] for a in rest if all(g[a] == ok[0][1][a] for _, g in ok)})
            elif not ok:
                if STATS is not None:
                    STATS[('merge/ret' if bad else 'unsolved' if any(a not in guess for a in rest) else
                           'negative' if any(guess[a] < 0 or guess[a] % 4 for a in rest) else 'unreached')] += 1
                    STATS['f %X %s' % (start, 'bad' if bad else '')] += 1
    return known


# virtual calls whose callee pop the balance leaves open: the functions at that offset of every vftable of the game
# (symbols/GAME.sym), when their ret pops all agree.  Only for calls with ECX set (a method of the game's classes:
# COM objects such as Direct3D's pass this on the stack and have no vftable in the symbols) and no more arguments
# than the pushes before the call.
vt_pops = {}
DEBUG = int(os.environ.get('ICALLS_DEBUG', '0'), 16)
import collections
STATS = collections.Counter() if os.environ.get('ICALLS_STATS') else None
POLICY = os.environ.get('ICALLS_POLICY', 'agree1')   # a function to print the balance of
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


# virtual calls on the method's own object ('mov eax, [esi]; mov ecx, esi; call [eax+0x30]' with esi = this): every
# override of one slot has the signature of the slot, so the pop of any implementation known in the class of this
# (from RTTI, out/GAME_rtti.json of rtti.py) is the pop of the call.  The class of this: the one each vftable
# holding the method has at the method's subobject (a base at that offset, not virtual), the most derived of them;
# the slot must be one of that class's own (an offset past its vftable belongs to a derived class: a sibling may
# use it for another method).
rt_group, rt_len, func_class = {}, {}, {}
vt_sub = []                     # (functions, classes of the subobject the vftable is for)
if len(sys.argv) > 7:
    import json
    for c in json.load(open(sys.argv[7])):
        for v in c['vtables']:
            sub = {b['name'] for b in c['bases'] if b['mdisp'] == v['offset'] and b['pdisp'] == -1}
            fl = [int(x, 16) for x in v['funcs']]
            vt_sub.append((fl, sub))
            if v['offset'] == 0:
                rt_len[c['name']] = max(rt_len.get(c['name'], 0), len(fl))
    for fl, sub in vt_sub:
        for t in sub:
            rt_group.setdefault(t, []).append(fl)
    inter = {}
    for fl, sub in vt_sub:
        for f in set(fl):
            inter[f] = inter[f] & sub if f in inter else set(sub)
    for f, ts in inter.items():
        if ts:
            # the most derived: the class with the fewest vftables taking it as a base
            func_class[f] = min(ts, key=lambda t: (len(rt_group.get(t, ())), t))


def class_slot_pop(cls, off):
    """the pop every known implementation of slot off in the vftables of cls and its derived classes agrees on"""
    if off is None or off % 4 or off // 4 >= rt_len.get(cls, 0):
        return None
    seen = {pops.get(fl[off // 4]) for fl in rt_group.get(cls, ()) if off // 4 < len(fl)}
    seen.discard(None)
    return seen.pop() if len(seen) == 1 else None


def this_regs(ins, start):
    """registers holding this for the whole function: 'mov esi, ecx' before any call or other write of ECX, the
    register written nowhere else (but the epilogue's pop)"""
    regs = set()
    for i in ins[:16]:
        if i.mnemonic == 'call':
            break
        if i.mnemonic == 'mov' and i.operands[0].type == x86.X86_OP_REG and i.op_str.endswith(', ecx') and \
                i.op_str.split(',')[0] in ('esi', 'edi', 'ebx', 'ebp'):
            regs.add(i.op_str.split(',')[0])
        elif i.operands and i.operands[0].type == x86.X86_OP_REG and i.op_str.split(',')[0] == 'ecx' and \
                i.mnemonic not in ('push', 'cmp', 'test'):
            break
    for r in list(regs):
        if sum(1 for i in ins if i.operands and i.operands[0].type == x86.X86_OP_REG and
               i.op_str.split(',')[0] == r and i.mnemonic not in ('push', 'pop', 'cmp', 'test')) != 1:
            regs.discard(r)
    return regs


def this_vcall(ins, k, regs):
    """slot offset of a virtual call on this ('mov eax, [esi]; ...; mov ecx, esi; call [eax+off]' or through a
    register loaded from [eax+off]), None if the object or the slot is not plain"""
    i = ins[k]
    op = i.operands[0]
    win = []
    for j in range(k - 1, max(k - 10, -1), -1):
        if ins[j].mnemonic == 'call' or ins[j].mnemonic.startswith('j'):
            break
        win.append(ins[j])
    def last_write(reg, before=None):
        for w in win:
            if before is not None and w.address >= before:
                continue
            if w.operands and w.operands[0].type == x86.X86_OP_REG and w.op_str.split(',')[0] == reg and \
                    w.mnemonic not in ('push', 'cmp', 'test'):
                return w
        return None
    if op.type == x86.X86_OP_MEM and op.mem.index == 0 and op.mem.base:
        vt, off = i.reg_name(op.mem.base), op.mem.disp
        at = i.address
    elif op.type == x86.X86_OP_REG:
        w = last_write(i.reg_name(op.reg))
        if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index:
            return None
        vt, off, at = w.reg_name(w.operands[1].mem.base), w.operands[1].mem.disp, w.address
    else:
        return None
    w = last_write(vt, at)
    if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index or \
            w.operands[1].mem.disp != 0:
        return None
    obj = w.reg_name(w.operands[1].mem.base)
    if obj not in regs:
        return None
    e = last_write('ecx')
    if not e or e.mnemonic != 'mov' or e.op_str != 'ecx, ' + obj:
        return None
    return off


# virtual calls on an object whose vftable is known where the call is made: one just built (the constructor called on
# it, or the result of the constructor, which returns this: 'push 0x224; call new; ...; mov ecx, eax; call ctor; mov
# edi, eax', 0x4C8C34) or one given its vftable in this function: the slot of that vftable is the callee itself
vt_funcs = {}
if len(sys.argv) > 7:
    for c in json.load(open(sys.argv[7])):
        for v in c['vtables']:
            vt_funcs[int(v['vt'], 16)] = [int(x, 16) for x in v['funcs']]
_ctor_vt = {}


def ctor_vt(f):
    """the vftable a constructor leaves in its object: its last store of one at this+0, when it returns this"""
    if f in _ctor_vt:
        return _ctor_vt[f]
    _ctor_vt[f] = None
    if f not in sizes:
        return None
    try:
        ins = list(md.disasm(pe.read(f, sizes[f]), f))
    except Exception:
        return None
    regs = {'ecx'}
    for i in ins[:16]:
        if i.mnemonic == 'mov' and i.op_str.endswith(', ecx') and i.operands[0].type == x86.X86_OP_REG:
            regs.add(i.op_str.split(',')[0])
        elif i.mnemonic == 'call' or (i.operands and i.operands[0].type == x86.X86_OP_REG and
                                      i.op_str.split(',')[0] == 'ecx' and i.mnemonic not in ('push', 'cmp', 'test')):
            break
    regs = {r for r in regs if r == 'ecx' or sum(1 for i in ins if i.operands and i.operands[0].type == x86.X86_OP_REG
                                                 and i.op_str.split(',')[0] == r and
                                                 i.mnemonic not in ('push', 'pop', 'cmp', 'test')) == 1}
    vt = None
    for i in ins:
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == x86.X86_OP_MEM and \
                i.operands[1].type == x86.X86_OP_IMM and i.operands[0].mem.disp == 0 and \
                not i.operands[0].mem.index and i.reg_name(i.operands[0].mem.base) in regs and \
                i.operands[1].imm in vt_funcs:
            vt = i.operands[1].imm
    if vt is not None and any(i.mnemonic == 'mov' and i.op_str in ['eax, ' + r for r in regs if r != 'ecx'] for i in ins):
        _ctor_vt[f] = vt
    return _ctor_vt[f]


def known_vcall(ins, k):
    """the callee of a virtual call on an object whose vftable is known here, None if not plain"""
    i = ins[k]
    op = i.operands[0]
    lo = max(k - 12, 0)
    def last_write(reg, before):
        for j in range(before - 1, lo - 1, -1):
            w = ins[j]
            if w.mnemonic == 'call' or w.mnemonic.startswith('j'):
                return None
            if w.operands and w.operands[0].type == x86.X86_OP_REG and w.op_str.split(',')[0] == reg and \
                    w.mnemonic not in ('push', 'cmp', 'test'):
                return j
        return None
    if op.type == x86.X86_OP_MEM and op.mem.index == 0 and op.mem.base:
        vt, off, at = i.reg_name(op.mem.base), op.mem.disp, k
    elif op.type == x86.X86_OP_REG:
        j = last_write(i.reg_name(op.reg), k)
        w = ins[j] if j is not None else None
        if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index:
            return None
        vt, off, at = w.reg_name(w.operands[1].mem.base), w.operands[1].mem.disp, j
    else:
        return None
    j = last_write(vt, at)
    w = ins[j] if j is not None else None
    if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index or \
            w.operands[1].mem.disp != 0 or off % 4:
        return None
    obj = w.reg_name(w.operands[1].mem.base)
    if obj != 'ecx':
        e = last_write('ecx', k)
        if e is None or ins[e].mnemonic != 'mov' or ins[e].op_str != 'ecx, ' + obj:
            return None
    # where the object came from: back through the code before the load of its vftable (a null tested and set on
    # another path, 'xor edi, edi', does not count)
    found = None
    for j in range(j - 1, max(j - 80, -1), -1):
        x = ins[j]
        if x.mnemonic in ('ret', 'int3'):
            break
        if x.mnemonic == 'call':
            t = x.operands[0].imm if x.operands[0].type == x86.X86_OP_IMM else None
            ce = last_write('ecx', j)
            if t is not None and (obj == 'eax' or (ce is not None and ins[ce].op_str == 'ecx, ' + obj)):
                found = ctor_vt(t)
                break
            if obj in ('eax', 'ecx', 'edx'):
                break
            continue
        if x.mnemonic == 'mov' and len(x.operands) == 2 and x.operands[0].type == x86.X86_OP_MEM and \
                x.operands[1].type == x86.X86_OP_IMM and x.operands[0].mem.disp == 0 and \
                not x.operands[0].mem.index and x.reg_name(x.operands[0].mem.base) == obj and \
                x.operands[1].imm in vt_funcs:
            found = x.operands[1].imm
            break
        if x.operands and x.operands[0].type == x86.X86_OP_REG and x.op_str.split(',')[0] == obj and \
                x.mnemonic not in ('push', 'cmp', 'test'):
            if x.mnemonic == 'xor' and x.op_str == obj + ', ' + obj:
                continue
            if x.mnemonic == 'mov' and x.operands[1].type == x86.X86_OP_REG:
                obj = x.op_str.split(', ')[1]
                continue
            break
    if found is None or off // 4 >= len(vt_funcs[found]):
        return None
    return vt_funcs[found][off // 4]


# virtual calls on an object kept in a field of this: the field's class is the one the class's methods store there
# (the result of a constructor: 'call new; mov ecx, eax; call CTOR; mov [esi+0x1bc], eax'), the pop the one every
# implementation of the slot in that class and the classes derived from it agrees on.  A method's class: its
# vftables' (RTTI) or its name's (symbols/GAME.sym 'C::m'); the fields of a base class are the derived class's too.
vt_class, class_bases, fn_named = {}, {}, {}
if len(sys.argv) > 7:
    for c in json.load(open(sys.argv[7])):
        class_bases[c['name']] = [b['name'] for b in c['bases'] if b['pdisp'] == -1 and b['mdisp'] == 0]
        for v in c['vtables']:
            if v['offset'] == 0:
                vt_class[int(v['vt'], 16)] = c['name']
if len(sys.argv) > 5:
    for l in open(sys.argv[5], encoding='utf-8'):
        q = l.split('#')[0].split(None, 2)
        if len(q) == 3 and q[1] == 'f' and '::' in q[2]:
            cn = q[2].strip().rsplit('::', 1)[0]
            if cn in class_bases:
                fn_named[int(q[0], 16)] = cn


def fn_class(f):
    if f in func_class:
        return func_class[f]
    if f in fn_named:
        return fn_named[f]
    v = ctor_vt(f)
    return vt_class.get(v) if v is not None else None


def built_by(ins, k, reg):
    """the class of the object in reg at instruction k when it comes from a constructor just called (the null of
    'new' failing, 'xor reg, reg' on another path, does not count), None otherwise"""
    for j in range(k - 1, max(k - 12, -1), -1):
        x = ins[j]
        if x.mnemonic == 'call':
            if reg == 'eax' and x.operands[0].type == x86.X86_OP_IMM:
                v = ctor_vt(x.operands[0].imm)
                return vt_class.get(v) if v is not None else None
            return None
        if x.mnemonic in ('jmp',) or (x.mnemonic == 'xor' and x.op_str == reg + ', ' + reg):
            continue
        if x.operands and x.operands[0].type == x86.X86_OP_REG and x.op_str.split(',')[0] == reg and \
                x.mnemonic not in ('push', 'cmp', 'test'):
            if x.mnemonic == 'mov' and x.operands[1].type == x86.X86_OP_REG:
                reg = x.op_str.split(', ')[1]
                continue
            return None
    return None


_fields = None


def field_types():
    """(class, offset) -> class of the object its methods store in that field"""
    global _fields
    if _fields is not None:
        return _fields
    votes = collections.defaultdict(set)
    for f, size, _e in funcs:
        cls = fn_class(f)
        if cls is None:
            continue
        try:
            ins = list(md.disasm(pe.read(f, size), f))
        except Exception:
            continue
        tregs = this_regs(ins, f)
        for k, i in enumerate(ins):
            if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == x86.X86_OP_MEM and \
                    i.operands[1].type == x86.X86_OP_REG and i.operands[0].mem.base and not i.operands[0].mem.index \
                    and i.reg_name(i.operands[0].mem.base) in tregs and i.operands[0].mem.disp > 0:
                t = built_by(ins, k, i.reg_name(i.operands[1].reg))
                if t is not None:
                    votes[(cls, i.operands[0].mem.disp)].add(t)
    _fields = {key: v.pop() for key, v in votes.items() if len(v) == 1}
    return _fields


def field_vcall(ins, k, start):
    """the pop of a virtual call on an object loaded from a field of this whose class is known"""
    cls = fn_class(start)
    if cls is None:
        return None
    tregs = this_regs(ins, start)
    i = ins[k]
    op = i.operands[0]
    lo = max(k - 12, 0)
    def last_write(reg, before):
        for j in range(before - 1, lo - 1, -1):
            w = ins[j]
            if w.mnemonic == 'call' or w.mnemonic.startswith('j'):
                return None
            if w.operands and w.operands[0].type == x86.X86_OP_REG and w.op_str.split(',')[0] == reg and \
                    w.mnemonic not in ('push', 'cmp', 'test'):
                return j
        return None
    if op.type == x86.X86_OP_MEM and op.mem.index == 0 and op.mem.base:
        vt, off, at = i.reg_name(op.mem.base), op.mem.disp, k
    elif op.type == x86.X86_OP_REG:
        j = last_write(i.reg_name(op.reg), k)
        w = ins[j] if j is not None else None
        if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index:
            return None
        vt, off, at = w.reg_name(w.operands[1].mem.base), w.operands[1].mem.disp, j
    else:
        return None
    j = last_write(vt, at)
    w = ins[j] if j is not None else None
    if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index or \
            w.operands[1].mem.disp != 0:
        return None
    obj = w.reg_name(w.operands[1].mem.base)
    if obj != 'ecx':
        e = last_write('ecx', k)
        if e is None or ins[e].mnemonic != 'mov' or ins[e].op_str != 'ecx, ' + obj:
            return None
    j = last_write(obj, j)
    w = ins[j] if j is not None else None
    if not w or w.mnemonic != 'mov' or w.operands[1].type != x86.X86_OP_MEM or w.operands[1].mem.index or \
            not w.operands[1].mem.base or w.reg_name(w.operands[1].mem.base) not in tregs:
        return None
    fo = w.operands[1].mem.disp
    fields = field_types()
    for b in class_bases.get(cls, [cls]):
        if (b, fo) in fields:
            return class_slot_pop(fields[(b, fo)], off)
    return None


measured = {}       # call address -> bytes popped, measured (icalltrace.cpp) where the code alone does not tell
if len(sys.argv) > 6:
    for l in open(sys.argv[6]):
        q = l.split()
        if l[0] != '#' and len(q) >= 2:
            measured[int(q[0], 16)] = int(q[1])


# methods of the Direct3D device (the game's global g_d3dDevice, symbols/GAME.sym): what each pops, from the
# argument lists of IDirect3DDevice9 in the mingw-w64 d3d9.h (all 4 bytes each, this on the stack)
dev_pops, DEVICE = {}, None
if len(sys.argv) > 5:
    for l in open(sys.argv[5], encoding='utf-8'):
        q = l.split('#')[0].split()
        if len(q) == 3 and q[1] == 'd' and q[2] == 'g_d3dDevice':
            DEVICE = int(q[0], 16)
    import re as _re
    for hp in ('/usr/i686-w64-mingw32/include/d3d9.h', '/usr/share/mingw-w64/include/d3d9.h'):
        if os.path.exists(hp):
            txt = open(hp, errors='replace').read()
            body = txt[txt.index('DECLARE_INTERFACE_(IDirect3DDevice9,'):]
            body = body[:body.index('};')]
            for k, m in enumerate(_re.finditer(r'STDMETHOD_?\((?:[^()]*)\)\s*\((THIS_?)([^)]*)\)', body)):
                n = 0 if m.group(1) == 'THIS' else m.group(2).count(',') + 1
                dev_pops[4 * k] = 4 * (n + 1)
            break


def device_call(ins, k):
    """the slot of a method call on the Direct3D device: 'mov eax, [g_d3dDevice]; mov ecx, [eax]; ...; push eax;
    call [ecx+0x148]' (the device loaded into the register pushed last, nothing else written to it between)"""
    if DEVICE is None:
        return None
    last = None
    for j in range(k - 1, max(-1, k - 10), -1):
        if ins[j].mnemonic == 'push':
            last = j
            break
    if last is None or ins[last].operands[0].type != x86.X86_OP_REG:
        return None
    r = ins[last].operands[0].reg
    for j in range(last - 1, max(-1, last - 14), -1):
        i = ins[j]
        if i.mnemonic.startswith(('call', 'j', 'ret')):
            return None
        if i.operands and i.operands[0].type == x86.X86_OP_REG and i.operands[0].reg == r:
            o = i.operands[1] if len(i.operands) > 1 else None
            if i.mnemonic == 'mov' and o is not None and o.type == x86.X86_OP_MEM and o.mem.base == 0 and \
                    o.mem.index == 0 and o.mem.disp == DEVICE:
                return vslot(ins, k)
            return None
    return None


def com_call(ins, k, entry=0):
    """a COM method call: the last push before the call is the object whose vftable the call reads ('mov ecx, [eax];
    push eax; call [ecx+0x108]' of Direct3D): this goes on the stack, ECX only holds the vftable.  Pushes of the
    prologue (from entry on: after it) save registers ('push esi; mov esi, ecx; mov eax, [esi]; call [eax+1Ch]' of
    0x426FB0 is a method of this)"""
    last = None
    for j in range(k - 1, max(entry - 1, k - 8), -1):
        m = ins[j].mnemonic
        if m == 'push':
            last = ins[j]
            break
        if not m.startswith(MOVES):
            return False
    if last is None or last.operands[0].type != x86.X86_OP_REG:
        return False
    r = last.operands[0].reg
    # 'push ecx' may only make room for an argument written next ('push ecx; fstp dword [esp]' of 0x4CCAF0, where
    # ECX is this): not the object on the stack
    if r in ECXS:
        return False
    for j in range(ins.index(last) + 1, k):
        for op in ins[j].operands:
            if op.type == x86.X86_OP_MEM and op.mem.base == ESP and op.mem.disp == 0 and op.access & capstone.CS_AC_WRITE:
                return False
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


def infer_direct_pops():
    """bytes popped by functions with no ret of their own to tell (thunks jumping on through a vftable: 0x4205C0
    'mov eax, [ecx+4]; mov eax, [eax+4]; add ecx, 4; jmp eax') from the ESP balance of their callers: the depth
    before a call followed from the entry, the path after it to a ret.  Every caller that tells must agree, and two
    must tell (one for a jump thunk).  A virtual one also from the other implementations of its slot.  Written into
    column 4 of functions.tsv"""
    found = {}
    for _ in range(4):
        votes = collections.defaultdict(list)
        for start, size, _e in funcs:
            if 0x401000 <= start < 0x4205A0:        # (the Lua library, built from its sources)
                continue
            try:
                ins = list(md.disasm(pe.read(start, size), start))
            except Exception:
                continue
            sites = [i for i in ins if i.mnemonic == 'call' and i.operands[0].type == x86.X86_OP_IMM and
                     i.operands[0].imm in pops and pops[i.operands[0].imm] is None]
            if not sites:
                continue
            code = {i.address: i for i in ins}
            d = depths(code, start, {})
            for i in sites:
                if i.address not in d:
                    continue
                t = to_ret(code, i.address + i.size, {})
                if t and len(t) == 1:
                    p = -(d[i.address] + t.pop())
                    votes[i.operands[0].imm].append(p if 0 <= p <= min(64, -d[i.address]) and p % 4 == 0 else None)
        new = {}
        # a virtual function: what the other implementations of its slot in the classes of its vftables pop
        for fl, sub in vt_sub:
            for k, f in enumerate(fl):
                if pops.get(f, 0) is not None or f in new:
                    continue
                seen = {pops.get(g[k]) for t in sub for g in rt_group.get(t, ()) if k < len(g)}
                seen.discard(None)
                if len(seen) == 1 and all(k < rt_len.get(t, 0) for t in sub if t in rt_len):
                    new[f] = seen.pop()
        for f, v in votes.items():
            last = None
            for j in md.disasm(pe.read(f, min(64, sizes[f])), f):
                if j.mnemonic != 'int3':
                    last = j
            thunk = last is not None and last.mnemonic == 'jmp'
            if None not in v and len(set(v)) == 1 and (len(v) >= 2 or thunk):
                new[f] = v[0]
        if not new:
            break
        pops.update(new)
        found.update(new)
    if found:
        rows = open(sys.argv[2]).read().splitlines(True)
        with open(sys.argv[2], 'w') as out:
            for l in rows:
                q = l.split('\t')
                if l[0] != '#' and int(q[0], 16) in found and q[3] == '?':
                    q[3] = str(found[int(q[0], 16)])
                    l = '\t'.join(q)
                out.write(l)
    print('pops of %d functions without a ret from their callers' % len(found))


sizes = {a: s_ for a, s_, _e in funcs}
infer_direct_pops()
with open(sys.argv[3], 'w') as f:
    f.write('# call address\tfunction\tecx set (1/0)\tadd esp after (-1: none)\tpushes right before'
            '\tbytes the callee pops (ESP balance, -1: unknown)\targument dwords pushed since the call before (-1: unknown)'
            '\tESP after the call irrelevant to the decompiled code (1/0)\n')
    n = solved = byvt = ntail = bym = byimp = bynone = bycls = 0
    tails = []
    for start, size, ecx_in in funcs:
        try:
            ins = list(md.disasm(pe.read(start, size), start))
        except Exception:
            continue
        code = {i.address: i for i in ins}
        preds = predecessors(ins, code)
        rows, cleanup, fixed = [], {}, {}
        saves = register_saves(ins)
        # the prologue's pushes save registers (or reserve locals, or are the SEH frame): not arguments of a call
        # with only moves between (0x479885's 'call edx' after 'push ecx; push esi' takes none)
        pe_end = prologue_end(code.get, start)
        entry = next((j for j, x in enumerate(ins) if x.address >= pe_end), len(ins))
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
            for j in range(k - 1, entry - 1, -1):
                m = ins[j].mnemonic
                if m == 'push':
                    pushes += 1
                elif not m.startswith(MOVES):
                    break
            cleanup[i.address] = cl
            com = com_call(ins, k, entry)
            if com:
                ecx = 0             # stdcall with this on the stack
                dv = device_call(ins, k)
                if dv in dev_pops and cl < 0:
                    fixed[i.address] = dev_pops[dv]
            rows.append((i.address, ecx, cl, pushes, None if com else vslot(ins, k), pushes_since_call(ins, k, preds),
                         pushes_since_call(ins, k, preds, saves)))
            slot = reg_import(ins, k)
            if slot is not None:
                fixed[i.address] = imports[slot]
        for a, ecx, pop in tails:
            f.write('%08X\t%08X\t%d\t-1\t0\t%d\n' % (a, start, ecx, pop))
            n += 1
            ntail += 1
        tails.clear()
        if not rows:
            continue
        # nothing pushed since the last call, counted either way: no arguments, nothing to pop (all 203 such sites
        # measured in the game agree); known before the balance, it solves the calls around them
        nopush = {r[0]: 0 for r in rows if cleanup[r[0]] < 0 and r[3] == 0 and r[5] == 0 and r[0] not in fixed}
        # virtual calls on this, from the class (before the balance: they solve the calls around them)
        clsfix = {}
        if start in func_class:
            tregs = this_regs(ins, start)
            for r in rows:
                if cleanup[r[0]] < 0 and r[1] == 1 and r[0] not in fixed:
                    t = class_slot_pop(func_class[start], this_vcall(ins, ins.index(code[r[0]]), tregs))
                    # (no more than what was pushed or made room for: 'sub esp, 8' for two floats, 0x4266BB)
                    if t is not None and t // 4 <= max(r[3], r[5] or 0):
                        clsfix[r[0]] = t
        for r in rows:
            if cleanup[r[0]] < 0 and r[1] == 1 and r[0] not in fixed and r[0] not in clsfix:
                c = known_vcall(ins, ins.index(code[r[0]]))
                t = pops.get(c) if c is not None else None
                if t is not None and t // 4 <= max(r[3], r[5] or 0):
                    clsfix[r[0]] = t
                    if STATS is not None:
                        STATS['vtable known here'] += 1
        for r in rows:
            if cleanup[r[0]] < 0 and r[1] == 1 and r[0] not in fixed and r[0] not in clsfix:
                t = field_vcall(ins, ins.index(code[r[0]]), start)
                if t is not None and t // 4 <= max(r[3], r[5] or 0):
                    clsfix[r[0]] = t
                    if STATS is not None:
                        STATS['field of this'] += 1
        known = callee_pops(code, start, [r[0] for r in rows], cleanup, {**fixed, **nopush, **clsfix},
                            {r[0]: 4 * r[6] for r in rows if r[6] is not None})
        # columns 7 and 8: the argument dwords pushed since the call before (-1 unknown), and whether ESP after
        # the call matters to the decompiled code (0: an EBP frame, or nothing ESP-relative after it): where it
        # does not, a call that restores ESP is right whatever the callee pops (ghidra/ICallOverride.java,
        # gh_call_any of rebuild/rt_support.c)
        ebp_frame = any(x.mnemonic == 'mov' and x.op_str == 'ebp, esp' for x in ins[:8])
        def esp_safe(a):
            if ebp_frame:
                return 1
            for x in ins:
                if x.address > a and not x.mnemonic.startswith(('push', 'pop')) and any(
                        o.type == x86.X86_OP_MEM and o.mem.base == ESP and o.mem.disp != 0 for o in x.operands):
                    return 0
            return 1
        extra = {r[0]: '\t%d\t%d' % (-1 if r[6] is None else r[6], esp_safe(r[0])) for r in rows}
        for a, ecx, cl, pushes, off, outstanding, _ in rows:
            if a in fixed:
                f.write('%08X\t%08X\t%d\t%d\t%d\t%d%s\n' % (a, start, ecx, cl, pushes, fixed[a] if cl < 0 else 0, extra[a]))
                n += 1
                byimp += 1
                continue
            pop = known.get(a, -1) if cl < 0 else 0
            # the balance fixes only the sum of the pops between two known depths: a callee 'popping nothing' after
            # pushes is as likely another call taking them (0x5B52A0: two COM calls in a row, the second given 0
            # once the first was known; it pops its four arguments)
            # (a pop the path to a ret fixes alone is exact, 0 included: 0x45B8C2's getter after a saving 'push edi')
            bycls += a in clsfix
            if cl < 0 and pop == 0 and pushes > 0 and a not in exact and a not in clsfix:
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
            if a in nopush:
                bynone += 1
            f.write('%08X\t%08X\t%d\t%d\t%d\t%d%s\n' % (a, start, ecx, cl, pushes, pop, extra[a]))
            n += 1
print('%d indirect calls (%d of them tail jumps), the pop of %d callee-pop ones from the ESP balance, %d from the '
      'vftables (%d offsets agree), %d from the class of this, %d measured, %d imports called through a register, %d '
      'with nothing pushed' % (n, ntail, solved, byvt, len(vt_pops), bycls, bym, byimp, bynone))
if STATS is not None:
    print('frame depth guesses rejected:', dict(STATS))
