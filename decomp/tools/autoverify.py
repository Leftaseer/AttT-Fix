#!/usr/bin/env python3
"""Check every auto-decompiled function of a rebuilt exe against the original in the emulator.

For each function: N random calls built from its prototype (pointers get random objects of the right size whose
dwords are partly pointers to further random objects), run once as the original (entry bytes restored) and once
through the replacement, from the same memory.  Compared: the result register(s), the volatile registers the
original keeps, callee-saved registers, ESP, and the writable memory (.data, the test objects, the caller's
stack).  Coverage of the original code is measured with block hooks.

    verified    at least MIN_OK calls returned normally, all calls behaved the same, coverage >= MIN_COV
    lowcov      the same behaviour, but too few normal returns or too little code covered
    differs     some call behaved differently (result, memory, or the new code crashed and the original not)
    faultdiff   the original crashed and the new code not (often only a load the compiler dropped)
    unsupported the code reached an import the emulator does not provide

usage: autoverify.py ORIG.exe REBUILT.exe REBUILT.map AUTO_DIR WORK_DIR OUT.tsv [--n 16] [--only ADDR,...]"""
import argparse, os, re, struct, sys, random, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from difftest import Harness, STOP, HEAP, HEAP_SIZE, STACK, STACK_SIZE
from unicorn import UcError, UC_HOOK_BLOCK, UC_PROT_ALL
from unicorn.x86_const import *

REGS = {'ECX': UC_X86_REG_ECX, 'EAX': UC_X86_REG_EAX, 'EDX': UC_X86_REG_EDX, 'EBX': UC_X86_REG_EBX,
        'ESI': UC_X86_REG_ESI, 'EDI': UC_X86_REG_EDI}
MIN_OK, MIN_COV = 3, 0.5


class FastHarness(Harness):
    """Harness that saves/compares only the writable regions (data section, used heap, stack)."""

    def setup_regions(self):
        self.regions = []
        for s in self.rb.pe.sections:
            n = s.Name.rstrip(b'\0')
            if n in (b'.data', b'.ndata'):
                self.regions.append((self.rb.base + s.VirtualAddress, (s.Misc_VirtualSize + 0xFFF) & ~0xFFF))
        # low memory: pointers to a few objects, mixed with small values
        self.uc.mem_map(0, LOW, UC_PROT_ALL)
        rnd = random.Random(7)
        objs = [make_object(self, rnd, 512, 2) for _ in range(64)]
        low = bytearray(LOW)
        for o in range(0, LOW, 4):
            struct.pack_into('<I', low, o, rnd.choice(objs) if rnd.random() < 0.6 else rnd.choice([0, 1, 0x10, 0x100]))
        self.uc.mem_write(0, bytes(low))
        self.regions.append((0, LOW))
        self.pristine = {b: bytes(self.uc.mem_read(b, n)) for b, n in self.regions}
        self.cov = set()
        self.cov_on = False
        self.uc.hook_add(UC_HOOK_BLOCK, self._on_block)

    def _on_block(self, uc, addr, size, user):
        if self.cov_on and self.cov_lo <= addr < self.cov_hi:
            self.cov.add((addr, size))

    def run_case(self, entry, head, args, regs, ret, arg_bytes, va):
        """one call as original (head bytes) and one as replacement from the same memory and heap state;
        returns [(registers, memory), (registers, memory)] (memory: writable regions, heap, caller's stack)"""
        hp0 = self.heap_ptr
        window = 0x40000
        heap0 = bytes(self.uc.mem_read(HEAP, hp0 - HEAP + window))
        runs = []
        for h in (head, None):
            self.heap_ptr = hp0
            if h is not None:
                self.uc.mem_write(entry, h)
            self.cov_on = h is not None
            r = self.call(entry, args, regs)
            self.cov_on = False
            if h is not None:
                self.uc.mem_write(entry, self.new_head)
            mem = [bytes(self.uc.mem_read(b, n)) for b, n in self.regions]
            mem.append(bytes(self.uc.mem_read(HEAP, hp0 - HEAP + window)))
            keep = STACK + STACK_SIZE - self.arg_sp
            mem.append(bytes(self.uc.mem_read(self.arg_sp, keep)))
            runs.append((r, mem))
            for b, n in self.regions:
                self.uc.mem_write(b, self.pristine[b])
            self.uc.mem_write(HEAP, heap0)
        self.heap_ptr = hp0
        return runs


