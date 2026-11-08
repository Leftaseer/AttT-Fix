# Modding tools

Tooling for editing Ascension to the Throne content without engine changes:
reading and writing `ResourceN.pak` overlays, decoding and patching the game's
Lua 5.1 data modules, and editing world, forest and story data.

This branch (`modding-tools`) is based on the decompilation history, but the
tools themselves live outside `decomp/` so that merges from the decompilation
branch never conflict with them.

## Layout

- `world-editor/` — edits world, forest and story content through numbered PAK
  overlays: GRES archive I/O, Lua 5.1 bytecode decoding and expression
  compilation, placement/town/army/forest/quest/trigger/dialogue editing,
  validation, build-identity checks, a preview server, and the `worldctl.py`
  command-line front end. See its [README](world-editor/README.md).

Each future tool gets its own sibling directory here. World, forest and story
editing share one directory because they reuse the same archive and bytecode
layer and the same CLI.

## Running

```sh
cd modding-tools/world-editor
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
