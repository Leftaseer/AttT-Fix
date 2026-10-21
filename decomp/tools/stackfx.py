# Small x86 stack facts shared by the machine-code tools (capstone instructions with detail).
from capstone import x86

ESP = x86.X86_REG_ESP


def touches_esp(i):
    """the instruction changes ESP (or uses it implicitly beyond addressing through it)"""
    if i.mnemonic in ('push', 'pop', 'pushal', 'popal', 'pushfd', 'popfd', 'leave', 'enter') or \
            i.mnemonic.startswith(('call', 'ret', 'j', 'loop')):
        return True
    for op in i.operands:
        if op.type == x86.X86_OP_REG and op.reg == ESP:
            return True
    return False


def cleanup_after(insn, a, limit=4):
    """N of the caller's 'add esp, N' after the call ending at a (the address after it), -1 if there is none: the
    compiler may put a few instructions that do not touch ESP in between ('call ebx; add edi, 1; add esp, 4' in
    0x5B54B0, where the callee was taken for one that pops its argument).  insn(address) -> instruction or None."""
    for _ in range(limit):
        i = insn(a)
        if i is None:
            return -1
        o = i.operands
        if i.mnemonic == 'add' and len(o) == 2 and o[0].type == x86.X86_OP_REG and o[0].reg == ESP:
            return o[1].imm if o[1].type == x86.X86_OP_IMM else -1
        if touches_esp(i):
            return -1
        a = i.address + i.size
    return -1


def switch_targets(i, u32, lo, hi, limit=512):
    """the case addresses of a switch jump 'jmp [reg*4 + table]': the table's entries while they point into
    [lo, hi) (the function's code); [] for other instructions.  u32(address) -> dword or None."""
    if i.mnemonic != 'jmp' or not i.operands or i.operands[0].type != x86.X86_OP_MEM:
        return []
    m = i.operands[0].mem
    if m.base != 0 or m.index == 0 or m.scale != 4 or not m.disp:
        return []
    out = []
    for k in range(limit):
        v = u32(m.disp + 4 * k)
        if v is None or not (lo <= v < hi):
            break
        out.append(v)
    return out


def prologue_end(insn, start, limit=24):
    """Address after the prologue at start: pushes of registers (saves, or room for locals), 'push ebp; mov ebp,
    esp', 'sub esp, N' and the SEH frame ('push -1; push handler; mov eax, fs:[0]; push eax; mov fs:[0], esp').
    Pushes up to there are not arguments of a call that follows with only moves between (0x479870 'push ecx;
    push esi; ... call edx', 0x433150 the same after an SEH frame)."""
    a, seh = start, 0
    for _ in range(limit):
        i = insn(a)
        if i is None:
            break
        m, ops = i.mnemonic, i.operands
        if m == 'push' and ops[0].type == x86.X86_OP_REG:
            pass
        elif m == 'push' and ops[0].type == x86.X86_OP_IMM and a == start and (ops[0].imm & 0xFFFFFFFF) == 0xFFFFFFFF:
            seh = 1                                     # push -1: the EH state of an SEH frame
        elif m == 'push' and ops[0].type == x86.X86_OP_IMM and seh == 1:
            seh = 2                                     # its handler
        elif m == 'mov' and 'fs:' in i.op_str and seh:
            pass
        elif m == 'mov' and i.op_str == 'ebp, esp':
            pass
        elif m == 'sub' and i.op_str.startswith('esp, ') and ops[1].type == x86.X86_OP_IMM:
            pass
        else:
            break
        a += i.size
    return a


def table_import_pops(pe):
    """IAT slot -> bytes popped, for the imports of symbols/import_protos.tsv (they override the decompiler's
    prototypes: D3DX9, MSVCP80 functions with a hidden parameter)"""
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'symbols', 'import_protos.tsv')
    pops = {}
    for l in open(path):
        q = l.rstrip('\n').split('\t')
        if l[0] == '#' or len(q) < 3:
            continue
        n = 4 * len([x for x in q[2].split(',') if x.strip()])
        cc = q[3].strip() if len(q) > 3 else '__stdcall'
        n = 0 if cc == '__cdecl' else n - 4 if cc == '__thiscall' else n
        for slot, (dll, name) in pe.imports.items():
            if name == q[0]:
                pops[slot] = n
    return pops
