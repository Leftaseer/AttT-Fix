#!/usr/bin/env python3
"""Hash-pinned, resumable autoverify shards (Linux/WSL).

Arguments match autoverify.py: ORIG REBUILT MAP AUTO WORK OUTDIR.
Each worker retries a killed shard; autoverify records its interrupted function
as crashed before proceeding. A manifest prevents mixing binaries or settings.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys

import unicorn

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint_tree(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('orig', 'rebuilt', 'map', 'auto', 'work', 'outdir'):
        ap.add_argument(key, type=lambda p: Path(p).resolve())
    ap.add_argument('--jobs', type=positive, default=8)
    ap.add_argument('--shards', type=positive, default=24)
    ap.add_argument('--n', type=positive, default=30)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--steps', type=positive, default=5_000_000)
    ap.add_argument('--fpcw', type=lambda s: int(s, 0), default=0x27f)
    ap.add_argument('--fn-timeout', type=positive, default=30)
    ap.add_argument('--only', help='comma-separated function addresses for focused runs')
    ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    only = sorted(set(int(s, 16) for s in a.only.split(','))) if a.only else None
    options = ['--n', str(a.n), '--seed', str(a.seed), '--steps', str(a.steps),
               '--fpcw', hex(a.fpcw), '--fn-timeout', str(a.fn_timeout)]
    if only is not None:
        options += ['--only', ','.join('%08X' % x for x in only)]
    identity = {
        'format': 1,
        'inputs': {str(p): digest(p) for p in (a.orig, a.rebuilt, a.map, a.work / 'replace.txt')},
        'tools': {p.name: digest(p) for p in (HERE / 'autoverify.py', HERE / 'difftest.py', HERE / 'pe.py', Path(__file__))},
        'symbols': fingerprint_tree(HERE.parent / 'symbols'),
        'auto': {'path': str(a.auto), 'files': fingerprint_tree(a.auto)},
        'options': options, 'shards': a.shards,
        'python': sys.version, 'unicorn': unicorn.__version__,
    }
    a.outdir.mkdir(parents=True, exist_ok=True)
    lock = (a.outdir / 'run.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        ap.error('another sweep is using this output directory')
    manifest = a.outdir / 'manifest.json'
    if manifest.exists():
        if not a.resume:
            ap.error('output already has a manifest; use --resume or a new directory')
        if json.loads(manifest.read_text()) != identity:
            ap.error('input hashes or settings changed; use a new output directory')
    else:
        if a.resume or any(a.outdir.glob('av_*.tsv*')):
            ap.error('cannot resume results without a matching manifest')
        manifest.write_text(json.dumps(identity, indent=2, sort_keys=True) + '\n')

    def run_shard(k):
        out = a.outdir / ('av_%d.tsv' % k)
        cur = Path(str(out) + '.cur')
        cmd = [sys.executable, '-I', str(HERE / 'autoverify.py'),
               *map(str, (a.orig, a.rebuilt, a.map, a.auto, a.work)), str(out),
               *options, '--shard', '%d/%d' % (k, a.shards), '--resume']
        previous = None
        with (a.outdir / ('av_%d.log' % k)).open('a') as log:
            while True:
                rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
                if rc == 0:
                    print('shard %d complete' % k, flush=True)
                    return 0
                progress = (out.stat().st_size if out.exists() else 0,
                            cur.read_text() if cur.exists() else '')
                if rc not in (3, -signal.SIGSEGV, -signal.SIGABRT) or not progress[1] or progress == previous:
                    print('shard %d stopped, exit %d' % (k, rc), flush=True)
                    return rc
                previous = progress

    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        codes = list(pool.map(run_shard, range(a.shards)))
    rows = []
    for path in sorted(a.outdir.glob('av_*.tsv')):
        with path.open() as f:
            rows.extend(csv.reader(f, delimiter='\t'))
    summary = {'rows': len(rows), 'verdicts': dict(Counter(r[1] for r in rows)),
               'shard_exit_codes': codes, 'complete': all(c == 0 for c in codes)}
    (a.outdir / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)
    return 0 if summary['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())
