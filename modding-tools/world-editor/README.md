# World and story editor

Edits Ascension to the Throne content by building numbered PAK overlays:
`ResourceN.pak`. The original archives are read, a JSON model is edited, and the
result is exported as the next free slot, so the game engine needs no changes
and every edit is a file you can copy in and out.

One directory holds both editors because they share the same overlay pipeline
and the same `worldctl.py` front end:

| Module | Role |
| --- | --- |
| `world.py` | continents, placements, towns/houses, army definitions and positions, snapping, validation, overlay export |
| `forests.py` | `.fst` forest zones with tree records, terrain grounding, validation, overlay export |
| `story.py` | quests, triggers and conversations as a JSON index with dialogue trees, search, validation, patching and overlay export |
| `gres.py` | GRES PAK reader/writer, slot overlay, deterministic output, build-identity trailer |
| `lua_data.py` | Lua 5.1 chunk decoder/evaluator (float32 numbers, 32-bit `size_t`), cp1251 source emitter and parser |
| `lua_patch.py` | inserts literal/table edits into a logic chunk before its final `RETURN`, appends new prototypes, copies functions by reference |
| `lua_expr.py` | compiles the JSON expression language into leaf Lua prototypes for conditions and actions |
| `luadis.py` | opcode table and byte reader shared by the Lua modules |
| `heightmap.py` | `.nmph` elevation data and sampling |
| `render.py` | hillshaded top-down SVG/PNG maps |
| `worldserve.py` | localhost preview server with a patch endpoint |
| `worldctl.py` | the command-line front end for everything above |

## How it works

- The game resolves `ResourceN.pak` slots by number; the highest slot wins.
  An overlay only contains the modules that changed, so a small PAK can replace
  a quest table without shipping the whole archive.
- World modules (`continentN{towns,npcs,saos,armies,armypos}.lua`) and story
  modules (`continentN{quests,triggers,conversations}.lua`) are Lua 5.1 bytecode
  built with float32 numbers and 32-bit `size_t`. `lua_data` reads them;
  `lua_patch` edits them without recompiling: assignments are inserted before
  the final `RETURN` and every existing instruction, jump, prototype and local
  stays intact.
- The JSON model is the shared interface. Humans edit it with any tool, agents
  query and patch it, and the CLI applies typed operations and refuses
  references that do not resolve.
- Exports carry a build-identity trailer (`ATTTID1` + JSON). `overlay-check`
  compares it against the target install and reports `match` or the exact
  differing files.

## Requirements

- Python 3.8 or newer, standard library only.
- A retail game folder with its `Resource*.pak` archives.

Run everything from this directory:

```sh
cd modding-tools/world-editor
python3 worldctl.py --help
```

## World editing

```sh
# decode continents into a JSON model (and render maps)
python3 worldctl.py extract --game <game> --continents 1 --out world.json --map

# inspect and search
python3 worldctl.py info world.json
python3 worldctl.py find world.json --name <text>

# single typed edits
python3 worldctl.py move world.json --continent 1 --town <town> --house <house> \
    --kind npc --index 1 --x 5 --z 5
python3 worldctl.py add-town world.json --continent 1 --town <name> ...
python3 worldctl.py add-house world.json --continent 1 --town <town> --house <name> ...
python3 worldctl.py add-army world.json --continent 1 --army <name> ...

# batch edits (attt-world-patch/1)
python3 worldctl.py patch world.json edits.json --dry-run
```

Operations accepted by `patch`: `move`, `add`, `remove`, `clone`, `rotate`,
`move-army`, `add-town`, `add-house`, `remove-town`, `remove-house`,
`add-army`, `remove-army`, `snap`. Every operation names its target by
continent, town, house and `kind` (`npc`, `object` or `tree`), plus an optional
`index` or `name`.

Validate and export:

```sh
python3 worldctl.py validate world.json --game <game>
python3 worldctl.py export world.json --game <game> --out out/
```

`export` refuses to write when validation has errors, picks the next free slot
unless `--slot` is given, and refuses to overwrite an existing file without
`--overwrite`. Deploy by copying `out/ResourceN.pak` into the game folder (back
up any file with that name first), then confirm with:

