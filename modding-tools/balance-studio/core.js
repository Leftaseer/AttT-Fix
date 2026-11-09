/* File formats and profile logic shared by the editor and its integration tests. */
(function (root) {
  "use strict";

  const cp1251 = new TextDecoder("windows-1251");
  const luaHeader = [27, 76, 117, 97, 81, 0, 1, 4, 4, 4, 4, 0];
  const files = {
    units: ["units.lua"],
    spells: ["spells.lua"],
    armies: ["continent1armies.lua", "continent2armies.lua", "continent3armies.lua"],
  };
  const globals = { units: "Unit", spells: "Spell", armies: "Army" };
  const editions = ["attt", "valkyrie"];
  const op = {
    MOVE: 0, LOADK: 1, LOADBOOL: 2, LOADNIL: 3, GETGLOBAL: 5, GETTABLE: 6,
    SETGLOBAL: 7, SETTABLE: 9, NEWTABLE: 10, JMP: 22, TEST: 26, RETURN: 30, SETLIST: 34,
  };
  const maxScript = 8 * 1024 * 1024;
  const magicPath = ["BattleParams", "Magic"];
  const rosterPath = ["TroopList"];
  const newArmyPath = ["NewArmy"];
  const mapScales = [18.75, 27, 16.667];
  const encounterRadiusMax = 500;
  const stockStackLimit = { attt: 9, valkyrie: 10 };
  const stockQuantityLimit = 10;
  const maxRoster = 64;
  const maxLoadout = 120;
  const economyFields = {
    Cost: "Recruitment price (gold)",
    Authority: "Authority required",
    ExperiencePoints: "XP per defeated unit",
  };
  const baseInitName = "balancestudio_base_maininit.lua";
  const economyInit = `-- Balance Studio recruitment and rewards
DoFile("balancestudio_base_maininit")
for id, unit in pairs(Unit) do
  if id ~= "Hero" then
    local params = unit.BattleParams
    if unit.BalanceStudioCost ~= nil then params.Cost = unit.BalanceStudioCost end
    if unit.BalanceStudioAuthority ~= nil then params.Authority = unit.BalanceStudioAuthority end
    if unit.BalanceStudioExperiencePoints ~= nil then params.ExperiencePoints = unit.BalanceStudioExperiencePoints end
  end
end
`;
  const unitFields = {
    Level: ["Level", "Combat"], Health: ["Health", "Combat", 1],
    Damage: ["Damage", "Combat"], Armor: ["Armor", "Combat"],
    Speed: ["Speed", "Combat"],
    RangeAttackAbility: ["Ranged attacks", "Ranged"], RangeAttackDamage: ["Ranged damage", "Ranged"],
    RangeAttackDistance: ["Ranged distance", "Ranged"], MagicPower: ["Magic power", "Magic"],
    MagicResist: ["Magic resistance", "Magic"],
  };

  function check(ok, message) {
    if (!ok) throw new Error(message);
  }

  function join(parts) {
    const out = new Uint8Array(parts.reduce((n, part) => n + part.length, 0));
    let position = 0;
    for (const part of parts) {
      out.set(part, position);
      position += part.length;
    }
    return out;
  }

  function int32(n) {
    const out = new Uint8Array(4);
    new DataView(out.buffer).setUint32(0, n, true);
    return out;
  }

  class Reader {
    constructor(bytes) {
      this.bytes = bytes;
      this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      this.position = 0;
    }

    take(n) {
      const from = this.position;
      check(n >= 0 && from + n <= this.bytes.length, "The Lua script ends unexpectedly.");
      this.position += n;
      return this.bytes.subarray(from, this.position);
    }

    byte() { return this.take(1)[0]; }
    uint() { this.take(4); return this.view.getUint32(this.position - 4, true); }
    float() { this.take(4); return this.view.getFloat32(this.position - 4, true); }

    string() {
      const size = this.uint();
      if (!size) return null;
      const value = this.take(size);
      check(value.at(-1) === 0, "Invalid Lua string terminator.");
      return cp1251.decode(value.subarray(0, -1));
    }
  }

  function parseChunk(bytes, name) {
    check(bytes.length <= maxScript, `${name} is too large to inspect.`);
    check(luaHeader.every((byte, i) => bytes[i] === byte),
      `${name} uses a format this editor cannot inspect. Select the original compiled game archives.`);
    const r = new Reader(bytes);
    r.take(12);
    r.string();
    r.take(8); // First and last source line.
    check(r.byte() === 0 && r.byte() === 0, `${name} is not a top-level data script.`);
    r.byte(); // vararg
    const stackOffset = r.position;
    r.byte();
    const codeOffset = r.position;
    const ncode = r.uint();
    check(ncode <= (bytes.length - r.position) / 4, `${name} has an invalid instruction count.`);
    const code = Array.from({ length: ncode }, () => r.uint());
    const constantsOffset = r.position;
    const nconstants = r.uint();
    check(nconstants <= bytes.length - r.position, `${name} has an invalid constant count.`);
    const constants = [];
    for (let i = 0; i < nconstants; i++) {
      const tag = r.byte();
      if (tag === 0) constants.push(null);
      else if (tag === 1) constants.push(r.byte() !== 0);
      else if (tag === 3) constants.push(r.float());
      else if (tag === 4) constants.push(r.string());
      else throw new Error(`${name} contains an unknown Lua constant.`);
    }
    const tailOffset = r.position;
    check(r.uint() === 0, `${name} contains executable Lua functions. This editor reads data scripts only.`);
    const lines = r.uint();
    check(lines === 0 || lines === code.length, `${name} has invalid Lua line information.`);
    r.take(4 * lines);
    const locals = r.uint();
    for (let i = 0; i < locals; i++) {
      r.string();
      r.take(8);
    }
    const upvalues = r.uint();
    for (let i = 0; i < upvalues; i++) r.string();
    check(r.position === bytes.length, `${name} has trailing Lua data.`);
    return { bytes, name, stackOffset, codeOffset, constantsOffset, tailOffset, code, constants, lines };
  }

  function readTables(chunk) {
    const { code, constants, name } = chunk;
    const tables = new Map();
    const registers = [];
    const rk = (i) => i < 256 ? registers[i] : constants[i - 256];
    const nil = (v) => v === undefined || v === null;
    const falsey = (v) => nil(v) || v === false;
    const table = (a) => {
      check(registers[a] instanceof Map, `${name} references a missing table.`);
      return registers[a];
    };
    let pc = 0;
    let budget = code.length * 2;
    while (pc >= 0 && pc < code.length && budget-- > 0) {
      const instruction = code[pc++];
      const a = (instruction >>> 6) & 255;
      const b = instruction >>> 23;
      const c = (instruction >>> 14) & 511;
      const bx = instruction >>> 14;
      switch (instruction & 63) {
        case op.MOVE: registers[a] = registers[b]; break;
        case op.LOADK: registers[a] = constants[bx]; break;
        case op.LOADBOOL:
          registers[a] = Boolean(b);
          if (c) pc++;
          break;
        case op.LOADNIL:
          for (let i = a; i <= b; i++) registers[i] = null;
          break;
        case op.GETGLOBAL: registers[a] = tables.get(constants[bx]); break;
        case op.GETTABLE: registers[a] = table(b).get(rk(c)); break;
        case op.SETGLOBAL: tables.set(constants[bx], registers[a]); break;
        case op.SETTABLE:
          if (nil(rk(c))) table(a).delete(rk(b));
          else table(a).set(rk(b), rk(c));
          break;
        case op.NEWTABLE: registers[a] = new Map(); break;
        case op.JMP: pc += bx - 131071; break;
        case op.TEST:
          if (falsey(registers[a]) === Boolean(c)) pc++;
          break;
        case op.SETLIST: {
          const block = c || code[pc++];
          check(b && block, `${name} uses a dynamic Lua array.`);
          for (let i = 1; i <= b; i++) table(a).set((block - 1) * 50 + i, registers[a + i]);
          break;
        }
        case op.RETURN:
          check(pc === code.length && b === 1, `${name} uses an early or nonempty return.`);
          return tables;
        default: throw new Error(`${name} uses an unsupported Lua instruction at ${pc}.`);
      }
    }
    throw new Error(`${name} did not terminate as a data script.`);
  }

  function readSource(bytes, name) {
    const source = cp1251.decode(bytes);
    const trivia = /(?:\s|--[^\r\n]*)+/y;
    const lex = /[A-Za-z_][A-Za-z0-9_]*|-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|"(?:\\[\s\S]|[^"\\\r\n])*"|'(?:\\[\s\S]|[^'\\\r\n])*'|[.{}\[\]=,;()]/y;
    const tokens = [];
    for (let position = 0; position < source.length;) {
      trivia.lastIndex = position;
      if (trivia.test(source)) {
        position = trivia.lastIndex;
        continue;
      }
      lex.lastIndex = position;
      const match = lex.exec(source);
      check(match, `${name} uses unsupported Lua source syntax at byte ${position + 1}.`);
      tokens.push(match[0]);
      position = lex.lastIndex;
    }
    const locals = new Map();
    const tables = new Map();
    const escapes = { a: "\x07", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t", v: "\v" };
    const identifier = /^[A-Za-z_][A-Za-z0-9_]*$/;
    const reserved = new Set("and break do else elseif end false for function if in local nil not or repeat return then true until while".split(" "));
    let cursor = 0;
    const peek = () => tokens[cursor];
    const take = (expected) => {
      const value = tokens[cursor++];
      check(value !== undefined && (expected === undefined || value === expected),
        `${name} uses unsupported Lua source near token ${cursor}.`);
      return value;
    };
    const id = () => {
      const value = take();
      check(identifier.test(value) && !reserved.has(value), `${name} contains executable Lua source.`);
      return value;
    };
    const set = (table, key, value) => {
      check(table instanceof Map && key != null, `${name} references a missing Lua table or key.`);
      if (value == null) table.delete(key);
      else table.set(key, value);
    };
    function reference() {
      const key = id();
      let parent = locals.has(key) ? locals : tables;
      let field = key;
      while (peek() === "." || peek() === "[") {
        parent = parent.get(field);
        check(parent instanceof Map, `${name} references a missing Lua table.`);
        if (take() === ".") field = id();
        else { field = expression(); take("]"); }
      }
      return { parent, field };
    }
    function atom() {
      const token = peek();
      if (token === "{") {
        take("{");
        const table = new Map();
        let index = 1;
        while (peek() !== "}") {
          if (peek() === "[") {
            take("[");
            const key = expression();
            take("]");
            take("=");
            set(table, key, expression());
          } else if (identifier.test(peek() || "") && tokens[cursor + 1] === "=") {
            const key = id();
            take("=");
            set(table, key, expression());
          } else set(table, index++, expression());
          if (peek() === "," || peek() === ";") take();
          else break;
        }
        take("}");
        return table;
      }
      if (token === "(") {
        take("(");
        const value = expression();
        take(")");
        return value;
      }
      if (token === "nil" || token === "true" || token === "false") {
        return { nil: null, true: true, false: false }[take()];
      }
      if (/^["']/.test(token || "")) return take().slice(1, -1).replace(/\\(\d{1,3}|[\s\S])/g, (_, code) =>
        /^\d/.test(code) ? cp1251.decode(Uint8Array.of(Number(code))) : Object.hasOwn(escapes, code) ? escapes[code] : code);
      if (/^-?(?:\d|\.\d)/.test(token || "")) return Math.fround(Number(take()));
      const { parent, field } = reference();
      return parent.get(field);
    }
    function expression() {
      let value = atom();
      while (peek() === "or") {
        take("or");
        const next = atom();
        if (value == null || value === false) value = next;
      }
      return value;
    }
    while (cursor < tokens.length) {
      if (peek() === ";") { take(";"); continue; }
      const local = peek() === "local";
      if (local) take("local");
      const targets = [];
      do {
        targets.push(local ? { parent: locals, field: id() } : reference());
        if (peek() !== ",") break;
        take(",");
      } while (true);
      const values = [];
      if (!local || peek() === "=") {
        take("=");
        do {
          values.push(expression());
          if (peek() !== ",") break;
          take(",");
        } while (true);
      }
      for (const [i, { parent, field }] of targets.entries()) {
        if (parent === locals) locals.set(field, values[i]);
        else set(parent, field, values[i]);
      }
    }
    return tables;
  }

  const gameCharacters = new Map(Array.from({ length: 224 }, (_, i) => [cp1251.decode(Uint8Array.of(i + 32)), i + 32]));
  function gameString(value) {
    check(typeof value === "string" && [...value].every((char) => gameCharacters.has(char) && char !== "\x7f"),
      "This text contains characters the game cannot display.");
    return Uint8Array.from(value, (char) => gameCharacters.get(char));
  }

  function patchSource(bytes, changes) {
    const quote = (value) => {
      if (Array.isArray(value)) return `{${value.map(quote).join(", ")}}`;
      if (value instanceof Map) return `{${[...value].map(([key, item]) => `[${quote(key)}] = ${quote(item)}`).join(", ")}}`;
      if (typeof value !== "string") return String(value);
      return '"' + Array.from(gameString(value), (byte) => byte >= 128 ?
        "\\" + String(byte).padStart(3, "0") : String.fromCharCode(byte).replace(/["\\]/g, "\\$&")).join("") + '"';
    };
    const reference = (path) => `${path[0]}${path.slice(1).map((key) => `[${quote(key)}]`).join("")}`;
    const lines = changes.map(({ path, value, copyFrom }) =>
      `${reference(path)} = ${copyFrom ? reference(copyFrom) : quote(value)}`);
    return join([bytes, new TextEncoder().encode(`\n\n-- Balance Studio\n${lines.join("\n")}\n`)]);
  }

  function constantBytes(value) {
    if (typeof value === "boolean") return Uint8Array.of(1, Number(value));
    if (typeof value === "number") {
      check(Number.isFinite(Math.fround(value)), "A value exceeds the game's float range.");
      const out = new Uint8Array(5);
      out[0] = 3;
      new DataView(out.buffer).setFloat32(1, value, true);
      return out;
    }
    const bytes = gameString(value);
    return join([Uint8Array.of(4), int32(bytes.length + 1), bytes, Uint8Array.of(0)]);
  }

  function patchChunk(chunk, changes) {
    const { bytes, code, constants, stackOffset, codeOffset, constantsOffset, tailOffset, lines } = chunk;
    check((code.at(-1) & 63) === op.RETURN && !lines, "This Lua script has unsupported debug or return information.");
    const indexes = new Map(constants.map((value, index) => [value, index]));
    const additions = [];
    const indexOf = (value) => {
      if (!indexes.has(value)) {
        indexes.set(value, constants.length + additions.length);
        additions.push(constantBytes(value));
      }
      return indexes.get(value);
    };
    const instructions = [];
    const abx = (opcode, a, value) => {
      const index = indexOf(value);
      check(index < (1 << 18), "Too many Lua constants in one export.");
      instructions.push(int32(opcode | (a << 6) | (index << 14)));
    };
    const abc = (opcode, a, b, c) => instructions.push(int32(opcode | (a << 6) | (c << 14) | (b << 23)));
    const readPath = (path, target, keyRegister) => {
      abx(op.GETGLOBAL, target, path[0]);
      for (const key of path.slice(1)) {
        abx(op.LOADK, keyRegister, key);
        abc(op.GETTABLE, target, target, keyRegister);
      }
    };
    let patchStack = 3;
    function loadValue(value, target) {
      patchStack = Math.max(patchStack, target + 1);
      if (!Array.isArray(value) && !(value instanceof Map)) {
        abx(op.LOADK, target, value);
        return;
      }
      abc(op.NEWTABLE, target, 0, 0);
      const entries = Array.isArray(value) ? value.map((item, index) => [index + 1, item]) : value;
      for (const [key, item] of entries) {
        abx(op.LOADK, target + 1, key);
        loadValue(item, target + 2);
        abc(op.SETTABLE, target, target + 1, target + 2);
      }
    }
    for (const { path, value, copyFrom } of changes) {
      readPath(path.slice(0, -1), 0, 1);
      abx(op.LOADK, 1, path.at(-1));
      if (copyFrom) {
        readPath(copyFrom, 2, 3);
        patchStack = Math.max(patchStack, 4);
      } else loadValue(value, 2);
      abc(op.SETTABLE, 0, 1, 2);
    }
    const prefix = bytes.slice(0, codeOffset);
    prefix[stackOffset] = Math.max(patchStack, prefix[stackOffset]);
    return join([
      prefix, int32(code.length + instructions.length), bytes.subarray(codeOffset + 4, constantsOffset - 4),
      ...instructions, bytes.subarray(constantsOffset - 4, constantsOffset),
      int32(constants.length + additions.length), bytes.subarray(constantsOffset + 4, tailOffset),
      ...additions, bytes.subarray(tailOffset),
    ]);
  }

  async function readArchive(file) {
    const header = new DataView(await file.slice(0, 12).arrayBuffer());
    check(header.byteLength === 12 && header.getUint32(0, false) === 0x47524553 &&
      header.getUint32(4, true) === 100, `${file.name} is not a supported GRES archive.`);
    const count = header.getUint32(8, true);
    const end = 12 + 136 * count;
    check(count <= 100000 && end <= file.size, `${file.name} has an invalid file table.`);
    const toc = new DataView(await file.slice(12, end).arrayBuffer());
    const entries = new Map();
    for (let i = 0; i < count; i++) {
      const position = 136 * i;
      const nameBytes = new Uint8Array(toc.buffer, position, 128);
      const zero = nameBytes.indexOf(0);
      check(zero > 0, `${file.name} has an invalid entry name.`);
      const name = cp1251.decode(nameBytes.subarray(0, zero)).toLowerCase();
      const offset = toc.getUint32(position + 128, true);
      const size = toc.getUint32(position + 132, true);
      check(offset >= end && offset + size <= file.size, `${file.name} has an invalid entry range.`);
      check(!entries.has(name), `${file.name} contains duplicate entry ${name}.`);
      entries.set(name, { file, offset, size });
    }
    return entries;
  }

  function makeArchive(entries) {
    const sorted = [...entries].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
    const toc = new Uint8Array(12 + 136 * sorted.length);
    toc.set([71, 82, 69, 83]);
    const view = new DataView(toc.buffer);
    view.setUint32(4, 100, true);
    view.setUint32(8, sorted.length, true);
    let offset = toc.length;
    for (const [i, [name, bytes]] of sorted.entries()) {
      check(/^[a-z0-9_.]{1,127}$/.test(name), "Invalid export resource name.");
      const position = 12 + 136 * i;
      toc.set(new TextEncoder().encode(name), position);
      view.setUint32(position + 128, offset, true);
      view.setUint32(position + 132, bytes.length, true);
      offset += bytes.length;
    }
    return join([toc, ...sorted.map(([, bytes]) => bytes)]);
  }

  function automaticEconomy(stats) {
    const level = stats.get("Level");
    const experience = 10 + 5 * Math.floor(level) * (Math.floor(level) + 1) / 2;
    const ranged = stats.get("RangeAttackAbility");
    const speedFactor = Math.fround(Math.fround(stats.get("Speed") / 6) + 0.5);
    const rangeFactor = Math.fround(Math.fround(stats.get("RangeAttackDistance") / 4) + 0.5);
    let cost = Math.fround(experience * speedFactor);
    if (ranged) cost = Math.fround(cost * rangeFactor);
    return {
      Cost: Math.floor(Math.fround(Math.fround(cost / 5) + 0.5)),
      Authority: Math.floor(Math.fround(Math.fround(experience / 10) + 0.5)),
      ExperiencePoints: experience,
    };
  }

  function hasAnimation(animation, key, entries) {
    const clips = animation?.get(key);
    return clips instanceof Map && clips.size > 0 && Array.from({ length: clips.size }, (_, i) => clips.get(i + 1))
      .every((clip) => {
        const reference = clip instanceof Map && clip.get(1);
        if (typeof reference !== "string") return false;
        const [model, , motion] = reference.toLowerCase().split(";");
        // Some animation records refer to a model stem with numbered LODs.
        const modelPresent = entries.has(model) || (model.endsWith(".skm") && entries.has(model.replace(/\.skm$/, "0.skm")));
        return modelPresent && entries.has(motion);
      });
  }

  function modelClips(animation, projectilePart, hero = false) {
    if (!(animation instanceof Map)) return [];
    const clips = [];
    const labels = {
      WaitWorld: "World idle", WaitTactical: "Battle idle", MoveWorld: "World movement",
      MoveTactical: "Battle movement", Attack: "Melee attack", RangeAttack: "Ranged attack",
      Cast: "Cast", CastTactical: "Tactical cast", Defense: "Defend", Death: "World death",
      DeathTactical: "Battle death", Stop: "Stop",
    };
    if (hero) Object.assign(labels, {
      WalkBack: "Walk back", RotateLeft: "Turn left", RotateRight: "Turn right",
      RankChange: "Rank change", CastWorld: "World cast", Victory: "Victory",
    });
    for (const [key, label] of Object.entries(labels)) {
      const variants = animation.get(key);
      if (!(variants instanceof Map)) continue;
      for (const [index, variant] of variants) {
        const value = variant instanceof Map && variant.get(1);
        if (typeof value !== "string" || !Number.isInteger(index)) continue;
        const [model, lod, motion] = value.toLowerCase().split(";");
        if (!/\.(skm|lskm)$/.test(model) || !motion?.endsWith(".ska")) continue;
        const clip = { label: variants.size > 1 ? `${label} ${index}` : label, model, numbered: Number(lod) > 0, motion };
        if (key === "RangeAttack" && Number.isInteger(projectilePart) && projectilePart >= 0) clip.projectilePart = projectilePart;
        clips.push(clip);
      }
    }
    return clips;
  }

  function recordFields(kind, table, id, hasEconomyInit, entries) {
    if (kind === "units") {
      const stats = table.get("BattleParams");
      if (!(stats instanceof Map)) return [];
      const animation = table.get("Animation") instanceof Map ? table.get("Animation") : null;
      const projectileId = stats.get("RangeAttackObjectID");
      const projectileTrail = stats.get("RangeAttackObjectPSP");
      const fields = Object.entries(unitFields).flatMap(([key, [label, group, min = 0]]) => {
        const value = stats.get(key);
        if (!["number", "boolean"].includes(typeof value)) return [];
        const field = { path: ["BattleParams", key], label, group, min, value };
        if (key === "RangeAttackAbility" && (!hasAnimation(animation, "RangeAttack", entries) ||
          !Number.isInteger(projectileId) || projectileId < 0 ||
          typeof projectileTrail !== "string" || !entries.has(projectileTrail.toLowerCase()))) {
          field.animationError = "Ranged attacks require a shooting animation and a projectile configured for this model.";
        }
        return [field];
      });
      const magic = stats.get("Magic");
      if (magic == null || (magic instanceof Map && [...magic].every(([slot, value]) =>
        Number.isInteger(slot) && slot >= 1 && slot <= magic.size && typeof value === "string"))) {
        const value = magic ? Array.from({ length: magic.size }, (_, index) => magic.get(index + 1)) : [];
        const field = { path: magicPath, label: "Spell loadout", group: "Spell loadout", value };
        if (!hasAnimation(animation, "Cast", entries) &&
          !(animation?.get("Cast") == null && hasAnimation(animation, "CastTactical", entries))) {
          field.castFallback = ["CastTactical", "Attack"].find((key) => hasAnimation(animation, key, entries));
          if (!field.castFallback) field.animationError = "This unit needs a cast animation or a usable melee clip to cast spells.";
        }
        fields.push(field);
      }
      if (hasEconomyInit && id !== "Hero") {
        const automatic = automaticEconomy(stats);
        for (const [key, label] of Object.entries(economyFields)) {
          const stored = table.get(`BalanceStudio${key}`);
          if (Number.isFinite(automatic[key])) {
            fields.push({ path: ["BattleParams", key], label, group: "Recruitment and rewards",
              value: stored ?? automatic[key], stored, economyKey: key, integer: true, min: 0 });
          }
        }
      }
      return fields;
    }
    if (kind === "spells") {
      const value = table.get("Level");
      return typeof value === "number" ? [{ path: ["Level"], label: "Required level", group: "Spell", min: 0, value }] : [];
    }
    const troops = table.get("TroopList");
    if (!(troops instanceof Map)) return [];
    return [...troops].flatMap(([slot, troop]) => {
      if (!Number.isInteger(slot) || !(troop instanceof Map)) return [];
      const unit = troop.get("Unit");
      const count = troop.get("Quantity");
      if (typeof unit !== "string" || typeof count !== "number") return [];
      return [
        { path: ["TroopList", slot, "Unit"], label: "Unit", group: `Slot ${slot}`, value: unit, choice: "units" },
        { path: ["TroopList", slot, "Quantity"], label: "Quantity", group: `Slot ${slot}`, min: 1, integer: true, value: count },
      ];
    });
  }

  async function loadGame(edition, filesSelected, { preferLocalization = false, worldOverlay } = {}) {
    check(editions.includes(edition), "Choose a game edition.");
    const archives = new Map();
    let localization;
    let attFix;
    for (const file of filesSelected) {
      const match = /^resource(0|[1-9][0-9]*)\.pak$/i.exec(file.name);
      if (!match) {
        if (/^localization\.pak$/i.test(file.name)) {
          check(!localization, "Select one Localization.pak from the game folder.");
          localization = file;
        }
        if (/^atttfix\.pak$/i.test(file.name) && edition === "attt") {
          check(!attFix, "Select one AttTFix.pak from the game folder.");
          attFix = file;
        }
        continue;
      }
      const slot = Number(match[1]);
      check(slot <= 255 && !archives.has(slot),
        "Select one Resource archive per slot from the same game folder.");
      archives.set(slot, file);
    }
    if (localization && (preferLocalization || !archives.has(1))) archives.set(1, localization);
    check(archives.has(0), "Resource0.pak is missing. Select the game folder or its PAK files.");
    // AttTFix supplies its generated PAK at the first missing slot. At the end
    // of the stack that slot remains available for a new numbered export.
    let missing = 1;
    while (archives.has(missing)) missing++;
    if (attFix && [...archives.keys()].some((slot) => slot > missing)) archives.set(missing, attFix);
    const ordered = [...archives.keys()].sort((a, b) => a - b);
    const gap = ordered.findIndex((slot, index) => slot !== index);
    check(gap < 0, `Resource${gap}.pak is missing before Resource${ordered[gap]}.pak. Select the complete game folder${edition === "attt" && !attFix ? ", including AttTFix.pak if your game uses it to fill the slot" : ""}.`);
    let worldEntries;
    if (worldOverlay) {
      check(ordered.length <= 255 && worldOverlay.name === `Resource${ordered.length}.pak`,
        `The world overlay must be Resource${ordered.length}.pak for this archive set.`);
      const archive = await readArchive(worldOverlay);
      check(archive.size && [...archive.keys()].every((name) => /^continent[1-3](towns|npcs|saos|armies|armypos)\.lua$/.test(name)),
        "Choose a World Editor world overlay with continent data.");
      worldEntries = new Map(await Promise.all([...archive].map(async ([name, { file, offset, size }]) => {
        check(size <= maxScript, `${name} in the world overlay exceeds the script size limit.`);
        return [name, new Uint8Array(await file.slice(offset, offset + size).arrayBuffer())];
      })));
      archives.set(ordered.length, worldOverlay);
      ordered.push(ordered.length);
    }
    const entries = new Map();
    for (const slot of ordered) {
      for (const [name, entry] of await readArchive(archives.get(slot))) entries.set(name, entry);
    }
    const initEntry = entries.get("maininit.lua");
    let init;
    if (initEntry && initEntry.size <= maxScript) {
      const bytes = new Uint8Array(await initEntry.file.slice(initEntry.offset, initEntry.offset + initEntry.size).arrayBuffer());
      if (bytes[0] !== 27 && cp1251.decode(bytes) === economyInit) {
        check(entries.has(baseInitName), `The installed balance archive is missing ${baseInitName}.`);
        init = { wrapped: true };
      } else if (!entries.has(baseInitName)) init = { bytes };
    }
    const records = { units: new Map(), spells: new Map(), armies: new Map() };
    const chunks = new Map();
    for (const [kind, names] of Object.entries(files)) {
      for (const name of names) {
        const entry = entries.get(name);
        if (!entry && kind === "armies") continue;
        if (!entry && edition === "attt" && !archives.has(1)) {
          throw new Error(`The original game’s Resource0.pak lacks ${name}. Open the game folder or select Resource0.pak and Resource1.pak together. Localization.pak can fill slot 1.`);
        }
        check(entry, `Could not find ${name} in ${ordered.map((slot) => archives.get(slot).name).join(", ")}.`);
        check(entry.size <= maxScript, `${name} in ${entry.file.name} exceeds the editor’s script size limit.`);
        const bytes = new Uint8Array(await entry.file.slice(entry.offset, entry.offset + entry.size).arrayBuffer());
        const compiled = bytes[0] === 27;
        const chunk = compiled ? parseChunk(bytes, name) : { bytes, source: true };
        const data = (compiled ? readTables(chunk) : readSource(bytes, name)).get(globals[kind]);
        check(data instanceof Map, `${name} does not define ${globals[kind]} records.`);
        chunks.set(name, chunk);
        for (const [id, table] of data) {
          if (typeof id !== "string" || !(table instanceof Map)) continue;
          const fields = recordFields(kind, table, id, Boolean(init), entries);
          if (!fields.length) continue;
          const key = kind === "armies" ? `${name}/${id}` : id;
          records[kind].set(key, {
            id, key, fields, name, title: table.get("DisplayName") || id,
            description: table.get("Description") || "",
            roster: kind === "armies" ? armyRoster(table.get("TroopList"), edition) : undefined,
            attitude: kind === "armies" ? table.get("Attitude") : undefined,
            clips: kind === "units" ? modelClips(table.get("Animation"), table.get("BattleParams").get("RangeAttackObjectID")) : undefined,
            group: kind === "armies" ? `Continent ${name[9]}` : kind === "units" ?
              table.get("BattleParams").get("BattleType") || "" : id.slice(2, 3),
          });
        }
      }
    }
    const assignedSpells = new Set();
    for (const unit of records.units.values()) {
      const loadout = unit.fields.find((field) => Array.isArray(field.value));
      for (const spell of loadout?.value ?? []) if (records.spells.has(spell)) assignedSpells.add(spell);
    }
    async function readAsset(name) {
      const entry = entries.get(name.toLowerCase());
      if (!entry) return null;
      check(entry.size <= 32 * 1024 * 1024, `${name} exceeds the viewer’s asset size limit.`);
      return new Uint8Array(await entry.file.slice(entry.offset, entry.offset + entry.size).arrayBuffer());
    }
    const positions = new Map();
    for (const name of files.armies) {
      const positionFile = name.replace("armies", "armypos");
      try {
        const bytes = await readAsset(positionFile);
        if (!bytes) continue;
        const chunk = bytes[0] === 27 ? parseChunk(bytes, positionFile) : { bytes, source: true };
        const table = (chunk.source ? readSource(bytes, positionFile) : readTables(chunk)).get("ArmyPos");
        if (!(table instanceof Map)) continue;
        chunks.set(positionFile, chunk);
        positions.set(name, table);
      } catch {
        // A scripted location table can be unavailable while the roster remains editable.
      }
    }
    for (const record of records.armies.values()) {
      const position = positions.get(record.name)?.get(record.id);
      if (!(position instanceof Map)) continue;
      record.position = { x: position.get("x"), z: position.get("z") };
      const radius = position.get("radius");
      if (Number.isFinite(radius)) record.fields.push(radiusField(radius));
    }
    return { edition, records, chunks, positions, assignedSpells, init, readAsset, hasAsset: (name) => entries.has(name.toLowerCase()), slot: ordered.length, worldEntries,
      archiveNames: ordered.map((n) => archives.get(n).name) };
  }

  async function loadHeroModels(game) {
    const read = async (name, key) => {
      const bytes = await game.readAsset(name);
      if (!bytes) return undefined;
      return (bytes[0] === 27 ? readTables(parseChunk(bytes, name)) : readSource(bytes, name)).get(key);
    };
    const heroes = await read("heroes.lua", "Hero");
    check(heroes instanceof Map, "The selected archives contain no supported hero outfits.");
    const names = new Map();
    const items = await read("artefacts.lua", "Artefact").catch(() => undefined);
    for (const item of items instanceof Map ? items.values() : []) {
      const skin = item instanceof Map && item.get("ChangeSkin");
      const name = skin && item.get("DisplayName");
      if (typeof skin === "string" && typeof name === "string" && !names.has(skin)) names.set(skin, name);
    }
    const records = [];
    for (const [group, hero] of heroes) {
      if (typeof group !== "string" || !(hero instanceof Map)) continue;
      const variants = hero.get("Skins");
      for (const [skin, table] of [[group, hero], ...(variants instanceof Map ? variants : [])]) {
        if (typeof skin !== "string" || !(table instanceof Map)) continue;
        const projectile = table.get("RangeAttackObjectID") ?? hero.get("BattleParams")?.get("RangeAttackObjectID");
        const clips = modelClips(table.get("Animation"), projectile, true)
          .filter((clip) => game.hasAsset(clip.motion));
        if (clips.length) records.push({
          id: skin, group, title: names.get(skin) || (table === hero ? `${group} · Starting model` : skin), clips,
        });
      }
    }
    check(records.length, "No hero outfit animations were found in the selected archives.");
    return records;
  }

  async function loadArmyMap(game, continent, profile) {
    // SceneMaps centers the three maps on (0, 0) in an 800 × 600 coordinate space.
    const scale = mapScales[continent - 1];
    check(scale && Number.isInteger(continent), "Choose a continent from 1 to 3.");
    const image = await game.readAsset(`mapcontinent${continent}.tga`);
    check(image, "This continent’s map image is missing from the selected archives.");
    const armies = [];
    for (const record of armyRecords(game, profile).values()) {
      if (record.group !== `Continent ${continent}`) continue;
      const { x: worldX, z: worldZ } = record.position ?? {};
      let pin = null;
      if (Number.isFinite(worldX) && Number.isFinite(worldZ)) {
        const x = 0.5 + worldX / (800 * scale);
        const y = 0.5 - worldZ / (600 * scale);
        if (x >= 0 && x <= 1 && y >= 0 && y <= 1) pin = { x, y };
      }
      armies.push({ record, pin });
    }
    return { image, armies, canPlace: game.positions.has(files.armies[continent - 1]) &&
      game.chunks.has(files.armies[continent - 1]) };
  }

  function pathKey(path) { return JSON.stringify(path); }
  function editKey(edit) { return JSON.stringify([edit.scope, edit.kind, edit.key, edit.path]); }

  function validTroop(troop) {
    return troop && typeof troop.unit === "string" && /^[\x20-\x7e]{1,120}$/.test(troop.unit) &&
      Number.isSafeInteger(troop.quantity) && troop.quantity >= 1 && Math.fround(troop.quantity) === troop.quantity;
  }

  function radiusField(value) {
    return { path: ["radius"], label: "Encounter radius", group: "Battlefield", value, min: 1,
      max: Math.max(encounterRadiusMax, value), integer: true, armyPosition: true };
  }

  function worldPoint(continent, x, y) {
    const scale = mapScales[continent - 1];
    return { x: Math.trunc((x - 0.5) * 800 * scale), z: Math.trunc((0.5 - y) * 600 * scale) };
  }

  function isNewArmy(edit) {
    return edit.kind === "armies" && pathKey(edit.path) === pathKey(newArmyPath);
  }

  function newArmyInfo(edit) {
    return /^continent([1-3])armies\.lua\/(bsArmy_[a-f0-9]{32})$/.exec(edit.key);
  }

  function validNewArmy(edit) {
    const info = newArmyInfo(edit);
    const value = edit.value;
    if (!info || !editions.includes(edit.scope) || !value || typeof value.title !== "string" ||
      !value.title.trim() || value.title.length > 64 ||
      ![...value.title].every((char) => gameCharacters.has(char) && char !== "\x7f")) return false;
    const scale = mapScales[Number(info[1]) - 1];
    return Number.isInteger(value.x) && Math.abs(value.x) <= 400 * scale &&
      Number.isInteger(value.z) && Math.abs(value.z) <= 300 * scale &&
      Number.isInteger(value.radius) && value.radius >= 1 && value.radius <= encounterRadiusMax &&
      Array.isArray(value.troops) && value.troops.length >= 1 && value.troops.length <= stockStackLimit[edit.scope] &&
      value.troops.every((troop) => validTroop(troop) && troop.quantity <= stockQuantityLimit);
  }

  function armyRecords(game, profile) {
    const records = new Map(game.records.armies);
    for (const edit of profile?.edits ?? []) {
      if (!isNewArmy(edit) || edit.scope !== game.edition || records.has(edit.key)) continue;
      const [, continent, id] = newArmyInfo(edit);
      const { title, x, z, radius, troops } = edit.value;
      records.set(edit.key, { id, title, key: edit.key, group: `Continent ${continent}`, attitude: "Agressive",
        position: { x, z }, custom: true, fields: [radiusField(radius)],
        roster: { path: rosterPath, label: "Army roster", value: troops,
          maxStacks: stockStackLimit[game.edition], maxQuantity: stockQuantityLimit } });
    }
    return records;
  }

  function newArmyEdit(game, continent, point, title, unit, id) {
    const key = `continent${continent}armies.lua/bsArmy_${id}`;
    return { scope: game.edition, kind: "armies", key, path: newArmyPath,
      value: { title, ...point, radius: 60, troops: [{ unit, quantity: 1 }] } };
  }

  function newArmyError(game, edit) {
    if (!validNewArmy(edit)) return "Check the army name, map position, radius, and roster. Names use the game’s character set.";
    const name = edit.key.split("/")[0];
    const id = newArmyInfo(edit)[2];
    if (!game.positions.has(name) || !game.chunks.has(name)) return "This continent’s army scripts are unavailable.";
    if (game.records.armies.has(edit.key) || game.positions.get(name).has(id)) {
      return "This army ID is already in the selected archives. Reopen the base archives used for the profile.";
    }
    return edit.value.troops.some(({ unit }) => unit === "Hero" || !game.records.units.has(unit)) ?
      "A unit in this new army is unavailable in this edition." : "";
  }

  function armyRoster(troops, edition) {
    if (!(troops instanceof Map) || !troops.size || troops.size > maxRoster) return undefined;
    const value = [];
    for (let slot = 1; slot <= troops.size; slot++) {
      const troop = troops.get(slot);
      // A structural edit replaces TroopList. Use individual fields for unusual modded tables.
      if (!(troop instanceof Map) || troop.size !== 2) return undefined;
      const stack = { unit: troop.get("Unit"), quantity: troop.get("Quantity") };
      if (!validTroop(stack)) return undefined;
      value.push(stack);
    }
    return { path: rosterPath, label: "Army roster", value,
      maxStacks: Math.max(stockStackLimit[edition], value.length),
      maxQuantity: Math.max(stockQuantityLimit, ...value.map((troop) => troop.quantity)) };
  }

  function isRosterEdit(edit) {
    return edit.kind === "armies" && pathKey(edit.path) === pathKey(rosterPath);
  }

  function isRosterSlotEdit(edit) {
    const [key, slot, field] = edit.path;
    return edit.kind === "armies" && edit.path.length === 3 && key === rosterPath[0] &&
      Number.isInteger(slot) && slot >= 1 && (field === "Unit" || field === "Quantity");
  }

  function resolveRoster(game, record, edits, scopes) {
    let value = record.roster.value.map((troop) => ({ ...troop }));
    const skipped = [];
    for (const scope of scopes) {
      const matching = edits.filter((edit) => edit.scope === scope && edit.key === record.key);
      const roster = matching.find(isRosterEdit);
      if (roster) {
        value = roster.value.map((troop) => ({ ...troop }));
        continue;
      }
      for (const edit of matching.filter(isRosterSlotEdit)) {
        const [, slot, field] = edit.path;
        const item = record.fields.find((field) => pathKey(field.path) === pathKey(edit.path));
        const error = !value[slot - 1] || !item ? "The army slot is unavailable in this edition." :
          fieldError(game, item, edit.value);
        if (error) skipped.push({ ...edit, label: `${record.title} · Stack ${slot} ${field.toLowerCase()}`, error });
        else value[slot - 1][field === "Unit" ? "unit" : "quantity"] = edit.value;
      }
    }
    return { value, skipped };
  }

  function rosterError(game, roster, value) {
    if (!Array.isArray(value) || value.length < 1 || value.length > roster.maxStacks) {
      return `Use 1 to ${roster.maxStacks} stacks for this army.`;
    }
    for (const [index, troop] of value.entries()) {
      if (!validTroop(troop) || troop.quantity > roster.maxQuantity) {
        return `Stack ${index + 1} needs a unit and a whole quantity from 1 to ${roster.maxQuantity}.`;
      }
      if (!game.records.units.has(troop.unit)) return `Stack ${index + 1} uses ${troop.unit}, which is unavailable in this edition.`;
    }
    return "";
  }

  function legacySpellSlot(path) {
    return path.length === 3 && path[0] === magicPath[0] && path[1] === magicPath[1] &&
      Number.isInteger(path[2]) && path[2] >= 1;
  }

  function isLoadoutEdit(edit) {
    return edit.kind === "units" && (pathKey(edit.path) === pathKey(magicPath) || legacySpellSlot(edit.path));
  }

  function resolveLoadout(record, edits, scopes) {
    const field = record.fields.find((item) => Array.isArray(item.value));
    if (!field) return { value: [], applied: [], skipped: [] };
    let value = field.value.slice();
    const applied = [];
    const skipped = [];
    for (const scope of scopes) {
      const matching = edits.filter((e) => e.scope === scope && e.kind === "units" && e.key === record.key);
      const loadout = matching.find((e) => pathKey(e.path) === pathKey(magicPath));
      if (loadout) {
        value = Array.isArray(loadout.value) ? loadout.value.slice() : loadout.value;
        applied.push(loadout);
        continue;
      }
      for (const edit of matching.filter((e) => legacySpellSlot(e.path))) {
        if (Array.isArray(value) && edit.path[2] <= value.length && typeof edit.value === "string") {
          value[edit.path[2] - 1] = edit.value;
          applied.push(edit);
        } else skipped.push(edit);
      }
    }
    return { value, applied, skipped };
  }

  function fieldError(game, field, value) {
    if (field.path === rosterPath) return rosterError(game, field, value);
    if (field.armyPosition && (!Number.isInteger(value) || value < field.min || value > field.max)) {
      return `Enter a whole radius from ${field.min} to ${field.max}.`;
    }
    if (Array.isArray(field.value)) {
      if (!Array.isArray(value) || value.length > maxLoadout) return `Use up to ${maxLoadout} spells.`;
      if (value.some((spell) => !game.assignedSpells.has(spell) && !field.value.includes(spell))) {
        return "A spell in this loadout is unavailable for units in this edition.";
      }
      if (value.length && field.animationError) return field.animationError;
      return "";
    }
    if (typeof value !== typeof field.value) return "Wrong value type for this game.";
    if (value === true && field.animationError) return field.animationError;
    if (typeof value === "number" && (!Number.isFinite(Math.fround(value)) || value < field.min ||
      (field.integer && !Number.isSafeInteger(value)))) return `Enter a ${field.integer ? "whole " : ""}number of at least ${field.min}.`;
    if (field.choice === "units" && !game.records.units.has(value)) return "This unit is unavailable in the selected game.";
    return "";
  }

  function planExport(game, profile) {
    const chosen = new Map();
    const skipped = [];
    const same = [];
    const changes = [];
    for (const scope of ["shared", game.edition]) {
      for (const edit of profile.edits.filter((item) => item.scope === scope)) {
        chosen.set(editKey({ ...edit, scope: "shared" }), edit);
      }
    }
    const loadouts = new Set();
    const rosterKeys = new Set([...chosen.values()].filter(isRosterEdit).map((edit) => edit.key));
    const resolvedRosters = new Set();
    for (let edit of chosen.values()) {
      const record = game.records[edit.kind].get(edit.key);
      if (isNewArmy(edit)) {
        const entry = { ...edit, label: `${edit.value.title} · New army` };
        const error = newArmyError(game, edit);
        if (error) skipped.push({ ...entry, error });
        else changes.push(entry);
        continue;
      }
      if ((isRosterEdit(edit) || isRosterSlotEdit(edit)) && rosterKeys.has(edit.key)) {
        if (resolvedRosters.has(edit.key)) continue;
        resolvedRosters.add(edit.key);
        const label = `${record?.title || edit.key} · Army roster`;
        if (!record?.roster) {
          skipped.push({ ...edit, label, error: "This army does not have an editable roster in this edition." });
          continue;
        }
        const { value, skipped: unavailable } = resolveRoster(game, record, profile.edits, ["shared", game.edition]);
        skipped.push(...unavailable);
        const entry = { ...edit, path: rosterPath, value, record, field: record.roster, label };
        const error = fieldError(game, record.roster, value);
        if (error) skipped.push({ ...entry, error });
        else if (pathKey(value) === pathKey(record.roster.value)) same.push(entry);
        else changes.push(entry);
        continue;
      }
      if (isLoadoutEdit(edit)) {
        if (loadouts.has(edit.key)) continue;
        loadouts.add(edit.key);
        if (record?.fields.some((item) => Array.isArray(item.value))) {
          const resolved = resolveLoadout(record, profile.edits, ["shared", game.edition]);
          for (const skippedEdit of resolved.skipped) {
            skipped.push({ ...skippedEdit, label: `${record.title} · Spell ${skippedEdit.path[2]}`,
              error: "The spell slot is unavailable in this edition." });
          }
          if (!resolved.applied.length) continue;
          edit = { ...edit, path: magicPath, value: resolved.value };
        }
      }
      const field = record?.fields.find((item) => pathKey(item.path) === pathKey(edit.path));
      const label = `${record?.title || edit.key} · ${field?.label || edit.path.at(-1)}`;
      const error = field ? fieldError(game, field, edit.value) : "Record or field is unavailable in this edition.";
      const entry = { ...edit, record, field, label };
      if (error) skipped.push({ ...entry, error });
      else if (Array.isArray(edit.value) && edit.value.length && field.castFallback) {
        changes.push({ ...entry, castFallback: field.castFallback });
      } else if (field.economyKey ? edit.value === field.stored : Array.isArray(edit.value) ?
        pathKey(edit.value) === pathKey(field.value) : edit.value === field.value) same.push(entry);
      else changes.push(entry);
    }
    const slot = game.worldEntries ? game.slot - 1 : game.slot;
    return { changes, skipped, same, name: `Resource${slot}.pak` };
  }

  function exportGame(game, plan) {
    const byFile = new Map();
    const add = (file, change) => {
      if (!byFile.has(file)) byFile.set(file, []);
      byFile.get(file).push(change);
    };
    const troops = (stacks) => stacks.map(({ unit, quantity }) => new Map([["Unit", unit], ["Quantity", quantity]]));
    let installEconomyInit = false;
    for (const entry of plan.changes) {
      const { record, kind, field, value } = entry;
      if (isNewArmy(entry)) {
        const [, continent, id] = newArmyInfo(entry);
        const { title, x, z, radius } = value;
        add(`continent${continent}armies.lua`, { path: ["Army", id], value: new Map([
          ["DisplayName", title], ["Attitude", "Agressive"], ["Standard", "stVagrant"], ["TroopList", troops(value.troops)],
        ]) });
        add(`continent${continent}armypos.lua`, { path: ["ArmyPos", id], value: new Map([["x", x], ["z", z], ["radius", radius]]) });
        continue;
      }
      if (field.armyPosition) {
        add(record.name.replace("armies", "armypos"), { path: ["ArmyPos", record.id, "radius"], value });
        continue;
      }
      const path = field.economyKey ? [globals[kind], record.id, `BalanceStudio${field.economyKey}`] :
        [globals[kind], record.id, ...field.path];
      if (field.economyKey && !game.init.wrapped) installEconomyInit = true;
      add(record.name, { path, value: isRosterEdit(entry) ? troops(value) : value });
      if (entry.castFallback) {
        const animationPath = ["Unit", record.id, "Animation"];
        add(record.name, {
          path: [...animationPath, "Cast"], copyFrom: [...animationPath, entry.castFallback],
        });
      }
    }
    check(byFile.size || game.worldEntries?.size, "There are no changes to export for this edition.");
    const files = new Map(game.worldEntries);
    for (const [name, changes] of byFile) {
      const chunk = game.chunks.get(name);
      files.set(name, chunk.source ? patchSource(chunk.bytes, changes) : patchChunk(chunk, changes));
    }
    if (installEconomyInit) {
      files.set("maininit.lua", new TextEncoder().encode(economyInit));
      files.set(baseInitName, game.init.bytes);
    }
    return makeArchive(files);
  }

  function validateProject(project) {
    check(project && project.version === 1 && Array.isArray(project.profiles) && project.profiles.length &&
      project.profiles.length <= 100, "This is not a supported Balance Studio project.");
    const ids = new Set();
    const profiles = project.profiles.map((p) => {
      check(p && typeof p.id === "string" && p.id.length <= 80 && !ids.has(p.id) &&
        typeof p.name === "string" && p.name.trim() && p.name.length <= 80 &&
        typeof p.group === "string" && p.group.length <= 80 &&
        Array.isArray(p.edits) && p.edits.length <= 20000, "A profile is invalid.");
      ids.add(p.id);
      const keys = new Set();
      const edits = p.edits.map((e) => {
        check(e && (e.scope === "shared" || editions.includes(e.scope)) && Object.hasOwn(files, e.kind) &&
          typeof e.key === "string" && e.key.length <= 160 && Array.isArray(e.path) && e.path.length <= 3 &&
          e.path.length >= 1 && e.path.every((v) => typeof v === "string" && v.length <= 64 || Number.isSafeInteger(v)) &&
          (isNewArmy(e) ? validNewArmy(e) : isRosterEdit(e) ? Array.isArray(e.value) && e.value.length > 0 && e.value.length <= maxRoster &&
            e.value.every(validTroop) : e.kind === "units" && pathKey(e.path) === pathKey(magicPath) ?
            Array.isArray(e.value) && e.value.length <= maxLoadout &&
              e.value.every((spell) => typeof spell === "string" && spell.length <= 120) :
            typeof e.value === "boolean" || typeof e.value === "string" && e.value.length <= 120 ||
              typeof e.value === "number" && Number.isFinite(Math.fround(e.value))), "A profile edit is invalid.");
        const key = editKey(e);
        check(!keys.has(key), "A profile contains duplicate edits.");
        keys.add(key);
        const value = isRosterEdit(e) ? e.value.map(({ unit, quantity }) => ({ unit, quantity })) : e.value;
        return { scope: e.scope, kind: e.kind, key: e.key, path: e.path, value };
      });
      return { id: p.id, name: p.name, group: p.group, edits };
    });
    return { version: 1, selected: ids.has(project.selected) ? project.selected : profiles[0].id, profiles };
  }

  const api = { editions, loadGame, loadHeroModels, loadArmyMap, armyRecords, newArmyEdit, newArmyError, isNewArmy, worldPoint,
    readArchive, makeArchive, parseChunk, readTables, readSource, patchChunk, patchSource, editKey, pathKey,
    isLoadoutEdit, resolveLoadout, isRosterEdit, isRosterSlotEdit, resolveRoster, planExport, exportGame, fieldError, validateProject };
  if (typeof module !== "undefined") module.exports = api;
  else root.BalanceCore = api;
})(globalThis);
