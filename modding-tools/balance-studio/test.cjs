/* Integration check against user-supplied game archives. Run with Node.js 22 or later. */
const assert = require("node:assert/strict");
const { existsSync, openAsBlob, readdirSync } = require("node:fs");
const { join } = require("node:path");
const core = require("./core.js");
const models = require("./models.js");
const { makeGlb } = require("./glb.js");
const rig = require("./model-rig.js");
const animation = require("./model-animation.js");

async function archives(dir, overlay) {
  const names = readdirSync(dir).filter((name) => /^Resource\d+\.pak$/i.test(name));
  const files = await Promise.all(names.map(async (name) => Object.assign(await openAsBlob(join(dir, name)), { name })));
  if (overlay) files.push(Object.assign(await openAsBlob(overlay), { name: "Resource2.pak" }));
  return files;
}

function field(game, kind, key, path) {
  return game.records[kind].get(key)?.fields.find((f) => core.pathKey(f.path) === core.pathKey(path));
}

function addBlenderHelper(parts, source, bindings, weightVertex) {
  const slot = parts[0].slot;
  const binding = bindings.get(slot);
  const extra = binding.joints.length;
  const bones = binding.bones.slice(), weights = binding.weights.slice();
  if (weightVertex) {
    const offset = parts[0].indices[0] * 4;
    bones.set([extra, 0, 0, 0], offset);
    weights.set([1, 0, 0, 0], offset);
  }
  const joints = [...binding.joints, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]];
  const extended = new Map(bindings).set(slot, { ...binding, joints, bones, weights, lengths: null });
  const glb = Buffer.from(makeGlb(parts, new Map(), source, extended));
  const binary = 20 + glb.readUInt32LE(12);
  const doc = JSON.parse(glb.subarray(20, binary).toString());
  doc.nodes[doc.skins[0].joints.at(-1)].name = "neutral_bone";
  const json = JSON.stringify(doc);
  const padded = Buffer.from(json.padEnd(Math.ceil(json.length / 4) * 4));
  const output = Buffer.concat([glb.subarray(0, 20), padded, glb.subarray(binary)]);
  output.writeUInt32LE(output.length, 8);
  output.writeUInt32LE(padded.length, 12);
  return output;
}

