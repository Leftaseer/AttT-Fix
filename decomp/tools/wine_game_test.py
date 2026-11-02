#!/usr/bin/env python3
"""Run one game EXE in a fresh WSL test directory, preserving inputs and all output artifacts.

Requires the local runtime documented in WINE_TESTING.md. Xvfb uses an authenticated abstract Unix socket;
the host's read-only /tmp/.X11-unix and the Windows desktop are not used. Runs sharing a prefix are serialized.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
import re
from pathlib import Path
import secrets
import select
import shutil
import struct
import subprocess
import tempfile
import time
import zlib


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def key_event(value):
    """Parse one timed X11 key, without invoking a shell or the engine's test hooks."""
    try:
        seconds, key = value.split(':', 1)
        seconds = float(seconds)
        if not math.isfinite(seconds) or seconds < 0 or not re.fullmatch(r'[A-Za-z0-9_+]+', key):
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError('key event must be finite nonnegative SECONDS:KEY')
    return seconds, key


def xwd_to_png(source, target):
    data = Path(source).read_bytes()
    if len(data) < 100:
        raise ValueError('truncated XWD header')
    header = struct.unpack('>25I', data[:100])
    size, version, format_, depth, width, height = header[:6]
    order, bpp, stride, masks, colors = header[7], header[11], header[12], header[14:17], header[19]
    if (version != 7 or format_ != 2 or bpp not in (24, 32) or not all(masks)
            or order not in (0, 1) or not 0 < width <= 8192 or not 0 < height <= 8192):
        raise ValueError('unsupported XWD pixel format')
    offset, step = size + colors * 12, bpp // 8
    if size < 100 or stride < width * step or offset + height * stride > len(data):
        raise ValueError('truncated or invalid XWD pixel data')
    shifts = [(mask & -mask).bit_length() - 1 for mask in masks]
    maxima = [mask >> shift for mask, shift in zip(masks, shifts)]
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)  # PNG scanline filter: none
        for x in range(width):
            start = offset + y * stride + x * step
            value = int.from_bytes(data[start:start + step], 'little' if order == 0 else 'big')
            pixels.extend(((value & mask) >> shift) * 255 // maximum
                          for mask, shift, maximum in zip(masks, shifts, maxima))

    def chunk(name, payload):
        return struct.pack('>I', len(payload)) + name + payload + struct.pack('>I', zlib.crc32(name + payload))

    Path(target).write_bytes(b'\x89PNG\r\n\x1a\n' +
                            chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0)) +
                            chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))


def environment(runtime):
    env = dict(os.environ)
    env.pop('LD_PRELOAD', None)
    libraries = [runtime / 'root/usr/lib/x86_64-linux-gnu',
                 runtime / 'root/usr/lib/x86_64-linux-gnu/pulseaudio', runtime / 'root/usr/lib']
    libraries += list((runtime / 'root/usr/lib').glob('pulse-*/modules'))
    env['PATH'] = ':'.join(map(str, [runtime / 'root/opt/wine-stable/bin', runtime / 'root/usr/bin'])) + ':' + env['PATH']
    env['LD_LIBRARY_PATH'] = ':'.join(map(str, libraries)) + ':' + env.get('LD_LIBRARY_PATH', '')
    env.update(WINEPREFIX=str(runtime / 'prefix'), WINEARCH='win64',
               WAYLAND_DISPLAY='',
               WINEDLLOVERRIDES='mscoree,mshtml,winemenubuilder.exe=;d3dx9_29=n',
               WINEDEBUG='err+all,+debugstr', LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe',
               LP_NUM_THREADS='4', VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/lvp_icd.json',
               XKB_BINDIR=str(runtime / 'root/usr/bin'), BROWSER='/bin/true')
    for key, directory in [('XDG_RUNTIME_DIR', 'runtime'), ('XDG_CONFIG_HOME', 'config'),
                           ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache'),
                           ('PULSE_RUNTIME_PATH', 'audio'), ('PULSE_STATE_PATH', 'audio-state'),
                           ('MESA_SHADER_CACHE_DIR', 'shader-cache')]:
        path = runtime / directory
        path.mkdir(exist_ok=True)
        path.chmod(0o700)
        env[key] = str(path)
    env['PULSE_SERVER'] = 'unix:' + str(runtime / 'audio/native')
    env['PULSE_COOKIE'] = str(runtime / 'audio-cookie')
    return env


