# Transferred project artifacts — review, 2026-11-02

Reference directory: `/home/attt-dev/AttT-decomp/`.
Active checkout remains `/home/attt-dev/work/AttT-Fix`, branch `decomp/continue`.
The user warned that the transferred code may be stale. No source tree or game asset was copied over the
active project. Instructions embedded in old session notes describe that session; they do not replace the
current user's workspace, deployment or game-launch constraints.

| Material | Finding / use |
|---|---|
| `context.md` | Historical mod research through October 18: formats, engine/Lua interfaces, rendering, sound, releases and reverted HD experiments. Useful technical context, not current verification evidence. |
| `AttT-Fix/` | Older checkout, commit `d7f7411` on `original_files`. It contains the original games, not the current decompilation branch. Its copied worktree has modifications; it was not reset or merged. |
| `src/attfix/`, `AttT-Fix/src/` | Both identify as AttTFix 2.1.0; differences require review before any reuse. They do not supersede the active code or the supplied 2.1.2 binary. |
| `release/AttTFix-2.1.2/AttTFix-2.1.2.zip` | Its `dinput8.dll` SHA-256 matches the v57 compatibility profile exactly: `202caa2282681878e84022dab6d72f3d72fea619981f3a68c592392ab29b5a79`. Useful for isolated tests without accessing the Windows installation. |
| `AttT-Fix/original_files/Original/depot_289201/` | Original EXE, resource archives, runtime DLLs, graphics settings and six saves. This can supply an isolated WSL test copy. |
| `orig/src_lua*`, `orig/lua*` | Compiled/decompiled original Lua; useful for building valid world/army/inventory fixture states and tracing real script APIs. |
| `ghidra/` | Earlier decompiler export and function inventory; useful as supplementary reconstruction evidence, not a replacement for current calling-convention metadata. |
| `models_probe/`, `hd/`, `fonts/`, `menu_extract/` | Asset-format research and experiments. The historical notes say the HD hero experiment was reverted; it was not reintroduced. |
| `perf/`, `debug/`, `atttfix-test/`, `build/` | Historical profiling, crash artifacts and binaries. Without matching executable/tool/input identities they are diagnosis references, not passing results for v57. |
| `valkyrie/` | Other-game research/assets; Valkyrie remains outside the active task. |

The transferred original EXE has SHA-256
`b8c69b8ac3b424c037f400654f9376fe6c8a403743cf0a45e3a2c71beae01b04`.
The active rebuild input has SHA-256
`6b452a1f4f5d4d8761444638a0886ef54390af149db6e679ca84b536ae179961`.
They differ at exactly two file offsets, `0x146` and `0x188`: the LAA flag and PE checksum.
The original engine payload bytes are identical. The existing active build input was retained.

Transferred PAK headers were checked, rather than assuming Git LFS files contained real data:

| Archive | Bytes | Format | Entries |
|---|---:|---|---:|
| `Resource0.pak` | 1,241,888,384 | GRES 100 | 7,349 |
| `Resource1.pak` | 91,153,649 | GRES 100 | 53 |
| `Localization.pak` | 91,153,649 | GRES 100 | 53 |

These files are not the same asset configuration as the user's current Steam installation with its later
overrides. An original/rebuilt comparison must use the same asset set and settings on both sides.

## Wine readiness

Update after this review: a new local Wine runtime/prefix and headless services are installed; a synthetic
PE32 graphics/audio probe passes. Actual game integration is pending. See [WINE_TESTING.md](WINE_TESTING.md)
for provenance, commands, evidence and the automatic approval rejection of the original-game launch.

At the initial review, no Wine executable, wineserver, Xvfb, xdotool or matchbox window manager was found;
no copied Wine prefix was found in the transferred material. No game was launched during this review.
The existing active-project scenario documentation (`tools/gametests/README.md`, `tools/rungame.py`) describes
the previous `/opt/re` setup, 32-bit Wine, a native `d3dx9_29.dll`, software graphics and an isolated prefix.
Those historical paths and dependencies must be adapted before running it here.

The old runner also deletes/recreates its named run directory. It must not be pointed at transferred artifacts
or existing test results. Any future Wine runner should create a fresh directory under `/home/attt-dev/work`,
keep mutable saves/configuration separate, and preserve logs and screenshots. Windows game launches and
deployment into the Steam installation remain the user's responsibility.

Machine-readable asset/save identities and dependency checks are saved in
`/home/attt-dev/work/verification-v57-20261102/transferred-artifacts.json`.
