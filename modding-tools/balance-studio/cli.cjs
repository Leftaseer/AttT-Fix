"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { parseArgs } = require("node:util");
const core = require("./core.js");

const help = `Balance Studio CLI (Node.js 22+)
Usage: attt.py balance <command> --game FOLDER [--edition attt|valkyrie]

  list    --kind units|spells|armies [--search TEXT]
  show    --kind units|spells|armies --id RECORD_KEY
  plan    --project PROJECT.json [--profile ID]
  export  --project PROJECT.json [--profile ID] --out FOLDER [--allow-skipped]

--overlay FILE       Load an additional numbered PAK. Repeat for multiple slots.
--world-overlay FILE Combine a World Editor PAK in the next slot with the balance export.
--prefer-localization Use Localization.pak as slot 1.
Results are JSON. Export refuses to replace an existing PAK.
`;

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function archive(file) {
  return Object.assign(await fs.openAsBlob(file), { name: path.basename(file) });
}

async function run(args) {
  if (!args.length || args.includes("--help") || args[0] === "-h") {
    process.stdout.write(help);
    return;
  }
  const [command, ...options] = args;
  check(["list", "show", "plan", "export"].includes(command), "Choose list, show, plan or export. See --help.");
  const { values: flags } = parseArgs({
    args: options,
    options: {
      game: { type: "string" },
      edition: { type: "string", default: "attt" },
      "prefer-localization": { type: "boolean" },
      overlay: { type: "string", multiple: true, default: [] },
      "world-overlay": { type: "string" },
      kind: { type: "string" },
      search: { type: "string", default: "" },
      id: { type: "string" },
      project: { type: "string" },
      profile: { type: "string" },
      out: { type: "string" },
      "allow-skipped": { type: "boolean" },
    },
  });
  check(flags.game, "Provide --game with the folder containing the game archives.");
  const files = fs.readdirSync(flags.game, { withFileTypes: true })
    .filter((entry) => (entry.isFile() || entry.isSymbolicLink()) && /^(resource\d+|localization)\.pak$/i.test(entry.name))
    .map((entry) => path.join(flags.game, entry.name));
  const game = await core.loadGame(flags.edition, await Promise.all([...files, ...flags.overlay].map(archive)), {
    preferLocalization: flags["prefer-localization"],
    worldOverlay: flags["world-overlay"] && await archive(flags["world-overlay"]),
  });
  if (command === "list" || command === "show") {
    check(Object.hasOwn(game.records, flags.kind), "Choose --kind units, spells or armies.");
    const records = game.records[flags.kind];
    if (command === "show") {
      const record = records.get(flags.id);
      check(record, "Unknown record key. Run list to get valid keys.");
      return record;
    }
    const search = flags.search.toLowerCase();
    return [...records.values()].filter((record) =>
      [record.key, record.title].some((value) => value.toLowerCase().includes(search)))
      .map(({ id, key, title, group }) => ({ id, key, title, group }));
  }
  check(flags.project, "Provide --project with a Balance Studio project JSON.");
  const project = core.validateProject(JSON.parse(fs.readFileSync(flags.project, "utf8")));
  const profile = project.profiles.find(({ id }) => id === (flags.profile ?? project.selected));
  check(profile, "Unknown profile ID.");
  const plan = core.planExport(game, profile);
  const edit = ({ label, scope, kind, key, path, value, field, error, castFallback }) =>
    ({ label, scope, kind, key, path, before: field?.value, value, error, castFallback });
  const report = {
    edition: game.edition, archives: game.archiveNames, profile: profile.id, archive: plan.name,
    worldModules: [...(game.worldEntries?.keys() ?? [])],
    changes: plan.changes.map(edit), skipped: plan.skipped.map(edit), alreadyMatch: plan.same.map(edit),
  };
  if (command === "export") {
    check(flags.out, "Provide --out with an existing output folder.");
    check(flags["allow-skipped"] || !plan.skipped.length, "Some edits would be skipped. Run plan or pass --allow-skipped.");
    const bytes = core.exportGame(game, plan);
    report.output = path.resolve(flags.out, plan.name);
    fs.writeFileSync(report.output, bytes, { flag: "wx" });
    report.bytes = bytes.length;
  }
  return report;
}

run(process.argv.slice(2)).then((result) => {
  if (result !== undefined) console.log(JSON.stringify(result, null, 2));
}).catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
