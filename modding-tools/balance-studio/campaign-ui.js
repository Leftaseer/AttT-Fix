"use strict";

window.makeCampaignEditor = function makeCampaignEditor(container, statusElement) {
  const titles = {
    world: ["World", "Inspect the terrain, edit placements and armies, and validate the world draft."],
    forests: ["Forests", "Add, move, ground, and remove trees in the campaign's forest zones."],
    story: ["Story", "Edit quests, triggers, and dialogue with an explicit dry run before saving."],
  };
  const storyFields = {
    quest: ["display_name", "description", "level"],
    trigger: ["want_live", "condition", "action"],
    dialogue: ["who", "speech", "condition", "action", "do"],
  };
  const storyLabels = {
    display_name: "Display name", description: "Description", level: "Level", want_live: "Want live",
    who: "Speaker", speech: "Dialogue text", condition: "Condition", action: "Action", do: "Do",
  };
  const storyText = new Set(["display_name", "description", "who", "speech"]);
  const state = {
    mode: "world", continent: 1, revision: null, syncedRevision: null,
    world: null, selectedArmy: null, worldPatch: "[]",
    forest: null, forestZone: "", forestModel: "", forestOffset: 0,
    forestOperation: "add", forestSelected: null, forestIndex: null,
    story: null, storyDetail: null, storyKind: "quest", storySearch: "",
    storySelected: null, storyOperation: "field",
  };
  let built = false;
  let loadTicket = 0;
  let storyTicket = 0;

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function button(text, className = "button secondary") {
    return Object.assign(node("button", className, text), { type: "button" });
  }

  function status(text, error = false) {
    statusElement.textContent = text;
    statusElement.classList.toggle("error", error);
  }

  async function request(path, body) {
    const response = await fetch(path, body === undefined ? {} : {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.error || `The workspace request failed (${response.status}).`);
    return data;
  }

  function parseJson(input, label) {
    try {
      return JSON.parse(input.value);
    } catch (error) {
      throw new Error(`${label} is not valid JSON: ${error.message}`);
    }
  }

  function fillSelect(select, values, selected, label = (value) => value) {
    select.replaceChildren(...values.map((value) => {
      const option = new Option(label(value), typeof value === "object" ? value.value : value);
      option.selected = option.value === String(selected);
      return option;
    }));
  }

  function syncContinents(continents) {
    const select = container.querySelector("#campaign-continent");
    const values = continents.map(String);
    if ([...select.options].map((option) => option.value).join() !== values.join()) {
      fillSelect(select, values, state.continent, (value) => `Continent ${value}`);
    }
    select.value = String(state.continent);
  }

  function showResult(title, value) {
    const panel = container.querySelector("#campaign-result");
    panel.hidden = false;
    panel.replaceChildren(node("h2", "", title),
      node("pre", "campaign-json", JSON.stringify(value, null, 2)));
    panel.scrollIntoView({ block: "nearest" });
  }

  function showIssues(issues, total) {
    const panel = container.querySelector("#campaign-result");
    panel.hidden = false;
    const content = [node("h2", "", total ? `Validation: ${total} issue${total === 1 ? "" : "s"}` : "Validation passed")];
    if (total > issues.length) content.push(node("p", "quiet", `Showing the first ${issues.length} issues.`));
    const list = node("div", "campaign-issues");
    for (const issue of issues) {
      const location = [issue.continent && `Continent ${issue.continent}`, issue.zone, issue.name,
        issue.index !== undefined && `Record ${issue.index}`].filter(Boolean).join(" · ");
      const item = node("div", `campaign-issue ${issue.level}`);
      item.append(node("strong", "", `${issue.level}: ${issue.kind}`),
        node("span", "", [location, issue.message, issue.file].filter(Boolean).join(" · ")));
      list.append(item);
    }
    content.push(list);
    panel.replaceChildren(...content);
  }

  async function perform(control, action) {
    control.disabled = true;
    try {
      await action();
    } catch (error) {
      status(error.message, true);
    } finally {
      control.disabled = false;
    }
  }

  function build() {
    if (built) return;
    built = true;
    container.innerHTML = `
      <div class="campaign-toolbar">
        <label for="campaign-continent">Continent</label>
        <select id="campaign-continent"></select>
        <button type="button" class="button secondary" id="campaign-validate">Validate</button>
        <span class="quiet">Changes are saved as project drafts, not written to the game archives.</span>
      </div>
      <div id="campaign-content" class="campaign-content"></div>
      <section id="campaign-result" class="campaign-result" aria-live="polite" hidden></section>`;
    container.querySelector("#campaign-continent").addEventListener("change", (event) => {
      state.continent = Number(event.target.value);
      state.selectedArmy = null;
      state.forestZone = "";
      state.forestOffset = 0;
      state.forestSelected = null;
      state.forestIndex = null;
      state.storySelected = null;
      state.storyDetail = null;
      loadMode();
    });
    container.querySelector("#campaign-validate").addEventListener("click", (event) => {
      perform(event.currentTarget, async () => {
        status("Validating the campaign draft…");
        const kind = state.mode === "world" ? "world" : state.mode;
        const result = await request(`/api/campaign/validate?continent=${state.continent}&kind=${kind}`);
        state.revision = result.revision;
        showIssues(result.issues, result.total);
        status(result.total ? `Validation found ${result.total} issue${result.total === 1 ? "" : "s"}.` : "No validation issues found.");
      });
    });
  }

  function worldPatchValue() {
    const input = container.querySelector("#campaign-world-patch");
    const value = parseJson(input, "World patch");
    if (Array.isArray(value)) return { format: "attt-world-patch/1", operations: value };
    if (!value || typeof value !== "object" || !Array.isArray(value.operations)) {
      throw new Error("World patch must be an operations array or an object with an operations array.");
    }
    return value;
  }

  async function applyWorld(operations, dryRun) {
    if (!operations.length) throw new Error("Add at least one world operation.");
    const result = await request("/api/campaign/world", {
      format: "attt-world-patch/1", operations, revision: state.revision, dry_run: dryRun,
    });
    if (!dryRun) {
      state.revision = result.revision;
      await loadMode();
    }
    showResult(dryRun ? "World dry run" : "World draft saved", result);
    status(dryRun ? "Review the proposed changes before applying them." : "World draft saved.");
  }

  const worldActions = {
    "add-army": "Add army", "move-army": "Move army or change radius", "remove-army": "Remove army",
    add: "Add a placement", move: "Move a placement", rotate: "Rotate a placement",
    clone: "Duplicate a placement", remove: "Remove a placement",
    "add-town": "Add town", "add-house": "Add house", "remove-town": "Remove town",
    "remove-house": "Remove house", snap: "Ground placements on terrain",
  };

  function worldForm(action, selection = {}) {
    const data = state.world;
    const form = container.querySelector("#campaign-world-form");
    const fields = form.querySelector(".campaign-form-grid");
    fields.replaceChildren();
    form.elements.action.value = action;
    const addField = (name, label, initial, options) => {
      const field = node(options ? "select" : "input");
      field.name = name;
      field.required = true;
      if (options) {
        fillSelect(field, options, initial, (entry) => entry.label ?? entry);
        if (initial !== undefined) field.value = initial;
      } else {
        field.type = typeof initial === "number" ? "number" : "text";
        if (field.type === "number") field.step = "any";
        field.value = initial ?? "";
      }
      const wrapper = node("label", "", label);
      wrapper.append(field);
      fields.append(wrapper);
      return field;
    };
    const number = (name, label, value) => addField(name, label, value ?? 0);
    const townOptions = Object.keys(data.towns);
    const needsTown = ["add", "move", "rotate", "clone", "remove", "add-house", "remove-house", "remove-town"].includes(action);
    const needsHouse = ["add", "move", "rotate", "clone", "remove", "remove-house"].includes(action);
    const isPlacement = ["add", "move", "rotate", "clone", "remove"].includes(action);
    const coordinates = (x, z, y) => {
      number("x", "X", x);
      if (y !== undefined) number("y", "Y", y);
      number("z", "Z", z);
    };
    const town = needsTown && addField("town", "Town", selection.town ?? townOptions[0], townOptions);
    const houses = data.towns[town?.value] ?? [];
    const house = needsHouse && addField("house", "House", selection.house ?? houses[0], houses);
    const selectContext = () => worldForm(action, { town: town?.value, house: house?.value, kind: form.elements.kind?.value });
    town?.addEventListener?.("change", () => worldForm(action, { town: town.value }));
    house?.addEventListener?.("change", selectContext);
    if (["move-army", "remove-army"].includes(action)) {
      const options = data.armies.filter((army) => action === "remove-army" ||
        (Number.isFinite(army.position?.x) && Number.isFinite(army.position?.z)))
        .map(({ name, title }) => ({ value: name, label: title === name ? name : title + " · " + name }));
      const armyField = addField("name", "Army", selection.army ?? options[0]?.value, options);
      const army = data.armies.find(({ name }) => name === armyField.value);
      if (action === "move-army" && army) {
        coordinates(army.position.x, army.position.z);
        const radius = number("radius", "Encounter radius", army.position.radius);
        if (army.position.radius == null) { radius.required = false; radius.value = ""; }
      }
      armyField.addEventListener("change", () => worldForm(action, { army: armyField.value }));
    } else if (action === "add-army") {
      addField("name", "Army ID", "aMod" + crypto.randomUUID().replaceAll("-", "").slice(0, 12));
      addField("display_name", "Display name", "New army");
      addField("attitude", "Attitude", "Agressive", [
        {value: "Agressive", label: "Hostile"}, "Neutral", "Disabled", "Dead",
      ]);
      addField("standard", "Standard", "stVagrant");
      const units = data.units.filter((id) => id !== "Hero");
      addField("unit", "First unit", units.includes("uPeasant") ? "uPeasant" : units[0], units);
      const quantity = number("quantity", "Quantity", 1);
      quantity.min = quantity.step = "1";
      coordinates();
      number("radius", "Encounter radius", 150).min = "1";
    } else if (isPlacement) {
      const kind = addField("kind", "Placement type", selection.kind ?? "npc", ["npc", "object", "tree"]);
      kind.addEventListener("change", selectContext);
      const entries = data.placements.filter((p) => p.town === town.value && p.house === house.value && p.kind === kind.value);
      let placement;
      if (action === "add" && kind.value === "npc") addField("name", "NPC", data.npcs[0], data.npcs);
      else if (action === "add") addField("name", "Model name", "");
      else {
        const index = addField("index", "Placement", selection.index ?? entries[0]?.index,
          entries.map((p) => ({ value: p.index, label: p.name + " · " + p.index })));
        placement = entries.find((p) => p.index === Number(index.value));
        index.addEventListener("change", () => worldForm(action, { town: town.value, house: house.value, kind: kind.value, index: index.value }));
      }
      if (action === "add" || action === "move") coordinates(placement?.local[0], placement?.local[2], placement?.local[1] ?? 0);
      if (action === "add" || action === "rotate") number("rot", "Rotation (degrees)", placement?.rotation);
    } else if (action.startsWith("add-")) {
      addField("name", action === "add-town" ? "Town ID" : "House ID", "");
      coordinates(0, 0, 0);
      number("rot", "Rotation (degrees)", 0);
    } else if (action === "remove-town" || action === "remove-house") {
      const force = addField("force", "Remove contained placements", "");
      force.type = "checkbox";
      force.required = false;
    } else if (action === "snap") number("offset", "Height offset", 0);
    const available = ![...fields.querySelectorAll("select")].some((select) => !select.options.length || !select.value);
    for (const control of form.querySelectorAll("[data-world-submit]")) control.disabled = !available;
  }

  function worldFormOperation(form) {
    const { action } = form.elements;
    const operation = { op: action.value, continent: state.continent };
    for (const field of form.querySelector(".campaign-form-grid").querySelectorAll("input, select")) {
      if (field.value === "") continue;
      operation[field.name] = field.type === "checkbox" ? field.checked :
        field.type === "number" ? field.valueAsNumber : field.value;
    }
    if (operation.index !== undefined) operation.index = Number(operation.index);
    if (operation.op === "add-army") {
      operation.troops = [[operation.unit, operation.quantity]];
      delete operation.unit;
      delete operation.quantity;
    }
    if (operation.op === "remove-town" || operation.op === "remove-house") {
      operation.name = operation.op === "remove-town" ? operation.town : operation.house;
    }
    return operation;
  }

  function renderWorldArmyList() {
    const data = state.world;
    const search = container.querySelector("#campaign-world-search").value.trim().toLowerCase();
    const armies = data.armies.filter((army) => `${army.title} ${army.name}`.toLowerCase().includes(search));
    const list = container.querySelector("#campaign-world-armies");
    list.replaceChildren(...armies.map((army) => {
      const row = button("", "campaign-record");
      row.setAttribute("aria-pressed", String(state.selectedArmy?.name === army.name));
      row.append(node("strong", "", army.title), node("small", "", army.name));
      row.addEventListener("click", () => {
        state.selectedArmy = army;
        renderWorldArmyList();
        renderWorldSelection();
      });
      return row;
    }));
    container.querySelector("#campaign-world-count").textContent =
      `${armies.length} of ${data.armies.length} armies · ${data.placements.length} placements`;
  }

  function renderWorldSelection() {
    const panel = container.querySelector("#campaign-world-selection");
    const army = state.selectedArmy;
    if (!army) {
      panel.replaceChildren(node("p", "quiet", "Select an army to move it or change its encounter radius."));
      return;
    }
    const position = army.position;
    const move = button("Move or change radius");
    move.disabled = !position || !Number.isFinite(position.x) || !Number.isFinite(position.z);
    move.addEventListener("click", () => worldForm("move-army", { army: army.name }));
    const remove = button("Remove army");
    remove.addEventListener("click", () => worldForm("remove-army", { army: army.name }));
    const actions = node("div", "campaign-inline-actions");
    actions.append(move, remove);
    panel.replaceChildren(node("h3", "", army.title),
      node("p", "quiet", position ? `X ${position.x ?? "?"} · Z ${position.z ?? "?"} · Radius ${position.radius ?? "default"}` : "No recorded position"),
      actions);
  }

  function renderWorld() {
    const data = state.world;
    const content = container.querySelector("#campaign-content");
    content.innerHTML = `
      <div class="campaign-world-layout">
        <section class="campaign-card campaign-map-card">
          <div class="campaign-card-heading"><h2>Terrain and armies</h2><span class="quiet">Select a pin or a roster name</span></div>
          <div class="campaign-map" id="campaign-world-map"><img id="campaign-world-image" alt="Rendered continent terrain"></div>
        </section>
        <div class="campaign-world-tools">
          <section class="campaign-card">
            <h2>Edit the world</h2>
            <form id="campaign-world-form" class="campaign-world-form">
              <label>Action<select id="campaign-world-action" name="action"></select></label>
              <div class="campaign-form-grid"></div>
              <p class="quiet">Click the terrain to fill X and Z for armies and new towns. Placement and house coordinates are local to their parent.</p>
              <div class="campaign-apply-actions">
                <button type="submit" class="button secondary" data-world-submit="preview">Preview edit</button>
                <button type="submit" class="button primary" data-world-submit="apply">Apply and save</button>
              </div>
            </form>
          </section>
          <section class="campaign-card campaign-catalog-card">
            <input id="campaign-world-search" type="search" placeholder="Search armies" aria-label="Search world armies">
            <p class="quiet" id="campaign-world-count"></p>
            <div class="campaign-record-list" id="campaign-world-armies"></div>
            <div class="campaign-selection" id="campaign-world-selection"></div>
          </section>
        </div>
      </div>
      <details class="campaign-card">
        <summary>Advanced world batch editor</summary>
        <label class="campaign-editor-label" for="campaign-world-patch">Operations JSON</label>
        <textarea id="campaign-world-patch" class="campaign-code" spellcheck="false"></textarea>
        <div class="campaign-apply-actions"><button type="button" class="button secondary" id="campaign-world-dry">Dry run</button><button type="button" class="button primary" id="campaign-world-apply">Apply and save</button></div>
      </details>`;
    const form = container.querySelector("#campaign-world-form");
    fillSelect(form.elements.action, Object.entries(worldActions).map(([value, label]) => ({ value, label })),
      "add-army", (entry) => entry.label);
    form.elements.action.addEventListener("change", () => worldForm(form.elements.action.value));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const operation = worldFormOperation(form);
      const preview = event.submitter?.dataset.worldSubmit !== "apply";
      if (!preview && operation.op.startsWith("remove") && !confirm("Remove this record from the draft?")) return;
      perform(event.submitter ?? form.querySelector("[data-world-submit]"), () => applyWorld([operation], preview));
    });
    worldForm("add-army");
    const patchText = container.querySelector("#campaign-world-patch");
    patchText.value = state.worldPatch;
    patchText.addEventListener("input", () => { state.worldPatch = patchText.value; });
    const image = container.querySelector("#campaign-world-image");
    if (data.bounds) image.src = `/api/campaign/terrain?continent=${state.continent}&revision=${encodeURIComponent(state.revision)}`;
    else {
      image.hidden = true;
      container.querySelector("#campaign-world-map").append(node("p", "quiet", "This continent has no terrain map."));
    }
    if (data.bounds) {
      const [minX, maxX, minZ, maxZ] = data.bounds;
      const width = maxX - minX, depth = maxZ - minZ;
      if (width > 0 && depth > 0) {
        image.addEventListener("click", (event) => {
          if (!["add-army", "move-army", "add-town"].includes(form.elements.action.value)) return;
          const rect = image.getBoundingClientRect();
          if (!rect.width || !rect.height || !form.elements.x || !form.elements.z) return;
          form.elements.x.value = Math.round(minX + width * (event.clientX - rect.left) / rect.width);
          form.elements.z.value = Math.round(minZ + depth * (event.clientY - rect.top) / rect.height);
          status("Map coordinates copied to the form.");
        });
        for (const army of data.armies) {
          const position = army.position;
          if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.z)) continue;
          const pin = button("", "campaign-pin");
          pin.style.left = `${(position.x - minX) / width * 100}%`;
          pin.style.top = `${(position.z - minZ) / depth * 100}%`;
          pin.title = army.title;
          pin.setAttribute("aria-label", `Select ${army.title}`);
          pin.setAttribute("aria-pressed", String(state.selectedArmy?.name === army.name));
          pin.addEventListener("click", () => {
            state.selectedArmy = army;
            renderWorldArmyList();
            renderWorldSelection();
            for (const marker of container.querySelectorAll(".campaign-pin")) marker.setAttribute("aria-pressed", "false");
            pin.setAttribute("aria-pressed", "true");
          });
          container.querySelector("#campaign-world-map").append(pin);
        }
      }
    }
    container.querySelector("#campaign-world-search").addEventListener("input", renderWorldArmyList);
    for (const [id, dryRun] of [["campaign-world-dry", true], ["campaign-world-apply", false]]) {
      container.querySelector("#" + id).addEventListener("click", (event) => {
        perform(event.currentTarget, async () => {
          const operations = worldPatchValue().operations;
          await applyWorld(operations, dryRun);
          if (!dryRun) {
            state.worldPatch = "[]";
            container.querySelector("#campaign-world-patch").value = "[]";
          }
        });
      });
    }
    renderWorldArmyList();
    renderWorldSelection();
  }

  function forestFormRequest(operation, dryRun) {
    const value = (id) => container.querySelector(`#campaign-forest-${id}`).valueAsNumber;
    const requestBody = {
      op: operation, continent: state.continent, zone: state.forestZone,
      revision: state.revision, dry_run: dryRun,
    };
    if (operation === "remove") {
      requestBody.index = state.forestSelected.index;
      return requestBody;
    }
    if (operation === "add") requestBody.model = container.querySelector("#campaign-forest-edit-model").value;
    else requestBody.index = state.forestSelected.index;
    for (const key of ["x", "z", "yaw", "scale", "y_scale"]) {
      const number = value(key);
      if (!Number.isFinite(number)) throw new Error(`Enter a finite ${key.replace("_", " ")} value.`);
      if (operation === "add" || number !== state.forestSelected[key]) requestBody[key] = number;
    }
    const ground = container.querySelector("#campaign-forest-ground").checked;
    requestBody.ground = ground;
    if (!ground) {
      const y = value("y");
      if (!Number.isFinite(y)) throw new Error("Enter a finite y value or enable terrain grounding.");
      requestBody.y = y;
    }
    return requestBody;
  }

  async function runForest(operation, dryRun) {
    if (operation !== "add" && !state.forestSelected) throw new Error("Select a forest record first.");
    if (operation === "remove" && !dryRun && !confirm("Remove this tree from the forest draft?")) return;
    const body = forestFormRequest(operation, dryRun);
    status(dryRun ? "Checking the forest edit…" : "Saving the forest draft…");
    const result = await request("/api/campaign/forests", body);
    showResult(dryRun ? "Forest dry run" : "Forest draft saved", result);
    if (!dryRun) {
      state.revision = result.revision;
      state.forestIndex = operation === "remove" ? null : result.index;
      if (operation === "add") {
        state.forestModel = "";
        state.forestOffset = Math.floor(result.index / 100) * 100;
      }
      state.forestSelected = null;
      state.forestOperation = operation === "remove" ? "add" : "move";
      await loadMode();
    }
    status(dryRun ? "Dry run complete. Review the result before applying it." : "Forest draft saved. Review the combined export to include it in a PAK.");
  }

  function renderForest() {
    const data = state.forest;
    state.forestZone = data.zone;
    if (state.forestIndex !== null) {
      state.forestSelected = data.rows.find((row) => row.index === state.forestIndex) || null;
      if (state.forestSelected) state.forestOperation = "move";
      state.forestIndex = null;
    }
    const moving = state.forestOperation === "move" && state.forestSelected;
    const selected = moving ? state.forestSelected : null;
    const editModel = selected?.model || state.forestModel || data.models[0] || "";
    const content = container.querySelector("#campaign-content");
    content.innerHTML = `
      <div class="campaign-forest-layout">
        <section class="campaign-card campaign-catalog-card">
          <div class="campaign-filter-grid">
            <label>Zone<select id="campaign-forest-zone"></select></label>
            <label>Model filter<select id="campaign-forest-model"><option value="">All models</option></select></label>
          </div>
          <p class="quiet" id="campaign-forest-count"></p>
          <div class="campaign-record-list campaign-forest-records" id="campaign-forest-records"></div>
          <div class="campaign-inline-actions"><button type="button" class="button secondary" id="campaign-forest-prev">Previous</button><button type="button" class="button secondary" id="campaign-forest-next">Next</button></div>
        </section>
        <section class="campaign-card">
          <div class="campaign-card-heading"><h2 id="campaign-forest-form-title"></h2><button type="button" class="button secondary" id="campaign-forest-new">New tree</button></div>
          <div class="campaign-form-grid">
            <label>Model<select id="campaign-forest-edit-model"></select></label>
            <label>X<input id="campaign-forest-x" type="number" step="any" required></label>
            <label>Y<input id="campaign-forest-y" type="number" step="any"></label>
            <label>Z<input id="campaign-forest-z" type="number" step="any" required></label>
            <label>Yaw °<input id="campaign-forest-yaw" type="number" step="any" required></label>
            <label>Scale<input id="campaign-forest-scale" type="number" step="any" min="0" required></label>
            <label>Vertical scale<input id="campaign-forest-y_scale" type="number" step="any" min="0" required></label>
          </div>
          <label class="campaign-check"><input id="campaign-forest-ground" type="checkbox"> Sample terrain height (ignore Y)</label>
          <p class="quiet" id="campaign-forest-selected"></p>
          <div class="campaign-apply-actions"><button type="button" class="button secondary" id="campaign-forest-dry">Dry run</button><button type="button" class="button primary" id="campaign-forest-apply">Apply and save</button><button type="button" class="button secondary" id="campaign-forest-remove">Remove tree</button></div>
        </section>
      </div>`;
    fillSelect(container.querySelector("#campaign-forest-zone"), data.zones, data.zone);
    fillSelect(container.querySelector("#campaign-forest-model"), data.models, state.forestModel);
    container.querySelector("#campaign-forest-model").insertBefore(new Option("All models", ""), container.querySelector("#campaign-forest-model").firstChild);
    container.querySelector("#campaign-forest-model").value = state.forestModel;
    fillSelect(container.querySelector("#campaign-forest-edit-model"), data.models, editModel);
    const noZone = !data.zone;
    for (const element of content.querySelectorAll("button, input, select")) element.disabled = noZone;
    if (noZone) {
      container.querySelector("#campaign-forest-count").textContent = "No forest zones are available on this continent.";
      return;
    }
    container.querySelector("#campaign-forest-count").textContent =
      `${data.rows.length} shown · ${data.total} records${state.forestModel ? ` · ${state.forestModel}` : ""}`;
    container.querySelector("#campaign-forest-prev").disabled = state.forestOffset === 0;
    container.querySelector("#campaign-forest-next").disabled = !data.more;
    const list = container.querySelector("#campaign-forest-records");
    list.replaceChildren(...data.rows.map((row) => {
      const record = button("", "campaign-record campaign-forest-record");
      record.setAttribute("aria-pressed", String(selected?.index === row.index));
      record.append(node("strong", "", `${row.index}: ${row.model || `Type ${row.type}`}`),
        node("small", "", `X ${row.x.toFixed(2)} · Y ${row.y.toFixed(2)} · Z ${row.z.toFixed(2)}`));
      record.addEventListener("click", () => {
        state.forestSelected = row;
        state.forestOperation = "move";
        renderForest();
      });
      return record;
    }));
    container.querySelector("#campaign-forest-zone").addEventListener("change", (event) => {
      state.forestZone = event.target.value;
      state.forestModel = "";
      state.forestOffset = 0;
      state.forestSelected = null;
      state.forestOperation = "add";
      loadMode();
    });
    container.querySelector("#campaign-forest-model").addEventListener("change", (event) => {
      state.forestModel = event.target.value;
      state.forestOffset = 0;
      state.forestSelected = null;
      state.forestOperation = "add";
      loadMode();
    });
    container.querySelector("#campaign-forest-prev").addEventListener("click", () => {
      state.forestOffset = Math.max(0, state.forestOffset - 100);
      state.forestSelected = null;
      loadMode();
    });
    container.querySelector("#campaign-forest-next").addEventListener("click", () => {
      state.forestOffset += 100;
      state.forestSelected = null;
      loadMode();
    });
    container.querySelector("#campaign-forest-new").addEventListener("click", () => {
      state.forestSelected = null;
      state.forestOperation = "add";
      renderForest();
    });
    container.querySelector("#campaign-forest-form-title").textContent = selected ? `Move tree ${selected.index}` : "Add a tree";
    container.querySelector("#campaign-forest-edit-model").disabled = Boolean(selected);
    for (const key of ["x", "y", "z"]) {
      container.querySelector(`#campaign-forest-${key}`).value = selected ? selected[key] : 0;
    }
    container.querySelector("#campaign-forest-yaw").value = selected?.yaw ?? 0;
    container.querySelector("#campaign-forest-scale").value = selected?.scale ?? 1;
    container.querySelector("#campaign-forest-y_scale").value = selected?.y_scale ?? 1;
    const ground = container.querySelector("#campaign-forest-ground");
    ground.checked = !selected;
    container.querySelector("#campaign-forest-y").disabled = ground.checked;
    ground.addEventListener("change", () => {
      container.querySelector("#campaign-forest-y").disabled = ground.checked;
    });
    container.querySelector("#campaign-forest-selected").textContent = selected ?
      `Record ${selected.index} in ${data.zone}. Model changes require adding a new tree.` :
      "Y is sampled from the heightmap when terrain grounding is enabled.";
    container.querySelector("#campaign-forest-remove").hidden = !selected;
    container.querySelector("#campaign-forest-dry").addEventListener("click", (event) =>
      perform(event.currentTarget, () => runForest(selected ? "move" : "add", true)));
    container.querySelector("#campaign-forest-apply").addEventListener("click", (event) =>
      perform(event.currentTarget, () => runForest(selected ? "move" : "add", false)));
    container.querySelector("#campaign-forest-remove").addEventListener("click", (event) =>
      perform(event.currentTarget, () => runForest("remove", false)));
  }

  function storyRecordValue() {
    const detail = state.storyDetail;
    if (!detail) return "";
    const field = container.querySelector("#campaign-story-field").value;
    if (state.storyKind === "dialogue") {
      const path = container.querySelector("#campaign-story-path").value || "root";
      const entry = detail.nodes?.find(([nodePath]) => nodePath === path);
      return entry?.[1]?.[field] ?? "";
    }
    return detail.record?.[field] ?? "";
  }

  function setStoryValue() {
    const operation = container.querySelector("#campaign-story-operation").value;
    const field = container.querySelector("#campaign-story-field").value;
    const input = container.querySelector("#campaign-story-value");
    const toggle = container.querySelector("#campaign-story-boolean");
    const useToggle = operation === "field" && field === "want_live";
    toggle.hidden = useToggle === false;
    input.hidden = useToggle;
    const plain = operation === "field" && (storyText.has(field) || field === "level" || useToggle);
    input.classList.toggle("campaign-code", !plain);
    container.querySelector("#campaign-story-value-label").textContent = operation === "create" ?
      "Create payload (JSON)" : plain ? storyLabels[field] : "Function or literal (JSON)";
    if (operation === "remove") {
      input.value = "";
      return;
    }
    if (operation === "create") {
      const templates = {
        quest: { DisplayName: "New quest", Description: "", Level: 1, SubQuest: {} },
        trigger: { WantLive: true, Condition: true, Action: true },
        dialogue: { who: "HERO", speech: "New line" },
      };
      input.value = JSON.stringify(templates[state.storyKind], null, 2);
      return;
    }
    const value = storyRecordValue();
    if (useToggle) toggle.value = String(value === true);
    else if (plain) input.value = value;
    else input.value = value && typeof value === "object" && value.function ? "" : JSON.stringify(value, null, 2);
  }

  function syncStoryOperation() {
    const operation = container.querySelector("#campaign-story-operation").value;
    state.storyOperation = operation;
    container.querySelector("#campaign-story-field-row").hidden = operation !== "field";
    container.querySelector("#campaign-story-value-row").hidden = operation === "remove";
    setStoryValue();
  }

  function renderStoryDetail() {
    const detail = state.storyDetail;
    const panel = container.querySelector("#campaign-story-record");
    panel.replaceChildren();
    if (!detail) {
      panel.append(node("p", "quiet", "Select a story record to inspect and edit it."));
      return;
    }
    panel.append(node("h3", "", state.storySelected.name));
    const preview = node("details", "campaign-record-json");
    preview.append(node("summary", "", "Record JSON"), node("pre", "campaign-json", JSON.stringify(detail.record, null, 2)));
    panel.append(preview);
    if (detail.nodes) {
      const nodes = node("div", "campaign-dialogue-nodes");
      for (const [path, record] of detail.nodes) {
        const row = button("", "campaign-dialogue-node");
        row.append(node("strong", "", path), node("small", "", record.speech || record.who || "No speech"));
        row.addEventListener("click", () => {
          state.storySelected.path = path;
          container.querySelector("#campaign-story-path").value = path;
          container.querySelector("#campaign-story-operation").value = "field";
          syncStoryOperation();
        });
        nodes.append(row);
      }
      panel.append(node("h3", "", "Dialogue nodes"), nodes);
    }
  }

  function storyOperation() {
    const name = container.querySelector("#campaign-story-name").value.trim();
    if (!name) throw new Error("Enter a story record name.");
    const operation = container.querySelector("#campaign-story-operation").value;
    const result = { kind: state.storyKind, continent: state.continent, name };
    if (state.storyKind === "dialogue") {
      const path = container.querySelector("#campaign-story-path").value.trim();
      if (path) result.path = path;
      else if (operation !== "create") result.path = "root";
    }
    if (operation === "remove") result.remove = true;
    else if (operation === "create") result.create = parseJson(container.querySelector("#campaign-story-value"), "Create payload");
    else {
      result.field = container.querySelector("#campaign-story-field").value;
      const input = container.querySelector("#campaign-story-value");
      if (storyText.has(result.field)) result.value = input.value;
      else if (result.field === "want_live") result.value = container.querySelector("#campaign-story-boolean").value === "true";
      else if (result.field === "level") {
        result.value = Number(input.value);
        if (!input.value.trim() || !Number.isFinite(result.value)) throw new Error("Enter a number for the quest level.");
      } else result.value = parseJson(input, "Story field value");
    }
    return result;
  }

  async function runStory(dryRun) {
    const operation = storyOperation();
    if (operation.remove && !dryRun && !confirm("Remove this story record or dialogue node from the draft?")) return;
    status(dryRun ? "Checking the story edit…" : "Saving the story draft…");
    const result = await request("/api/campaign/story", {
      operations: [operation], revision: state.revision, dry_run: dryRun,
    });
    showResult(dryRun ? "Story dry run" : "Story draft saved", result);
    if (!dryRun) {
      state.revision = result.revision;
      state.storySelected = operation.remove ? null : { name: operation.name, path: operation.path || "root" };
      state.storyDetail = null;
      await loadMode();
    }
    status(dryRun ? "Dry run complete. Review the result before applying it." : "Story draft saved. Review the combined export to include it in a PAK.");
  }

  function renderStory() {
    const data = state.story;
    const content = container.querySelector("#campaign-content");
    content.innerHTML = `
      <div class="campaign-story-layout">
        <section class="campaign-card campaign-catalog-card">
          <div class="campaign-filter-grid">
            <label>Record type<select id="campaign-story-kind"><option value="quest">Quests</option><option value="trigger">Triggers</option><option value="dialogue">Dialogues</option></select></label>
            <label>Search<input id="campaign-story-search" type="search" placeholder="Names and text"></label>
          </div>
          <div class="campaign-record-list" id="campaign-story-records"></div>
          <p class="quiet">Up to 150 matching rows are shown.</p>
        </section>
        <section class="campaign-card campaign-story-detail" id="campaign-story-record"></section>
      </div>
      <section class="campaign-card campaign-patch-card">
        <div class="campaign-card-heading"><div><h2>Story operation</h2><p class="quiet">Edit text and settings directly. Advanced record creation and function fields accept JSON.</p></div></div>
        <div class="campaign-form-grid campaign-story-form">
          <label>Operation<select id="campaign-story-operation"><option value="field">Edit field</option><option value="create">Create record or reply</option><option value="remove">Remove record or reply</option></select></label>
          <label>Record name<input id="campaign-story-name" required></label>
          <label id="campaign-story-path-row">Dialogue path<input id="campaign-story-path" value="root"></label>
          <label id="campaign-story-field-row">Field<select id="campaign-story-field"></select></label>
        </div>
        <label class="campaign-editor-label" id="campaign-story-value-row"><span id="campaign-story-value-label">Value</span><textarea id="campaign-story-value" class="campaign-story-value"></textarea><select id="campaign-story-boolean" hidden><option value="true">On</option><option value="false">Off</option></select></label>
        <div class="campaign-apply-actions"><button type="button" class="button secondary" id="campaign-story-dry">Dry run</button><button type="button" class="button primary" id="campaign-story-apply">Apply and save</button></div>
      </section>`;
    container.querySelector("#campaign-story-kind").value = state.storyKind;
    container.querySelector("#campaign-story-search").value = state.storySearch;
    const list = container.querySelector("#campaign-story-records");
    list.replaceChildren(...data.rows.map((row) => {
      const record = button("", "campaign-record");
      const selected = state.storySelected?.name === row.name &&
        (state.storyKind !== "dialogue" || !row.path || state.storySelected.path === row.path);
      record.setAttribute("aria-pressed", String(selected));
      record.append(node("strong", "", row.display_name || row.name),
        node("small", "", row.path ? `${row.name} · ${row.path}` : row.name));
      if (row.speech) record.append(node("small", "", row.speech));
      record.addEventListener("click", async () => {
        state.storySelected = { name: row.name, path: row.path || "root" };
        state.storyOperation = "field";
        await loadStoryDetail();
      });
      return record;
    }));
    container.querySelector("#campaign-story-kind").addEventListener("change", (event) => {
      state.storyKind = event.target.value;
      state.storySelected = null;
      state.storyDetail = null;
      state.storyOperation = "field";
      loadMode();
    });
    container.querySelector("#campaign-story-search").addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      state.storySearch = event.currentTarget.value.trim();
      state.storySelected = null;
      state.storyDetail = null;
      loadMode();
    });
    container.querySelector("#campaign-story-search").addEventListener("search", (event) => {
      state.storySearch = event.currentTarget.value.trim();
      state.storySelected = null;
      state.storyDetail = null;
      loadMode();
    });
    container.querySelector("#campaign-story-operation").value = state.storyOperation;
    container.querySelector("#campaign-story-name").value = state.storySelected?.name || "";
    container.querySelector("#campaign-story-path").value = state.storySelected?.path || "root";
    container.querySelector("#campaign-story-path-row").hidden = state.storyKind !== "dialogue";
    fillSelect(container.querySelector("#campaign-story-field"), storyFields[state.storyKind], storyFields[state.storyKind][0],
      (field) => storyLabels[field]);
    container.querySelector("#campaign-story-operation").addEventListener("change", syncStoryOperation);
    container.querySelector("#campaign-story-field").addEventListener("change", setStoryValue);
    container.querySelector("#campaign-story-path").addEventListener("change", setStoryValue);
    syncStoryOperation();
    renderStoryDetail();
    container.querySelector("#campaign-story-dry").addEventListener("click", (event) =>
      perform(event.currentTarget, () => runStory(true)));
    container.querySelector("#campaign-story-apply").addEventListener("click", (event) =>
      perform(event.currentTarget, () => runStory(false)));
  }

  async function loadStoryDetail() {
    const selected = state.storySelected;
    if (!selected) {
      state.storyDetail = null;
      renderStory();
      return;
    }
    const ticket = ++storyTicket;
    status("Reading the story record…");
    try {
      const detail = await request(`/api/campaign/story?continent=${state.continent}&kind=${state.storyKind}&name=${encodeURIComponent(selected.name)}`);
      if (ticket !== storyTicket || selected !== state.storySelected) return;
      state.storyDetail = detail;
      state.revision = detail.revision;
      renderStory();
      status("Story record loaded.");
    } catch (error) {
      if (ticket === storyTicket) status(error.message, true);
    }
  }

  async function loadMode() {
    const ticket = ++loadTicket;
    const mode = state.mode;
    status(`Loading ${titles[mode][0].toLowerCase()} data…`);
    try {
      let data;
      if (mode === "world") {
        data = await request(`/api/campaign/world?continent=${state.continent}`);
      } else if (mode === "forests") {
        const query = new URLSearchParams({ continent: state.continent, offset: state.forestOffset });
        if (state.forestZone) query.set("zone", state.forestZone);
        if (state.forestModel) query.set("model", state.forestModel);
        data = await request(`/api/campaign/forests?${query}`);
      } else {
        const query = new URLSearchParams({ continent: state.continent, kind: state.storyKind, search: state.storySearch });
        data = await request(`/api/campaign/story?${query}`);
      }
      if (ticket !== loadTicket || mode !== state.mode) return;
      state.revision = data.revision;
      syncContinents(data.continents);
      if (mode === "world") {
        state.world = data;
        if (state.selectedArmy) state.selectedArmy = data.armies.find((army) => army.name === state.selectedArmy.name);
        renderWorld();
      } else if (mode === "forests") {
        state.forest = data;
        renderForest();
      } else {
        state.story = data;
        if (!state.storySelected && data.rows.length) {
          const row = data.rows[0];
          state.storySelected = { name: row.name, path: row.path || "root" };
        }
        if (state.storySelected) {
          const detail = await request(`/api/campaign/story?continent=${state.continent}&kind=${state.storyKind}&name=${encodeURIComponent(state.storySelected.name)}`);
          if (ticket !== loadTicket || mode !== state.mode) return;
          state.storyDetail = detail;
          state.revision = detail.revision;
        } else state.storyDetail = null;
        renderStory();
      }
      status(`${titles[mode][0]} draft loaded.`);
    } catch (error) {
      if (ticket === loadTicket) status(error.message, true);
    }
  }

  return {
    request,
    open(mode) {
      if (!titles[mode]) return;
      build();
      state.mode = mode;
      document.getElementById("campaign-title").textContent = titles[mode][0];
      document.getElementById("campaign-summary").textContent = titles[mode][1];
      loadMode();
    },
    reset() {
      loadTicket++;
      storyTicket++;
      built = false;
      container.replaceChildren();
      state.revision = null;
      state.syncedRevision = null;
      state.world = null;
      state.worldPatch = "[]";
      state.selectedArmy = null;
      state.continent = 1;
      state.forest = null;
      state.forestZone = "";
      state.forestModel = "";
      state.forestOffset = 0;
      state.forestSelected = null;
      state.forestIndex = null;
      state.story = null;
      state.storyDetail = null;
      state.storySelected = null;
      state.storySearch = "";
      status("");
    },
    dirty() {
      return state.revision !== null && state.revision !== state.syncedRevision;
    },
    synced() {
      state.syncedRevision = state.revision;
    },
  };
};