async function main() {
  const [original, valkyrie, textOverlay] = process.argv.slice(2);
  assert(original && valkyrie, "Usage: node test.cjs ORIGINAL_DIR VALKYRIE_DIR [MOD_MAGE_RESOURCE2]");
  const inputs = [
    { edition: "attt", files: await archives(original) },
    { edition: "valkyrie", files: await archives(valkyrie) },
  ];
  if (textOverlay) inputs.push({ edition: "attt", files: await archives(original, textOverlay) });
  const originalFiles = inputs[0].files;
  const baseArchive = originalFiles.find((file) => /^Resource0\.pak$/i.test(file.name));
  await assert.rejects(core.loadGame("attt", [baseArchive]), /select Resource0\.pak and Resource1\.pak together/);
  const localizationPath = join(original, "Localization.pak");
  if (existsSync(localizationPath)) {
    const localization = Object.assign(await openAsBlob(localizationPath), { name: "Localization.pak" });
    const native = await core.loadGame("attt", [...originalFiles, localization]);
    const english = await core.loadGame("attt", [...originalFiles, localization], { preferLocalization: true });
    const replacement = await core.loadGame("attt", [
      ...originalFiles.filter((file) => !/^Resource1\.pak$/i.test(file.name)), localization,
    ]);
    assert.equal(native.archiveNames[1], originalFiles.find((file) => /^Resource1\.pak$/i.test(file.name))?.name ?? "Localization.pak");
    assert.equal(english.archiveNames[1], "Localization.pak");
    assert.deepEqual(english.records.units, replacement.records.units);
    assert.equal(english.slot, native.slot);
  }
  const health = ["BattleParams", "Health"];
  const spell = ["Level"];
  const army = ["TroopList", 1, "Quantity"];
  const armyKey = "continent1armies.lua/aAlternatePath1";
  const edit = (scope, kind, key, path, value) => ({ scope, kind, key, path, value });
  const profile = {
    id: "profile1", name: "Integration check", group: "Test",
    edits: [
      edit("shared", "units", "uDragon", health, 999),
      edit("valkyrie", "units", "uDragon", health, 1000),
      edit("shared", "spells", "spF01_Fireball", spell, 7),
      edit("shared", "armies", armyKey, army, 15),
      edit("shared", "units", "missing-unit", health, 30),
      edit("shared", "armies", armyKey, ["TroopList", 1, "Unit"], "missing-unit"),
    ],
  };
  const project = { version: 1, selected: profile.id, profiles: [profile] };
  assert.deepEqual(core.validateProject(JSON.parse(JSON.stringify(project))), project);
  assert.throws(() => core.validateProject({ ...project, profiles: [profile, profile] }), /profile is invalid/i);

  for (const { edition, files } of inputs) {
    const base = await core.loadGame(edition, files);
    if (edition === "attt") {
      const attFix = new File([core.makeArchive([["slot_check.txt", Uint8Array.of(1)]])], "AttTFix.pak");
      const later = new File([core.makeArchive([["slot_check.txt", Uint8Array.of(2)]])],
        `Resource${base.slot + 1}.pak`);
      const ordinary = await core.loadGame(edition, [...files, attFix]);
      assert.equal(ordinary.slot, base.slot);
      assert.equal(await ordinary.readAsset("slot_check.txt"), null);
      await assert.rejects(core.loadGame(edition, [...files, later]), /is missing before/);
      const filled = await core.loadGame(edition, [...files, attFix, later]);
      assert.deepEqual(filled.archiveNames.slice(-2), [attFix.name, later.name]);
      assert.deepEqual(await filled.readAsset("slot_check.txt"), Uint8Array.of(2));
      assert.equal(filled.slot, base.slot + 2);
    }
    for (const continent of [1, 2, 3]) {
      const { image, armies } = await core.loadArmyMap(base, continent);
      assert(image.length > 18);
      assert(armies.some(({ pin }) => pin));
      assert(armies.every(({ record }) => record.group === `Continent ${continent}`));
      if (continent === 1) {
        const hunter = armies.find(({ record }) => record.id === "aBountyHunter1");
        assert(Math.abs(hunter.pin.x - 0.79895) < 0.00001);
        assert(Math.abs(hunter.pin.y - 0.81144) < 0.00001);
        const alternatePath = armies.find(({ record }) => record.id === "aAlternatePath1");
        assert.equal(Boolean(alternatePath.pin), edition === "attt");
      }
    }
    const hunterKey = "continent1armies.lua/aBountyHunter1";
    const hunter = base.records.armies.get(hunterKey);
    const custom = core.newArmyEdit(base, 1, core.worldPoint(1, 0.6, 0.4), 'Дозор "Север"', "uPeasant",
      "00112233445566778899aabbccddeeff");
    custom.value.radius = 500;
    custom.value.troops.push({ unit: "uArcher", quantity: 2 });
    const placement = { ...profile, edits: [custom, edit("shared", "armies", hunterKey, ["radius"], 400)] };
    assert.deepEqual(core.validateProject(JSON.parse(JSON.stringify({ version: 1, profiles: [placement] }))).profiles[0], placement);
    const pin = (await core.loadArmyMap(base, 1, placement)).armies.find(({ record }) => record.key === custom.key).pin;
    assert(Math.abs(pin.x - 0.6) < 0.001 && Math.abs(pin.y - 0.4) < 0.001);
    const encounterPlan = core.planExport(base, placement);
    assert.equal(encounterPlan.changes.length, 2);
    assert.equal(encounterPlan.skipped.length, 0);
    const encounterFile = new File([core.exportGame(base, encounterPlan)], encounterPlan.name);
    assert.deepEqual([...await core.readArchive(encounterFile)].map(([name]) => name).sort(),
      ["continent1armies.lua", "continent1armypos.lua"]);
    const placed = await core.loadGame(edition, [...files, encounterFile]);
    const record = placed.records.armies.get(custom.key);
    assert.equal(record.title, custom.value.title);
    assert.equal(record.attitude, "Agressive");
    assert.deepEqual(record.position, { x: custom.value.x, z: custom.value.z });
    assert.deepEqual(record.roster.value, custom.value.troops);
    assert.equal(field(placed, "armies", custom.key, ["radius"]).value, 500);
    assert.equal(field(placed, "armies", hunterKey, ["radius"]).value, 400);
    assert.deepEqual(placed.records.armies.get(hunterKey).position, hunter.position);
    assert.match(core.planExport(placed, placement).skipped[0].error, /already in the selected archives/);
    const draft = await core.loadGame(edition, files, { worldOverlay: encounterFile });
    const combinedPlan = core.planExport(draft, { edits: [
      edit("shared", "armies", hunterKey, ["radius"], 415),
    ] });
    assert.equal(combinedPlan.name, encounterFile.name);
    const combinedFile = new File([core.exportGame(draft, combinedPlan)], combinedPlan.name);
    const combined = await core.loadGame(edition, [...files, combinedFile]);
    assert.deepEqual(combined.records.armies.get(custom.key), record);
    assert.equal(field(combined, "armies", hunterKey, ["radius"]).value, 415);
    const draftOnly = core.planExport(draft, { edits: [] });
    assert.deepEqual(core.exportGame(draft, draftOnly), core.exportGame(base, encounterPlan));
    const campaignEntries = new Map();
    for (const [name, entry] of await core.readArchive(encounterFile)) {
      campaignEntries.set(name, new Uint8Array(
        await encounterFile.slice(entry.offset, entry.offset + entry.size).arrayBuffer()));
    }
    campaignEntries.set("fzone1test.fst", Uint8Array.of(0, 1, 2, 3));
    campaignEntries.set("continent1quests.lua", new TextEncoder().encode("Quest = {}\n"));
    const campaignFile = new File([core.makeArchive(campaignEntries)], encounterFile.name);
    const campaign = await core.loadGame(edition, files, { worldOverlay: campaignFile });
    assert.deepEqual(await campaign.readAsset("fzone1test.fst"), Uint8Array.of(0, 1, 2, 3));
    const campaignPlan = core.planExport(campaign, { edits: [] });
    assert.equal(campaignPlan.name, encounterFile.name);
    assert.deepEqual(core.exportGame(campaign, campaignPlan),
      new Uint8Array(await campaignFile.arrayBuffer()));
    assert.equal(core.planExport({ ...base, edition: edition === "attt" ? "valkyrie" : "attt" }, placement).changes.length, 1);
    const oversized = { ...custom, value: { ...custom.value, radius: 501 } };
    const invalidRadius = edit("shared", "armies", hunterKey, ["radius"], 501);
    assert.equal(core.planExport(base, { edits: [oversized, invalidRadius] }).skipped.length, 2);
    const textBase = { ...base, chunks: new Map(base.chunks) };
    for (const [name, global] of [["continent1armies.lua", "Army"], ["continent1armypos.lua", "ArmyPos"]]) {
      textBase.chunks.set(name, { source: true, bytes: new TextEncoder().encode(`${global} = {}\n`) });
    }
    const textPlan = core.planExport(textBase, { edits: [custom] });
    const textFile = new File([core.exportGame(textBase, textPlan)], textPlan.name);
    const textPlaced = await core.loadGame(edition, [...files, textFile]);
    assert.deepEqual(textPlaced.records.armies.get(custom.key), record);
    for (const [unit, label] of [["uDragon", "World idle 1"], ["uArcher", "Ranged attack"], ["uValkyr1", "Battle idle"]]) {
      const clip = base.records.units.get(unit).clips.find((item) => item.label === label);
      const preview = await models.loadModel(base, clip);
      assert(preview.frameCount > 1);
      assert(preview.parts.every((part) => part.vertices.every(Number.isFinite)));
      const firstFrame = preview.parts[0].vertices.slice();
      preview.setFrame(Math.floor(preview.frameCount / 2));
      assert(preview.parts.every((part) => part.vertices.every(Number.isFinite)));
      assert(preview.parts[0].vertices.some((value, index) => value !== firstFrame[index]));
      const texture = preview.parts[0].materials[0].texture;
      const { width, height, pixels } = models.readTexture(await base.readAsset(texture));
      assert.equal(pixels.length, width * height * 4);
      assert(pixels.some((value, index) => index % 4 !== 3 && value !== pixels[index % 4]));
    }
    const leper = await models.loadModel(base, base.records.units.get("uLeper2").clips[0]);
    assert(leper.parts.every((part) => part.materials.every(({ texture }) => texture === "leper2.dds")));
    const fury = base.records.units.get("uFury");
    for (const label of ["World idle 1", "Battle idle 3"]) {
      const preview = await models.loadModel(base, fury.clips.find((clip) => clip.label === label));
      for (const name of ["1Shield", "2Spear"]) {
        const { vertices } = preview.parts.find((part) => part.name === name);
        const minHeight = vertices.reduce((lowest, value, index) =>
          index % 8 === 1 ? Math.min(lowest, value) : lowest, Infinity);
        assert(minHeight > 0, `Fury's ${name} should be held above the ground in ${label}.`);
      }
    }
    const furyThrow = await models.loadModel(base, fury.clips.find((clip) => clip.label === "Ranged attack"));
    assert.deepEqual(furyThrow.parts.filter((part) => part.projectile).map((part) => part.name), ["2Spear"]);
    const reference = { unit: fury.id, edition, mesh: furyThrow.mesh, motion: "furyattackranged.ska", frame: 0 };
    const glb = makeGlb(furyThrow.parts, new Map(), reference);
    const header = new DataView(glb.buffer);
    assert.equal(header.getUint32(0, true), 0x46546c67);
    assert.equal(header.getUint32(4, true), 2);
    assert.equal(header.getUint32(8, true), glb.length);
    const binary = 20 + header.getUint32(12, true) + 8;
    const scene = JSON.parse(new TextDecoder().decode(glb.subarray(20, binary - 8)));
    assert.deepEqual(scene.scenes[0].extras, reference);
    assert.deepEqual(scene.nodes.map((node) => node.name), furyThrow.parts.map((part) => part.name));
    const part = furyThrow.parts[0];
    const primitive = scene.meshes[0].primitives[0];
    const positionView = scene.bufferViews[scene.accessors[primitive.attributes.POSITION].bufferView];
    assert.equal(header.getFloat32(binary + positionView.byteOffset + 8, true), -part.vertices[2]);
    const indexView = scene.bufferViews[scene.accessors[primitive.indices].bufferView];
    assert.deepEqual(Array.from({ length: 3 }, (_, i) => header.getUint16(binary + indexView.byteOffset + i * 2, true)),
      [part.indices[0], part.indices[2], part.indices[1]]);
    const spear = furyThrow.parts.find((part) => part.projectile);
    const transform = { move: [0.2, -0.1, 0.15], rotate: [10, 25, -5], scale: 1.25 };
    const replacement = await base.readAsset("amazon.dds");
    assert(models.readReplacementTexture(replacement).pixels.length);
    assert.throws(() => models.readReplacementTexture(replacement.subarray(0, 130)), /ends unexpectedly/);
    const paintImage = { width: 2, height: 1, pixels: new Uint8Array([240, 40, 20, 255, 5, 10, 250, 0]) };
    const paintedDds = models.writePaintedTexture(paintImage);
    assert.deepEqual(models.readReplacementTexture(paintedDds), paintImage);
    assert.deepEqual([...paintedDds.subarray(136)], [20, 40, 240, 128]);
    assert.throws(() => models.readReplacementTexture(paintedDds.subarray(0, 139)), /mipmap data ends unexpectedly/);
    const modelExport = await models.exportModelEdits(base, new Map([[furyThrow.family, {
      files: new Set(furyThrow.meshFiles), edits: new Map([[spear.attachment, transform]]),
    }]]), new Map([["fury.dds", { bytes: replacement }]]));
    const modelFile = new File([modelExport.bytes], modelExport.name);
    const modelEntries = await core.readArchive(modelFile);
    assert.deepEqual([...modelEntries.keys()],
      ["fury.dds", "fury0.skm", "fury1.skm", "fury2.skm", "fury3.skm", "fury4.skm"]);
    const editedModels = await core.loadGame(edition, [...files, modelFile]);
    assert.deepEqual(await editedModels.readAsset("fury.dds"), replacement);
    assert.deepEqual(editedModels.records.units, base.records.units);
    const rangedClip = fury.clips.find((clip) => clip.label === "Ranged attack");
    for (const lod of furyThrow.lods) {
      const original = await models.loadModel(base, rangedClip, lod);
      const result = await models.loadModel(editedModels, rangedClip, lod);
      const originalSpear = original.parts.find((part) => part.projectile);
      const editedSpear = result.parts.find((part) => part.projectile);
      assert.notDeepEqual(editedSpear.vertices, originalSpear.vertices);
      original.setTransform(originalSpear.attachment, transform);
      for (const frame of [0, Math.floor(result.frameCount / 2), result.frameCount - 1]) {
        original.setFrame(frame);
        result.setFrame(frame);
        assert.deepEqual(result.parts.map((part) => part.vertices), original.parts.map((part) => part.vertices));
        assert.deepEqual(result.parts.map((part) => part.indices), original.parts.map((part) => part.indices));
      }
    }
    const referenceRig = await rig.template(base, rangedClip, 0, fury.clips);
    const binding = referenceRig.bindings.get(furyThrow.parts[0].slot);
    assert(binding.parents.filter((parent) => parent >= 0).length > 20);
    assert(new Set(binding.weld).size < binding.weld.length);
    const huntress = base.records.units.get("uValkyr1");
    const hunterRig = await rig.template(base, huntress.clips[0], 0, huntress.clips);
    for (const [parents, wrists] of [[binding.parents, [17, 36]], [hunterRig.bindings.get(0).parents, [15, 34]]]) {
      for (const wrist of wrists) {
        assert.equal(parents[wrist], wrist - 1);
        for (let joint = 1; joint <= 15; joint++) {
          assert.equal(parents[wrist + joint], joint % 3 === 1 ? wrist : wrist + joint - 1);
        }
      }
    }
    const rigGlb = makeGlb(referenceRig.scene.parts, new Map(), reference, referenceRig.bindings);
    const rebuilt = await rig.importUnit(base, referenceRig, rigGlb);
    assert.deepEqual([...rebuilt.assets.keys()], referenceRig.scene.meshFiles);
    const withHelper = (weighted) => addBlenderHelper(referenceRig.scene.parts, reference, referenceRig.bindings, weighted);
    assert.deepEqual(await rig.importUnit(base, referenceRig, withHelper(false)), rebuilt);
    await assert.rejects(rig.importUnit(base, referenceRig, withHelper(true)), /1 exported vertex without game weights/);
    const repaired = await rig.importUnit(base, referenceRig, withHelper(true), { fillWeights: true });
    assert.equal(repaired.filled, 1);
    assert.deepEqual([...repaired.assets.keys()], [...rebuilt.assets.keys()]);
    const rebuiltThrow = await models.loadModel(base, rangedClip, 0, rebuilt.assets);
    assert.deepEqual(rebuiltThrow.parts.filter((entry) => entry.projectile).map((entry) => entry.name), ["2Spear"]);
    for (const frame of [0, Math.floor(furyThrow.frameCount / 2), furyThrow.frameCount - 1]) {
      furyThrow.setFrame(frame);
      rebuiltThrow.setFrame(frame);
      for (const [partIndex, original] of furyThrow.parts.entries()) {
        const edited = rebuiltThrow.parts[partIndex];
        assert.equal(edited.indices.length, original.indices.length);
        for (const [i, index] of original.indices.entries()) {
          for (let axis = 0; axis < 3; axis++) {
            const expected = original.vertices[index * 8 + axis];
            const actual = edited.vertices[edited.indices[i] * 8 + axis];
            assert(Math.abs(expected - actual) < 0.0001, `A rig round trip moved ${original.name} in frame ${frame}.`);
          }
        }
      }
    }
    const lowerRig = await rig.template(base, rangedClip, 1);
    await assert.rejects(rig.importUnit(base, lowerRig, rigGlb), /Use the rig template/);
    const motion = animation.exportClip(referenceRig);
    const animatedGlb = () => makeGlb(referenceRig.scene.parts, new Map(), reference, referenceRig.bindings, motion);
    assert.deepEqual(animation.importClip(referenceRig, animatedGlb()), referenceRig.motionBytes);
    assert.throws(() => animation.importClip(referenceRig, rigGlb), /contains no animation/);
    const projectile = referenceRig.scene.parts.find((entry) => entry.projectile);
    const frame = 5;
    motion.parts.get(projectile.slot)[0].translations[frame * 3] += 0.15;
    const changedClip = animation.importClip(referenceRig, animatedGlb());
    const changedKeys = models.readMotion(changedClip);
    for (const [i, track] of changedKeys.entries()) {
      const original = referenceRig.tracks[i];
      assert.equal(track.frames, original.frames);
      assert.equal(track.bones, original.bones);
      const expected = original.keys.slice();
      if (i === projectile.trackIndex) expected[frame * track.bones * 6 + 3] -= 0.15;
      assert(track.keys.every((value, j) => Math.abs(value - expected[j]) < 0.00002));
    }
    if (edition === "valkyrie") {
      const dragon = await models.loadModel(base, base.records.units.get("uBlackDragon").clips[0]);
      assert.deepEqual(dragon.parts.map((part) => part.materials[0].texture), ["mmdragon.dds", "mmdragonwings.dds"]);
    }
    const plan = core.planExport(base, profile);
    assert.equal(plan.changes.length, 3);
    assert.equal(plan.skipped.length, 2);
    const bytes = core.exportGame(base, plan);
    const patched = await core.loadGame(edition, [...files, new File([bytes], plan.name)]);
    const expectedHealth = edition === "attt" ? 999 : 1000;
    assert.equal(field(patched, "units", "uDragon", health).value, expectedHealth);
    assert.equal(field(patched, "spells", "spF01_Fireball", spell).value, 7);
    assert.equal(field(patched, "armies", armyKey, army).value, 15);
    for (const kind of ["units", "spells", "armies"]) {
      assert.equal(base.records[kind].size, patched.records[kind].size);
      for (const [key, record] of base.records[kind]) {
        for (const before of record.fields) {
          const planned = plan.changes.find((c) => c.kind === kind && c.key === key &&
            core.pathKey(c.path) === core.pathKey(before.path));
          assert.deepEqual(field(patched, kind, key, before.path).value, planned ? planned.value : before.value);
        }
      }
    }
    const armyRecord = base.records.armies.get(armyKey);
    const rosterPath = armyRecord.roster.path;
    const sharedRoster = [
      { unit: "uPeasant", quantity: 2 }, { unit: "uArcher", quantity: 3 },
      { unit: "uPeasant", quantity: 1 },
    ];
    const rosterProfile = { ...profile, edits: [
      edit("shared", "armies", armyKey, army, 5),
      edit("shared", "armies", armyKey, rosterPath, sharedRoster),
      edit("valkyrie", "armies", armyKey, army, 4),
    ] };
    assert.deepEqual(core.validateProject(JSON.parse(JSON.stringify({ version: 1, profiles: [rosterProfile] }))).profiles[0],
      rosterProfile);
    const rosterPlan = core.planExport(base, rosterProfile);
    const expectedRoster = [{ unit: "uPeasant", quantity: edition === "attt" ? 2 : 4 }, ...sharedRoster.slice(1)];
    assert.equal(rosterPlan.skipped.length, 0);
    assert.equal(rosterPlan.changes.length, 1);
    assert.deepEqual(rosterPlan.changes[0].value, expectedRoster);
    const rosterFile = new File([core.exportGame(base, rosterPlan)], rosterPlan.name);
    const changedArmies = (await core.loadGame(edition, [...files, rosterFile])).records.armies;
    assert.deepEqual(changedArmies.get(armyKey).roster.value, expectedRoster);
    assert.equal(changedArmies.size, base.records.armies.size);
    for (const [key, record] of base.records.armies) {
      if (key !== armyKey) assert.deepEqual(changedArmies.get(key), record);
    }
    for (const value of [
      [], Array(armyRecord.roster.maxStacks + 1).fill(sharedRoster[0]),
      [{ unit: "missing-unit", quantity: 2 }], [{ unit: "uPeasant", quantity: armyRecord.roster.maxQuantity + 1 }],
    ]) {
      const invalid = core.planExport(base, { edits: [edit("shared", "armies", armyKey, rosterPath, value)] });
      assert.equal(invalid.changes.length, 0);
      assert.equal(invalid.skipped.length, 1);
    }
    const shorter = core.planExport(base, { edits: [
      edit("shared", "armies", armyKey, rosterPath, sharedRoster.slice(0, 1)),
      edit(edition, "armies", armyKey, ["TroopList", 2, "Quantity"], 1),
    ] });
    assert.equal(shorter.changes.length, 1);
    assert.match(shorter.skipped[0].error, /army slot is unavailable/);
    const shortenedFile = new File([core.exportGame(base, shorter)], shorter.name);
    const shortened = await core.loadGame(edition, [...files, shortenedFile]);
    assert.deepEqual(shortened.records.armies.get(armyKey).roster.value, sharedRoster.slice(0, 1));

    const sourceChunks = new Map(base.chunks);
    const source = `Army = { ${armyRecord.id} = { TroopList = {{ Unit = "uPeasant", Quantity = 2 }} } }`;
    sourceChunks.set(armyRecord.name, { source: true, bytes: new TextEncoder().encode(source) });
    const sourceFile = new File([core.exportGame({ ...base, chunks: sourceChunks }, rosterPlan)], rosterPlan.name);
    const sourceImported = await core.loadGame(edition, [...files, sourceFile]);
    assert.deepEqual(sourceImported.records.armies.get(armyKey).roster.value, expectedRoster);

    const magic = ["BattleParams", "Magic"];
    const withSpell = [...base.records.units.values()].find((r) => field(base, "units", r.key, magic)?.value.length);
    const noSpells = [...base.records.units.values()].find((r) => field(base, "units", r.key, magic)?.value.length === 0);
    const loadout = field(base, "units", withSpell.key, magic).value;
    const [first, second] = [...base.assignedSpells].filter((id) => !loadout.includes(id));
    const expanded = [...loadout, first];
    const price = ["BattleParams", "Cost"];
    const authority = ["BattleParams", "Authority"];
    const xp = ["BattleParams", "ExperiencePoints"];
    const profileWithEconomy = { ...profile, edits: [
      edit("shared", "units", noSpells.key, magic, [first, second]),
      edit("shared", "units", withSpell.key, [...magic, 1], second),
      edit(edition, "units", withSpell.key, magic, expanded),
      edit("shared", "units", "uDragon", price, 221),
      edit("shared", "units", "uDragon", authority, 0),
      edit("shared", "units", "uDragon", xp, 777),
    ] };
    assert.deepEqual(core.validateProject({ version: 1, profiles: [profileWithEconomy] }).profiles[0], profileWithEconomy);
    const extra = core.planExport(base, profileWithEconomy);
    assert.equal(extra.changes.length, 5);
    assert.equal(extra.skipped.length, 0);
    const extraFile = new File([core.exportGame(base, extra)], extra.name);
    const extraEntries = await core.readArchive(extraFile);
    assert(extraEntries.has("maininit.lua"));
    assert(extraEntries.has("balancestudio_base_maininit.lua"));
    const imported = await core.loadGame(edition, [...files, extraFile]);
    assert.equal(imported.init.wrapped, true);
    assert.deepEqual(field(imported, "units", noSpells.key, magic).value, [first, second]);
    assert.deepEqual(field(imported, "units", withSpell.key, magic).value, expanded);
    assert.equal(field(imported, "units", "uDragon", price).value, 221);
    assert.equal(field(imported, "units", "uDragon", authority).value, 0);
    assert.equal(field(imported, "units", "uDragon", xp).value, 777);
    const legacy = core.planExport(base, { edits: [edit("shared", "units", withSpell.key, [...magic, 1], second)] });
    assert.deepEqual(legacy.changes[0].value, [second, ...loadout.slice(1)]);
    const next = core.planExport(imported, { edits: [edit("shared", "units", "uDragon", price, 222)] });
    const nextFile = new File([core.exportGame(imported, next)], next.name);
    assert.deepEqual([...(await core.readArchive(nextFile)).keys()], ["units.lua"]);
    const stacked = await core.loadGame(edition, [...files, extraFile, nextFile]);
    assert.equal(field(stacked, "units", "uDragon", price).value, 222);
    assert.equal(field(stacked, "units", "uDragon", xp).value, 777);

    const ranged = ["BattleParams", "RangeAttackAbility"];
    const peasant = "uPeasant";
    assert.equal(field(base, "units", peasant, magic).castFallback, "Attack");
    assert.equal(core.fieldError(base, field(base, "units", "uArcher", ranged), true), "");
    const animationProfile = { edits: [
      edit("shared", "units", peasant, magic, ["spF01_Fireball"]),
      edit("shared", "units", peasant, ranged, true),
    ] };
    const animationPlan = core.planExport(base, animationProfile);
    assert.equal(animationPlan.changes.length, 1);
    assert.equal(animationPlan.changes[0].castFallback, "Attack");
    assert.equal(animationPlan.skipped.length, 1);
    assert.match(animationPlan.skipped[0].error, /shooting animation and a projectile/);
    const animationFile = new File([core.exportGame(base, animationPlan)], animationPlan.name);
    const safe = await core.loadGame(edition, [...files, animationFile]);
    assert.deepEqual(field(safe, "units", peasant, magic).value, ["spF01_Fireball"]);
    assert.equal(field(safe, "units", peasant, magic).castFallback, undefined);
    assert.equal(field(safe, "units", peasant, ranged).value, false);

    const oldPlan = { ...animationPlan, changes: [{ ...animationPlan.changes[0], castFallback: undefined }] };
    const oldFile = new File([core.exportGame(base, oldPlan)], oldPlan.name);
    const old = await core.loadGame(edition, [...files, oldFile]);
    const repair = core.planExport(old, animationProfile);
    assert.equal(repair.changes[0].castFallback, "Attack");
    assert.deepEqual(repair.changes[0].value, repair.changes[0].field.value);
    console.log(`${edition} ${base.archiveNames.join(" + ")} → ${plan.name}: ${bytes.length} bytes, selected changes only`);
  }
  await assert.rejects(core.loadGame("attt", [new File([new Uint8Array(12)], "Resource2.pak")]), /Resource0\.pak is missing/);
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
