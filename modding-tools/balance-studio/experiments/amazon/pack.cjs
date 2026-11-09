// Build an Amazon-only model override from an existing game's data archives.
const assert = require("node:assert/strict");
const { mkdirSync, openAsBlob, readdirSync, readFileSync, writeFileSync } = require("node:fs");
const { join } = require("node:path");
const core = require("../../core.js");
const models = require("../../models.js");

function unitTables(game) {
  const chunk = game.chunks.get("units.lua");
  return (chunk.source ? core.readSource(chunk.bytes, "units.lua") : core.readTables(chunk)).get("Unit");
}

async function main([edition, archiveFolder, assetFolder, outputFolder]) {
  assert(outputFolder, "Usage: node pack.cjs attt|valkyrie GAME_FOLDER ASSET_FOLDER OUTPUT_FOLDER");
  const files = await Promise.all(readdirSync(archiveFolder)
    .filter((name) => /^(resource\d+|localization)\.pak$/i.test(name))
    .map(async (name) => {
      const blob = await openAsBlob(join(archiveFolder, name));
      return Object.assign(blob, { name });
    }));
  const game = await core.loadGame(edition, files);
  const units = unitTables(game);
  const changes = [];
  for (const [action, variants] of units.get("uAmazon").get("Animation")) {
    if (!(variants instanceof Map)) continue;
    for (const [slot, clip] of variants) {
      const model = clip instanceof Map ? clip.get(1) : undefined;
      if (typeof model !== "string" || !/^amazon\.(l?skm);/i.test(model)) continue;
      const value = model.replace(/^amazon/i, "bsamazon");
      changes.push({ path: ["Unit", "uAmazon", "Animation", action, slot, 1], value });
      clip.set(1, value);
    }
  }
  assert(changes.length, "No stock uAmazon model references were found.");
  const chunk = game.chunks.get("units.lua");
  const bytes = chunk.source ? core.patchSource(chunk.bytes, changes) : core.patchChunk(chunk, changes);
  const names = ["bsamazon.dds", ...Array.from({ length: 5 }, (_, level) => `bsamazon${level}.skm`)];
  if (changes.some(({ value }) => value.startsWith("bsamazon.lskm;"))) names.push("bsamazon.lskm");
  for (const name of names) assert.equal(await game.readAsset(name), null, `Resource already exists: ${name}`);
  const archive = core.makeArchive([["units.lua", bytes],
    ...names.map((name) => [name, readFileSync(join(assetFolder, name))])]);
  const name = `Resource${game.slot}.pak`;
  const patched = await core.loadGame(edition, [...files, new File([archive], name)]);
  assert.deepEqual(unitTables(patched), units, "The archive should change only uAmazon's model paths.");
  const texture = models.readTexture(await patched.readAsset("bsamazon.dds"));
  assert([1024, 2048].includes(texture.width));
  assert.equal(texture.height, texture.width);
  const clips = patched.records.units.get("uAmazon").clips;
  for (const clip of clips) {
    const model = await models.loadModel(patched, clip);
    if (clip.projectilePart !== undefined) assert.equal(model.parts.find((part) => part.projectile)?.name, "2Spear");
    assert(model.parts.every((part) => part.materials.every(({ texture }) => texture === "bsamazon.dds")));
    for (const frame of [0, Math.floor(model.frameCount / 2), model.frameCount - 1]) {
      model.setFrame(frame);
      for (const part of model.parts) {
        assert(part.vertices.every(Number.isFinite), `Invalid pose in ${clip.label}`);
      }
    }
  }
  const output = join(outputFolder, name);
  mkdirSync(outputFolder, { recursive: true });
  writeFileSync(output, archive, { flag: "wx" });
  console.log(`${output}: verified ${clips.length} clip references and the full unit table`);
}

main(process.argv.slice(2)).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
