#!/usr/bin/env python3
"""EAX as a register parameter of the functions that hand on their caller's EAX.

A function that reaches its ret, on some path, without writing EAX returns the EAX its caller had (0x42AE80
'ret' with three parameters; virtual functions whose slot others return a value from; LTCG code returning its
EAX argument).  The machine-code analysis finds no read of EAX there, so no register parameter, and the
decompiler shows in_EAX: the generated code would return garbage of its own.  With EAX among the register
inputs (ghidra/ApplyRegParams.java) the decompiler takes it as a parameter, and a caller's code passes what its
EAX holds (when that is an in_EAX of the caller in turn, the next export adds the caller: a few rounds converge).

usage: eaxin.py update AUTO.jsonl symbols/GAME_eaxin.tsv     add the functions with in_EAX in the export
       eaxin.py apply symbols/GAME_eaxin.tsv REGPARAMS.tsv symbols/GAME_functions.tsv
                                                              add EAX to their register inputs (in place)"""
import json, re, sys


def load(path):
    try:
        return {l.split()[0] for l in open(path) if l.strip() and l[0] != '#'}
    except FileNotFoundError:
        return set()


def add_eax(regs):
    r = [x for x in regs.split(',') if x]
    return ','.join(r if 'EAX' in r else ['EAX'] + r)


def main():
    if sys.argv[1] == 'update':
        jsonl, out = sys.argv[2:4]
        have = load(out)
        new = set()
        for l in open(jsonl):
            d = json.loads(l)
            if re.search(r'\bin_EAX\b', d['code']) and not 0x401000 <= int(d['a'], 16) < 0x420600:   # (Lua library)
                new.add(d['a'])
        with open(out, 'w') as f:
            f.write('# functions that hand on their caller\'s EAX: EAX is a register input (tools/eaxin.py)\n')
            f.write(''.join('%s\n' % a for a in sorted(have | new)))
        print('EAX inputs: %d (%d new)' % (len(have | new), len(new - have)))
    elif sys.argv[1] == 'apply':
        eax = load(sys.argv[2])
        for path, col in ((sys.argv[3], 1), (sys.argv[4], 2)):
            lines = []
            for l in open(path):
                q = l.rstrip('\n').split('\t')
                if l[0] != '#' and q[0] in eax and len(q) > col:
                    q[col] = add_eax(q[col])
                    l = '\t'.join(q) + '\n'
                lines.append(l)
            open(path, 'w').write(''.join(lines))


if __name__ == '__main__':
    main()