```sh
python3 worldctl.py overlay-check out/ResourceN.pak --game <game> --json
```

## Forest editing

```sh
python3 worldctl.py forest-extract --game <game> --out forests/
python3 worldctl.py forest-add forests/forests.json --continent 1 --zone <zone> ...
python3 worldctl.py forest-move forests/forests.json --continent 1 --zone <zone> --index 3 ...
python3 worldctl.py forest-remove forests/forests.json --continent 1 --zone <zone> --index 3
python3 worldctl.py forest-validate forests/forests.json --game <game>
python3 worldctl.py forest-export forests/forests.json --game <game> --out out/
```

## Story editing

```sh
python3 worldctl.py story-extract --game <game> --out story.json
python3 worldctl.py story-info story.json
python3 worldctl.py story-find story.json --kind dialogue --text <text>
python3 worldctl.py story-dialogue story.json <dialogue> --json
python3 worldctl.py story-validate story.json
```

`story-patch` applies an `attt-story-patch/1` document of operations:

```json
{
  "format": "attt-story-patch/1",
  "operations": [
    {"kind": "quest", "continent": 1, "name": "q1",
     "field": "display_name", "value": "New title"},
    {"kind": "trigger", "continent": 1, "name": "q1.sq.Start.trigger",
     "field": "condition",
     "value": {"$expr": {"op": "and", "args": [
       {"call": "Conditions.Check", "args": [{"global": "Current"}, "Warrior"]},
       {"op": "eq", "args": [1, 1]}]}}},
    {"kind": "dialogue", "continent": 1, "name": "cIntro",
     "path": "root.1.1", "field": "speech", "value": "New line"}
  ]
}
```

Supported operations per record:

| Operation | Meaning |
| --- | --- |
| `field` + `value` | set a literal field (`display_name`, `description`, `level`, `want_live`, `who`, `speech`, `condition`, `action`, `do`) |
| `create` + object | create a whole quest, trigger or dialogue record/reply |
| `remove: true` | delete a record or dialogue node |

Function-valued fields accept three forms: `{"$ref": [keys]}` copies an existing
function from the same module, `{"$expr": ...}` compiles a new leaf function,
and literal booleans stay booleans. Functions can only replace `Condition`,
`Action` or `Do`, only on bytecode modules.

The expression language supports literals, `{"global": name}` and
`{"global": [name, key, ...]}`, `and`/`or`/`not`, `seq` (evaluate in order,
keep the last), comparisons (`eq ne lt le gt ge`), arithmetic
(`add sub mul div mod pow`), `neg`, `len`, `concat`, calls
(`{"call": "Table.Method", "args": [...], "method": true}`) and
`{"if": cond, "then": expr, "else": expr}`. Compiled functions take no
parameters and have no upvalues or nested functions.

Run a dry run first; it prints the changes and the source-file identity. Copy
that identity block into the patch as `identity` to make the patch refuse to
build against a different game build:

```sh
python3 worldctl.py story-patch patch.json --game <game> --dry-run
python3 worldctl.py story-patch patch.json --game <game> --out out/ --slot 3
```

`story-patch` overlays the changed story modules with the same slot rules as
world export. `value_file` in an operation reads a string value from a file
relative to the patch, which is convenient for long dialogue lines.

## Preview server

```sh
python3 worldserve.py world.json --game <game> [--forests forests/forests.json]
```

Serves the rendered map, entity listings and validation on localhost and applies
batch patches with an explicit dry-run step. It never writes to the game
archives; it only saves the JSON model when a request asks for it.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

95 tests, no game installation required: synthetic PAK and Lua chunks cover the
archive format, bytecode patching, expression compilation, overlay identity and
the CLI.

## Limits

- Overlays replace whole modules; there is no partial-table merge at runtime.
- Story functions are leaf prototypes: no parameters, upvalues, loops or
  statements. Anything richer needs a Lua source overlay or a future statement
  compiler.
- Quest subquest `Start`/`Finish` action tables are not exposed as story fields
  yet; triggers and dialogues are.
- Quadtree, grass and tessellation data are not decoded.
- The engine format is reverse-engineered; keep a backup of every archive slot
  you deploy to.
