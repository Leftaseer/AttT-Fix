"use strict";

window.openArmyMap = (() => {
  const element = (name) => document.getElementById("army-map-" + name);
  const dialog = element("dialog");
  const canvas = element("image");
  const view = element("view");
  const layer = element("layer");
  const continent = element("continent");
  const groupButtons = [...element("groups").querySelectorAll("button")];
  const search = element("search");
  const list = element("list");
  const pins = element("pins");
  const status = element("status");
  const hint = element("hint");
  const selection = element("selection");
  const summary = element("summary");
  const roster = element("roster");
  const add = element("add");
  const stances = { Agressive: "Hostile", Neutral: "Neutral", Disabled: "Disabled", Dead: "Dead" };
  const groupHints = {
    hostile: "",
    other: "Includes neutral and disabled army records. ",
    dead: "Shows army records marked Dead in the game data. ",
  };
  let game, profile, onPick, onPlace, selected;
  let armies = [];
  let request = 0;
  let zoom = 1;
  let group = "hostile";
  let placing = false;

  function groupFor(record) {
    if (record.attitude === "Agressive") return "hostile";
    if (record.attitude === "Dead") return "dead";
    return "other";
  }

  function showGroup(next) {
    group = next;
    for (const button of groupButtons) button.setAttribute("aria-pressed", String(button.dataset.group === group));
    hint.textContent = placing ? "Click an open patch of land to place the army. The map cannot check walkability." :
      `${groupHints[group]}Scroll over the map to zoom. Drag to pan.`;
  }

  function setPlacement(active) {
    placing = active;
    add.setAttribute("aria-pressed", String(active));
    add.textContent = active ? "Cancel placement" : "Add army";
    canvas.classList.toggle("placing", active);
    showGroup(group);
  }

  function drawMap(bytes) {
    const header = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const width = bytes.length >= 18 ? header.getUint16(12, true) : 0;
    const height = bytes.length >= 18 ? header.getUint16(14, true) : 0;
    const type = bytes[2];
    const channels = bytes[16] / 8;
    if (!width || !height || width > 4096 || height > 4096 || bytes[1] !== 0 ||
      (type !== 2 && type !== 10) || (channels !== 3 && channels !== 4)) {
      throw new Error("This map image uses an unsupported TGA format.");
    }
    const context = canvas.getContext("2d");
    const image = context.createImageData(width, height);
    let offset = 18 + bytes[0];
    let index = 0;
    while (index < width * height) {
      const packet = type === 10 ? bytes[offset++] : 0;
      const count = (packet & 127) + 1;
      const repeat = Boolean(packet & 128);
      if (index + count > width * height || offset + channels * (repeat ? 1 : count) > bytes.length) {
        throw new Error("The map image ends unexpectedly.");
      }
      for (let i = 0; i < count; i++, index++) {
        const column = index % width, row = Math.floor(index / width);
        const x = bytes[17] & 16 ? width - 1 - column : column;
        const y = bytes[17] & 32 ? row : height - 1 - row;
        const at = (y * width + x) * 4;
        image.data[at] = bytes[offset + 2];
        image.data[at + 1] = bytes[offset + 1];
        image.data[at + 2] = bytes[offset];
        image.data[at + 3] = channels === 4 ? bytes[offset + 3] : 255;
        if (!repeat) offset += channels;
      }
      if (repeat) offset += channels;
    }
    canvas.width = width;
    canvas.height = height;
    context.putImageData(image, 0, 0);
  }

  function pinIntoView(pin) {
    if (!pin) return;
    view.scrollTo(pin.x * layer.clientWidth - view.clientWidth / 2,
      pin.y * layer.clientHeight - view.clientHeight / 2);
  }

  function select(army, centerMap = false) {
    selected = army;
    for (const button of [...list.children, ...pins.children]) {
      button.setAttribute("aria-pressed", String(button.dataset.key === selected?.record.key));
    }
    if (army) {
      const { record, pin } = army;
      const name = record.title === record.id ? record.title : `${record.title} · ${record.id}`;
      selection.textContent = `${name}${pin ? "" : " · No recorded starting position"}`;
    } else selection.textContent = "Select an army to inspect its roster.";
    const stacks = army?.record.roster?.value ?? [];
    const preview = stacks.slice(0, 3).map(({ unit, quantity }) =>
      `${quantity} × ${game.records.units.get(unit)?.title ?? unit}`);
    summary.textContent = `Base roster · ${preview.join(", ")}${stacks.length > 3 ? ` + ${stacks.length - 3} more` : ""}`;
    summary.hidden = !stacks.length;
    roster.disabled = !army;
    if (centerMap) pinIntoView(army?.pin);
  }

  function renderArmies() {
    const query = search.value.trim().toLocaleLowerCase();
    const matches = armies.filter(({ record }) =>
      groupFor(record) === group &&
      `${record.title} ${record.id}`.toLocaleLowerCase().includes(query));
    list.replaceChildren();
    pins.replaceChildren();
    for (const army of matches) {
      const { record, pin } = army;
      const row = document.createElement("button");
      row.type = "button";
      row.className = "record";
      row.dataset.key = record.key;
      const title = document.createElement("strong");
      title.textContent = record.title;
      const detail = document.createElement("small");
      const detailItems = [stances[record.attitude] ?? "Other"];
      if (record.title !== record.id) detailItems.unshift(record.id);
      if (record.roster) {
        const count = record.roster.value.length;
        detailItems.push(`${count} ${count === 1 ? "stack" : "stacks"}`);
      }
      if (!pin) detailItems.push("No pin");
      detail.textContent = detailItems.join(" · ");
      row.append(title, detail);
      row.addEventListener("click", () => select(army, true));
      row.addEventListener("dblclick", () => openRoster(army));
      list.append(row);
      if (!pin) continue;
      const marker = document.createElement("button");
      marker.type = "button";
      marker.className = `army-pin ${group}`;
      marker.style.left = `${pin.x * 100}%`;
      marker.style.top = `${pin.y * 100}%`;
      marker.title = `${record.title} (${record.id})`;
      marker.setAttribute("aria-label", marker.title);
      marker.dataset.key = record.key;
      marker.addEventListener("click", () => {
        select(army);
        row.scrollIntoView({ block: "nearest" });
      });
      marker.addEventListener("dblclick", () => openRoster(army));
      pins.append(marker);
    }
    select(matches.includes(selected) ? selected : null);
    status.textContent = matches.length ? `${pins.childElementCount} pins · ${matches.length - pins.childElementCount} without a starting position` :
      "No armies match the current filters.";
  }

  function changeZoom(next, anchorX = view.clientWidth / 2, anchorY = view.clientHeight / 2) {
    const x = (view.scrollLeft + anchorX) / Math.max(1, layer.clientWidth);
    const y = (view.scrollTop + anchorY) / Math.max(1, layer.clientHeight);
    zoom = Math.min(4, Math.max(1, next));
    layer.style.width = `${zoom * 100}%`;
    element("zoom-in").disabled = layer.hidden || zoom === 4;
    element("zoom-out").disabled = element("reset").disabled = layer.hidden || zoom === 1;
    view.scrollTo(x * layer.clientWidth - anchorX, y * layer.clientHeight - anchorY);
  }

  async function load(keepKey) {
    const ticket = ++request;
    layer.hidden = true;
    add.disabled = true;
    setPlacement(false);
    changeZoom(1);
    armies = [];
    renderArmies();
    status.textContent = "Loading map and army positions…";
    try {
      const data = await window.BalanceCore.loadArmyMap(game, Number(continent.value), profile);
      if (request !== ticket) return;
      drawMap(data.image);
      armies = data.armies.sort((a, b) => a.record.title.localeCompare(b.record.title) || a.record.id.localeCompare(b.record.id));
      selected = armies.find(({ record }) => record.key === keepKey);
      if (selected) showGroup(groupFor(selected.record));
      layer.hidden = false;
      add.disabled = !data.canPlace;
      changeZoom(1);
      renderArmies();
      [...list.children].find((row) => row.dataset.key === keepKey)?.scrollIntoView({ block: "nearest" });
    } catch (error) {
      if (request === ticket) status.textContent = error.message;
    }
  }

  function openRoster(army) {
    const pick = onPick;
    dialog.close();
    pick(army.record.key);
  }

  continent.addEventListener("change", () => load());
  for (const button of groupButtons) button.addEventListener("click", () => {
    showGroup(button.dataset.group);
    renderArmies();
  });
  search.addEventListener("input", renderArmies);
  element("zoom-in").addEventListener("click", () => changeZoom(zoom * 1.5));
  element("zoom-out").addEventListener("click", () => changeZoom(zoom / 1.5));
  element("reset").addEventListener("click", () => {
    changeZoom(1);
    view.scrollTo(0, 0);
  });
  view.addEventListener("wheel", (event) => {
    if (layer.hidden || !event.deltaY || event.ctrlKey || event.metaKey) return;
    event.preventDefault();
    const rect = view.getBoundingClientRect();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? view.clientHeight : 1;
    changeZoom(zoom * Math.exp(-event.deltaY * unit / 480),
      event.clientX - rect.left - view.clientLeft, event.clientY - rect.top - view.clientTop);
  }, { passive: false });
  roster.addEventListener("click", () => { if (selected) openRoster(selected); });
  add.addEventListener("click", () => setPlacement(!placing));
  canvas.addEventListener("click", (event) => {
    if (!placing) return;
    const rect = canvas.getBoundingClientRect();
    const number = Number(continent.value);
    const point = window.BalanceCore.worldPoint(number,
      (event.clientX - rect.left) / rect.width, (event.clientY - rect.top) / rect.height);
    setPlacement(false);
    onPlace(number, point, () => dialog.close());
  });
  dialog.addEventListener("close", () => { request++; game = profile = onPick = onPlace = selected = null; armies = []; });

  let drag;
  view.addEventListener("pointerdown", (event) => {
    if (placing || (view.scrollWidth <= view.clientWidth && view.scrollHeight <= view.clientHeight) ||
      event.button !== 0 || event.pointerType !== "mouse" || event.target.closest("button")) return;
    drag = { x: event.clientX, y: event.clientY, left: view.scrollLeft, top: view.scrollTop };
    view.setPointerCapture(event.pointerId);
  });
  view.addEventListener("pointermove", (event) => {
    if (drag) view.scrollTo(drag.left + drag.x - event.clientX, drag.top + drag.y - event.clientY);
  });
  view.addEventListener("lostpointercapture", () => { drag = null; });

  return (loaded, activeProfile, record, pick, place) => {
    game = loaded;
    profile = activeProfile;
    onPick = pick;
    onPlace = place;
    element("edition").textContent = loaded.edition === "attt" ? "Original game" : "Valkyrie";
    continent.value = record?.group.at(-1) ?? "1";
    showGroup("hostile");
    search.value = "";
    dialog.showModal();
    load(record?.key);
  };
})();
