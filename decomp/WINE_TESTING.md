# WSL Wine testing — updated 2026-11-03

Wine is installed under `/home/attt-dev/work/wine-runtime/`, without root installation or changes to the
Windows game installation. The private prefix is initialized. A **standalone synthetic PE32 probe passed**;
the original EXE and both v57 builds also pass the initial developer world-start smoke test below.

Newest evidence: [extended save and continent checks](WINE_EXTENDED_RESULTS.md), with ten more passing
runs across other saves, native timing controls and original/plain/mod-enabled continent-2 transitions.

The latest milestone compares original/plain save loading, write-save/reload and bounded tactical input
with identical test-only Lua assets, and checks actual AttTFix activation/runtime counters. See
[WINE_SHARED_RESULTS.md](WINE_SHARED_RESULTS.md) for the seven completed runs, exact serialized-state
comparisons, input limitations and reproduction. The tooling suite now passes 42 tests.

The initial original-game launch was rejected by automatic approval review. The user subsequently explicitly
authorized running anything within the home directory. The same home-directory Wine launch was then
approved and executed; there was no indirect workaround. All game runs use private test copies in WSL.
The earlier synthetic probe remains separate evidence containing no game code or assets.

## Initial game integration results

### Normal startup, menus and copied saves

The next cohort is `/home/attt-dev/work/wine-tests/menu-load-v57-20261102.json`. All runs use normal
startup, 800x600 and WineD3D, with unchanged v57 binaries. Six smoke checks pass; one required-marker check
fails as retained below. No run produced a game error file. Screenshots were visually reviewed.

| Scenario | Run directory under the evidence root | Result |
|---|---|---|
| Original, no input, 60 s | `original-normal-_9duzv4z` | Intro video visibly plays; still in video at capture |
| v57 plain, no input, 60 s | `v57-plain-normal-tn5o4l96` | Intro video visibly plays; still in video at capture |
| Original, Escape at 5/12/20 s, 35 s | `original-menu-keys-sdyy42gp` | Main menu visible |
| v57 plain, same keys/settings/saves, 35 s | `v57-plain-menu-keys-9r1lue75` | Main menu visible, visually matches original; PNGs are not identical |
| Debug, old `skipintro` fixture, no keys, 60 s | `v57-debug-load-game0-n89tlnyp` | Required world marker absent; intro still playing; **failed**, not a game crash |
| Debug, copied `game0`, Escape at 5/12/20 s, 60 s | `v57-debug-load-game0-keys-1vdeojtm` | Load-screen selection logged; world-scene marker 1; loaded world behind pause/debug menus |
| Debug, copied `game00`, same keys/settings, 60 s | `v57-debug-load-game00-keys-njaa1ngg` | Load-screen selection logged; world-scene marker 1; tactical "Your turn" screen behind debug menu |

The AttTFix compatibility profile reserves original `CEngine::Init` (`0044F2E0`), so the old rewritten-init
`skipintro` hook is bypassed even though its flag logs as enabled. Do not rely on that flag as evidence that
videos were skipped. The failed attempt demonstrated that a surviving process without the required state
marker is rejected. External Escape input reached the menu in original/plain, and enabled debug save loading
without changing the game EXE or weakening its native compatibility reservations.

`tools/scenarios/load-game0.txt` and `load-game00.txt` drive the existing debug-only harness. They request a
named save through the load screen, then log `scenario: world-scene 1` only if a world GUI scene exists after
the harness reports loading complete. Use `--require-log 'scenario: world-scene 1'`. The original/plain EXEs
do not implement this injection harness; these save checks are not comparisons against original save-state
execution. The late Escape can pause an already loaded world, as in the game0 capture. The tactical capture
proves entry into that screen, not correct combat actions or turn processing.

The maintained runner accepts repeated `--key-at SECONDS:KEY` events, holds each key for 0.5 s through X11,
and records requested/completed times. It also records hashes of copied save inputs and injected test input.
The two successful save runs used identical save inputs; the supplied source files still match those hashes.
All **37 tooling tests** pass, including malformed-key-event controls. Log:
`/home/attt-dev/work/wine-runtime/tooling-tests-menu-load.log`.

