#!/usr/bin/env python3
"""Inventory the active replacements of one exact build and their verification evidence.

Usage: verification_inventory.py ORIGINAL REBUILT MAP AUTO WORK OUTPUT [--report DIFFERENTIAL_JSON] [--sweep DIR]
Native compatibility reservations are excluded through the build's actual replace.txt, not a stale address list.
Fixture and sweep verdicts describe the sampled inputs. Both entry comparisons share their callees.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autoverify import select_targets
from pe import PE
from verify_sweep import fingerprint_tree


SWEEP_VERDICTS = {'verified', 'lowcov', 'differs', 'faultdiff', 'unsupported', 'noproto',
                  'timeout', 'emulator_crash', 'interrupted'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sweep(directory, inputs, auto, eligible):
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['format'] != 2 or manifest['inputs'] != inputs:
        raise ValueError('sweep manifest belongs to different build inputs')
    if manifest['auto'] != {'path': str(auto), 'files': fingerprint_tree(auto)}:
        raise ValueError('sweep manifest belongs to different generated sources')

    options = manifest['options']
    only = None
    if '--only' in options:
        only = [int(value, 16) for value in options[options.index('--only') + 1].split(',')]
    targets = select_targets(eligible, eligible, only)
    shards = manifest['shards']
    summary = json.loads((directory / 'summary.json').read_text())
    if shards < 1 or summary['complete'] is not True or summary['shard_exit_codes'] != [0] * shards:
        raise ValueError('sweep did not complete all shards')

    files = [directory / f'av_{i}.tsv' for i in range(shards)]
    if set(files) != set(directory.glob('av_*.tsv')):
        raise ValueError('sweep directory has missing or unexpected shard files')
    rows = {}
    for i, path in enumerate(files):
        remaining = set(targets[i::shards])
        with path.open(newline='') as stream:
            for address_text, verdict, coverage_text, detail in csv.reader(stream, delimiter='\t'):
                address = int(address_text, 16)
                if address not in remaining:
                    raise ValueError(f'{path.name}: unexpected or duplicate address {address:08X}')
                remaining.remove(address)
                coverage = float(coverage_text)
                if verdict not in SWEEP_VERDICTS or not 0 <= coverage <= 1:
                    raise ValueError(f'{path.name}: invalid verdict or coverage for {address:08X}')
                rows[f'{address:08X}'] = {'verdict': verdict, 'normal_coverage': coverage, 'detail': detail}
        if remaining:
            raise ValueError(f'{path.name}: missing {len(remaining)} expected addresses')

    counts = Counter(row['verdict'] for row in rows.values())
    if summary['rows'] != len(rows) or summary['verdicts'] != counts:
        raise ValueError('sweep summary disagrees with its shard rows')
    return rows, {'directory': str(directory), 'manifest_sha256': digest(directory / 'manifest.json'),
                  'options': options, 'shard_sha256': {path.name: digest(path) for path in files},
                  'rows': len(rows), 'verdicts': dict(sorted(counts.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('original', 'rebuilt', 'map', 'auto', 'work', 'output'):
        parser.add_argument(key, type=lambda p: Path(p).resolve())
    parser.add_argument('--report', type=lambda p: Path(p).resolve())
    parser.add_argument('--sweep', type=lambda p: Path(p).resolve(),
                        help='attach one complete hash-pinned sweep or focused run')
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
    inputs = {str(path): digest(path) for path in (args.original, args.rebuilt, args.map, replacements_path)}
    for path in (args.original, args.rebuilt, args.map):
        if args.report and report['inputs'].get(str(path)) != inputs[str(path)]:
            parser.error('differential report belongs to a different input: ' + str(path))
    sweep_rows, sweep = {}, None
    if args.sweep:
        try:
            sweep_rows, sweep = read_sweep(args.sweep, inputs, args.auto, eligible)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            parser.error(f'invalid sweep: {error}')
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
        if sweep is not None:
            rows[key]['sweep_evidence'] = sweep_rows.get(key)
    tested = {int(address, 16) for address, row in rows.items() if row['direct_fixture_evidence']}
    normal = {int(address, 16) for address, row in rows.items()
              if row['direct_fixture_evidence'] and row['direct_fixture_evidence']['normal_return_pairs'] > 0}
    summary = {'active_replacements': len(rows), 'generated_replacements': len(eligible),
               'other_replacements': len(rows) - len(eligible), 'with_direct_fixtures': len(tested),
               'with_normal_return_pairs': len(normal), 'generated_with_direct_fixtures': len(tested & eligible),
               'generated_without_direct_fixtures': len(eligible - tested)}
    output = {'format': 1, 'summary': summary,
              'scope': 'direct fixture evidence, not branch coverage or end-to-end correctness',
              'inputs': inputs,
              'differential_report': str(args.report) if args.report else None, 'replacements': rows}
    if sweep is not None:
        output['scope'] = 'entry fixture and sweep evidence; shared dependencies and bounded sampled inputs'
        output['sweep'] = sweep
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
