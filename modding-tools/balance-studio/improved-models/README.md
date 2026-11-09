# Improved models

The original-game `Resource2.pak` combines the starting hero and the shared Amazon and Helga upgrade. It contains only graphics and animation assets. The two starting-hero mesh families use private diffuse textures so the later hero outfits can continue to use their existing shared textures. The introduction keeps its two stock arrow attachments.

## Starting hero

Build from the original English game's `warrior0.skm` through `warrior4.skm`, `warriorappearance0.skm` through `warriorappearance4.skm`, `warrior.dds`, and `warriorhead.dds`. Add the archived `skm.py`, `pn.py`, and `dds.py` to `PYTHONPATH` as described in the [Amazon tools](../experiments/amazon/README.md). Python needs NumPy and Pillow.

```sh
python3 warrior/mesh.py STOCK_WARRIOR_ASSETS REWORKED_WARRIOR
python3 warrior/texture.py STOCK_WARRIOR_ASSETS GENERATED_BODY.png GENERATED_HEAD.png REWORKED_WARRIOR --face-retouch STOCK_MATCHED_FACE.png
node pack.cjs REWORKED_WARRIOR AMAZON_HELGA_SHARED.pak Resource2.pak ORIGINAL_GAME
```

The last command checks the combined archive against the original game's hero and unit definitions and loads the start and intro clips through the editor's pose evaluator. The closest body and hair meshes go from 6,578 to 26,312 triangles. The first three detail levels are refined. The hero uses the proportions of the first remaster. The optional face repaint is blended with the stock face. The original rig and animation tracks drive both hero meshes.

The [Amazon tools](../experiments/amazon/README.md) produce the shared Amazon and Helga input archive. The combined archive supersedes earlier Amazon-only and Amazon/Helga releases for the original game.
