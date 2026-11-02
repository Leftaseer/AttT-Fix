#!/usr/bin/env python3
"""Generate/audit native functions reserved for AttTFix's byte-checked hooks.

generate: ORIGINAL_EXE MOD_DLL PROFILE_JSON [--source-dir MOD_SOURCE_DIR]
check:    ORIGINAL_EXE REBUILT_EXE PROFILE_JSON

The mod's executable sections supply x86 immediate/absolute code references. Optional mod source adds
literal code addresses (excluding profiler/address-map headers). Entire enclosing functions are reserved,
including interior patch sites; Lua API calls and CRT constants do not reserve the replaced Lua library.
This is a conservative profile for the recorded DLL hash, not an in-game compatibility test.
"""
import argparse
import bisect
import hashlib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pe import PE


def function_sizes():
    path = pathlib.Path(__file__).resolve().parents[1] / 'symbols/attt_functions.tsv'
    return {int(p[0], 16): int(p[1]) for line in path.read_text().splitlines()
            if line and not line.startswith('#') and (p := line.split())}


def generate(original, mod, output, source_dir):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM

    pe, dll = PE(original), PE(mod)
    if pe.pe.FILE_HEADER.TimeDateStamp != 0x475EABAF:
        raise ValueError('profile generation supports AttT Steam 1.1.128 only')
    low, high = pe.text_range()
    references = {}

    def reference(value, origin):
        # Lua is replaced as a complete library; these are API calls, not mod hook sites.
        if max(low, 0x410000) <= value < min(high, 0x5E0000):
            references.setdefault(value, set()).add(origin)

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail, md.skipdata = True, True
    for section in dll.pe.sections:
        if section.Characteristics & 0x20000000:
            for ins in md.disasm(section.get_data(), dll.base + section.VirtualAddress):
                if ins.id:
                    for operand in ins.operands:
                        if operand.type == X86_OP_IMM:
                            reference(operand.imm, 'dll code')
                        elif operand.type == X86_OP_MEM:
                            reference(operand.mem.disp, 'dll code')
    sources = {}
    if source_dir:
        for path in sorted(pathlib.Path(source_dir).iterdir()):
            if path.suffix not in ('.cpp', '.inc'):
                continue
            data = path.read_bytes()
            sources[path.name] = hashlib.sha256(data).hexdigest()
            for match in re.finditer(rb'\b0x([0-9a-fA-F]+)\b', data):
                reference(int(match[1], 16), path.name)
    sizes = function_sizes()
    starts, functions = sorted(sizes), {}
    for value, origins in sorted(references.items()):
        index = bisect.bisect_right(starts, value) - 1
        if index >= 0 and value < starts[index] + sizes[starts[index]]:
            functions.setdefault('%08X' % starts[index], {})['%08X' % value] = sorted(origins)
    profile = {
        'game_timestamp': '475EABAF',
        'mod_sha256': hashlib.sha256(pathlib.Path(mod).read_bytes()).hexdigest(),
        'source_sha256': sources,
        'method': 'conservative code-reference reservation; complete enclosing functions; excludes Lua/CRT',
        'functions': functions,
    }
    pathlib.Path(output).write_text(json.dumps(profile, indent=2) + '\n')
    print('Reserved %d native functions for mod %s' % (len(functions), profile['mod_sha256']))


def check(original, rebuilt, profile_path):
    original, rebuilt = PE(original), PE(rebuilt)
    profile = json.loads(pathlib.Path(profile_path).read_text())
    stamp = int(profile['game_timestamp'], 16)
    assert original.pe.FILE_HEADER.TimeDateStamp == rebuilt.pe.FILE_HEADER.TimeDateStamp == stamp
    assert original.base == rebuilt.base == 0x400000
    sizes, total = function_sizes(), 0
    for key in profile['functions']:
        address = int(key, 16)
        size = sizes[address]
        before = original.pe.get_data(address - original.base, size)
        after = rebuilt.pe.get_data(address - rebuilt.base, size)
        assert len(before) == len(after) == size and before == after, 'native hook bytes differ at ' + key
        total += size
    print('Verified %d reserved functions, %d native bytes; timestamp/image base unchanged' % (
        len(profile['functions']), total))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('generate', 'check'))
    parser.add_argument('original')
    parser.add_argument('binary', help='mod DLL for generate; rebuilt EXE for check')
    parser.add_argument('profile')
    parser.add_argument('--source-dir')
    args = parser.parse_args()
    if args.mode == 'generate':
        generate(args.original, args.binary, args.profile, args.source_dir)
    else:
        check(args.original, args.binary, args.profile)


if __name__ == '__main__':
    main()
