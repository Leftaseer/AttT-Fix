# Amazon model experiment

Both prototypes give Amazon distinct model and texture paths so Helga can keep using the shared stock assets.

- **Remaster** keeps the stock palette, outfit and proportions. It refines the two nearest skinned meshes, adds relief to the shoulder guard and leather, and rebuilds the spear with a round shaft and a beveled blade. The original animation tracks, object slots and gameplay data are retained. The closest model goes from 4,347 to 18,054 triangles. The 2,048-pixel texture uses the stock art with new engraved metal, material detail, and a complete mip chain.
- **Bronze and teal** is the earlier visual experiment. It uses a teal cuirass and boots, a larger shoulder guard, and a wider spear blade.

## Build

Use Python with NumPy and Pillow and Node.js 22 or later. Put `skm.py`, `pn.py`, and `dds.py` from the archived HD tools (`/home/attt-dev/AttT-decomp/hd/hd_tools.tgz` in the project workspace) on `PYTHONPATH`. Extract the five `amazon0.skm` through `amazon4.skm` meshes and `amazon.dds` from a stock game archive into a working folder.

```sh
python3 remaster.py STOCK_ASSETS REWORKED_ASSETS
node pack.cjs attt ORIGINAL_GAME REWORKED_ASSETS ORIGINAL_OUTPUT
node pack.cjs valkyrie VALKYRIE_GAME REWORKED_ASSETS VALKYRIE_OUTPUT
```

Run the last command separately for each Valkyrie language. To build the bronze-and-teal experiment, substitute `rework.py` in the first command. The packer selects the next archive slot and checks the result against the complete effective unit table. It samples the beginning, middle, and end of each Amazon animation and checks that ranged attacks still designate the spear as the projectile.

## Install

Copy the generated archive alongside the game's `Resource0.pak`. For the tested stock installations, use these paths from the release ZIP.

| Game | Archive |
| --- | --- |
| Original, English | `Original-English/Resource2.pak` |
| Valkyrie, English | `Valkyrie-English/Resource1.pak` |
| Valkyrie, Russian | `Valkyrie-Russian/Resource2.pak` |

If you installed the earlier Amazon experiment, swap its archive for this edition's remaster archive. Both variants use the same asset names. If the filename is taken by another add-on, keep your existing file and generate a combined setup. The replacement ships a complete `units.lua`, and the last archive providing that script takes precedence. For a Balance Studio profile, open the stock archives plus the Amazon archive in the editor and export the profile again into the next slot. Keep both archives installed. Remove the Amazon archive to revert on a stock setup. If you built a combined setup, re-export the profile against the stock archives to revert the appearance.

The comparison shows both models at the same battle-idle frame and zoom. The included GLB is a textured pose for inspection in Blender. It contains posed geometry and separate body, shoulder, and spear meshes.

## Generated texture overlay

The generated repaint uses the remaster's UVs and adds only `bsamazon.dds`. Keep the remaster installed and place the overlay in the next consecutive resource slot. With the remaster as the last installed archive, that is `Resource3.pak` for original English and Valkyrie Russian, and `Resource2.pak` for Valkyrie English.

To reproduce the DDS from the square generated atlas, run `python3 fit_texture.py STOCK_AMAZON_DDS GENERATED_ATLAS OUTPUT_FOLDER` with the same Python dependencies as the remaster. This prepares the 2,048-pixel atlas, preserves the stock alpha and repairs small areas along UV gutters. The overlay is a GRES archive with one entry, `bsamazon.dds`, made using `makeArchive` from Balance Studio's `core.js`.

## Shared Amazon and Helga update

The shared package uses the stock asset names and contains no unit scripts. It applies the remastered mesh, generated texture, cleaner hair mask and updated idle and run tracks to both `uAmazon` and `uHelga`. Both units retain the stock 60-bone body track and two equipment tracks. Idle and run keep their original frame counts and the event poses used by the unit tables. Melee, ranged, defense and death clips still come from the game.

Extract the stock Amazon meshes, DDS and SKAs. Use the generated square atlas from the previous texture experiment, and add `ska.py` and `pose.py` from the archived HD tools to `PYTHONPATH`.

```sh
python3 fit_texture.py STOCK_ASSETS/amazon.dds GENERATED_ATLAS TEXTURES --clean-hair
python3 remaster.py STOCK_ASSETS SHARED_ASSETS --shared-texture TEXTURES/bsamazon.dds
python3 animate.py STOCK_ASSETS SHARED_ASSETS
node pack-shared.cjs SHARED_ASSETS Amazon-Helga.pak ORIGINAL_GAME VALKYRIE_EN_GAME VALKYRIE_RU_GAME
```

Remove the earlier Amazon-only remaster and texture overlay before using the shared version. A balance profile exported with the earlier Amazon-only remaster may still reference `bsamazon`. Re-export it from the stock archives with the shared package loaded to restore the stock asset names.
