"use strict";

window.createModelEditor = ({ redraw, previewTexture, enterEditMode, paintState, drawPaint, activeClip, activeClips, exportRig, reload }) => {
  const models = window.BalanceModels;
  const rig = window.BalanceRig;
  const animation = window.BalanceAnimation;
  const element = (name) => document.getElementById("model-" + name);
  const editTab = element("edit-mode");
  const inspectTab = element("inspect-mode");
  const partSelect = element("edit-part");
  const transform = element("edit-transform");
  const fields = [...transform.querySelectorAll("input")];
  const resetPart = element("edit-reset-part");
  const texturePanel = element("edit-textures");
  const textureSelect = element("edit-texture");
  const downloadDds = element("edit-download-dds");
  const upload = element("edit-upload");
  const restore = element("edit-restore");
  const fileInput = element("edit-dds");
  const paintButton = element("paint-mode");
  const paintControls = element("paint-controls");
  const paintColor = element("paint-color");
  const paintSize = element("paint-size");
  const paintUndo = element("paint-undo");
  const paintDownload = element("paint-download");
  const rigTools = element("rig-tools");
  const rigTemplate = element("rig-template");
  const rigImport = element("rig-import");
  const rigReset = element("rig-reset");
  const rigFillWeights = element("rig-fill-weights");
  const rigFile = element("rig-file");
  const rigStatus = element("rig-status");
  const motionTools = element("motion-tools");
  const motionTemplate = element("motion-template");
  const motionImport = element("motion-import");
  const motionReset = element("motion-reset");
  const motionFile = element("motion-file");
  const motionStatus = element("motion-status");
  const status = element("edit-status");
  const exportButton = element("edit-download");
  const discard = element("edit-discard");
  const drafts = new WeakMap();
  let game, scene, save, selection;
  let textureRequest = 0, exporting = false;
  let paintSource, stroke;
  let rigRequest = 0, rigBusy = false;

  const draftKey = (loaded) => loaded.modelDraftKey ?? loaded;
  const draft = () => drafts.get(draftKey(game));
  const part = () => scene?.parts[Number(partSelect.value)];
  const validTransform = () => fields.every((input) => input.validity.valid);
  const transformFor = (entry) => entry?.attachment && draft().meshes.get(scene.family)?.edits.get(entry.attachment);
  const textureNames = (entry) => [...new Set(entry.materials.map(({ texture }) => texture)
    .filter((name) => /^[a-z0-9_.]{1,123}\.dds$/.test(name) && name.length <= 127))];

  function mode(edit) {
    if (!edit) stopPainting();
    element("inspect-controls").hidden = edit;
    element("edit-controls").hidden = !edit;
    element("inspection-heading").textContent = edit ? "Model editor" : "Mesh inspection";
    editTab.setAttribute("aria-pressed", String(edit));
    inspectTab.setAttribute("aria-pressed", String(!edit));
    if (edit) enterEditMode();
  }

  function updateStatus(message = "") {
    const current = draft();
    const attachments = current ? [...current.meshes.values()].reduce((count, family) => count + family.edits.size, 0) : 0;
    const textures = current?.textures.size ?? 0;
    const overrides = current?.overrides;
    const motions = overrides ? [...overrides.keys()].filter((name) => name.endsWith(".ska")).length : 0;
    const meshes = (overrides?.size ?? 0) - motions;
    const changed = attachments + textures + meshes + motions > 0;
    const invalid = !transform.disabled && !validTransform();
    exportButton.disabled = !scene || !changed || exporting || invalid || game.slot > 255;
    discard.disabled = !scene || !changed;
    const replacement = current?.textures.get(textureSelect.value);
    status.textContent = message || (invalid ? "Complete the transform fields to preview and export." : [
      replacement?.painted ? `${textureSelect.value} has brush edits.` : replacement && `Replacement: ${replacement.fileName}.`,
      changed ? `${attachments} attachment ${attachments === 1 ? "edit" : "edits"} · ${textures} texture ${textures === 1 ? "swap" : "swaps"}. ${game.slot <= 255 ?
        `${meshes ? `${meshes} replacement ${meshes === 1 ? "mesh" : "meshes"}. ` : ""}${motions ? `${motions} replacement ${motions === 1 ? "clip" : "clips"}. ` : ""}Export slot: Resource${game.slot}.pak.` : "No free archive slot."}` :
        "Preview changes here and export a separate PAK.",
    ].filter(Boolean).join(" "));
  }

  function syncTexture() {
    const name = textureSelect.value;
    const current = draft();
    upload.disabled = !scene || !textureSelect.value;
    downloadDds.disabled = upload.disabled || !game.hasAsset(name);
    const replacement = current?.textures.get(name);
    restore.disabled = upload.disabled || !replacement;
    paintButton.disabled = downloadDds.disabled && !replacement;
    paintUndo.disabled = !current?.undo.has(name);
    paintDownload.hidden = !replacement?.painted;
    updateStatus();
  }

  function syncPart() {
    stopPainting();
    const entry = part();
    if (entry) selection = { family: scene.family, name: entry.name, track: entry.trackIndex };
    transform.disabled = !entry?.attachment;
    const edit = transformFor(entry);
    const values = edit ? [...edit.move, ...edit.rotate, edit.scale * 100] : [0, 0, 0, 0, 0, 0, 100];
    for (const [i, input] of fields.entries()) input.value = values[i];
    resetPart.disabled = !edit;
    const names = entry ? textureNames(entry) : [];
    texturePanel.hidden = !names.length;
    textureSelect.replaceChildren(...names.map((name) => new Option(name, name)));
    syncTexture();
  }

  function setScene(next) {
    rigRequest++;
    rigBusy = false;
    rigStatus.textContent = "";
    motionStatus.textContent = "";
    scene = next;
    const candidates = (scene?.parts ?? []).map((entry, i) => ({ entry, i }))
      .filter(({ entry }) => entry.attachment || textureNames(entry).length);
    editTab.disabled = !candidates.length;
    partSelect.disabled = !candidates.length;
    partSelect.replaceChildren(...candidates.map(({ entry, i }) => new Option(
      `${i + 1}. ${entry.name || "Unnamed part"}${entry.attachment ? "" : " (texture only)"}`, i)));
    if (!candidates.length) partSelect.add(new Option(scene ? "No editable parts" : "Reading mesh…", "-1"));
    const preferred = candidates.find(({ entry }) =>
      selection?.family === scene?.family && selection.name === entry.name && selection.track === entry.trackIndex);
    const initial = preferred ?? candidates.find(({ entry }) => entry.attachment);
    if (initial) partSelect.value = initial.i;
    syncPart();
    syncRig();
    if (scene && draft().overrides.has(activeClip().motion)) motionStatus.textContent = "Previewing the edited clip.";
  }

  function syncRig() {
    rigTemplate.disabled = rigImport.disabled = !scene || rigBusy;
    rigReset.disabled = !scene || rigBusy || !scene.meshFiles.some((name) => draft().overrides.has(name));
    motionTemplate.disabled = motionImport.disabled = !scene || rigBusy || scene.frameCount < 2;
    motionReset.disabled = !scene || rigBusy || !draft().overrides.has(activeClip().motion);
  }

  async function rigOperation(run, forExport = false, feedback = rigStatus) {
    const ticket = ++rigRequest;
    const loaded = game;
    const clip = activeClip(), lod = scene.lod;
    rigBusy = true;
    syncRig();
    feedback.textContent = "Reading the original rig…";
    try {
      const reference = await rig.template(loaded, clip, lod, forExport ? activeClips() : undefined);
      if (ticket !== rigRequest) return;
      await run(loaded, reference, () => ticket === rigRequest);
    } catch (error) {
      if (ticket === rigRequest) feedback.textContent = error.message;
    } finally {
      if (ticket === rigRequest) {
        rigBusy = false;
        syncRig();
      }
    }
  }

  rigTemplate.addEventListener("click", () => rigOperation(async (loaded, reference, current) => {
    const bytes = await exportRig(loaded, reference);
    if (!current()) return;
    const name = `${reference.scene.mesh.replace(/\.skm$/, "")}-${reference.motion.replace(/\.ska$/, "")}-rig.glb`;
    save(name, new Blob([bytes], { type: "model/gltf-binary" }));
    rigStatus.textContent = `Exported ${name}. Reopen this clip and detail level for import.`;
  }, true));
  rigImport.addEventListener("click", () => {
    rigFile.value = "";
    rigFile.click();
  });
  rigFile.addEventListener("change", () => {
    const file = rigFile.files[0];
    if (!scene || !file) return;
    if (file.size > 96 * 1024 * 1024) {
      rigStatus.textContent = "Choose a GLB file of up to 96 MiB.";
      return;
    }
    const fillWeights = rigFillWeights.checked;
    rigOperation(async (loaded, reference, current) => {
      const result = await rig.importUnit(loaded, reference, new Uint8Array(await file.arrayBuffer()), { fillWeights });
      if (!current()) return;
      await models.loadModel(loaded, activeClip(), reference.scene.lod, result.assets);
      if (!current()) return;
      const { overrides } = draft();
      for (const name of reference.scene.meshFiles) overrides.delete(name);
      for (const [name, bytes] of result.assets) overrides.set(name, bytes);
      const pending = reload();
      const reloadTicket = rigRequest;
      await pending;
      if (game === loaded && scene && rigRequest === reloadTicket + 1) {
        const parts = result.count === 1 ? "part" : "parts";
        const skipped = result.skipped.length ? ` Unmatched meshes: ${result.skipped.join(", ")}.` : "";
        const filled = result.filled ? ` Filled weights on ${result.filled.toLocaleString()} vertices.` : "";
        rigStatus.textContent = `Imported ${result.count} ${parts} into ${result.assets.size} mesh files.${filled}${skipped}`;
      }
    });
  });
  rigReset.addEventListener("click", () => {
    for (const name of scene.meshFiles) draft().overrides.delete(name);
    reload();
  });

  motionTemplate.addEventListener("click", () => rigOperation(async (loaded, reference, current) => {
    const clip = animation.exportClip(reference, draft().overrides.get(reference.motion));
    const bytes = await exportRig(loaded, reference, clip);
    if (!current()) return;
    const name = `${reference.scene.mesh.replace(/\.skm$/, "")}-${clip.name}-clip.glb`;
    save(name, new Blob([bytes], { type: "model/gltf-binary" }));
    motionStatus.textContent = `Exported ${clip.times.length} frames at 30 FPS.`;
  }, true, motionStatus));
  motionImport.addEventListener("click", () => {
    motionFile.value = "";
    motionFile.click();
  });
  motionFile.addEventListener("change", () => {
    const file = motionFile.files[0];
    if (!scene || !file) return;
    if (file.size > 96 * 1024 * 1024) {
      motionStatus.textContent = "Choose a GLB file of up to 96 MiB.";
      return;
    }
    rigOperation(async (loaded, reference, current) => {
      const input = new Uint8Array(await file.arrayBuffer());
      if (!current()) return;
      const bytes = animation.importClip(reference, input);
      const { overrides } = draft();
      await models.loadModel(loaded, activeClip(), reference.scene.lod, new Map([...overrides, [reference.motion, bytes]]));
      if (!current()) return;
      overrides.set(reference.motion, bytes);
      const pending = reload();
      const reloadTicket = rigRequest;
      await pending;
      if (game === loaded && scene && rigRequest === reloadTicket + 1) {
        motionStatus.textContent = `Imported ${reference.scene.frameCount} frames. Preview the edited clip or export the model PAK.`;
      }
    }, false, motionStatus);
  });
  motionReset.addEventListener("click", () => {
    draft().overrides.delete(activeClip().motion);
    reload();
  });

  function applyEdit(edit) {
    const { attachment } = part();
    const { meshes } = draft();
    let family = meshes.get(scene.family);
    if (edit) {
      if (!family) meshes.set(scene.family, family = { files: new Set(), edits: new Map() });
      for (const file of scene.meshFiles) family.files.add(file);
      family.edits.set(attachment, edit);
    } else if (family) {
      family.edits.delete(attachment);
      if (!family.edits.size) meshes.delete(scene.family);
    }
    scene.setTransform(attachment, edit);
    redraw();
    resetPart.disabled = !edit;
    updateStatus();
  }

  function stopPainting() {
    textureRequest++;
    endStroke();
    paintSource = undefined;
    transform.hidden = rigTools.hidden = motionTools.hidden = false;
    paintButton.textContent = "Paint texture";
    paintButton.setAttribute("aria-pressed", "false");
    paintControls.hidden = true;
    paintState(false);
  }

  function beginStroke() {
    const name = textureSelect.value;
    const hex = paintColor.value;
    const color = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16));
    const radius = Math.max(1, Math.min(64, (paintSize.valueAsNumber || 16) / 2));
    stroke = { name, color, radius, original: paintSource };
  }

  function paintStroke(hits) {
    if (!stroke) return;
    const { name, color, radius, original } = stroke;
    const { width, height } = original;
    let left = width, top = height, right = 0, bottom = 0;
    function stamp(x, y) {
      const x0 = Math.max(0, Math.floor(x - radius)), x1 = Math.min(width, Math.ceil(x + radius));
      const y0 = Math.max(0, Math.floor(y - radius)), y1 = Math.min(height, Math.ceil(y + radius));
      stroke.image ??= { width, height, pixels: original.pixels.slice() };
      const { pixels } = stroke.image;
      for (let row = y0; row < y1; row++) {
        for (let col = x0; col < x1; col++) {
          const d = Math.hypot(col + 0.5 - x, row + 0.5 - y);
          if (d >= radius) continue;
          const at = (row * width + col) * 4;
          if (!pixels[at + 3]) continue;
          const blend = Math.min(1, radius - d);
          for (let channel = 0; channel < 3; channel++) {
            pixels[at + channel] = Math.round(pixels[at + channel] * (1 - blend) + color[channel] * blend);
          }
        }
      }
      left = Math.min(left, x0);
      top = Math.min(top, y0);
      right = Math.max(right, x1);
      bottom = Math.max(bottom, y1);
    }
    for (const hit of hits) {
      if (hit?.name !== name) {
        stroke.last = undefined;
        continue;
      }
      const x = (hit.u - Math.floor(hit.u)) * width;
      const y = (hit.v - Math.floor(hit.v)) * height;
      const previous = stroke.last;
      if (previous) {
        const distance = Math.hypot(x - previous.x, y - previous.y);
        // Short gaps can cross triangle edges. Long UV jumps may cross atlas seams.
        if (distance <= Math.max(8, radius * 4)) {
          const steps = Math.ceil(distance / Math.max(1, radius / 2));
          for (let i = 1; i < steps; i++) stamp(previous.x + (x - previous.x) * i / steps,
            previous.y + (y - previous.y) * i / steps);
        }
      }
      stamp(x, y);
      stroke.last = { x, y };
    }
    if (right <= left || bottom <= top) return;
    if (!stroke.staged) {
      const current = draft();
      current.undo.set(name, { image: original, entry: current.textures.get(name) });
      current.textures.set(name, { image: stroke.image, painted: true });
      stroke.staged = true;
    }
    drawPaint(name, stroke.image, { left, top, right, bottom });
  }

  function endStroke() {
    if (stroke?.staged) {
      paintSource = stroke.image;
      drawPaint(stroke.name, stroke.image);
      syncTexture();
    }
    stroke = undefined;
  }

  async function readTexture(loaded, name) {
    const replacement = drafts.get(draftKey(loaded))?.textures.get(name);
    if (replacement) return replacement.image;
    try {
      const bytes = await loaded.readAsset(name);
      return bytes ? models.readTexture(bytes) : null;
    } catch {
      return null;
    }
  }

  paintButton.addEventListener("click", async () => {
    const ticket = ++textureRequest;
    if (paintSource) {
      stopPainting();
      return;
    }
    const image = await readTexture(game, textureSelect.value);
    if (ticket !== textureRequest) return;
    if (!models.canPaintTexture(image)) {
      updateStatus("Painting needs a readable power-of-two texture up to 2048 pixels per side.");
      return;
    }
    paintSource = image;
    previewTexture(textureSelect.value, image);
    transform.hidden = rigTools.hidden = motionTools.hidden = true;
    paintButton.textContent = "Done painting";
    paintButton.setAttribute("aria-pressed", "true");
    paintControls.hidden = false;
    paintState(true);
  });
  paintUndo.addEventListener("click", () => {
    endStroke();
    const name = textureSelect.value;
    const current = draft();
    const previous = current.undo.get(name);
    if (!previous) return;
    current.undo.delete(name);
    if (previous.entry) current.textures.set(name, previous.entry);
    else current.textures.delete(name);
    if (paintSource) paintSource = previous.image;
    previewTexture(name, previous.image);
    syncTexture();
  });
  paintDownload.addEventListener("click", () => {
    const name = textureSelect.value;
    const replacement = draft().textures.get(name);
    if (!replacement?.painted) return;
    try {
      const filename = name.replace(/\.dds$/, "-painted.dds");
      const bytes = models.writePaintedTexture(replacement.image);
      save(filename, new Blob([bytes], { type: "application/octet-stream" }));
      updateStatus(`Downloaded ${filename}.`);
    } catch (error) {
      updateStatus(error.message);
    }
  });

  inspectTab.addEventListener("click", () => mode(false));
  editTab.addEventListener("click", () => mode(true));
  partSelect.addEventListener("change", syncPart);
  textureSelect.addEventListener("change", () => {
    stopPainting();
    syncTexture();
  });
  transform.addEventListener("input", () => {
    if (!part()?.attachment) return;
    if (!validTransform()) {
      updateStatus();
      return;
    }
    const [x, y, z, rx, ry, rz, percent] = fields.map((input) => input.valueAsNumber);
    applyEdit(x || y || z || rx || ry || rz || percent !== 100 ?
      { move: [x, y, z], rotate: [rx, ry, rz], scale: percent / 100 } : undefined);
  });
  resetPart.addEventListener("click", () => {
    applyEdit(undefined);
    syncPart();
  });
  downloadDds.addEventListener("click", async () => {
    const loaded = game, activeScene = scene, name = textureSelect.value, download = save;
    let message;
    try {
      const bytes = await loaded.readAsset(name);
      if (!bytes) throw new Error(`${name} is missing from the loaded archives.`);
      download(name, new Blob([bytes], { type: "application/octet-stream" }));
      message = `Downloaded ${name} from the loaded archives.`;
    } catch (error) {
      message = error.message;
    }
    if (game === loaded && scene === activeScene && textureSelect.value === name) updateStatus(message);
  });
  upload.addEventListener("click", () => {
    fileInput.value = "";
    fileInput.click();
  });
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0], name = textureSelect.value;
    if (!file || !name || !scene) return;
    const ticket = ++textureRequest;
    try {
      if (file.size > 32 * 1024 * 1024) throw new Error("Choose a DDS file of up to 32 MiB.");
      const bytes = new Uint8Array(await file.arrayBuffer());
      if (ticket !== textureRequest) return;
      const image = models.readReplacementTexture(bytes);
      stopPainting();
      draft().undo.delete(name);
      draft().textures.set(name, { bytes, image, fileName: file.name });
      previewTexture(name);
      syncTexture();
    } catch (error) {
      if (ticket === textureRequest) updateStatus(error.message);
    }
  });
  restore.addEventListener("click", () => {
    stopPainting();
    const name = textureSelect.value;
    draft().textures.delete(name);
    draft().undo.delete(name);
    previewTexture(name);
    syncTexture();
  });
  discard.addEventListener("click", () => {
    if (!confirm("Discard all model edits for these archives?")) return;
    stopPainting();
    const current = draft();
    const textures = [...current.textures.keys()];
    current.meshes.clear();
    const hadOverrides = current.overrides.size > 0;
    current.overrides.clear();
    current.textures.clear();
    current.undo.clear();
    for (const entry of scene.parts) if (entry.attachment) scene.setTransform(entry.attachment);
    for (const name of textures) previewTexture(name);
    if (hadOverrides) reload();
    else {
      redraw();
      syncPart();
    }
  });
  exportButton.addEventListener("click", async () => {
    const target = game, download = save;
    const { meshes, textures, overrides } = draft();
    exporting = true;
    updateStatus("Preparing model PAK…");
    let message;
    try {
      const result = await models.exportModelEdits(target, meshes, textures, overrides);
      download(result.name, new Blob([result.bytes], { type: "application/octet-stream" }));
      message = `Exported ${result.name} with ${result.resources.length} assets. Install it after the loaded archives.`;
    } catch (error) {
      message = error.message;
    } finally {
      exporting = false;
      updateStatus(game === target ? message : "");
    }
  });

  return {
    open(loaded, download) {
      game = loaded;
      save = download;
      selection = undefined;
      const key = draftKey(game);
      if (!drafts.has(key)) drafts.set(key, { meshes: new Map(), textures: new Map(), undo: new Map(), overrides: new Map() });
      mode(false);
    },
    close() {
      setScene(undefined);
      game = save = undefined;
    },
    setScene,
    overrides: (loaded) => drafts.get(draftKey(loaded))?.overrides,
    painting: () => Boolean(paintSource),
    beginStroke,
    paintStroke,
    endStroke,
    apply(loaded, pose) {
      const family = drafts.get(draftKey(loaded))?.meshes.get(pose.family);
      if (family) for (const [key, edit] of family.edits) pose.setTransform(key, edit);
    },
    readTexture,
  };
};
