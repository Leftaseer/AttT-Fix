#!/usr/bin/env python3
"""Build and run a synthetic PE32 graphics/audio probe. No game code or assets are used."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wine_game_test', HERE / 'wine_game_test.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def build(output, includes):
    imports = {
        'KERNEL32.dll': ['GetStdHandle@4', 'WriteFile@20', 'ExitProcess@4', 'LoadLibraryA@4',
                         'GetProcAddress@8', 'GetModuleHandleA@4', 'Sleep@4'],
        'USER32.dll': ['DefWindowProcA@16', 'RegisterClassA@4', 'CreateWindowExA@48', 'DestroyWindow@4'],
        # MinGW's inline math helpers are emitted by these headers; none is called by the probe.
        'MSVCR80.dll': ['memset', 'memcpy', 'sinh', 'cosh', 'tanh', 'exp', 'frexp', 'ldexp', 'hypot', 'pow'],
    }
    libraries = []
    for dll, names in imports.items():
        definition, library = output / (dll + '.def'), output / (dll + '.lib')
        definition.write_text('LIBRARY ' + dll + '\nEXPORTS\n' + '\n'.join(names) + '\n')
        subprocess.run(['llvm-dlltool', '-m', 'i386', '-k', '-d', str(definition), '-l', str(library)], check=True)
        libraries.append(str(library))
    obj, exe = output / 'probe.obj', output / 'RuntimeProbe.exe'
    subprocess.run(['clang', '--target=i686-pc-windows-msvc', '-O1', '-fms-extensions', '-fgnuc-version=4.2.1',
                    '-D_X86_', '-isystem', str(includes), '-fno-exceptions', '-fno-rtti', '-fno-stack-protector',
                    '-fno-builtin', '-ffreestanding', '-c', str(HERE / 'wine_probe.cpp'), '-o', str(obj)], check=True)
    subprocess.run(['lld-link', '/machine:x86', '/entry:probe_entry', '/subsystem:console', '/nodefaultlib',
                    '/safeseh:no', '/out:' + str(exe), str(obj), *libraries], check=True)
    return exe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=Path.home() / 'work/wine-runtime')
    parser.add_argument('--runs', type=Path, default=Path.home() / 'work/wine-probes')
    parser.add_argument('--includes', type=Path, default=os.environ.get('MINGW_INCLUDE'))
    args = parser.parse_args()
    if args.includes is None:
        parser.error('source ~/env.sh or supply --includes (MinGW headers)')
    runtime = args.runtime.resolve()
    args.runs.mkdir(parents=True, exist_ok=True)
    with (runtime / 'prefix.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output = Path(tempfile.mkdtemp(prefix='probe-', dir=args.runs.resolve()))
        print('Probe directory:', output, flush=True)
        exe = build(output, args.includes)
        services = runner.Services(runtime, output, 800, 600)
        result = {'status': 'preparing', 'exe_sha256': runner.sha256(exe), 'game_code_or_assets': False}
        try:
            env = services.start()
            process = services.start_process(['wine', str(exe)], 'probe', cwd=output)
            result['exit_code'] = process.wait(timeout=120)
            subprocess.run(['xwd', '-root', '-silent', '-out', str(output / 'screen.xwd')],
                           env=env, check=True, timeout=15)
            runner.xwd_to_png(output / 'screen.xwd', output / 'screen.png')
            log = (output / 'probe.log').read_text(errors='replace')
            result['status'] = 'passed' if result['exit_code'] == 0 and 'PROBE_PASSED' in log else 'failed'
            print(log, flush=True)
        except Exception as error:
            result.update(status='setup_or_probe_error', error=str(error))
            raise
        finally:
            try:
                services.stop()
            finally:
                (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps(result, indent=2), flush=True)
        return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
