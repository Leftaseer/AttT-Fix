#!/usr/bin/env python3
"""Inventory the active replacements of one exact build and its direct differential-test evidence.

Usage: verification_inventory.py ORIGINAL REBUILT MAP AUTO WORK OUTPUT [--report DIFFERENTIAL_JSON]
Native compatibility reservations are excluded through the build's actual replace.txt, not a stale address list.
The report counts direct fixture comparisons; it does not infer branch coverage or validate call chains.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autoverify import select_targets
from pe import PE


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('original', 'rebuilt', 'map', 'auto', 'work', 'output'):
        parser.add_argument(key, type=lambda p: Path(p).resolve())
    parser.add_argument('--report', type=lambda p: Path(p).resolve())
    args = parser.parse_args()
    replacements_path = args.work / 'replace.txt'
    replacements = {int(p[0], 16): p[1] for line in replacements_path.read_text().splitlines()
                    if (p := line.split())}
    generated = {int(match[1], 16) for path in args.auto.glob('auto_*.c')
                 for match in re.finditer(r'^/\* @func ([0-9A-F]{8})', path.read_text(), re.M)}
    eligible = set(select_targets([address for address, symbol in replacements.items()
                                   if re.match(r'^@?(adp_|f_)', symbol)], generated))
    image = PE(str(args.rebuilt))
    for address in replacements:
        if image.read(address, 1) != b'\xE9':
            parser.error('%08X has no replacement jump in this binary' % address)
    report = json.loads(args.report.read_text()) if args.report else {'functions': {}}
    for path in (args.original, args.rebuilt, args.map):
        if args.report and report['inputs'].get(str(path)) != digest(path):
            parser.error('differential report belongs to a different input: ' + str(path))
    names = {}
    for line in (Path(__file__).resolve().parents[1] / 'symbols/attt.sym').read_text().splitlines():
        parts = line.split('#')[0].split(maxsplit=2)
        if len(parts) == 3 and parts[1] == 'f':
            names.setdefault(int(parts[0], 16), parts[2])
    rows = {}
    for address, symbol in sorted(replacements.items()):
        key = '%08X' % address
        rows[key] = {'symbol': symbol, 'name': names.get(address, ''), 'generated': address in eligible,
                     'direct_fixture_evidence': report['functions'].get(key)}
    tested = {int(address, 16) for address, row in rows.items() if row['direct_fixture_evidence']}
    normal = {int(address, 16) for address, row in rows.items()
              if row['direct_fixture_evidence'] and row['direct_fixture_evidence']['normal_return_pairs'] > 0}
    summary = {'active_replacements': len(rows), 'generated_replacements': len(eligible),
               'other_replacements': len(rows) - len(eligible), 'with_direct_fixtures': len(tested),
               'with_normal_return_pairs': len(normal), 'generated_with_direct_fixtures': len(tested & eligible),
               'generated_without_direct_fixtures': len(eligible - tested)}
    output = {'format': 1, 'summary': summary,
              'scope': 'direct fixture evidence, not branch coverage or end-to-end correctness',
              'inputs': {str(path): digest(path) for path in (args.original, args.rebuilt, args.map, replacements_path)},
              'differential_report': str(args.report) if args.report else None, 'replacements': rows}
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
