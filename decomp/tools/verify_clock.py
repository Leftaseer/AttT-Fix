#!/usr/bin/env python3
"""Verify CClock virtual updates through independent original and rebuilt images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from difftest import Harness
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW


UPDATE_SLOT = 0x609ECC
UPDATE = 0x43B2E0
CLOCK_FIELDS = 0x44
FIELD_NAMES = ('year', 'month', 'day', 'hour', 'minute', 'second', 'millisecond')
BASE = (1176, 5, 27, 14, 8, 46, 945)
CASES = (
    ('zero delta', BASE, 60.0, (0.0,), BASE),
    ('zero coefficient', BASE, 0.0, (1000.0,), BASE),
    ('fractional ticks truncate individually', BASE, 6.0, (0.125,) * 8, BASE),
    ('fractional tick', BASE, 6.0, (2.125,), (*BASE[:-1], 957)),
    ('second carry', BASE, 60.0, (1.0,), (1176, 5, 27, 14, 8, 47, 5)),
    ('minute carry', (1176, 5, 27, 14, 8, 59, 999), 1.0, (1.0,), (1176, 5, 27, 14, 9, 0, 0)),
    ('hour carry', (1176, 5, 27, 14, 59, 59, 999), 1.0, (1.0,), (1176, 5, 27, 15, 0, 0, 0)),
    ('day carry', (1176, 5, 27, 23, 59, 59, 999), 1.0, (1.0,), (1176, 5, 28, 0, 0, 0, 0)),
    ('month carry', (1176, 2, 30, 23, 59, 59, 999), 1.0, (1.0,), (1176, 3, 1, 0, 0, 0, 0)),
    ('year carry', (1176, 12, 30, 23, 59, 59, 990), 6.0, (2.0,), (1177, 1, 1, 0, 0, 0, 2)),
    ('carry across frames', (1176, 12, 30, 23, 59, 59, 960), 60.0, (0.5, 0.5, 16.0), (1177, 1, 1, 0, 0, 0, 980)),
    ('multi-second advance', BASE, 60.0, (50.0,), (1176, 5, 27, 14, 8, 49, 945)),
)


def virtual_entry(harness):
    slot = harness.to_rebuilt(UPDATE_SLOT)
    return struct.unpack('<I', harness.uc.mem_read(slot, 4))[0]


def run(harness, entry, name, initial, coefficient, deltas, expected, control_word):
    machine = harness.uc
    address = harness.alloc(0x90)
    clock = address + 0x10
    guarded = bytearray(b'\xa5' * 0x10 + b'\0' * 0x70 + b'\x5a' * 0x10)
    struct.pack_into('<I', guarded, 0x10, harness.to_rebuilt(UPDATE_SLOT - 4))
    struct.pack_into('<7If', guarded, 0x10 + CLOCK_FIELDS, *initial, coefficient)
    machine.mem_write(address, bytes(guarded))
    machine.reg_write(UC_X86_REG_FPCW, control_word)
    faults = []
    for delta in deltas:
        bits, = struct.unpack('<I', struct.pack('<f', delta))
        result = harness.call(entry, (bits,), {UC_X86_REG_ECX: clock})
        if result['fault'] or result['esp'] != 8:
            faults.append(result['fault'] or 'incorrect stack cleanup')
            break
        if machine.reg_read(UC_X86_REG_FPCW) != control_word:
            faults.append('x87 control word changed')
            break
    observed = struct.unpack('<7I', machine.mem_read(clock + CLOCK_FIELDS, 28))
    struct.pack_into('<7I', guarded, 0x10 + CLOCK_FIELDS, *observed)
    if bytes(machine.mem_read(address, len(guarded))) != bytes(guarded):
        faults.append('clock coefficient, object data or adjacent guard changed')
    return {'case': name, 'control_word': hex(control_word), 'initial': initial, 'coefficient': coefficient,
            'deltas': deltas, 'expected': expected, 'observed': observed, 'faults': faults,
            'passed': observed == expected and not faults}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('rebuilt', type=Path)
    parser.add_argument('map', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    original = Harness(args.original, args.original, '/dev/null')
    rebuilt = Harness(args.original, args.rebuilt, args.map)
    if any(harness.rb.pe.FILE_HEADER.TimeDateStamp != 0x475EABAF for harness in (original, rebuilt)):
        parser.error('clock layout is for the supported AttT executable')
    original_entry = virtual_entry(original)
    rebuilt_entry = virtual_entry(rebuilt)
    if original_entry != UPDATE:
        parser.error('unexpected original clock virtual slot')
    if rebuilt_entry == rebuilt.to_rebuilt(UPDATE) and rebuilt.uc.mem_read(rebuilt_entry, 1) != b'\xe9':
        parser.error('rebuilt virtual slot does not reach a replaced clock update')
    report = {'scope': 'independent PE images, CClock virtual Update with explicit float32 frame deltas',
              'inputs': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (args.original, args.rebuilt, args.map)},
              'virtual_entries': {'original': hex(original_entry), 'rebuilt': hex(rebuilt_entry)},
              'field_order': FIELD_NAMES, 'cases': []}
    for case in CASES:
        for control_word in (0x027F, 0x007F):
            report['cases'].append({'original': run(original, original_entry, *case, control_word),
                                    'rebuilt': run(rebuilt, rebuilt_entry, *case, control_word)})
    failed = [row for row in report['cases'] if not row['original']['passed'] or not row['rebuilt']['passed']]
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(report["cases"]) - len(failed)}/{len(report["cases"])} clock cases pass in both images')
    for row in failed:
        print(json.dumps(row))
    return int(bool(failed))


if __name__ == '__main__':
    raise SystemExit(main())
