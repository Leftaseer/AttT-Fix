"use strict";

const core = window.BalanceCore;
const names = { attt: "Original game", valkyrie: "Valkyrie" };
const storeKey = "attt-balance-studio-v1";
const $ = (id) => document.getElementById(id);
const games = {};
const history = [];
const state = { edition: "attt", kind: "units", scope: "shared", key: null, compare: "" };
let archiveEdition = null;
let profileAction = "new";
let pendingArmy;
let project = newProject();
let workspace;
let archiveRequest = 0;

function node(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content !== undefined) element.textContent = content;
  return element;
}

function newProfile(name, group = "", edits = []) {
  return { id: crypto.randomUUID(), name, group, edits };
}

function newProject() {
  const first = newProfile("Untitled balance");
  return { version: 1, selected: first.id, profiles: [first] };
}

function profile() { return project.profiles.find((p) => p.id === project.selected); }
function game() { return games[state.edition]; }
function catalog() { return state.kind === "armies" ? core.armyRecords(game(), profile()) : game().records[state.kind]; }
function otherEdition() { return core.editions.find((e) => e !== state.edition); }
function scope() { return state.scope === "shared" ? "shared" : state.edition; }
function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}

function autosave() {
  try {
    localStorage.setItem(storeKey, JSON.stringify(project));
    return true;
  } catch {
    return false;
  }
}

function remember() {
  history.push(JSON.stringify(project));
  if (history.length > 35) history.shift();
}

function undo() {
  if (!history.length) return;
  project = JSON.parse(history.pop());
  autosave();
  render();
  status("Last change undone.");
}

