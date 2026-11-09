# AttT Balance Studio

An offline balance editor for Ascension to the Throne and Valkyrie. On Windows, open **Balance Studio.html**
in Microsoft Edge or Chrome. Keep the HTML, CSS and JavaScript files together.
Game data and projects are processed in the browser on your computer.

## Open game data

1. Select **Original game** or **Valkyrie**.
2. Choose the folder containing `Resource0.pak`. If you pick files manually, select all numbered
   `Resource*.pak` files together. Include `AttTFix.pak` if it fills a gap before a later
   numbered archive. The original game stores units and spells in `Resource1.pak` or
   `Localization.pak`. If you play the original game with AttTFix’s English option, select
   **Use Localization.pak if present** to load that archive in slot 1.
3. Open the other edition the same way to see its base values beside the active edition’s values.

The editor reads the game's Lua 5.1 float bytecode and plain Lua tables built by static assignments. An archive
containing a data script that runs arbitrary code will produce an import error. The archived Mod Mage overlay
uses supported source syntax.

## Keep several balances

- **+** creates a profile. Give related profiles the same group to keep them together.
- **Duplicate** copies a profile’s edits for a new experiment. **Compare** displays another profile’s effective
  values for the active edition.
- **Both editions** assigns the same absolute value to matching record IDs. **This edition only** takes
  precedence for the active edition. The export review lists edits with missing records, fields or choices.
- **Save project** downloads a JSON containing all groups, profiles and edits. **Open project** loads it again.
  The editor also attempts to restore the last project in the same browser. Save a JSON for a portable backup.
