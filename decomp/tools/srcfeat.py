#!/usr/bin/env python3
"""Source-side features from unoptimized COFF objects: per function (in file order) the strings it
references and the functions it calls.  usage: srcfeat.py OUT.json OBJ...  (objects in link order)"""
import sys, json, re, subprocess
def rdata_strings(obj):
    out = subprocess.run(['llvm-objdump', '-s', '-j', '.rdata', obj], capture_output=True, text=True).stdout
    data = bytearray()
    for l in out.splitlines():
        m = re.match(r'^ ([0-9a-f]{4,}) ((?:[0-9a-f]{2,8} ?){1,4})', l)
        if m:
            hx = m.group(2).replace(' ', '')
            data += bytes.fromhex(hx)
    return data
def cstr(data, off):
    e = data.find(b'\0', off)
    return data[off:e].decode('latin1') if e >= 0 else None
res = []
for obj in sys.argv[2:]:
    rd = rdata_strings(obj)
    dis = subprocess.run(['llvm-objdump', '-dr', '--no-show-raw-insn', obj], capture_output=True, text=True).stdout
    funcs = []; cur = None; pending_addend = None
    lines = dis.splitlines()
    for idx, l in enumerate(lines):
        m = re.match(r'^[0-9a-f]+ <(.+)>:$', l)
        if m:
            cur = {'name': m.group(1).lstrip('_'), 'strings': [], 'calls': [], 'file': obj.split('/')[-1][:-2]}
            funcs.append(cur); continue
        if cur is None: continue
        m = re.search(r'IMAGE_REL_I386_(\w+)\s+(\S+)', l)
        if m:
            kind, sym = m.groups()
            prev = lines[idx - 1]
            if sym.startswith('.rdata'):
                # addend is the immediate in the previous instruction
                mm = re.search(r'\$0x([0-9a-f]+)|0x([0-9a-f]+)', prev)
                off = int((mm.group(1) or mm.group(2)), 16) if mm else 0
                s = cstr(rd, off)
                if s: cur['strings'].append(s)
            elif kind == 'REL32' or 'call' in prev:
                cur['calls'].append(sym.lstrip('_'))
            else:
                cur['calls'].append(sym.lstrip('_'))
    res.extend(funcs)
json.dump(res, open(sys.argv[1], 'w'), indent=0)
print(len(res), 'functions')
