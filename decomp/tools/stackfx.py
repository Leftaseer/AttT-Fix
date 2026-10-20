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
