// Combine the starting hero and the existing shared Amazon/Helga remaster.
const assert = require("node:assert/strict");
const { openAsBlob, readFileSync, writeFileSync } = require("node:fs");
const { join } = require("node:path");
const core = require("../core.js");
const models = require("../models.js");

const heroAssets = ["warriorhd.dds", "warriorheadhd.dds", ...["warrior", "warriorappearance"]
  .flatMap(stem => Array.from({length: 5}, (_, level) => `${stem}${level}.skm`))];

async function verify(archive, stockFolder) {
  const files = await Promise.all(["Resource0.pak", "Resource1.pak"].map(async name =>
    Object.assign(await openAsBlob(join(stockFolder, name)), { name })));
  const stock = await core.loadGame("attt", files);
  const upgraded = await core.loadGame("attt", [...files, new File([archive], "Resource2.pak")]);
  assert.deepEqual(upgraded.records, stock.records);
  const heroScript = await stock.readAsset("heroes.lua");
  assert.deepEqual(await upgraded.readAsset("heroes.lua"), heroScript);
  const refs = core.parseChunk(heroScript, "heroes.lua").constants
    .filter(value => typeof value === "string" && /^warrior\.skm;\d+;.*\.ska$/i.test(value))
    .map(ref => ref.toLowerCase().split(";")[2]);
  const clips = [...new Set(refs)].map(motion => ({model:"warrior.skm", numbered:true, motion}));
  assert(clips.length >= 12, "Expected the starting hero's stock animations");
  clips.push({model:"warriorappearance.skm", numbered:true, motion:"warriorappearance.ska"});
  for (const clip of clips) {
    const original = await models.loadModel(stock, clip);
    const result = await models.loadModel(upgraded, clip);
    assert.equal(result.frameCount, original.frameCount);
    assert.deepEqual(result.parts.map(({name}) => name), original.parts.map(({name}) => name));
    assert.equal(result.parts[0].indices.length, 4 * original.parts[0].indices.length);
    assert.equal(result.parts[1].indices.length, 4 * original.parts[1].indices.length);
    for (const frame of [0, Math.floor(result.frameCount / 2), result.frameCount - 1]) {
      result.setFrame(frame);
      assert(result.parts.every(part => part.vertices.every(Number.isFinite)), clip.motion);
    }
  }
  for (const name of heroAssets.filter(name => name.endsWith(".dds"))) {
    const texture = models.readTexture(await upgraded.readAsset(name));
    assert.equal(texture.width, 2048);
    assert.equal(texture.height, 2048);
  }
  for (const id of ["uAmazon", "uHelga"]) {
    const { clips } = upgraded.records.units.get(id);
    for (const clip of clips) {
      const result = await models.loadModel(upgraded, clip);
      assert.equal(result.mesh, "amazon0.skm");
      assert.equal(result.parts.reduce((triangles, part) => triangles + part.indices.length / 3, 0), 18054);
    }
  }
  console.log(`Verified ${clips.length} starting-hero animations and both shared Amazon/Helga units`);
}

async function main([warrior, sharedAmazonPak, output, stockFolder]) {
  assert(output, "Usage: node pack.cjs WARRIOR_ASSETS AMAZON_HELGA_PAK OUTPUT [ORIGINAL_GAME]");
  const amazon = await core.readArchive(await openAsBlob(sharedAmazonPak));
  assert(amazon.has("amazon0.skm") && [...amazon.keys()].every(name => /^amazon\w*\.(dds|skm|ska)$/.test(name)),
    "Provide the shared Amazon and Helga archive");
  const entries = await Promise.all([...amazon].map(async ([name, {file, offset, size}]) =>
    [name, new Uint8Array(await file.slice(offset, offset + size).arrayBuffer())]));
  entries.push(...heroAssets.map(name => [name, readFileSync(join(warrior, name))]));
  const archive = core.makeArchive(entries);
  if (stockFolder) await verify(archive, stockFolder);
  writeFileSync(output, archive, { flag: "wx" });
}

main(process.argv.slice(2)).catch(error => {
  console.error(error);
  process.exitCode = 1;
});
