#!/usr/bin/env python3
"""Drive an active private Wine test display, recording every action alongside its artifacts."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import time

spec = importlib.util.spec_from_file_location('runner', Path(__file__).with_name('wine_game_test.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--target', default='Ascension|ATThrone|Throne', help='X11 window title regex')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('capture').add_argument('label')
    sub.add_parser('key').add_argument('key')
    sub.add_parser('finish')
    for action in ('click', 'move-relative', 'click-relative'):
        mouse = sub.add_parser(action)
        mouse.add_argument('x', type=int)
        mouse.add_argument('y', type=int)
    args = parser.parse_args()
    session = json.loads((args.run / 'session.json').read_text())
    if not session['active']:
        parser.error('test session has stopped')
    env = runner.environment(Path(session['runtime']))
    env.update({key: session[key] for key in ('DISPLAY', 'XAUTHORITY')})
    record = {'action': args.action, 'target': args.target, 'unix_time': time.time()}

    def xdo(*command):
        result = subprocess.run(['xdotool', *map(str, command)], env=env, capture_output=True,
                                text=True, check=True, timeout=10)
        return result.stdout.strip()

    try:
        if args.action == 'finish':
            (args.run / 'finish-request.json').write_text(json.dumps(record) + '\n')
        elif args.action == 'capture':
            if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label):
                parser.error('capture label must use letters, digits, hyphens or underscores')
            source, target = args.run / (args.label + '.xwd'), args.run / (args.label + '.png')
            if source.exists() or target.exists():
                parser.error('capture already exists')
            subprocess.run(['xwd', '-root', '-silent', '-out', str(source)], env=env, check=True, timeout=15)
            runner.xwd_to_png(source, target)
            record['capture'] = str(target)
        else:
            windows = xdo('search', '--onlyvisible', '--name', args.target).split()
            if len(windows) != 1:
                raise RuntimeError('expected one target window, found ' + repr(windows))
            window = windows[0]
            record['window'] = window
            record['geometry'] = xdo('getwindowgeometry', '--shell', window)
            xdo('windowfocus', window)
            if args.action == 'key':
                runner.key_event('0:' + args.key)
                record['key'] = args.key
                try:
                    xdo('keydown', args.key)
                    time.sleep(.6)
                finally:
                    xdo('keyup', args.key)
            else:
                if args.action == 'click':
                    record['client_xy'] = [args.x, args.y]
                    xdo('mousemove', '--window', window, args.x, args.y)
                else:
                    record['delta'] = [args.x, args.y]
                    xdo('mousemove_relative', '--', args.x, args.y)
                time.sleep(.4)
                if args.action != 'move-relative':
                    try:
                        xdo('mousedown', 1)
                        time.sleep(.6)
                    finally:
                        xdo('mouseup', 1)
        record['status'] = 'completed'
    except Exception as error:
        record.update(status='failed', error=str(error))
        raise
    finally:
        with (args.run / 'control.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
