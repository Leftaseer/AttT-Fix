# WSL Wine testing — 2026-11-02

Wine is installed under `/home/attt-dev/work/wine-runtime/`, without root installation or changes to the
Windows game installation. The private prefix is initialized. A **standalone synthetic PE32 probe passed**;
no original or rebuilt game EXE has been launched by the agent.

The original-game launch was rejected by automatic approval review, which cited an existing restriction
against launching the game on Windows or Wine. That launch was not retried through another command or
wrapper. Game integration results remain pending. The synthetic probe is a separate program containing
no game code and loading no game executable or assets.

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

## Game runner prepared; integration runs pending

`tools/wine_game_test.py --help` describes the prepared runner. It requires explicit EXE and asset paths.
Each run creates a new directory under `/home/attt-dev/work/wine-tests/`; no prior run is overwritten.
The PAKs are reflinked or copied, DLLs/MSS plugins are copied, configuration is private, and saves are copied
only when requested. Shared prefix use is locked. The runner records executable and archive identities,
runtime/backend, elapsed time, exit/crash status, logs and a PNG screenshot. A required literal log marker
can gate a run. It does not install or activate AttTFix automatically.

`smoke_survived` means the process stayed alive for the requested interval without a game error file and
with any required log marker. A blank or broken menu can still survive: inspect the screenshot and logs.
These directories isolate test data; Wine is not a security boundary for untrusted Windows programs.

After the game-launch restriction is resolved, use this order:

1. Original EXE, original transferred assets, no mod: establish a stable menu/startup baseline.
2. v57 plain and debug EXEs with the same assets/settings: compare visible state and errors with baseline.
3. Copies of the supplied saves: loading, world movement, UI, combat, save/reload; use bounded scenarios.
4. AttTFix 2.1.2 and debug menu in separate runs: verify actual hook activation and effects from logs and state.
5. Optional DXVK x32 backend only after the WineD3D baseline works; keep backend evidence separate.

Wine adds integration coverage to emulation, differential fixtures and native Windows playtests. Software
rendering timings do not establish native Windows speedups, and a Wine-specific failure needs comparison
with the original EXE before changing game code. This setup did not alter either v57 binary or delivery package.