def parse_sizes(pre):
    sizes = {}
    for m in re.finditer(r'_Static_assert\(sizeof\((\w+)\) == (\d+)', open(pre, encoding='utf-8').read()):
        sizes[m.group(1)] = int(m.group(2))
    return sizes


def load_protos(path):
    p = {}
    for l in open(path, encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) < 6:
            continue
        plist = [x.rsplit(' ', 1)[0] for x in q[4].split(',') if x.strip()] if q[4] else []
        p[int(q[0], 16)] = (q[1], q[2] == 'true', q[3], plist)
    return p


PTR_RATE = [0.0]     # chance that an untyped dword is a pointer to a further random object (set per case)
LOW = 0x10000        # the first 64 KiB are mapped and full of pointers: small integers used as pointers work


def rand_dword(rnd, h=None, depth=0):
    c = rnd.random()
    if h is not None and depth > 0 and c < PTR_RATE[0]:
        return make_object(h, rnd, 256, depth - 1)
    c = rnd.random()
    if c < 0.25: return rnd.choice([0, 1, 2, 3, 0xFFFFFFFF])
    if c < 0.55: return rnd.randint(0, 100)
    if c < 0.75: return struct.unpack('<I', struct.pack('<f', rnd.choice([0.0, 1.0, -1.0, 0.5, rnd.uniform(-100, 100)])))[0]
    return rnd.getrandbits(32)


def make_object(h, rnd, size, depth):
    size = max(16, min(size, 0x2000))
    data = bytearray(rnd.getrandbits(8) for _ in range(size))
    for o in range(0, size - 3, 4):
        c = rnd.random()
        if c < 0.15 + PTR_RATE[0] / 2 and depth > 0:
            struct.pack_into('<I', data, o, make_object(h, rnd, 256, depth - 1))
        elif c < 0.45:
            struct.pack_into('<I', data, o, rand_dword(rnd))
        elif c < 0.6:
            struct.pack_into('<I', data, o, 0)
    return h.alloc(size, data)


def make_arg(h, rnd, t, sizes):
    t = t.strip()
    if t.endswith('*'):
        if rnd.random() < 0.08:
            return [0]
        base = t[:-1].strip().rstrip('*').strip()
        size = sizes.get(base, 256)
        if base in ('char', 'undefined1', 'byte', 'uchar'):
            s = bytes(rnd.choice(b'abcdefgh./\\_ 0123') for _ in range(rnd.randint(0, 24))) + b'\0'
            return [h.alloc(max(64, len(s)), s + bytes(64))]
        return [make_object(h, rnd, size, 2)]
    if t in ('float',):
        return [struct.unpack('<I', struct.pack('<f', rnd.choice([0.0, 1.0, -1.0, 0.5, 2.0, rnd.uniform(-1000, 1000)])))[0]]
    if t in ('double', 'float10'):
        return list(struct.unpack('<II', struct.pack('<d', rnd.choice([0.0, 1.0, -1.0, rnd.uniform(-1000, 1000)]))))
    if t in ('longlong', 'ulonglong', 'undefined8', 'qword'):
        return [rand_dword(rnd), rand_dword(rnd)]
    if t in sizes and sizes[t] > 4:           # a structure by value
        n = (sizes[t] + 3) // 4
        return [rand_dword(rnd) for _ in range(n)]
    return [rand_dword(rnd, h, 3)]