- **Undo** reverses the last edit. The arrow beside a field clears the edit for the selected scope.
  Press **/** to focus search. Select **Edited records** to see which entries a profile touches.
- **Bulk edit** sets, adds to or scales a stat across the units visible in the current search and filter.
  Review the changes before applying them. One undo reverses the entire batch. When sharing a batch, the
  editor computes the results from the active edition and shares those resulting values.

## Edit and export

**Units** covers basic battle statistics, ranged attacks, magic power and magic resistance. Use **Spell loadout**
to add, replace or remove spells, including on units with an empty starting loadout. The choices come from
spells already used by units in the selected edition. A shared loadout replaces the list for both editions.
When a unit has no cast animation, the export uses its tactical cast clip if available, then its melee
attack clip. The editor skips spell additions if neither is available. Enabling ranged attacks requires a
shooting clip and a projectile configured for the model. If a previous export enabled an unsupported
ability, reopen the same base archives and export your saved profile again to replace that PAK.
**Recruitment and rewards** lets you override gold cost, authority required and XP awarded per defeated unit
independently. Automatic values follow the game’s formulas. Recruitment price also contributes to battle gold.
**Spells** covers the level requirement. Spell damage, duration and targeting formulas are defined by separate
scripts and require their own editing support.
**Armies** edits the full roster of an existing encounter. Add, duplicate, remove, or move stacks and
set the unit and quantity on each row. A shared roster replaces the full list in both editions. Compare
the base rosters before sharing, since the same army ID can have a different composition in each game.
The largest stock rosters set the editor's default caps of nine stacks in the original game, ten in
Valkyrie, and ten units per stack. It preserves higher counts already present in a loaded roster. Older
profiles keep their slot edits. When a shared roster replaces the list, any edition-specific slot edits
from an older profile still apply to those slot numbers if available.

Open **Army map** from **Armies** to see starting locations on the selected edition's map. Switch
continents, scroll over the map to zoom around the pointer, or search the list by name or ID.
Select a pin and choose **Open roster** to edit that encounter. **Hostile at start** shows red pins.
**Scripted & other** groups neutral, disabled, and other encounters. **Dead armies** shows records
marked `Dead` in the game data.
Armies without recorded starting coordinates appear in the list without pins.

To place a new hostile army, choose **Add army** and click an open patch of land. Give it a name
and first unit, then edit its stacks in **Armies**. Custom armies belong to the current profile and
edition. The map artwork cannot verify that a point is walkable, so test the placement in the game.
When revising a previously exported custom army, open the same base archives, regenerate the PAK,
and replace the earlier profile export. If no profile edits remain, remove the earlier export.

For armies with a stored location, **Battlefield → Encounter radius** edits the value used for the
world-map area and tactical battlefield. The editor allows a radius of up to 500 game units by default.
Combat uses an effective radius of at least 110.

Choose **Review export**, select the target edition and download the proposed `ResourceN.pak`. Close the game
and add it next to the exact archive set used for editing. If that slot is occupied, reopen the installation
with its full active archive set and export again. Remove the exported PAK to revert to the earlier balance.
Keep each edition's export separately. Profile JSON files contain edits only and can be shared across editions.

The editor folder contains no game assets. Balance exports contain the selected installation's modified game
scripts. Keep the profile JSON as the source of a balance so you can regenerate exports against another install.

## Inspect models in 3D

Choose a unit, then click **View 3D model**. Left-drag to orbit, right-drag to pan, and scroll to zoom.
With the canvas focused, use the arrow keys to orbit, **Shift** with the arrow keys to pan, and **+**
or **−** to zoom. **Reset view** or **Home** restores the starting camera. Choose an animation and
press **Play**, or drag the slider to inspect a frame.

Use **Hero outfits** to browse the active archives’ starting hero models and outfit variants by class.
For [Hero Modpack 3.2.0](hero-modpack.md), open the modpack’s own archive folder as **Original game**.

Switch between textured, solid, and wireframe surfaces in **Mesh inspection**. Use **Detail level** to
compare available meshes and **Mesh part** to isolate the body or a piece of equipment. The panel shows
geometry counts, texture names, and animation track details. **Skin weights** highlights how strongly
the selected bone moves each vertex. **Show bone markers and links** displays each bone at the center
of its weighted vertices. Click a marker to highlight it and select its bone in **Weighted bone**.
You can pick from any visible mesh part while viewing the whole model. The viewer infers links from
the strongest shared skin weights. The SKM and SKA data used by the viewer provide indexed weights
and transforms without a parent-bone hierarchy.

The viewer reads the model, animation and DDS textures from the selected edition's archives. It uses
WebGL and preview lighting. Game shaders, particle effects and custom material effects are outside this
preview.

Choose **Export pose (.glb)** to download the current frame with its mesh parts and embedded textures.
In Blender, use **File → Import → glTF 2.0**. The GLB contains the full posed geometry, even when a part
is isolated in the preview.

## Edit equipment and textures

1. Open a unit or hero outfit in the viewer and click **Edit model**. Choose an attachment under
   **Part to edit**, such as Amazon's `2Spear`.
2. Adjust **Move**, **Rotate °**, or **Scale %**. These use the attachment's local axes and pivot.
   Scrub or play a clip to see the result in motion. **Reset** restores the selected attachment.
3. To repaint a part, choose its **Texture asset** and click **Download DDS** for the source file
   from the loaded archives. The download preserves the original DDS bytes, including alpha and
   mipmaps. Edit it using the original UV layout, then use **Replace DDS**. Use a 2D, power-of-two
   legacy DDS in DXT1, DXT3, or DXT5 format, or a supported uncompressed DDS.
   **Restore** brings back the loaded texture.
4. Choose **Export model PAK** and put the downloaded `ResourceN.pak` after the same archive set you
   opened, with the game closed. Remove the PAK to revert. If its slot is occupied, open the full
   installed archive set before exporting. To revise an earlier model PAK from scratch, reopen the
   same base archives and replace the earlier model PAK with the new export.

Transforms apply to matching attachment names and animation tracks in the resolved SKM family.
Unmatched detail levels retain their existing geometry. Texture swaps replace a named DDS everywhere
it is used, including through LSKM material overrides. Shared assets affect all models using them,
such as Amazon and Helga. The first editor supports rigid attachment transforms and DDS swaps.
Drafts stay available across animations and viewer windows until you reload the archives or the page.
**Discard all** clears that archive set's model draft. Exported model PAKs contain the changed SKMs and DDS
files. Balance profile JSON tracks balance edits separately.

### Paint on the model

Choose a **Texture asset** and click **Paint texture**. Set the brush color and size, then left-drag
over the model. Use **Alt + left-drag** to orbit, right-drag to pan, and the wheel to zoom. Painting
targets the visible surface and preserves the texture's original transparency. A mirrored or shared
UV region can display the same stroke in more than one place.

**Undo stroke** reverts the last stroke on that texture. **Download painted DDS** saves the painted
atlas with fresh mipmaps. **Export model PAK** includes the painted DDS under its game asset name.
Painting supports power-of-two textures up to 2048 pixels per side. The source DDS is available
separately through **Download DDS**.

### Replace a unit mesh using Blender

1. Open the unit's model, select the animation and detail level you want to use as a reference,
   and open **Edit model → Replace from GLB → Export rig template**. The template uses the
   first frame of that clip. Use **Highest detail** when replacing the full mesh family.
2. In Blender 4.2 or later, install `attt_blender_import.py` once via **Edit → Preferences → Add-ons**
   and **Install from Disk** in the add-ons menu. Enable **AttT Rig Template**, then use
   **File → Import → AttT Rig Template (.glb)**. The importer joins matching boundary edges
   inside each mesh part and keeps per-corner UVs and normals. Edit the meshes or fit your own
   geometry to the template.
   For a new skinned body, transfer or paint weights using the template's armature.
   Keep the tagged object names, bone names and material slots. Keep rigid equipment as
   separate objects. You can omit objects you want to retain from the stock model.
3. Export as **glTF Binary (.glb)** with normals, UVs and skinning. Use at most four bone
   influences per vertex and leave mesh compression off. Keep the rig in its reference pose.
4. Reopen the same archive set, model, animation and detail level. Choose **Import edited GLB…**.
   Preview idle, movement and attacks before using **Export model PAK**. **Restore mesh**
   removes the draft replacement for this mesh family.

If the importer reports vertices without game weights, Blender may have assigned them to
`neutral_bone` during export. Assign weights in Blender, or enable **Fill missing weights
from template** to borrow weights from the nearest surface on the original part. The editor
keeps existing game weights. Check the resulting motion, especially where the new mesh
differs from the template.

The template builds a Blender armature from skin weights and sampled animation transforms. Joint
placement and parenting are inferred because the game assets provide no authoring hierarchy.
For recognized humanoid layouts, each finger chain follows its own hand in Blender Pose Mode.
The game keeps its original bone indices, SKA animations, attachment tracks and collision records.
Geometry, normals, UVs and weights can change.
Imported material slots still use the game textures. Use **Replace DDS** or **Paint texture** to
change them. The replacement geometry is reused at all compatible detail levels, so keep the
triangle budget suitable for battles. The importer reports incompatible detail levels and each
skinned part is limited to 65,535 bone-space vertex copies. Shared mesh assets affect every unit
that uses them, including Amazon and Helga.

### Edit an existing animation in Blender

1. Select a clip such as **Battle idle 2**, then open **Edit model → Edit animation → Export animated GLB**.
   The GLB includes the full clip as well as the skinned model and its equipment tracks.
2. Update the included `attt_blender_import.py` add-on and use **File → Import → AttT Rig Template (.glb)**.
   Animated templates set the Blender scene to 30 FPS and the clip's original frame range.
3. Edit the imported actions, then export a **glTF Binary (.glb)** with **Animation** enabled,
   **Mode** set to **Scene**, and animation sampling enabled. Keep all template objects and
   bones, the same frame range, and 30 FPS. SKA tracks use rotation and translation.
   Held equipment has its own action. Adjust that action too when changing a grip.
4. In Balance Studio, reopen the same archive set, model, clip, and detail level. Use
   **Import animation GLB…** and preview the result. **Export model PAK** packages the
   edited SKA. **Restore clip** removes its draft override.

The importer writes into the existing clip's track layout and frame count so the game's event
frames still line up. Shared SKA assets apply to every unit or outfit that references them.

## Verification and scope

A Node.js 22+ integration check can read your archives and verify an export without touching your installation.

```text
node test.cjs ORIGINAL_DIRECTORY VALKYRIE_DIRECTORY [MOD_MAGE_RESOURCE2]
```
