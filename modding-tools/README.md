# Modding tools

AttT Modding Studio edits Ascension to the Throne content through
`ResourceN.pak` overlays. It brings world, campaign, balance and model tools
into one local HTML workspace and one command-line entry point.

This branch (`modding-tools`) is based on the decompilation history, but the
tools themselves live outside `decomp/` so that merges from the decompilation
branch never conflict with them.

## Layout

- `world-editor/` — edits world, forest and story content through numbered PAK
  overlays: GRES archive I/O, Lua 5.1 bytecode decoding and expression
  compilation, placement/town/army/forest/quest/trigger/dialogue editing,
  validation, build-identity checks, a preview server, and the `worldctl.py`
  command-line front end. See its [README](world-editor/README.md).
- `balance-studio/` — offline browser editor for units, spells, encounters and
  models in Ascension to the Throne and Valkyrie. Open `Balance Studio.html`
  in Edge or Chrome. See the [Balance Studio guide](balance-studio/README.md).

## HTML workspace

Run with Python 3.8 or newer. In Windows PowerShell, from this directory:

```powershell
py -3 attt.py serve --game "E:\Games\Ascension to the Throne" --world "my-world.json"
```

On Linux or WSL, use `python3` and the game folder's Linux path. The launcher
opens the local workspace in your browser and prints its address. It creates the
world JSON from the selected archives if the file does not exist. Pass
`--edition valkyrie` for Valkyrie or `--prefer-localization` to use
`Localization.pak` in slot 1. The workspace reads the same archive selection
in both tabs. Use consecutive numbered PAK slots starting at zero.

1. Open **World & campaign** to inspect the terrain map and apply World Editor
   [batch operations](world-editor/README.md#world-editing). **Apply and save**
   updates the world project JSON. Forest and story commands are available in
   the CLI. Use `--forests` to display an extracted forest project in the map.
2. Choose **Use world draft in Balance**. New or moved armies appear in
   Balance Studio. Edit rosters, encounter radius, unit stats or spells as usual.
3. Choose **Review export → Download PAK**. The download includes the world
   draft and balance edits in one archive, with overlapping army scripts built
   from the edited world. Install the combined PAK in the next slot after the
   base archive set. Export model changes separately after this slot.

Load the draft into Balance again after editing the world. Restart the launcher
after changing the world JSON or archives with another process. Save a Balance
Studio project JSON and open it in the new workspace to move profiles from the
standalone HTML file. You can still open `balance-studio/Balance Studio.html`
directly for offline balance and model editing.

## CLI for agents

Use `python3 attt.py --help`. World, forest and story commands use Python.
Balance commands use Node.js 22 or newer from your PATH. Set `ATTT_NODE` to
an explicit Node executable if needed.

```sh
python3 attt.py world --help
python3 attt.py world extract --game GAME_FOLDER --continents 1 --out world.json
python3 attt.py world export world.json --game GAME_FOLDER --out WORLD_OUT

python3 attt.py balance list --game GAME_FOLDER --kind armies --search hunter
python3 attt.py balance show --game GAME_FOLDER --kind units --id uPeasant
python3 attt.py balance plan --game GAME_FOLDER --project balance.json
python3 attt.py balance export --game GAME_FOLDER --project balance.json \
  --world-overlay WORLD_OUT/Resource2.pak --out COMBINED_OUT

python3 attt.py overlaps Resource2.pak Resource3.pak
```

The balance commands emit JSON. `plan` reports proposed, skipped and already
matching edits. `export` uses the selected profile unless you pass `--profile ID`.
Provide an existing output folder. `--world-overlay` combines a World Editor
world export at the next available slot. Use `--overlay` to include a PAK that
will be installed separately, such as a story or forest overlay. To check the
order of independently exported archives, `overlaps` lists duplicate resources
and their winning slots.

## World Editor tests

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