def ret_kind(t):
    t = t.strip()
    if t == 'void': return None
    if t in ('float', 'double', 'float10'): return 'st0'
    if t in ('longlong', 'ulonglong', 'undefined8', 'qword'): return 'eax:edx'
    if t in ('bool', 'char', 'uchar', 'byte', 'undefined1', 'sbyte'): return 'al'
    if t in ('short', 'ushort', 'word', 'undefined2', 'wchar16', 'wchar_t'): return 'ax'
    return 'eax'


def main():
    ap = argparse.ArgumentParser()
    for x in ('orig', 'rebuilt', 'map', 'auto', 'work', 'out'):
        ap.add_argument(x)
    ap.add_argument('--n', type=int, default=16)
    ap.add_argument('--only')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    h = FastHarness(a.orig, a.rebuilt, a.map)
    h.setup_regions()
    sizes = parse_sizes(os.path.join(a.auto, 'auto_pre.h'))
    jsonl = [f for f in os.listdir(os.path.dirname(os.path.abspath(a.auto))) if False]
    protos = load_protos(a.protos) if hasattr(a, 'protos') else None
    # prototypes come with the auto export: AUTO_DIR/../<game>_auto.jsonl.protos or AUTO_DIR/protos
    pp = os.path.join(a.auto, 'protos')
    protos = load_protos(pp)
    rets = {}
    rp = os.path.join(a.auto, 'rets.tsv')
    if os.path.exists(rp):
        for l in open(rp):
            q = l.rstrip('\n').split('\t')
            rets[int(q[0], 16)] = q[1]
    for k, v in rets.items():
        if k in protos:
            cc_, cu_, r_, pl_ = protos[k]
            protos[k] = (cc_, cu_, v, pl_)
    replaced = []
    for l in open(os.path.join(a.work, 'replace.txt')):
        q = l.split()
        if len(q) == 2 and re.match(r'^@?(adp_|f_)', q[1]):
            replaced.append(int(q[0], 16))
    autos = set()
    for fn in os.listdir(a.auto):
        if fn.startswith('auto_') and fn.endswith('.c'):
            for m in re.finditer(r'^/\* @func ([0-9A-F]{8})', open(os.path.join(a.auto, fn), encoding='utf-8').read(), re.M):
                autos.add(int(m.group(1), 16))
    todo = [x for x in replaced if x in autos]
    if a.only:
        todo = [int(x, 16) for x in a.only.split(',')]
    funcs = {}
    game = 'valk' if h.orig.pe.FILE_HEADER.TimeDateStamp == 0x4883FB4F else 'attt'
    for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'symbols', game + '_functions.tsv')):
        if l[0] == '#':
            continue
        q = l.rstrip('\n').split('\t')
        funcs[int(q[0], 16)] = (int(q[1]), [r for r in q[2].split(',') if r and r != 'EBP'])
    convs = {}           # register parameters in parameter order, as the generated code declares them
    cp = os.path.join(a.auto, 'convs.tsv')
    if os.path.exists(cp):
        for l in open(cp):
            if l[0] != '#':
                q = l.rstrip('\n').split('\t')
                convs[int(q[0], 16)] = [r for r in q[1].split(',') if r]
    heap_mark = h.heap_ptr
    # everything mapped, restored before each function: a function under test can write anywhere (code, import
    # table, TEB, the CRT state), and later functions must not inherit that
    world = [(b, e - b + 1, bytes(h.uc.mem_read(b, e - b + 1))) for b, e, _ in h.uc.mem_regions()]
    out = open(a.out, 'w')
    stats = {}
    t0 = time.time()
    for k, va in enumerate(todo):
        rnd = random.Random(a.seed * 1000003 + va)
        for b, n, data in world:
            h.uc.mem_write(b, data)
        h.uc.reg_write(UC_X86_REG_FPCW, 0x27F)      # x87 state a faulting function may have left behind
        h.uc.reg_write(UC_X86_REG_FPSW, 0)
        h.uc.reg_write(UC_X86_REG_FPTAG, 0xFFFF)
        h.uc.reg_write(UC_X86_REG_EFLAGS, 0x202)
        pr = protos.get(va)
        size, regs = funcs.get(va, (0, []))
        if not pr:
            status, detail, cov = 'noproto', '', 0
        else:
            cc, custom, ret, plist = pr
            entry = h.to_rebuilt(va)
            head = h.orig.read(va, max(5, size))          # the whole body: the build changes more than the jmp
            h.new_head = bytes(h.uc.mem_read(entry, len(head)))
            h.cov = set()
            h.cov_lo, h.cov_hi = entry, entry + size
            n_ok = n_same_fault = 0
            status, detail = None, ''
            for case in range(a.n):
                h.heap_ptr = heap_mark
                PTR_RATE[0] = (0.0, 0.3, 0.6)[case % 3]
                args = [make_arg(h, rnd, t, sizes) for t in plist]
                regv = {}
                flat = []
                order = convs[va] if va in convs else regs if custom else (['ECX'] if cc == '__thiscall' else ['ECX', 'EDX'] if cc == '__fastcall' else [])
                for i, av in enumerate(args):
                    if i < len(order) and len(av) == 1:
                        regv[REGS[order[i]]] = av[0]
                    else:
                        flat += av
                (r1, m1), (r2, m2) = h.run_case(entry, head, flat, regv, ret_kind(ret), 0, va)
                f1, f2 = r1['fault'], r2['fault']
                if f1 and 'unsupported' in f1 or f2 and 'unsupported' in f2:
                    status, detail = 'unsupported', (f1 if f1 and 'unsupported' in f1 else f2)
                    break
                if bool(f1) != bool(f2):
                    # the original faulting where the new code does not is often a load the compiler dropped
                    status = 'faultdiff' if f1 and not f2 else 'differs'
                    detail = 'case %d: orig %s / new %s' % (case, f1, f2)
                    break
                if f1:
                    n_same_fault += 1
                    continue
                rk = ret_kind(ret)
                diff = []
                keys = ['esp', 'ebx', 'esi', 'edi', 'ebp'] + [x for x in ('eax', 'ecx', 'edx') if x not in h.clobbered(va)]
                for kx in keys:
                    if r1[kx] != r2[kx]:
                        diff.append(kx)
                if rk == 'eax' and r1['eax'] != r2['eax']: diff.append('eax')
                if rk == 'eax:edx' and (r1['eax'], r1['edx']) != (r2['eax'], r2['edx']): diff.append('eax:edx')
                if rk == 'al' and (r1['eax'] & 0xFF) != (r2['eax'] & 0xFF): diff.append('al')
                if rk == 'ax' and (r1['eax'] & 0xFFFF) != (r2['eax'] & 0xFFFF): diff.append('ax')
                if rk == 'st0' and r1['st0'] != r2['st0'] and not (r1['st0'] != r1['st0'] and r2['st0'] != r2['st0']):
                    diff.append('st0 %r %r' % (r1['st0'], r2['st0']))
                for i, (x, y) in enumerate(zip(m1, m2)):
                    if x != y:
                        j = next(j for j in range(len(x)) if x[j] != y[j])
                        base = (h.regions + [(HEAP, 0), (h.arg_sp, 0)])[i][0]
                        diff.append('mem %08X: %s / %s' % (base + j, x[j:j + 8].hex(), y[j:j + 8].hex()))
                        break
                if diff:
                    status, detail = 'differs', 'case %d: %s' % (case, ', '.join(diff))
                    break
                n_ok += 1
            cov = sum(s for _, s in h.cov) / max(1, size)
            if status is None:
                status = 'verified' if n_ok >= MIN_OK and cov >= MIN_COV else 'lowcov'
                detail = '%d ok, %d both faulted' % (n_ok, n_same_fault)
        stats[status] = stats.get(status, 0) + 1
        out.write('%08X\t%s\t%.2f\t%s\n' % (va, status, min(cov, 1.0), detail))
        if k % 200 == 0:
            out.flush()
            print('%d/%d %s %.0fs' % (k, len(todo), stats, time.time() - t0), flush=True)
    out.close()
    print('done:', stats)


if __name__ == '__main__':
    main()