Next: baseline save loading via original/plain UI, write-save/reload in private directories, bounded world
and combat actions, and actual AttTFix 2.1.2 activation/effects. No mod was installed in this cohort.

### Developer world start

The original, v57 plain and v57 debug EXEs each survived **35 seconds** of developer world start (`-nologo`),
at 800x600 with the same WineD3D runtime and hash-matched original assets. No mod, saves or scripted inputs
were injected. No game error files appeared. Screenshots were visually reviewed: all render the opening
world/dialogue scene; debug also displays its menu and logs `debug menu ready (Ctrl+Alt+D)`.
These are qualitative scene checks, not pixel comparisons; animation poses differ with timing.

Evidence root: `/home/attt-dev/work/wine-tests/`:

| EXE | Run directory | Verdict |
|---|---|---|
| Original | `original-menu-7lr0xqnp` | smoke survived, opening scene visible |
| v57 plain | `v57-plain-menu-ilqhahfn` | smoke survived, opening scene visible |
| v57 debug | `v57-debug-world-repeat-iehd4k3o` | smoke survived, opening scene and debug menu visible; initialization marker seen |

Each directory contains `result.json`, `screen.png`, XWD capture, Wine/service logs and the private game
copy. `world-start-v57-20261102.json` aggregates identities/results and records effective launch arguments.
The first two labels say "menu" because the initial runner unconditionally passed `-nologo`; that switch
also bypasses the menu and starts a developer world. The runner now defaults to normal startup and requires
explicit `--launch-mode developer` for this scenario, recording that choice in the manifest.

An earlier debug attempt, `v57-debug-world-_0d4hu3l`, ended with runner status 143 before final capture.
Its cause is unestablished; `interruption.json` records it as incomplete, not a game crash or a pass. It was
repeated successfully. Normal startup/videos/menu navigation, save/load, combat, and AttTFix activation
remain untested in these runs. Both v57 executable hashes are unchanged from the delivered checkpoint.

## Installed runtime and provenance

| Component | Configuration |
|---|---|
| Wine | WineHQ stable `11.0.0.0~resolute-1`, reports `wine-11.0`; amd64 package with PE32 support through new WoW64 |
| Host | Ubuntu 26.04.1, x86_64 WSL |
| Prefix | `/home/attt-dev/work/wine-runtime/prefix`, `WINEARCH=win64`, Windows 10 |
| Graphics | WineD3D / Mesa llvmpipe software rendering, four worker threads |
| Legacy D3DX | Microsoft x86 `d3dx9_29.dll` in the prefix's `windows/syswow64`, native override |
| Display | Authenticated Xvfb, private high-number display, abstract Unix socket; no TCP or filesystem X11 listener |
| Audio | Private PulseAudio Unix socket and null sink; DirectSound8 initialization passed |
| Runtime dependencies | 144 Ubuntu packages extracted locally; no `dpkg` installation/configuration |

