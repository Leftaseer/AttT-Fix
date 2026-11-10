#!/usr/bin/env python3
"""Launch the AttT modding workspace or run either editor from the command line."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'world-editor'))

import gres
import worldctl


def inspect_archives(args):
    with gres.ArchiveSet(args.archives, allow_gaps=True) as archives:
        providers = {}
        for slot in archives.slots:
            archive = archives.archives[slot]
            for name in archive.entries:
                providers.setdefault(name, []).append(archive.path.name)
        result = [
            {'file': name, 'providers': names, 'winner': names[-1]}
            for name, names in sorted(providers.items())
            if len(names) > 1
        ]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'world':
        return worldctl.main(argv[1:])
    if argv and argv[0] == 'balance':
        node = os.environ.get('ATTT_NODE', 'node')
        return subprocess.call([node, str(ROOT / 'balance-studio' / 'cli.cjs'), *argv[1:]])

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve', help='open the shared HTML workspace')
    serve.add_argument('--game', type=Path, help='folder containing the game PAKs')
    serve.add_argument('--edition', choices=('attt', 'valkyrie'), default='attt')
    serve.add_argument('--world', type=Path, help='world project JSON, created if absent')
    serve.add_argument('--forests', type=Path, help='existing forest project JSON for the map')
    serve.add_argument('--prefer-localization', action='store_true', help='use Localization.pak as slot 1')
    serve.add_argument('--port', type=int, default=8765)
    serve.add_argument('--no-browser', action='store_true')
    serve.add_argument('--data-dir', type=Path, help='directory for browser-created projects')
    commands.add_parser('world', help='world, forest and story CLI')
    commands.add_parser('balance', help='balance CLI for lists, profiles and PAK export (Node.js 22+)')
    inspect = commands.add_parser('overlaps', help='show files supplied by multiple numbered PAKs and their winners')
    inspect.add_argument('archives', nargs='+', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'serve':
        from workspace import serve_workspace
        return serve_workspace(args)
    return inspect_archives(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        sys.exit(str(error))