class Services:
    def __init__(self, runtime, output, width, height):
        self.runtime, self.output = runtime, output
        self.env = environment(runtime)
        self.width, self.height = width, height
        self.processes, self.streams = [], []

    def start_process(self, command, name, **kwargs):
        stream = (self.output / (name + '.log')).open('w')
        self.streams.append(stream)
        process = subprocess.Popen(command, env=kwargs.pop('env', self.env), stdout=stream,
                                   stderr=subprocess.STDOUT, **kwargs)
        self.processes.append(process)
        return process

    def start(self):
        number = secrets.randbelow(800) + 100
        display = ':' + str(number)
        authority = self.output / 'Xauthority'
        subprocess.run(['xauth', '-f', str(authority), 'add', display, '.', secrets.token_hex(16)],
                       env=self.env, check=True, capture_output=True)
        read_fd, write_fd = os.pipe()
        try:
            xvfb = self.start_process(['Xvfb', display, '-displayfd', str(write_fd), '-screen', '0',
                                      '%dx%dx24' % (self.width, self.height), '-nolisten', 'unix', '-nolisten', 'tcp',
                                      '-auth', str(authority), '-fp', 'built-ins'], 'xvfb', pass_fds=(write_fd,),
                                     env=dict(self.env, LD_PRELOAD=str(self.runtime / 'bind_loopback.so')))
            os.close(write_fd)
            write_fd = None
            if not select.select([read_fd], [], [], 15)[0] or not os.read(read_fd, 64).strip() or xvfb.poll() is not None:
                raise RuntimeError('private display failed; see xvfb.log')
        finally:
            os.close(read_fd)
            if write_fd is not None:
                os.close(write_fd)
        self.env.update(DISPLAY=display, XAUTHORITY=str(authority))
        modules = next((self.runtime / 'root/usr/lib').glob('pulse-*/modules'))
        pulse = self.start_process(['pulseaudio', '--daemonize=no', '--exit-idle-time=-1', '--use-pid-file=no',
                                    '--dl-search-path=' + str(modules), '-n',
                                    '--load=module-null-sink sink_name=attt_test',
                                    '--load=module-native-protocol-unix socket=' + str(self.runtime / 'audio/native') +
                                    ' auth-anonymous=1'], 'pulse')
        for _ in range(50):
            if (self.runtime / 'audio/native').exists() or pulse.poll() is not None:
                break
            time.sleep(.1)
        if pulse.poll() is not None or not (self.runtime / 'audio/native').exists():
            raise RuntimeError('private audio failed; see pulse.log')
        return self.env

    def stop(self):
        try:
            subprocess.run(['wineserver', '-k'], env=self.env, capture_output=True, timeout=20)
            subprocess.run(['wineserver', '-w'], env=self.env, capture_output=True, timeout=20)
        finally:
            for process in reversed(self.processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for stream in self.streams:
                stream.close()


def stage_game(assets, exe, directory, width, height, saves=None, test_input=None):
    directory.mkdir()
    (directory / 'Saves').mkdir()
    (directory / 'Screenshots').mkdir()
    identities = {}
    for source in sorted(assets.glob('*.pak')):
        # Reflink when possible; otherwise copy. Never expose the supplied archives for writing.
        subprocess.run(['cp', '--reflink=auto', '--', str(source), str(directory / source.name)], check=True)
        identities[source.name] = {'bytes': source.stat().st_size, 'sha256': sha256(source)}
    if not (directory / 'Resource0.pak').exists():
        raise ValueError('asset directory has no Resource0.pak')
    for name in ('mss32.dll', 'binkw32.dll'):
        shutil.copy2(assets / name, directory / name)
        identities[name] = {'sha256': sha256(assets / name)}
    shutil.copytree(assets / 'MSS', directory / 'MSS')
    cfg = bytearray((assets / 'graphic.cfg').read_bytes())
    if len(cfg) < 17:
        raise ValueError('graphic.cfg is too short')
    cfg[:8] = struct.pack('<II', width, height)
    cfg[16] = 0
    (directory / 'graphic.cfg').write_bytes(cfg)
    shutil.copy2(exe, directory / 'ATThrone.exe')
    if saves:
        for source in sorted(saves.iterdir()):
            if source.is_file():
                shutil.copy2(source, directory / 'Saves' / source.name)
    if test_input:
        shutil.copy2(test_input, directory / 'testinput.txt')
    return identities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--runtime', type=Path, default=Path.home() / 'work/wine-runtime')
    parser.add_argument('--runs', type=Path, default=Path.home() / 'work/wine-tests')
    parser.add_argument('--label', default='smoke')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--launch-mode', choices=('normal', 'developer'), default='normal',
                        help='normal startup, or developer world start (-nologo bypasses the menu)')
    parser.add_argument('--key-at', action='append', type=key_event, default=[], metavar='SECONDS:KEY',
                        help='hold an X11 key for 0.5 seconds; repeat to drive original and rebuilt EXEs alike')
    parser.add_argument('--width', type=int, default=800)
    parser.add_argument('--height', type=int, default=600)
    parser.add_argument('--saves', type=Path)
    parser.add_argument('--test-input', type=Path)
    parser.add_argument('--require-log', help='literal marker required in Wine or decomp_debug.log')
    parser.add_argument('--dxvk', type=Path, help='directory containing the 32-bit DXVK d3d9.dll')
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 1 <= args.seconds <= 3600:
        parser.error('seconds must be finite and between 1 and 3600')
    if any(when >= args.seconds for when, _ in args.key_at):
        parser.error('key events must occur before the end of the run')
    if not 320 <= args.width <= 4096 or not 200 <= args.height <= 2160:
        parser.error('resolution must be between 320x200 and 4096x2160')
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label):
        parser.error('label must contain only letters, numbers, hyphens or underscores')
    args.exe, args.assets, args.runtime, args.runs = [p.resolve() for p in
                                                    (args.exe, args.assets, args.runtime, args.runs)]
    if not (args.runtime / 'prefix/drive_c/windows/syswow64/d3dx9_29.dll').exists():
        parser.error('private Wine prefix is not initialized; see WINE_TESTING.md')
    lock = (args.runtime / 'prefix.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('another test is using this Wine prefix')
    args.runs.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix=args.label + '-', dir=args.runs))
    print('Run directory:', output, flush=True)
    services = Services(args.runtime, output, max(1024, args.width + 32), max(768, args.height + 64))
    result = {'exe': str(args.exe), 'exe_sha256': sha256(args.exe), 'assets': str(args.assets),
              'seconds': args.seconds, 'launch_mode': args.launch_mode, 'resolution': [args.width, args.height],
              'renderer': 'DXVK' if args.dxvk else 'WineD3D', 'status': 'preparing'}
    result['key_events_requested'], result['key_events_sent'] = sorted(args.key_at), []
    result['required_log_marker'] = args.require_log
    try:
        result['asset_identities'] = stage_game(args.assets, args.exe, output / 'game', args.width, args.height,
                                               args.saves, args.test_input)
        result['save_inputs'] = {p.name: {'bytes': p.stat().st_size, 'sha256': sha256(p)}
                                 for p in sorted((output / 'game/Saves').iterdir()) if p.is_file()}
        result['test_input_sha256'] = sha256(output / 'game/testinput.txt') if args.test_input else None
        env = services.start()
        if args.dxvk:
            dll = args.dxvk / 'd3d9.dll'
            shutil.copy2(dll, output / 'game/d3d9.dll')
            env['WINEDLLOVERRIDES'] += ';d3d9=n'
            result['dxvk_sha256'] = sha256(dll)
        version = subprocess.run(['wine', '--version'], env=env, capture_output=True, text=True, check=True)
        result['wine'] = version.stdout.strip()
        result['native_d3dx9_29_sha256'] = sha256(args.runtime / 'prefix/drive_c/windows/syswow64/d3dx9_29.dll')
        command = ['wine', 'ATThrone.exe'] + (['-nologo'] if args.launch_mode == 'developer' else [])
        game = services.start_process(command, 'wine', cwd=output / 'game')
        started, next_focus = time.monotonic(), 0
        pending_keys = list(sorted(args.key_at))
        while time.monotonic() - started < args.seconds:
            if game.poll() is not None or list((output / 'game').glob('__ATThrone__ERRORS*')):
                break
            if time.monotonic() >= next_focus:
                windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', 'Ascension|ATThrone|Throne'],
                                         env=env, capture_output=True, text=True, timeout=5)
                for window in windows.stdout.split():
                    subprocess.run(['xdotool', 'windowfocus', window], env=env, capture_output=True, timeout=5)
                next_focus = time.monotonic() + 2
            while pending_keys and time.monotonic() - started >= pending_keys[0][0]:
                due, key = pending_keys.pop(0)
                subprocess.run(['xdotool', 'keydown', key], env=env, check=True, capture_output=True, timeout=5)
                try:
                    time.sleep(.5)
                finally:
                    subprocess.run(['xdotool', 'keyup', key], env=env, check=True, capture_output=True, timeout=5)
                result['key_events_sent'].append({'requested_at': due, 'key': key,
                                                  'completed_at': round(time.monotonic() - started, 2)})
            time.sleep(.25)
        result['elapsed'] = round(time.monotonic() - started, 2)
        result['alive_at_end'] = game.poll() is None
        result['exit_code'] = game.poll()
        result['error_files'] = [p.name for p in (output / 'game').glob('__ATThrone__ERRORS*')]
        subprocess.run(['xwd', '-root', '-silent', '-out', str(output / 'screen.xwd')], env=env, check=True, timeout=15)
        xwd_to_png(output / 'screen.xwd', output / 'screen.png')
        text = (output / 'wine.log').read_text(errors='replace')
        debug = output / 'game/decomp_debug.log'
        if debug.exists():
            text += debug.read_text(errors='replace')
        result['required_marker_seen'] = args.require_log is None or args.require_log in text
        result['status'] = 'smoke_survived' if (result['alive_at_end'] and not result['error_files'] and
                                              result['required_marker_seen']) else 'failed'
    except Exception as error:
        result.update(status='setup_or_runner_error', error=str(error))
        raise
    finally:
        try:
            services.stop()
        finally:
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result, indent=2), flush=True)
            lock.close()
    return 0 if result['status'] == 'smoke_survived' else 1


if __name__ == '__main__':
    raise SystemExit(main())