Wine came from the [official WineHQ Ubuntu repository](https://dl.winehq.org/wine-builds/ubuntu/dists/resolute/).
Its signed InRelease and Packages digest were verified using WineHQ key
`D43F640145369C51D786DDEA76F1A20FF987672F`. Wine's package SHA-256 is
`3ea2463584eb0891f3e1230c3d1d71d09c9f3a03f696d46d98d79bce17808194`.
The Ubuntu package files were checked against the apt-provided digests before extraction.

The DLL was extracted from Microsoft's [DirectX June 2010 runtime](https://www.microsoft.com/en-us/download/details.aspx?id=8109),
`Feb2006_d3dx9_29_x86.cab`; no Windows installer was run. The redist SHA-256 is
`053f76dcbb28802e23341b6a787e3b0791c0fa5c8d4d011b1044172dbf89c73b` and the extracted DLL SHA-256 is
`c5e21c18f8c79bc517da59e3192c39ea73bdcaf85867628187f6b3cca07dd21f`.
VC80 libraries in the probe are Wine's implementations, not a separately installed Microsoft VC80 redist.

Downloaded packages, signed repository metadata, `ubuntu-downloads.json` with URLs/digests, bootstrap
logs, `env.sh` and `installation.json` stay in the runtime directory. They are not committed as game assets.
To reconstruct on this host: verify the recorded package hashes, extract the `.deb` files with
`dpkg-deb -x PACKAGE runtime/root`, extract the native D3DX CAB with cabextract, build the shim below,
then initialize a new private prefix with `wineboot -u` on the private display/audio services before copying
the native DLL into `syswow64`. The retained `boot.py` records the initial setup; its failed optional window
manager attempt was removed from the maintained runner. Never initialize over an unrelated prefix.

## Probe and evidence

From `/home/attt-dev/work/AttT-Fix`:

```sh
source /home/attt-dev/env.sh
clang --target=x86_64-linux-gnu -shared -fPIC -nostdlib -fuse-ld=lld \
  decomp/tools/wine_xvfb_shim.c \
  -o /home/attt-dev/work/wine-runtime/bind_loopback.so
python3 -u -I decomp/tools/wine_probe.py
```

The runner starts its own services and stops only its private prefix/server and service processes.
The application sandbox may require approval for the local IPC sockets. Wine and the Windows probe do
not load the Xvfb shim. Xvfb needs it because this extracted build hardcodes `/usr/bin/xkbcomp`; the shim
redirects that helper to `XKB_BINDIR`. It avoids modifications to host files or WSLg's read-only X11 directory.

Passing evidence: `/home/attt-dev/work/wine-probes/probe-rui6xcff/`, including source-built PE32 probe,
console log, display/audio logs, screenshot capture and `result.json`. The executable SHA-256 is
`bb6a896bdcf09b0bf2283c6c2e2415386a0480ae456dcac2f7f0e9ca08cec29c`; exit code 0 and `PROBE_PASSED`.
Checks: 32-bit process, VC80 DLL loads, native D3DX version, Direct3D9 device creation, render-target
clear/readback with exact color equality, native `ps_2_0` effect compilation and DirectSound8 creation.
The screenshot is captured after the probe closes; the color readback assertion is the rendering evidence.
Expected diagnostics include unavailable `/dev/dri` access (software rendering is selected), a disabled
winemenubuilder startup entry and Wine implementation notices. None failed the probe.

The offline tooling suite passes **35 tests**, including six new checks for input preservation, fresh-directory
enforcement, private environment settings, both screenshot byte orders, truncated captures and cleanup after
a wineserver timeout. Log: `/home/attt-dev/work/wine-runtime/tooling-tests.log`.

## Game runner and remaining scenarios

`tools/wine_game_test.py --help` describes the prepared runner. It requires explicit EXE and asset paths.
Each run creates a new directory under `/home/attt-dev/work/wine-tests/`; no prior run is overwritten.
The PAKs are reflinked or copied, DLLs/MSS plugins are copied, configuration is private, and saves are copied
only when requested. Shared prefix use is locked. The runner records executable and archive identities,
runtime/backend, elapsed time, exit/crash status, logs and a PNG screenshot. A required literal log marker
can gate a run. It does not install or activate AttTFix automatically.

`smoke_survived` means the process stayed alive for the requested interval without a game error file and
with any required log marker. A blank or broken menu can still survive: inspect the screenshot and logs.
These directories isolate test data; Wine is not a security boundary for untrusted Windows programs.

Continue with:

1. Original/plain UI save loading as a baseline for the successful debug harness checks above.
2. Menu interactions and a new game: compare visible state and errors with the original.
3. Copies of the supplied saves: world movement, UI, combat actions, write-save/reload; use bounded scenarios.
4. AttTFix 2.1.2 and debug menu in separate runs: verify actual hook activation and effects from logs and state.
5. Optional DXVK x32 backend only after the WineD3D baseline works; keep backend evidence separate.

Wine adds integration coverage to emulation, differential fixtures and native Windows playtests. Software
rendering timings do not establish native Windows speedups, and a Wine-specific failure needs comparison
with the original EXE before changing game code. This setup did not alter either v57 binary or delivery package.
