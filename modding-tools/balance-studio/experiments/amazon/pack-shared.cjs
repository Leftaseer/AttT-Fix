// Package the shared Amazon/Helga assets under their stock resource names.
const assert = require("node:assert/strict");
const { openAsBlob, readdirSync, readFileSync, writeFileSync } = require("node:fs");
const { join } = require("node:path");
const core = require("../../core.js");
const models = require("../../models.js");

const editedMotions = ["amazonwait.ska", "amazonwaitbattle.ska", "amazonrun.ska"];
const names = ["amazon.dds", ...editedMotions,
  ...Array.from({ length: 5 }, (_, level) => `amazon${level}.skm`)];
const units = ["uAmazon", "uHelga"];

async function verify(archive, edition, folder) {
  const files = await Promise.all(readdirSync(folder)
    .filter((name) => /^(resource\d+|localization)\.pak$/i.test(name))
    .map(async (name) => Object.assign(await openAsBlob(join(folder, name)), { name })));
  const stock = await core.loadGame(edition, files);
  const name = `Resource${stock.slot}.pak`;
  const upgraded = await core.loadGame(edition, [...files, new File([archive], name)]);
  assert.deepEqual(upgraded.records, stock.records, "The package must leave all unit and balance records intact.");

  const users = [...stock.records.units.values()].filter(({ clips }) =>
    clips.some((clip) => /^amazon\.l?skm$/.test(clip.model) || editedMotions.includes(clip.motion)));
  assert.deepEqual(users.map(({ id }) => id).sort(), units);
  const texture = models.readTexture(await upgraded.readAsset("amazon.dds"));
  assert.equal(texture.width, 2048);
  assert.equal(texture.height, 2048);
  for (const { id, clips } of users) {
    for (const clip of clips) {
      const model = await models.loadModel(upgraded, clip);
      assert.equal(model.mesh, "amazon0.skm");
      assert(model.parts.every((part) => part.materials.every(({ texture }) => texture === "amazon.dds")));
      if (clip.projectilePart !== undefined) {
        assert.equal(model.parts.find(({ projectile }) => projectile)?.name, "2Spear");
      }
      for (const frame of [0, Math.floor(model.frameCount / 2), model.frameCount - 1]) {
        model.setFrame(frame);
        assert(model.parts.every((part) => part.vertices.every(Number.isFinite)), `${id}: ${clip.label}`);
      }
    }
    console.log(`${folder}: ${id}, ${clips.length} clips using ${name}`);
  }
}

async function main([assets, output, original, valkyrieEnglish, valkyrieRussian]) {
  assert(output, "Usage: node pack-shared.cjs ASSETS OUTPUT [ORIGINAL_DIR VALKYRIE_EN_DIR VALKYRIE_RU_DIR]");
  const archive = core.makeArchive(names.map((name) => [name, readFileSync(join(assets, name))]));
  for (const [edition, folder] of [["attt", original], ["valkyrie", valkyrieEnglish], ["valkyrie", valkyrieRussian]]) {
    if (folder) await verify(archive, edition, folder);
  }
  writeFileSync(output, archive, { flag: "wx" });
}

main(process.argv.slice(2)).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