function download(name, blob) {
  const url = URL.createObjectURL(blob);
  const link = node("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

function valueText(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "No spells";
  if (typeof value === "boolean") return value ? "On" : "Off";
  if (typeof value === "number") return String(Number(value.toPrecision(8)));
  return String(value);
}

function resetSearch() {
  $("search").value = "";
  $("filter").value = "all";
  $("records").scrollTop = 0;
}

function pickArchives(edition) {
  archiveEdition = edition;
  $("archives-title").textContent = `Open ${names[edition]}`;
  $("attt-archive-hint").hidden = edition !== "attt";
  $("localization-option").hidden = edition !== "attt";
  $("prefer-localization").checked = Boolean(games[edition]?.archiveNames.includes("Localization.pak"));
  $("archives-dialog").showModal();
}

function selectGame(edition) {
  if (!games[edition]) {
    pickArchives(edition);
    return;
  }
  state.edition = edition;
  resetSearch();
  render();
  status(`${names[edition]} is the active edition.`);
}

async function openArchives(event) {
  const input = event.currentTarget;
  if (!input.files.length) return;
  const selected = [...input.files].filter((file) =>
    input.id !== "archive-folder" || file.webkitRelativePath.split("/").length === 2);
  const edition = archiveEdition;
  const preferLocalization = edition === "attt" && $("prefer-localization").checked;
  $("archives-dialog").close();
  await readArchives(edition, selected, { preferLocalization });
}

async function readArchives(edition, selected, options, worldRevision) {
  const request = ++archiveRequest;
  status(`Reading ${names[edition]} archives…`);
  try {
    const loaded = await core.loadGame(edition, selected, options);
    if (request !== archiveRequest) return;
    loaded.worldRevision = worldRevision;
    games[edition] = loaded;
    state.edition = edition;
    resetSearch();
    render();
    status(`${names[edition]} loaded from ${loaded.archiveNames.join(", ")}.`);
    return loaded;
  } catch (error) {
    if (request === archiveRequest) status(error.message, true);
  }
}

function openWorkspacePane(world) {
  $("balance-panel").hidden = world;
  $("world-panel").hidden = !world;
  $("balance-data").hidden = world;
  document.querySelector(".profile-section").hidden = world;
  document.querySelector(".side-footer").hidden = world;
  $("workspace-balance").setAttribute("aria-pressed", String(!world));
  $("workspace-world").setAttribute("aria-pressed", String(world));
  if (world && !$("world-frame").hasAttribute("src")) $("world-frame").src = "/world/";
}

async function loadWorldDraft() {
  const button = $("use-world-draft");
  const feedback = $("world-status");
  button.disabled = true;
  feedback.textContent = "Reading the world draft…";
  try {
    const response = await fetch("/api/world-overlay");
    if (!response.ok) throw new Error((await response.json()).error);
    const worldOverlay = response.status === 204 ? undefined :
      new File([await response.blob()], `Resource${workspace.archives.length}.pak`);
    const archives = workspace.archives.map(({ slot, name, size }) => ({
      name, size,
      slice: (start, end) => ({
        async arrayBuffer() {
          const data = await fetch(`/api/archive/${slot}?start=${start}&end=${end}`);
          if (!data.ok) throw new Error(`Could not read ${name} from the workspace.`);
          return data.arrayBuffer();
        },
      }),
    }));
    const loaded = await readArchives(workspace.edition, archives, { worldOverlay }, response.headers.get("X-World-Revision"));
    if (!loaded) {
      feedback.textContent = $("status").textContent;
      return;
    }
    feedback.textContent = worldOverlay ? "World draft loaded in Balance." : "No world edits yet.";
    openWorkspacePane(false);
    if (worldOverlay) status("World draft loaded. Review export combines it with this balance profile.");
  } catch (error) {
    feedback.textContent = error.message;
    if ($("world-panel").hidden) status(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function connectWorkspace() {
  if (location.protocol === "file:") return;
  try {
    const response = await fetch("/api/session");
    if (!response.ok) return;
    workspace = await response.json();
    if (!core.editions.includes(workspace.edition) || !Array.isArray(workspace.archives)) return;
    $("workspace-nav").hidden = false;
    await loadWorldDraft();
  } catch (error) {
    status(error.message, true);
  }
}

function renderProfiles() {
  const groups = new Map();
  for (const p of project.profiles) {
    if (!groups.has(p.group)) groups.set(p.group, []);
    groups.get(p.group).push(p);
  }
  const content = [];
  for (const [group, profiles] of groups) {
    content.push(node("p", "profile-group", group || "Ungrouped"));
    for (const p of profiles) {
      const button = node("button", "profile");
      button.setAttribute("aria-pressed", String(p.id === project.selected));
      button.append(node("span", "", p.name), node("span", "profile-count", p.edits.length || ""));
      button.addEventListener("click", () => {
        project.selected = p.id;
        autosave();
        render();
      });
      content.push(button);
    }
  }
  $("profiles").replaceChildren(...content);
  $("profile-delete").disabled = project.profiles.length === 1;
  $("profile-title").textContent = profile().name;
  $("workspace-label").textContent = profile().group || "Local workspace";
  const count = profile().edits.length;
  $("workspace-summary").textContent = game() ?
    `${names[state.edition]} · ${count} saved ${count === 1 ? "edit" : "edits"} in this profile` :
    "Create and compare game balance profiles.";
  $("undo").disabled = !history.length;
  $("export").disabled = !game() || (!count && !game().worldEntries?.size);
  const others = project.profiles.filter((p) => p.id !== project.selected);
  if (!others.some((p) => p.id === state.compare)) state.compare = "";
  $("compare-profile").replaceChildren(Object.assign(node("option", "", "No profile"), { value: "" }),
    ...others.map((p) => Object.assign(node("option", "", p.name), { value: p.id })));
  $("compare-profile").value = state.compare;
  $("compare-profile").disabled = !others.length;
}

function openProfileDialog(action) {
  profileAction = action;
  const p = profile();
  $("profile-dialog-title").textContent = { new: "New profile", edit: "Rename profile", copy: "Duplicate profile" }[action];
  $("profile-name").value = action === "new" ? "" : action === "edit" ? p.name : `${p.name} copy`.slice(0, 80);
  $("profile-group").value = action === "new" ? "" : p.group;
  $("groups").replaceChildren(...[...new Set(project.profiles.map((item) => item.group).filter(Boolean))]
    .map((name) => Object.assign(node("option"), { value: name })));
  $("profile-dialog").showModal();
  $("profile-name").select();
}

function saveProfile(event) {
  event.preventDefault();
  const name = $("profile-name").value.trim();
  const group = $("profile-group").value.trim();
  if (!name) {
    $("profile-name").setCustomValidity("Enter a profile name.");
    $("profile-name").reportValidity();
    return;
  }
  if (profileAction !== "edit" && project.profiles.length >= 100) {
    status("This project already has 100 profiles. Save it and start another project to add more.", true);
    $("profile-dialog").close();
    return;
  }
  remember();
  if (profileAction === "edit") Object.assign(profile(), { name, group });
  else {
    const p = newProfile(name, group, profileAction === "copy" ? structuredClone(profile().edits) : []);
    project.profiles.push(p);
    project.selected = p.id;
  }
  $("profile-dialog").close();
  autosave();
  render();
}

function editFor(record, field, targetScope = scope(), targetProfile = profile()) {
  const descriptor = { scope: targetScope, kind: state.kind, key: record.key, path: field.path };
  return { descriptor, existing: targetProfile.edits.find((e) => core.editKey(e) === core.editKey(descriptor)) };
}

function visibleRecords() {
  const query = $("search").value.trim().toLocaleLowerCase();
  const filter = $("filter").value;
  const other = games[otherEdition()];
  const edited = new Set(profile().edits.filter((e) => e.kind === state.kind &&
    (e.scope === "shared" || e.scope === state.edition)).map((e) => e.key));
  const records = [...catalog().values()].filter((r) =>
    `${r.title} ${r.id} ${r.group}`.toLocaleLowerCase().includes(query) &&
    (filter !== "edited" || edited.has(r.key)) && (filter !== "common" || other?.records[state.kind].has(r.key)) &&
    (!filter.startsWith("group:") || r.group === filter.slice(6)))
    .sort((a, b) => a.title.localeCompare(b.title, undefined, { numeric: true }) || a.key.localeCompare(b.key));
  return { records, edited };
}

function renderRecords() {
  const loaded = game();
  if (!loaded) return;
  const groupLabel = { units: "Battle type", spells: "School code", armies: "Area" }[state.kind];
  const filter = $("filter");
  const previous = filter.value;
  const all = catalog();
  const groups = [...new Set([...all.values()].map((r) => r.group).filter(Boolean))].sort();
  filter.replaceChildren(...[["all", "All records"], ["edited", "Edited records"], ["common", "In both editions"],
    ...groups.map((group) => [`group:${group}`, `${groupLabel} · ${group}`])]
    .map(([value, title]) => Object.assign(node("option", "", title), { value, disabled: value === "common" && !games[otherEdition()] })));
  if ([...filter.options].some((option) => option.value === previous && !option.disabled)) filter.value = previous;
  const { records, edited } = visibleRecords();
  $("bulk-edit").hidden = state.kind !== "units";
  $("bulk-edit").disabled = !records.length;
  $("open-army-map").hidden = state.kind !== "armies";
  if (!records.some((r) => r.key === state.key)) state.key = records[0]?.key ?? null;
  $("record-count").textContent = `${records.length} of ${all.size} records`;
  $("records").replaceChildren(...records.map((record) => {
    const button = node("button", "record");
    button.setAttribute("aria-pressed", String(record.key === state.key));
    const title = node("span");
    title.append(node("strong", "", record.title), node("small", "", record.group ?
      `${record.id} · ${record.group}` : record.id));
    button.append(title);
    if (edited.has(record.key)) button.append(node("span", "mark", "Edited"));
    button.addEventListener("click", () => {
      state.key = record.key;
      for (const row of $("records").children) row.setAttribute("aria-pressed", String(row === button));
      renderInspector(true);
    });
    return button;
  }));
}

function updateEdit(record, field, value, reset = false) {
  if (record.custom) {
    if (reset) return false;
    const edit = profile().edits.find((entry) => core.isNewArmy(entry) && entry.key === record.key && entry.scope === state.edition);
    const replacement = { ...edit, value: { ...edit.value, [field.armyPosition ? "radius" : "troops"]: value } };
    const error = core.fieldError(game(), field, value) || core.newArmyError(game(), replacement);
    if (error) { status(error, true); return false; }
    remember();
    edit.value = replacement.value;
    autosave();
    renderProfiles();
    renderRecords();
    status("Custom army updated.");
    return true;
  }
  const { descriptor, existing } = editFor(record, field);
  let edits = existing ? [existing] : [];
  if (Array.isArray(field.value)) {
    edits = profile().edits.filter((edit) => edit.scope === descriptor.scope && edit.key === record.key &&
      (core.isRosterEdit(descriptor) ? core.isRosterEdit(edit) || core.isRosterSlotEdit(edit) : core.isLoadoutEdit(edit)));
  }
  if (reset && !edits.length) return false;
  if (!reset) {
    const error = core.fieldError(game(), field, value);
    if (error) {
      status(error, true);
      return false;
    }
    if (existing && existing.value === value) return true;
  }
  remember();
  profile().edits = profile().edits.filter((edit) => !edits.includes(edit));
  if (!reset) profile().edits.push({ ...descriptor, value });
  const saved = autosave();
  renderProfiles();
  renderRecords();
  status(saved ? "Profile updated. Save project to keep a portable copy." :
    "Profile updated. Use Save project to keep your changes.");
  return true;
}

function scopedValue(record, field) {
  const current = editFor(record, field).existing;
  const shared = editFor(record, field, "shared").existing;
  return current?.value ?? (scope() !== "shared" ? shared?.value : undefined) ?? field.value;
}

function previewBulk() {
  const { records } = visibleRecords();
  const stat = $("bulk-field").value;
  const operation = $("bulk-operation").value;
  const amount = $("bulk-value").valueAsNumber;
  const review = $("bulk-review");
  const result = [];
  let invalid = 0;
  if (Number.isFinite(amount)) {
    for (const record of records) {
      const field = record.fields.find((candidate) => core.pathKey(candidate.path) === stat);
      if (!field) continue;
      const before = scopedValue(record, field);
      const value = Math.fround(operation === "set" ? amount : operation === "add" ? before + amount : before * amount);
      if (value === before) continue;
      const error = core.fieldError(game(), field, value);
      if (error) invalid++;
      const { descriptor } = editFor(record, field);
      result.push({ edit: { ...descriptor, value }, label: record.title, before, error });
    }
  }
  $("bulk-summary").textContent = Number.isFinite(amount) ?
    `${result.length - invalid} changes across ${records.length} visible units${invalid ? ` · ${invalid} invalid` : ""}.` :
    `Enter a value to preview changes across ${records.length} visible units.`;
  review.replaceChildren(...result.map(({ edit, label, before, error }) => node("div",
    error ? "export-item skipped" : "export-item",
    `${label} · ${error || `${valueText(before)} → ${valueText(edit.value)}`}`)));
  review.hidden = !result.length;
  $("apply-bulk").disabled = !result.length || Boolean(invalid);
  return invalid ? [] : result.map((item) => item.edit);
}

function openBulk() {
  const { records } = visibleRecords();
  const stats = new Map();
  for (const record of records) {
    for (const field of record.fields) {
      if (typeof field.value === "number") stats.set(core.pathKey(field.path), field.label);
    }
  }
  $("bulk-field").replaceChildren(...[...stats].map(([value, title]) =>
    Object.assign(node("option", "", title), { value })));
  $("bulk-scope").textContent = scope() === "shared" ?
    `Uses ${names[state.edition]} values and saves the resulting numbers for both editions. Edition-specific edits take precedence.` :
    `Applies only to ${names[state.edition]}.`;
  $("bulk-value").value = "";
  $("bulk-operation").value = "set";
  previewBulk();
  $("bulk-dialog").showModal();
}

function renderField(record, field, otherRecord, index) {
  const row = node("div", "field");
  const labelBox = node("div");
  const id = `field-${index}`;
  const label = node("label", "", field.label);
  label.htmlFor = id;
  const base = node("small", "", `${record.custom ? "Custom army" : `${names[state.edition]} base`} ${valueText(field.value)}`);
  labelBox.append(label, base);
  if (field.animationError) labelBox.append(node("small", "", field.animationError));
  const otherField = otherRecord?.fields.find((f) => core.pathKey(f.path) === core.pathKey(field.path));
  if (otherField) labelBox.append(node("small", "", `${names[otherEdition()]} base ${valueText(otherField.value)}`));
  const comparison = project.profiles.find((p) => p.id === state.compare);
  if (comparison) {
    const local = editFor(record, field, state.edition, comparison).existing;
    const shared = editFor(record, field, "shared", comparison).existing;
    labelBox.append(node("small", "comparison", `${comparison.name} · ${valueText(local?.value ?? shared?.value ?? field.value)}`));
  }
  const override = node("small");
  labelBox.append(override);
  const reset = node("button", "reset", "↶");
  reset.title = "Remove this profile edit";
  reset.setAttribute("aria-label", `Reset ${field.label}`);

  const input = node(typeof field.value === "string" ? "select" : "input");
  input.id = id;
  if (typeof field.value === "string") {
    const choices = [...game().records[field.choice].values()]
      .filter((choice) => field.choice !== "spells" || game().assignedSpells.has(choice.id))
      .sort((a, b) => a.title.localeCompare(b.title));
    if (!choices.some((choice) => choice.id === field.value)) {
      input.append(Object.assign(node("option", "", field.value), { value: field.value }));
    }
    for (const choice of choices) input.append(Object.assign(node("option", "", `${choice.title} (${choice.id})`), { value: choice.id }));
  } else if (typeof field.value === "boolean") input.type = "checkbox";
  else {
    input.type = "number";
    input.min = field.min;
    if (field.max !== undefined) input.max = field.max;
    input.step = field.integer ? "1" : "any";
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") input.blur(); });
  }

  function refresh() {
    const edited = editFor(record, field).existing;
    const shared = editFor(record, field, "shared").existing;
    const local = editFor(record, field, state.edition).existing;
    const value = scopedValue(record, field);
    override.textContent = scope() === "shared" && local ? `This edition overrides it with ${valueText(local.value)}` :
      scope() !== "shared" && shared ? `Shared value ${valueText(shared.value)}` : "";
    override.hidden = !override.textContent;
    if (input.type === "checkbox") {
      input.checked = value;
      input.disabled = Boolean(field.animationError && !value);
    }
    else if (field.economyKey && !edited && !(scope() !== "shared" && shared) && field.stored === undefined) {
      input.value = "";
      input.placeholder = "Automatic";
    }
    else input.value = value;
    reset.disabled = !edited;
    row.classList.toggle("changed", Boolean(edited));
  }

  input.addEventListener("change", () => {
    const value = input.type === "number" ? input.valueAsNumber : input.type === "checkbox" ? input.checked : input.value;
    const saved = updateEdit(record, field, value, Boolean(field.economyKey && input.value === ""));
    if (saved && record.custom) {
      renderInspector();
      $(id)?.focus({ preventScroll: true });
    } else if (state.key === record.key) refresh();
    else renderInspector();
  });
  reset.addEventListener("click", () => {
    updateEdit(record, field, null, true);
    if (state.key === record.key) refresh();
    else renderInspector();
  });
  row.append(labelBox, input, reset);
  refresh();
  return row;
}

function renderLoadout(record, field, otherRecord) {
  const panel = node("div", "loadout");
  const edits = profile().edits;
  const activeScope = scope();
  const { value } = core.resolveLoadout(record, edits, activeScope === "shared" ? ["shared"] : ["shared", activeScope]);
  const hasEdit = (target) => edits.some((edit) =>
    edit.key === record.key && edit.scope === target && core.isLoadoutEdit(edit));
  const choices = [...game().assignedSpells].sort((a, b) =>
    game().records.spells.get(a).title.localeCompare(game().records.spells.get(b).title));
  const spellTitle = (id) => game().records.spells.get(id)?.title ?? id;
  const summary = (list) => list.length ? list.map(spellTitle).join(", ") : "No spells";
  const save = (next, reset = false) => {
    if (updateEdit(record, field, next, reset)) renderInspector();
  };
  const makeSelect = (label, selected) => {
    const select = node("select");
    select.setAttribute("aria-label", label);
    if (selected === "") select.append(Object.assign(node("option", "", "Choose a spell"), { value: "", disabled: true }));
    for (const id of choices.includes(selected) || !selected ? choices : [selected, ...choices]) {
      select.append(Object.assign(node("option", "", `${spellTitle(id)} (${id})`), { value: id }));
    }
    select.value = selected;
    return select;
  };
  panel.append(node("p", "quiet", `Base loadout · ${summary(field.value)}`));
  if (field.castFallback) panel.append(node("p", "quiet", field.castFallback === "Attack" ?
    "This unit will use its melee animation to cast." : "This unit will use its tactical cast animation."));
  if (field.animationError) panel.append(node("p", "quiet", field.animationError));
  const otherLoadout = otherRecord?.fields.find((item) => Array.isArray(item.value));
  if (otherLoadout) panel.append(node("p", "quiet", `${names[otherEdition()]} base · ${summary(otherLoadout.value)}`));
  const comparison = project.profiles.find((item) => item.id === state.compare);
  if (comparison) {
    const compared = core.resolveLoadout(record, comparison.edits, ["shared", state.edition]);
    panel.append(node("p", "quiet", `${comparison.name} · ${summary(compared.value)}`));
  }
  if (activeScope === "shared" && hasEdit(state.edition)) {
    panel.append(node("p", "quiet", "This edition has its own spell loadout."));
  }
  for (const [index, spell] of value.entries()) {
    const row = node("div", "loadout-row");
    const select = makeSelect(`Spell ${index + 1}`, spell);
    select.disabled = Boolean(field.animationError);
    select.addEventListener("change", () => save(value.with(index, select.value)));
    row.append(select);
    if (!field.animationError) {
      const remove = node("button", "button secondary", "Remove");
      remove.setAttribute("aria-label", `Remove spell ${index + 1}`);
      remove.addEventListener("click", () => save(value.toSpliced(index, 1)));
      row.append(remove);
    }
    panel.append(row);
  }
  const actions = node("div", "loadout-row");
  const select = makeSelect("Spell to add", "");
  const add = node("button", "button secondary", "Add spell");
  add.disabled = true;
  select.disabled = Boolean(field.animationError);
  select.addEventListener("change", () => { add.disabled = !select.value || Boolean(field.animationError); });
  add.addEventListener("click", () => save([...value, select.value]));
  const reset = node("button", "button secondary", "Reset");
  reset.disabled = !hasEdit(activeScope);
  reset.setAttribute("aria-label", "Reset spell loadout");
  reset.addEventListener("click", () => save(null, true));
  actions.append(select, add, reset);
  if (field.animationError && value.length) {
    const clear = node("button", "button secondary", "Clear loadout");
    clear.addEventListener("click", () => save([]));
    actions.append(clear);
  }
  panel.append(actions);
  return panel;
}

function rosterText(stacks, loaded) {
  return stacks.map(({ unit, quantity }) => `${quantity} × ${loaded.records.units.get(unit)?.title ?? unit}`).join(", ");
}

function renderRoster(record, otherRecord) {
  const field = record.roster;
  const targetScope = scope();
  const scopes = targetScope === "shared" ? ["shared"] : ["shared", targetScope];
  const { value } = core.resolveRoster(game(), record, profile().edits, scopes);
  const hasEdit = (scope) => profile().edits.some((edit) => edit.key === record.key && edit.scope === scope &&
    (core.isRosterEdit(edit) || core.isRosterSlotEdit(edit)));
  const choices = [...game().records.units.values()].filter((unit) => unit.id !== "Hero")
    .sort((a, b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id));
  const group = node("div", "field-group");
  const panel = node("div", "roster");
  group.append(node("h3", "", "Army roster"), panel);
  panel.append(node("p", "quiet", `${value.length} of ${field.maxStacks} stacks · ${value.reduce((n, troop) => n + troop.quantity, 0)} units`),
    node("p", "quiet", `Base roster · ${rosterText(field.value, game())}`));
  if (otherRecord?.roster) panel.append(node("p", "quiet",
    `${names[otherEdition()]} base · ${rosterText(otherRecord.roster.value, games[otherEdition()])}`));
  if (targetScope === "shared" && hasEdit(state.edition)) {
    panel.append(node("p", "quiet", "This edition also has its own roster edits."));
  }
  const comparison = project.profiles.find((item) => item.id === state.compare);
  if (comparison) {
    const compared = core.resolveRoster(game(), record, comparison.edits, ["shared", state.edition]);
    panel.append(node("p", "quiet", `${comparison.name} · ${rosterText(compared.value, game())}`));
  }
  const save = (next, focus, reset = false) => {
    if (!updateEdit(record, field, next, reset)) return false;
    renderInspector();
    $(focus)?.focus({ preventScroll: true });
    return true;
  };
  const action = (id, label, run, disabled = false) => {
    const button = node("button", "button secondary", label);
    button.id = id;
    button.disabled = disabled;
    button.addEventListener("click", run);
    return button;
  };
  for (const [index, stack] of value.entries()) {
    const row = node("div", "roster-row");
    const slot = index + 1;
    const unit = node("select");
    unit.id = `roster-unit-${slot}`;
    unit.setAttribute("aria-label", `Stack ${slot} unit`);
    if (!choices.some((choice) => choice.id === stack.unit)) {
      unit.append(Object.assign(node("option", "", stack.unit), { value: stack.unit }));
    }
    for (const choice of choices) {
      unit.append(Object.assign(node("option", "", `${choice.title} (${choice.id})`), { value: choice.id }));
    }
    unit.value = stack.unit;
    unit.addEventListener("change", () => {
      if (!save(value.with(index, { ...stack, unit: unit.value }), unit.id)) unit.value = stack.unit;
    });
    const quantity = node("input");
    Object.assign(quantity, { type: "number", id: `roster-quantity-${slot}`, min: 1,
      max: field.maxQuantity, step: 1, value: stack.quantity });
    quantity.setAttribute("aria-label", `Stack ${slot} quantity`);
    quantity.addEventListener("change", () => {
      if (!save(value.with(index, { ...stack, quantity: quantity.valueAsNumber }), quantity.id)) quantity.value = stack.quantity;
    });
    quantity.addEventListener("keydown", (event) => { if (event.key === "Enter") quantity.blur(); });
    const controls = node("div", "roster-controls");
    for (const [offset, label, arrow] of [[-1, "up", "↑"], [1, "down", "↓"]]) {
      const next = index + offset;
      const move = action(`roster-${label}-${slot}`, arrow, () => {
        const reordered = value.with(next, stack).with(index, value[next]);
        const canMoveAgain = next + offset >= 0 && next + offset < value.length;
        save(reordered, canMoveAgain ? `roster-${label}-${next + 1}` : `roster-unit-${next + 1}`);
      }, next < 0 || next >= value.length);
      move.setAttribute("aria-label", `Move stack ${slot} ${label}`);
      move.title = `Move stack ${slot} ${label}`;
      controls.append(move);
    }
    const duplicate = action(`roster-copy-${slot}`, "Duplicate", () =>
      save(value.toSpliced(index + 1, 0, { ...stack }), `roster-unit-${slot + 1}`), value.length >= field.maxStacks);
    duplicate.setAttribute("aria-label", `Duplicate stack ${slot}`);
    const remove = action(`roster-remove-${slot}`, "Remove", () =>
      save(value.toSpliced(index, 1), `roster-unit-${Math.min(slot, value.length - 1)}`), value.length === 1);
    remove.setAttribute("aria-label", `Remove stack ${slot}`);
    controls.append(duplicate, remove);
    row.append(node("span", "quiet", String(slot)), unit, quantity, controls);
    panel.append(row);
  }
  const actions = node("div", "roster-actions");
  const template = value.at(-1);
  actions.append(action("roster-add", "Add stack", () =>
    save([...value, { unit: template.unit, quantity: 1 }], `roster-unit-${value.length + 1}`),
    value.length >= field.maxStacks),
  action("roster-reset", "Reset roster", () => save(null, "roster-unit-1", true), !hasEdit(targetScope)));
  const error = core.fieldError(game(), field, value);
  if (error) {
    panel.append(node("p", "quiet", error));
    actions.append(action("roster-base", "Use base roster", () => save(field.value, "roster-unit-1")));
  }
  panel.append(actions);
  return group;
}

function renderInspector(resetScroll = false) {
  const panel = $("inspector");
  if (!game()) return;
  const record = catalog().get(state.key);
  if (!record) {
    panel.replaceChildren(node("p", "quiet", "No matching records."));
    return;
  }
  const other = games[otherEdition()];
  const otherRecord = other?.records[state.kind].get(record.key);
  const content = [
    node("p", "eyebrow", record.id),
    node("h2", "", record.title),
    node("span", "badge", record.custom ? `Custom army · ${names[state.edition]} only` :
      otherRecord ? "Available in both games" : other ? `${names[state.edition]} only` : names[state.edition]),
  ];
  if (record.description) content.push(node("p", "description", record.description));
  if (record.clips?.length) {
    const preview = node("button", "button secondary model-launch", "View 3D model");
    preview.addEventListener("click", () => window.openUnitViewer(game(), record, download));
    content.push(preview);
  }
  if (state.kind === "spells") content.push(node("p", "description",
    "Edit the spell’s required level here. Use Units to tune magic power, resistance, and spell loadouts."));
  if (state.kind === "armies") {
    if (record.roster) content.push(renderRoster(record, otherRecord));
    else content.push(node("p", "description", "This army uses a custom roster. You can edit the existing slots."));
    if (record.custom) {
      const remove = node("button", "button secondary", "Remove custom army");
      remove.addEventListener("click", () => {
        remember();
        profile().edits = profile().edits.filter((edit) =>
          !(core.isNewArmy(edit) && edit.key === record.key && edit.scope === state.edition));
        autosave();
        render();
        status("Custom army removed from this profile. Use Undo to restore it.");
      });
      content.push(remove);
    }
  }
  const groups = new Map();
  for (const [index, field] of record.fields.entries()) {
    if (record.roster && !field.armyPosition) continue;
    if (!groups.has(field.group)) groups.set(field.group, []);
    groups.get(field.group).push(Array.isArray(field.value) ? renderLoadout(record, field, otherRecord) :
      renderField(record, field, otherRecord, index));
  }
  for (const [name, rows] of groups) {
    const group = node("div", "field-group");
    group.append(node("h3", "", name));
    if (name === "Battlefield") {
      group.append(node("p", "quiet field-note",
        "The encounter radius also controls the army’s world-map area. Combat uses at least 110 game units."));
    }
    if (name === "Recruitment and rewards") {
      group.append(node("p", "quiet field-note", "Reset an override to use the base archive’s value or game formula. Recruitment price also contributes to battle gold."));
    }
    group.append(...rows);
    content.push(group);
  }
  const top = resetScroll ? 0 : panel.scrollTop;
  panel.replaceChildren(...content);
  panel.scrollTop = top;
}

function render() {
  const loaded = game();
  $("start").hidden = Boolean(loaded);
  $("editor").hidden = !loaded;
  $("reload").hidden = !loaded;
  for (const edition of core.editions) {
    const button = $(`game-${edition}`);
    button.setAttribute("aria-pressed", String(Boolean(games[edition]) && edition === state.edition));
    button.classList.toggle("loaded", Boolean(games[edition]));
    $(`status-${edition}`).textContent = games[edition] ?
      `${games[edition].records.units.size} units · ${games[edition].records.spells.size} spells` : "Choose archives";
  }
  renderProfiles();
  renderRecords();
  renderInspector();
}

function exportPreview() {
  const target = games[$("export-game").value];
  const plan = core.planExport(target, profile());
  $("export-summary").replaceChildren(
    node("p", "", `${plan.name} · ${plan.changes.length} changes · ${plan.skipped.length} skipped · ${plan.same.length} already match`),
    node("p", "quiet", target.worldEntries ?
      `Includes ${target.worldEntries.size} world draft modules. Install this combined PAK after the workspace’s game archives.` :
      "Use this PAK with the same archive set. Add it alongside those archives and remove it to restore their balance."),
  );
  const changes = plan.changes.map((e) => node("div", "export-item",
    core.isNewArmy(e) ? `${e.label} · ${rosterText(e.value.troops, target)} · Radius ${e.value.radius}` :
      core.isRosterEdit(e) ? `${e.label} · ${rosterText(e.field.value, target)} → ${rosterText(e.value, target)}` :
      `${e.label} · ${valueText(e.field.value)} → ${valueText(e.value)}${e.castFallback ? " · Uses a fallback cast animation" : ""}`));
  const skipped = plan.skipped.map((e) => node("div", "export-item skipped", `${e.label} · ${e.error}`));
  $("export-review").replaceChildren(...skipped, ...changes);
  $("export-review").hidden = !changes.length && !skipped.length;
  $("download-pak").disabled = !changes.length && !target.worldEntries?.size;
  return { target, plan };
}

for (const edition of core.editions) {
  $(`game-${edition}`).addEventListener("click", () => selectGame(edition));
  $(`start-${edition}`).addEventListener("click", () => pickArchives(edition));
}
for (const [buttonId, inputId] of [["choose-archives", "archives"], ["choose-archive-folder", "archive-folder"]]) {
  const input = $(inputId);
  $(buttonId).addEventListener("click", () => {
    input.value = "";
    input.click();
  });
  input.addEventListener("change", openArchives);
}
$("reload").addEventListener("click", () => pickArchives(state.edition));
$("workspace-balance").addEventListener("click", () => openWorkspacePane(false));
$("workspace-world").addEventListener("click", () => openWorkspacePane(true));
$("use-world-draft").addEventListener("click", loadWorldDraft);
window.addEventListener("message", (event) => {
  if (event.origin === location.origin && event.source === $("world-frame").contentWindow &&
      event.data === "attt-world-updated") {
    $("world-status").textContent = "Draft saved. Use world draft in Balance to include the changes in your export.";
  }
});
$("open-hero-models").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const loaded = game();
  button.disabled = true;
  try {
    const outfits = await core.loadHeroModels(loaded);
    if (loaded !== game()) return;
    if (!outfits.length) throw new Error("No hero outfits were found in these archives.");
    window.openUnitViewer(loaded, outfits[0], download, outfits);
  } catch (error) {
    status(error.message, true);
  } finally {
    button.disabled = false;
  }
});
$("new-profile").addEventListener("click", () => openProfileDialog("new"));
$("profile-edit").addEventListener("click", () => openProfileDialog("edit"));
$("profile-copy").addEventListener("click", () => openProfileDialog("copy"));
$("profile-delete").addEventListener("click", () => {
  if (project.profiles.length === 1 || !confirm(`Delete “${profile().name}”? You can undo this during this session.`)) return;
  remember();
  project.profiles = project.profiles.filter((p) => p.id !== project.selected);
  project.selected = project.profiles[0].id;
  autosave();
  render();
});
$("profile-name").addEventListener("input", () => $("profile-name").setCustomValidity(""));
$("profile-form").addEventListener("submit", saveProfile);
for (const button of document.querySelectorAll("[data-close]")) {
  button.addEventListener("click", () => $(button.dataset.close).close());
}
$("open-project").addEventListener("click", () => {
  $("project-file").value = "";
  $("project-file").click();
});
$("project-file").addEventListener("change", async () => {
  const file = $("project-file").files[0];
  if (!file) return;
  try {
    if (file.size > 8 * 1024 * 1024) throw new Error("This project file is too large.");
    const loaded = core.validateProject(JSON.parse(await file.text()));
    remember();
    project = loaded;
    autosave();
    render();
    status(`Opened ${file.name}.`);
  } catch (error) {
    status(`Could not open project. ${error.message}`, true);
  }
});
$("save-project").addEventListener("click", () => {
  download("AttT Balance Project.json", new Blob([JSON.stringify(project, null, 2) + "\n"], { type: "application/json" }));
  status("Project downloaded.");
});
$("undo").addEventListener("click", undo);
$("bulk-edit").addEventListener("click", openBulk);
for (const id of ["bulk-field", "bulk-operation", "bulk-value"]) {
  $(id).addEventListener("input", previewBulk);
}
$("bulk-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const edits = previewBulk();
  if (!edits.length) return;
  remember();
  const merged = new Map(profile().edits.map((edit) => [core.editKey(edit), edit]));
  for (const edit of edits) merged.set(core.editKey(edit), edit);
  profile().edits = [...merged.values()];
  $("bulk-dialog").close();
  autosave();
  render();
  status(`Applied ${edits.length} unit edits. Undo reverses the entire batch.`);
});
$("export").addEventListener("click", () => {
  $("export-game").replaceChildren(...core.editions.filter((e) => games[e])
    .map((e) => Object.assign(node("option", "", names[e]), { value: e })));
  $("export-game").value = state.edition;
  exportPreview();
  $("export-dialog").showModal();
});
$("export-game").addEventListener("change", exportPreview);
$("download-pak").addEventListener("click", async () => {
  try {
    const { target, plan } = exportPreview();
    if (target.worldRevision != null) {
      const response = await fetch("/api/session");
      if (!response.ok || String((await response.json()).worldRevision) !== target.worldRevision) {
        throw new Error("The world draft changed. Open World & campaign and choose Use world draft in Balance.");
      }
    }
    const bytes = core.exportGame(target, plan);
    download(plan.name, new Blob([bytes], { type: "application/octet-stream" }));
    $("export-dialog").close();
    status(`Downloaded ${plan.name} for ${names[target.edition]}.`);
  } catch (error) {
    $("export-dialog").close();
    status(error.message, true);
  }
});
for (const button of $("sections").querySelectorAll("[data-kind]")) {
  button.addEventListener("click", () => {
    state.kind = button.dataset.kind;
    state.key = null;
    resetSearch();
    for (const tab of $("sections").children) tab.setAttribute("aria-pressed", String(tab === button));
    renderRecords();
    renderInspector(true);
  });
}
$("scope").addEventListener("change", () => {
  state.scope = $("scope").value;
  renderInspector();
});
$("compare-profile").addEventListener("change", () => {
  state.compare = $("compare-profile").value;
  renderInspector();
});
$("search").addEventListener("input", () => {
  renderRecords();
  renderInspector(true);
});
$("filter").addEventListener("change", () => {
  renderRecords();
  renderInspector(true);
});
$("open-army-map").addEventListener("click", () => {
  const loaded = game();
  window.openArmyMap(loaded, profile(), catalog().get(state.key), (key) => {
    resetSearch();
    state.key = key;
    renderRecords();
    $("records").querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest" });
    renderInspector(true);
  }, (continent, point, closeMap) => {
    pendingArmy = { continent, point, closeMap };
    $("new-army-location").textContent = `${names[state.edition]} only · X ${point.x}, Z ${point.z}`;
    $("new-army-name").value = "";
    $("new-army-error").hidden = true;
    $("new-army-unit").replaceChildren(...[...loaded.records.units.values()].filter((unit) => unit.id !== "Hero")
      .sort((a, b) => a.title.localeCompare(b.title)).map(({ id, title }) =>
        Object.assign(node("option", "", `${title} (${id})`), { value: id })));
    if (loaded.records.units.has("uPeasant")) $("new-army-unit").value = "uPeasant";
    $("new-army-dialog").showModal();
    $("new-army-name").focus();
  });
});
$("new-army-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const { continent, point, closeMap } = pendingArmy;
  const edit = core.newArmyEdit(game(), continent, point, $("new-army-name").value.trim(),
    $("new-army-unit").value, crypto.randomUUID().replaceAll("-", ""));
  const error = core.newArmyError(game(), edit);
  if (error) {
    $("new-army-error").textContent = error;
    $("new-army-error").hidden = false;
    return;
  }
  remember();
  profile().edits.push(edit);
  autosave();
  $("new-army-dialog").close();
  closeMap();
  resetSearch();
  state.key = edit.key;
  render();
  status("Custom army added. Edit its roster and encounter radius here.");
});
document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, select, textarea") || document.querySelector("dialog[open]")) return;
  if (event.key === "/" && game()) {
    event.preventDefault();
    $("search").focus();
  }
  if (event.ctrlKey && !event.shiftKey && event.key.toLowerCase() === "z") {
    event.preventDefault();
    undo();
  }
});
try {
  const saved = localStorage.getItem(storeKey);
  if (saved) project = core.validateProject(JSON.parse(saved));
} catch {
  status("The last workspace could not be restored. You can open a saved project.", true);
}
render();
connectWorkspace();
