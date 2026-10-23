#!/usr/bin/env python3
"""std::string parameters passed by value: functions that destroy a string in their own parameter area
('lea ecx, [esp+N]; call [~basic_string]' with N past the return address).  MSVC has the caller copy-construct the
string in the outgoing arguments and the callee destroy it; the decompiler took its 7 dwords for separate
parameters and lost the depth of the stack in the callers (0x42AF50 -> 0x42A010).  ghidra/ByValueParams.java
gives those slots one 28-byte parameter.

usage: byvalue.py GAME.exe symbols/GAME_functions.tsv out/GAME_icalls.tsv OUT.tsv
       OUT: address, offsets of the string parameters from the return address (4 = the first stack slot), ret pop"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
from stackfx import table_import_pops
import capstone
from capstone import x86

pe = PE(sys.argv[1])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
DTOR = next(a for a, (dll, n) in pe.imports.items()
            if n == '??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ')
ipops = table_import_pops(pe)
funcs = {}
for l in open(sys.argv[2]):
    if l[0] != '#':
        q = l.rstrip('\n').split('\t')
        funcs[int(q[0], 16)] = (int(q[1]), q[3])
icp = {}            # indirect call -> bytes popped (0 when its caller cleans up), None: unknown
for l in open(sys.argv[3]):
    if l[0] != '#':
        q = l.rstrip('\n').split('\t')
        icp[int(q[0], 16)] = int(q[5]) if q[5] != '-1' else (0 if q[3] != '-1' else None)


def effect(i):
    """ESP change of an instruction, None when unknown"""
    m, ops = i.mnemonic, i.operands
    if m == 'push':
        return -4
    if m == 'pop':
        return 4
    if m in ('sub', 'add') and ops and ops[0].type == x86.X86_OP_REG and ops[0].reg == x86.X86_REG_ESP:
        if ops[1].type != x86.X86_OP_IMM:
            return None
        return -ops[1].imm if m == 'sub' else ops[1].imm
    if (ops and ops[0].type == x86.X86_OP_REG and ops[0].reg == x86.X86_REG_ESP and m in ('mov', 'lea', 'and')) or \
            m == 'leave':
        return None
    if m == 'call':
        o = ops[0]
        if o.type == x86.X86_OP_IMM:
            p = funcs.get(o.imm, (0, '?'))[1]
            return None if p in ('?', '') else int(p)
        if o.type == x86.X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0:
            dll, name = pe.imports.get(o.mem.disp, ('', ''))
            if o.mem.disp not in ipops and dll.upper() == 'MSVCR80.DLL' and not name.startswith('?'):
                return 0                # the C runtime: __cdecl (_strlwr in 0x46D380)
            return ipops.get(o.mem.disp)
        return icp.get(i.address)
    return 0


def dtor_follows(ins, p):
    """the instructions after 'lea ecx, ...' at p reach a call of the string destructor without writing ECX"""
    q = p + ins[p].size
    for _ in range(5):
        n = ins.get(q)
        if n is None:
            return False
        if n.mnemonic == 'call':
            o = n.operands[0]
            return o.type == x86.X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0 and o.mem.disp == DTOR
        if 'ecx' in n.op_str.split(',')[0]:
            return False
        q += n.size
    return False


res = {}
for a, (size, pop) in funcs.items():
    try:
        ins = {i.address: i for i in md.disasm(pe.read(a, size), a)}
    except Exception:
        continue
    seen, todo, offs = set(), [(a, 0, None)], set()
    while todo:
        p, d, ebp = todo.pop()
        while p in ins and p not in seen:
            seen.add(p)
            i = ins[p]
            if i.mnemonic == 'lea' and i.operands[0].type == x86.X86_OP_REG and i.operands[0].reg == x86.X86_REG_ECX \
                    and dtor_follows(ins, p):
                base = i.operands[1].mem.base
                # (an EBP frame: 0x46D380 'lea ecx, [ebp+8]')
                off = d + i.operands[1].mem.disp if base == x86.X86_REG_ESP else \
                    ebp + i.operands[1].mem.disp if base == x86.X86_REG_EBP and ebp is not None else None
                if off is not None and off > 0:
                    offs.add(off)
            if i.mnemonic == 'mov' and i.op_str == 'ebp, esp':
                ebp = d
            if i.mnemonic.startswith('ret') or i.mnemonic in ('int3', 'hlt'):
                break
            e = effect(i)
            if e is None:
                break
            d += e
            if i.mnemonic == 'jmp':
                if i.operands[0].type == x86.X86_OP_IMM:
                    p = i.operands[0].imm
                    continue
                break
            if (i.mnemonic.startswith('j') or i.mnemonic.startswith('loop')) and i.operands[0].type == x86.X86_OP_IMM:
                todo.append((i.operands[0].imm, d, ebp))
            p += i.size
    if offs:
        res[a] = (sorted(offs), pop)
with open(sys.argv[4], 'w') as f:
    f.write('# address\tstring parameters by value (offsets from the return address)\tret pop (tools/byvalue.py)\n')
    f.write(''.join('%08X\t%s\t%s\n' % (a, ','.join(map(str, o)), p) for a, (o, p) in sorted(res.items())))
print('functions taking std::string by value: %d' % len(res))
