# Hero Modpack 3.2.0

Local reference folder `E:\Programs\Qoder_plays\AttT-Fix\Hero_Modpack_3.2.0`.
It contains `Resource0.pak` and `Resource1.pak`. In Balance Studio, select **Original game**, open
that folder, and click **Hero outfits**. Choose an outfit and switch between world and battle clips
to see which meshes, animations, and textures it uses.

## Archive comparison

Compared each resource by name and SHA-256 against the Steam English original-game archives
from depot `289201`.

| Archive | Stock / mod entries | Added | Changed |
| --- | ---: | --- | --- |
| `Resource0.pak` | 7,349 / 7,349 | None | `hero_additional.lua`, `scenespellbook.lua`, `worldlevel.lua` |
| `Resource1.pak` | 53 / 63 | Ten item icons in TGA format | `heroes.lua`, `artefacts.lua`, and the conversation and SAO scripts for continents 1–3 |

All stock SKM meshes, LSKM descriptors, SKA animations, and DDS textures are byte-identical.
The mod also keeps the original `units.lua`.

## How equipment switches appearance

An item’s `Artefact[item].ChangeSkin` points to a key under `Hero[class].Skins`. Each skin
supplies its own animation table. In `hero_additional.lua`, `DressItem` and `UndressItem`
apply the equipped skin and restore the class base skin through the game’s existing
`WorldHero:ChangeSkin` path.

| Equipment ID | Skin key |
| --- | --- |
| `iConquerorArmor` | `Conqueror` |
| `iDragonslayerArmor` | `Dragonslayer` |
| `iRevenantSkin` | `Revenant` |
| `iHereticRobe` | `Heretic` |
| `iVampireIncarnation` | `Vampire` |
| `iHunterUniform` | `V02_Hunter` |
| `iFuryUniform` | `V05_Fury` |
| `iPriestessUniform` | `V06_Priestess` |

For example, Conqueror’s first world idle refers to `Conqueror.skm;5;ConquerorWait.ska`.
Battle clips can refer to LSKM descriptors that redirect to a mesh and apply texture overrides.
The Warrior table expands from 16 to 35 alternate skins. The Valkyr table adds Priestess.
The added Amazon outfit icon and display name have no matching `ChangeSkin` on that item.
The archives list a Valkyr defend animation whose SKA file is absent in both the mod and the
stock English original. The outfit picker omits animation references with missing SKA files.

## Implications for model work

The armor variants demonstrate how to connect equipment to an existing model and compatible
animation set. When replacing a model, inspect all affected skins and both world and battle
descriptors because several appearances can reference the same underlying assets. The current
Improved Models `Resource2.pak` replaces assets only. Its replacements can be layered over the
mod’s two archives in Balance Studio, where the active outfit definitions resolve against that
overlay. Gameplay compatibility was outside this inspection.
