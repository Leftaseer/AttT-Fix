# Modding tools

Tooling for editing Ascension to the Throne content without engine changes:
reading and writing `ResourceN.pak` overlays, decoding and patching the game's
Lua 5.1 data modules, and editing world, forest and story data.

This branch (`modding-tools`) is based on the decompilation history, but the
tools themselves live outside `decomp/` so that merges from the decompilation
branch never conflict with them.

## Layout

- `world/` — world and story data toolkit: GRES PAK reader/writer, Lua bytecode
  decoder and expression compiler, quest/trigger/dialogue and placement CRUD,
  validation, overlay export with build identity, preview server, and the
  `worldctl.py` command-line front end.

Each future tool gets its own sibling directory here.

## Running

```sh
cd modding-tools/world
python3 worldctl.py --help
python3 -m unittest discover -s tests
```

## Branch workflow

Decompilation continues on `decomp/continue`. To pick up new engine work:

```sh
git fetch origin
git merge origin/decomp/continue
```

Fetched data changes stay under `decomp/`; the toolkit and its tests are not
touched by those merges.
