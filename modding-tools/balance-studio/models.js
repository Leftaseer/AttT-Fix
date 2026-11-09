/* Readers and pose evaluation for AttT's unit meshes, animation tracks and textures. */
(function (root) {
  "use strict";

  const core = typeof module === "undefined" ? root.BalanceCore : require("./core.js");
  const cp1251 = new TextDecoder("windows-1251");

  function check(ok, message) {
    if (!ok) throw new Error(message);
  }

  class Reader {
    constructor(bytes) {
      this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      this.offset = 0;
    }

    take(size) {
      const offset = this.offset;
      this.offset += size;
      check(this.offset <= this.view.byteLength, "The model asset ends unexpectedly.");
      return offset;
    }

    u32() { return this.view.getUint32(this.take(4), true); }
    u16() { return this.view.getUint16(this.take(2), true); }
    f32() { return this.view.getFloat32(this.take(4), true); }

    count(max) {
      const count = this.u32();
      check(count <= max, "The model asset contains an oversized table.");
      return count;
    }

    string() {
      const size = this.count(4096);
      return cp1251.decode(new Uint8Array(this.view.buffer, this.view.byteOffset + this.take(size), size));
    }

    floats(length) {
      const start = this.take(length * 4);
      return Float32Array.from({ length }, (_, i) => this.view.getFloat32(start + i * 4, true));
    }

    indices() {
      const length = this.count(1_000_000);
      const start = this.take(length * 2);
      return Uint16Array.from({ length }, (_, i) => this.view.getUint16(start + i * 2, true));
    }
  }

  function readMaterials(r, indexCount) {
    let previous = -1;
    return Array.from({ length: r.count(256) }, () => {
      const recordStart = r.offset;
      r.take(0x44); // D3D material parameters. The preview uses its own lighting.
      const texture = r.string().replace(/\0+$/, "").toLowerCase();
      const rangeOffset = r.offset;
      const start = r.u16();
      check(start >= previous && start <= indexCount && start % 3 === 0, "The model has an invalid material range.");
      previous = start;
      return { texture, start, recordStart, rangeOffset };
    });
  }

  function readSkin(r) {
    const start = r.offset;
    const name = r.string();
    const nameEnd = r.offset;
    const indices = r.indices();
    const positions = r.floats(r.count(65535) * 3);
    const normals = r.floats(r.count(65535) * 3);
    const vertexCount = r.count(65535);
    const uv = r.floats(vertexCount * 2);
    check(normals.length === positions.length, "The model has mismatched positions and normals.");
    const boneCount = r.count(4096);
    const bones = new Uint16Array(positions.length / 3);
    for (let bone = 0; bone < boneCount; bone++) {
      const begin = r.u32();
      const end = r.u32();
      check(begin <= end && end <= bones.length, "The model has an invalid bone range.");
      bones.fill(bone, begin, end);
    }
    const copies = new Uint16Array(vertexCount * 4);
    const weights = new Float32Array(vertexCount * 4);
    let vertex = 0;
    for (let count = 1; count <= 4; count++) {
      const vertices = r.count(vertexCount);
      check(vertex + vertices <= vertexCount, "The model has too many skin weights.");
      for (let i = 0; i < vertices; i++, vertex++) {
        const offset = vertex * 4;
        for (let j = 0; j < count; j++) {
          const copy = r.u16();
          check(copy < bones.length, "The model has an invalid skin weight index.");
          copies[offset + j] = copy;
        }
        if (count === 3) r.take(2); // Alignment before the weights.
        for (let j = 0; j < count; j++) weights[offset + j] = count === 1 ? 1 : r.f32();
      }
    }
    check(vertex === vertexCount && !indices.some((i) => i >= vertexCount), "The model has invalid skinned geometry.");
    const materials = readMaterials(r, indices.length);
    const trackIndex = r.u32();
    return { name, indices, positions, normals, uv, bones, boneCount, copies, weights, materials, trackIndex,
      start, nameEnd, end: r.offset };
  }

  function readRigid(r) {
    const start = r.offset;
    const name = r.string();
    const nameEnd = r.offset;
    const count = r.count(65535);
    const vertexOffset = r.offset;
    const vertices = r.floats(count * 8);
    const indices = r.indices();
    check(!indices.some((i) => i >= vertices.length / 8), "The model has invalid rigid geometry.");
    const materials = readMaterials(r, indices.length);
    const trackIndex = r.u32();
    return { name, vertices, vertexOffset, indices, materials, trackIndex, start, nameEnd, end: r.offset };
  }

  function readModel(bytes) {
    const r = new Reader(bytes);
    const parts = Array.from({ length: r.count(128) }, () => readSkin(r));
    parts.push(...Array.from({ length: r.count(128) }, () => readRigid(r)));
    r.take(0x60); // Collision bounds.
    check(parts.some((part) => part.indices.length >= 3), "The model has no drawable geometry.");
    const attachments = new Map();
    for (const part of parts) {
      if (!part.vertices) continue;
      const key = JSON.stringify([part.name, part.trackIndex]);
      if (attachments.has(key)) {
        const previous = attachments.get(key);
        if (previous) delete previous.attachment;
        attachments.set(key, null);
      } else {
        part.attachment = key;
        attachments.set(key, part);
      }
    }
    return parts;
  }

  function readMotion(bytes) {
    const r = new Reader(bytes);
    const count = r.count(256);
    r.take(1); // Animation flags.
    const tracks = Array.from({ length: count }, () => {
      const bones = r.count(4096);
      const frames = r.count(30000);
      const keyOffset = r.offset;
      return { bones, frames, keyOffset, keys: r.floats(bones * frames * 6) };
    });
    check(r.offset === bytes.length, "The animation has an unsupported layout.");
    return tracks;
  }

  function rotation(keys, at) {
    const cp = Math.cos(keys[at]), sp = Math.sin(keys[at]);
    const cy = Math.cos(keys[at + 1]), sy = Math.sin(keys[at + 1]);
    const cr = Math.cos(keys[at + 2]), sr = Math.sin(keys[at + 2]);
    // D3DX yaw-pitch-roll for row vectors, followed by translation.
    return [
      cr * cy + sr * sp * sy, sr * cp, -cr * sy + sr * sp * cy,
      -sr * cy + cr * sp * sy, cr * cp, sr * sy + cr * sp * cy,
      cp * sy, -sp, cp * cy, keys[at + 3], keys[at + 4], keys[at + 5],
    ];
  }

  function transform(source, at, matrix, translation, out, target) {
    const x = source[at], y = source[at + 1], z = source[at + 2];
    for (let i = 0; i < 3; i++) {
      out[target + i] = x * matrix[i] + y * matrix[i + 3] + z * matrix[i + 6] + (translation ? matrix[i + 9] : 0);
    }
  }

  function transformAttachment(vertices, { move, rotate, scale }) {
    check(move.length === 3 && move.every((value) => Number.isFinite(value) && Math.abs(value) <= 1000) &&
      rotate.length === 3 && rotate.every((value) => Number.isFinite(value) && Math.abs(value) <= 360) &&
      Number.isFinite(scale) && scale >= 0.01 && scale <= 10, "Enter a valid attachment transform.");
    const matrix = rotation([...rotate.map((value) => value * Math.PI / 180), ...move], 0);
    const output = vertices.slice();
    for (let at = 0; at < output.length; at += 8) {
      for (let i = 0; i < 3; i++) output[at + i] *= scale;
      transform(output, at, matrix, true, output, at);
      transform(vertices, at + 3, matrix, false, output, at + 3);
    }
    return output;
  }

  async function exportModelEdits(game, meshes, textures, overrides = new Map()) {
    check(game.slot <= 255, "There is no free Resource archive slot.");
    const targets = new Map();
    for (const { files, edits } of meshes.values()) {
      for (const name of files) {
        if (!targets.has(name)) targets.set(name, new Map());
        const target = targets.get(name);
        for (const [attachment, edit] of edits) {
          check(!target.has(attachment) || JSON.stringify(target.get(attachment)) === JSON.stringify(edit),
            `Conflicting transforms for ${name}. Reset one of the overlapping edits.`);
          target.set(attachment, edit);
        }
      }
    }
    const entries = new Map(overrides);
    for (const [name, { bytes, image }] of textures) entries.set(name, bytes ?? writePaintedTexture(image));
    for (const [name, edits] of targets) {
      const bytes = entries.get(name) ?? await game.readAsset(name);
      check(bytes, `Model ${name} is missing from the selected archives.`);
      let output, view;
      for (const part of readModel(bytes)) {
        if (!edits.has(part.attachment)) continue;
        if (!output) {
          output = bytes.slice();
          view = new DataView(output.buffer, output.byteOffset, output.byteLength);
        }
        const vertices = transformAttachment(part.vertices, edits.get(part.attachment));
        for (let at = 0; at < vertices.length; at += 8) {
          for (let i = at; i < at + 6; i++) view.setFloat32(part.vertexOffset + i * 4, vertices[i], true);
        }
      }
      if (output) entries.set(name, output);
    }
    check(entries.size, "There are no model edits to export.");
    return { name: `Resource${game.slot}.pak`, bytes: core.makeArchive(entries), resources: [...entries.keys()] };
  }

  function boneLinks(part, boneIds) {
    const { weights, bones, copies } = part;
    const count = boneIds.length;
    const markerIndex = new Map(boneIds.map((bone, index) => [bone, index]));
    const shared = new Map();
    for (let vertex = 0; vertex < weights.length; vertex += 4) {
      for (let i = vertex; i < vertex + 4; i++) {
        const a = markerIndex.get(bones[copies[i]]);
        if (weights[i] <= 0 || a === undefined) continue;
        for (let j = i + 1; j < vertex + 4; j++) {
          const b = markerIndex.get(bones[copies[j]]);
          if (weights[j] <= 0 || b === undefined || a === b) continue;
          const pair = Math.min(a, b) * count + Math.max(a, b);
          shared.set(pair, (shared.get(pair) ?? 0) + Math.min(weights[i], weights[j]));
        }
      }
    }

    // Keep the strongest shared influences while avoiding cycles. Disjoint
    // regions stay separate because the asset supplies no parent bone IDs.
    const components = Array.from(boneIds.keys());
    function rootOf(index) {
      while (components[index] !== index) {
        components[index] = components[components[index]];
        index = components[index];
      }
      return index;
    }
    const links = [];
    for (const [pair] of [...shared].sort(([a, first], [b, second]) => second - first || a - b)) {
      const a = Math.floor(pair / count), b = pair % count;
      const rootA = rootOf(a), rootB = rootOf(b);
      if (rootA === rootB) continue;
      components[rootA] = rootB;
      links.push(a, b);
    }
    return Uint16Array.from(links);
  }

  function skinInspection(part) {
    const centers = new Float32Array(part.boneCount * 3);
    const totals = new Float32Array(part.boneCount);
    for (const [i, weight] of part.weights.entries()) {
      if (!weight) continue;
      const copy = part.copies[i];
      const bone = part.bones[copy];
      totals[bone] += weight;
      for (let axis = 0; axis < 3; axis++) centers[bone * 3 + axis] += part.positions[copy * 3 + axis] * weight;
    }
    const boneIds = Array.from(totals.keys()).filter((bone) => totals[bone] > 0);
    for (const bone of boneIds) {
      for (let axis = 0; axis < 3; axis++) centers[bone * 3 + axis] /= totals[bone];
    }
    function influence(bone) {
      const values = new Float32Array(part.uv.length / 2);
      for (const [i, weight] of part.weights.entries()) {
        if (weight && part.bones[part.copies[i]] === bone) values[Math.floor(i / 4)] += weight;
      }
      return values;
    }
    return { centers, boneIds, influence, markers: new Float32Array(boneIds.length * 3),
      links: () => boneLinks(part, boneIds) };
  }

  function posePart(part, track, frame, output, skin) {
    const first = (frame < track.frames ? frame : 0) * track.bones * 6;
    if (part.vertices) {
      // CMatrixMeshSubObject multiplies the rigid pose by diag(-1, -1, -1, 1).
      const matrix = rotation(track.keys, first).map((value) => -value);
      const vertices = part.editedVertices ?? part.vertices;
      for (let at = 0; at < output.length; at += 8) {
        transform(vertices, at, matrix, true, output, at);
        transform(vertices, at + 3, matrix, false, output, at + 3);
        output[at + 6] = part.vertices[at + 6];
        output[at + 7] = part.vertices[at + 7];
      }
      return;
    }
    const matrices = Array.from({ length: part.boneCount }, (_, bone) => rotation(track.keys, first + bone * 6));
    for (const [i, bone] of skin.boneIds.entries()) {
      transform(skin.centers, bone * 3, matrices[bone], true, skin.markers, i * 3);
    }
    const { posedPositions, posedNormals } = part;
    for (let i = 0; i < part.bones.length; i++) {
      const at = i * 3;
      const matrix = matrices[part.bones[i]];
      transform(part.positions, at, matrix, true, posedPositions, at);
      transform(part.normals, at, matrix, false, posedNormals, at);
    }
    for (let vertex = 0; vertex < part.uv.length / 2; vertex++) {
      const at = vertex * 8;
      const weights = vertex * 4;
      output.fill(0, at, at + 6);
      for (let i = weights; i < weights + 4; i++) {
        if (!part.weights[i]) continue;
        const copy = part.copies[i] * 3;
        for (let axis = 0; axis < 3; axis++) {
          output[at + axis] += posedPositions[copy + axis] * part.weights[i];
          output[at + 3 + axis] += posedNormals[copy + axis] * part.weights[i];
        }
      }
      output[at + 6] = part.uv[vertex * 2];
      output[at + 7] = part.uv[vertex * 2 + 1];
    }
  }

  function makePose(parts, tracks, projectile) {
    const drawable = parts.flatMap((part, slot) => {
      if (!part.indices.length) return [];
      const track = tracks[part.trackIndex];
      check(track?.frames > 0 && track.bones >= (part.boneCount || 1),
        `This clip has incompatible tracks for mesh part ${part.name}.`);
      if (!part.vertices) {
        part.posedPositions = new Float32Array(part.positions.length);
        part.posedNormals = new Float32Array(part.normals.length);
      }
      const vertices = new Float32Array(part.vertices?.length ?? part.uv.length * 4);
      const skin = part.vertices ? undefined : skinInspection(part);
      return [{ part, slot, track, vertices, skin }];
    });
    const frameCount = Math.max(...drawable.map(({ track }) => track.frames));
    return {
      parts: drawable.map(({ part, slot, track, vertices, skin }) => ({
        name: part.name, slot, indices: part.indices, materials: part.materials, vertices, projectile: part === projectile,
        attachment: part.attachment,
        trackIndex: part.trackIndex, trackFrames: track.frames, trackBoneCount: track.bones,
        boneCount: part.boneCount, boneIds: skin?.boneIds, markers: skin?.markers, influence: skin?.influence, links: skin?.links,
      })),
      frameCount,
      setTransform(attachment, edit) {
        const match = drawable.find(({ part }) => part.attachment === attachment);
        if (match) match.part.editedVertices = edit ? transformAttachment(match.part.vertices, edit) : undefined;
      },
      setFrame(frame) {
        for (const { part, track, vertices, skin } of drawable) posePart(part, track, frame, vertices, skin);
      },
    };
  }

  async function loadModel(game, clip, lod = 0, overrides) {
    const readAsset = (name) => overrides?.get(name) ?? game.readAsset(name);
    let model = clip.model.replace(/\.lskm$/, ".skm");
    let descriptor;
    if (clip.model.endsWith(".lskm")) {
      const source = await game.readAsset(clip.model);
      check(source, `Model descriptor ${clip.model} is missing.`);
      descriptor = core.readSource(source, clip.model).get("LSKM");
      const base = descriptor?.get(1);
      check(typeof base === "string", `Model descriptor ${clip.model} has an unsupported layout.`);
      if (base) model = base.toLowerCase().replace(/(?:\.skm)?$/, ".skm");
    }
    const meshName = (level) => model.replace(/\.skm$/, `${level}.skm`);
    const lods = [0, ...[1, 2, 3, 4].filter((level) => game.hasAsset?.(meshName(level)))];
    check(lods.includes(lod), `Mesh detail LOD ${lod} is unavailable for ${model}.`);
    let mesh = (lod !== 0 || clip.numbered) ? meshName(lod) : model;
    let [bytes, motion] = await Promise.all([readAsset(mesh), readAsset(clip.motion)]);
    if (!bytes && lod === 0) {
      mesh = clip.numbered ? model : meshName(0);
      bytes = await readAsset(mesh);
    }
    check(bytes, `Model ${model} is missing from the selected archives.`);
    check(motion, `Animation ${clip.motion} is missing from the selected archives.`);
    const parts = readModel(bytes);
    if (descriptor) {
      for (let index = 2; index <= descriptor.size; index += 2) {
        const name = descriptor.get(index);
        const group = descriptor.get(index + 1);
        const slots = group instanceof Map && group.get(2);
        if (typeof name !== "string" || !name || !(slots instanceof Map)) continue;
        const texture = (name.includes(".") ? name : `${name}.dds`).toLowerCase();
        const ids = new Set(slots.values());
        for (const [i, part] of parts.entries()) {
          if (ids.has(0) || ids.has(i + 1)) {
            part.materials = part.materials.length ? part.materials.map(({ start }) => ({ texture, start })) :
              [{ texture, start: 0 }];
          }
        }
      }
    }
    const pose = makePose(parts, readMotion(motion), parts[clip.projectilePart]);
    pose.setFrame(0);
    const meshFiles = [mesh, model, ...lods.map(meshName)];
    return { ...pose, mesh, family: model, meshFiles: [...new Set(meshFiles.filter((name) =>
      name === mesh || game.hasAsset?.(name)))], lod, lods, descriptor: descriptor ? clip.model : undefined };
  }

  function readTexture(bytes) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    check(bytes.length >= 128 && view.getUint32(0, false) === 0x44445320 && view.getUint32(4, true) === 124,
      "This texture is not a supported DDS image.");
    const width = view.getUint32(16, true);
    const height = view.getUint32(12, true);
    const pixels = texturePixels(width, height);
    const fourCC = String.fromCharCode(...bytes.subarray(84, 88));
    if (["DXT1", "DXT3", "DXT5"].includes(fourCC)) {
      readBlocks(view, width, height, pixels, fourCC);
    } else {
      const bpp = view.getUint32(88, true) / 8;
      const flags = view.getUint32(80, true);
      const pitch = view.getUint32(8, true) & 8 ? view.getUint32(20, true) : width * bpp;
      check((flags & 0x40) && (bpp === 3 || bpp === 4) && pitch >= width * bpp &&
        bytes.length >= 128 + pitch * height, "This DDS pixel format is unsupported.");
      const masks = [92, 96, 100, 104].map((at) => {
        const mask = view.getUint32(at, true);
        const shift = mask ? 31 - Math.clz32(mask & -mask) : 0;
        return { mask, shift, max: mask >>> shift };
      });
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const at = 128 + y * pitch + x * bpp;
          const word = bpp === 4 ? view.getUint32(at, true) : view.getUint16(at, true) | (bytes[at + 2] << 16);
          for (const [i, { mask, shift, max }] of masks.entries()) {
            pixels[(y * width + x) * 4 + i] = mask ? ((word & mask) >>> shift) * 255 / max : 255;
          }
        }
      }
    }
    return { width, height, pixels };
  }

  function readReplacementTexture(bytes) {
    check(bytes.length >= 128 && bytes.length <= 32 * 1024 * 1024, "Choose a DDS file of up to 32 MiB.");
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const width = view.getUint32(16, true), height = view.getUint32(12, true);
    const powerOfTwo = (value) => value > 0 && value <= 4096 && (value & (value - 1)) === 0;
    check(powerOfTwo(width) && powerOfTwo(height) && !(view.getUint32(112, true) & 0x20fe00),
      "Choose a 2D DDS with power-of-two dimensions up to 4096.");
    const fourCC = String.fromCharCode(...bytes.subarray(84, 88));
    const block = fourCC === "DXT1" ? 8 : ["DXT3", "DXT5"].includes(fourCC) ? 16 : 0;
    const levels = view.getUint32(8, true) & 0x20000 ? view.getUint32(28, true) : 1;
    check(levels > 0 && levels <= Math.log2(Math.max(width, height)) + 1, "The DDS mipmap count is invalid.");
    if (block) {
      let size = 128;
      for (let level = 0; level < levels; level++) {
        size += block * Math.ceil(Math.max(1, width >> level) / 4) * Math.ceil(Math.max(1, height >> level) / 4);
      }
      check(size <= bytes.length, "The DDS mipmap data ends unexpectedly.");
    } else {
      check(!(view.getUint32(80, true) & 4), "Use DXT1, DXT3, DXT5 or an uncompressed DDS.");
      if (levels > 1) {
        const bpp = view.getUint32(88, true) / 8;
        const pitch = view.getUint32(8, true) & 8 ? view.getUint32(20, true) : width * bpp;
        check(bpp === 4 && pitch === width * 4, "Uncompressed DDS mipmaps require tightly packed 32-bit pixels.");
        let size = 128;
        for (let level = 0; level < levels; level++) {
          size += Math.max(1, width >> level) * Math.max(1, height >> level) * 4;
        }
        check(size <= bytes.length, "The DDS mipmap data ends unexpectedly.");
      }
    }
    return readTexture(bytes);
  }

  function canPaintTexture(image) {
    const supported = (n) => n > 0 && n <= 2048 && (n & (n - 1)) === 0;
    return image && supported(image.width) && supported(image.height);
  }

  function writePaintedTexture(image) {
    check(canPaintTexture(image), "Paint supports power-of-two textures up to 2048 pixels per side.");
    const { width, height } = image;
    const levels = Math.log2(Math.max(width, height)) + 1;
    let size = 128;
    for (let level = 0; level < levels; level++) {
      size += Math.max(1, width >> level) * Math.max(1, height >> level) * 4;
    }
    const bytes = new Uint8Array(size);
    const view = new DataView(bytes.buffer);
    bytes.set([68, 68, 83, 32]); // DDS, legacy BGRA8 with a complete mip chain.
    view.setUint32(4, 124, true);
    view.setUint32(8, levels > 1 ? 0x2100f : 0x100f, true);
    view.setUint32(12, height, true);
    view.setUint32(16, width, true);
    view.setUint32(20, width * 4, true);
    view.setUint32(28, levels, true);
    view.setUint32(76, 32, true);
    view.setUint32(80, 0x41, true);
    view.setUint32(88, 32, true);
    view.setUint32(92, 0x00ff0000, true);
    view.setUint32(96, 0x0000ff00, true);
    view.setUint32(100, 0x000000ff, true);
    view.setUint32(104, 0xff000000, true);
    view.setUint32(108, levels > 1 ? 0x401008 : 0x1000, true);
    let offset = 128;
    let pixels = image.pixels, w = width, h = height;
    for (let level = 0; level < levels; level++) {
      for (let i = 0; i < pixels.length; i += 4, offset += 4) {
        bytes[offset] = pixels[i + 2];
        bytes[offset + 1] = pixels[i + 1];
        bytes[offset + 2] = pixels[i];
        bytes[offset + 3] = pixels[i + 3];
      }
      if (level === levels - 1) break;
      const columns = w > 1 ? 2 : 1, rows = h > 1 ? 2 : 1;
      const next = new Uint8Array(w / columns * (h / rows) * 4);
      let out = 0;
      for (let y = 0; y < h; y += rows) {
        for (let x = 0; x < w; x += columns, out += 4) {
          let r = 0, g = 0, b = 0, alpha = 0;
          for (let dy = 0; dy < rows; dy++) {
            for (let dx = 0; dx < columns; dx++) {
              const at = ((y + dy) * w + x + dx) * 4;
              const a = pixels[at + 3];
              r += pixels[at] * a;
              g += pixels[at + 1] * a;
              b += pixels[at + 2] * a;
              alpha += a;
            }
          }
          if (alpha) {
            next[out] = Math.round(r / alpha);
            next[out + 1] = Math.round(g / alpha);
            next[out + 2] = Math.round(b / alpha);
          }
          next[out + 3] = Math.round(alpha / (columns * rows));
        }
      }
      pixels = next;
      w /= columns;
      h /= rows;
    }
    return bytes;
  }

  function texturePixels(width, height) {
    check(width > 0 && width <= 4096 && height > 0 && height <= 4096, "The texture size is unsupported.");
    return new Uint8Array(width * height * 4);
  }

  function readBlocks(view, width, height, pixels, format) {
    const dxt1 = format === "DXT1";
    const dxt3 = format === "DXT3";
    const size = dxt1 ? 8 : 16;
    const blocksWide = Math.ceil(width / 4);
    check(view.byteLength >= 128 + size * blocksWide * Math.ceil(height / 4), "The DDS image ends unexpectedly.");
    const colors = new Uint8Array(16);
    const alphas = new Uint8Array(8);
    let block = 128;
    for (let by = 0; by < height; by += 4) {
      for (let bx = 0; bx < width; bx += 4, block += size) {
        const at = block + (dxt1 ? 0 : 8);
        const first = view.getUint16(at, true);
        const second = view.getUint16(at + 2, true);
        const four = !dxt1 || first > second;
        for (let i = 0; i < 2; i++) {
          const color = i === 0 ? first : second;
          colors[i * 4] = ((color >> 11) & 31) * 255 / 31;
          colors[i * 4 + 1] = ((color >> 5) & 63) * 255 / 63;
          colors[i * 4 + 2] = (color & 31) * 255 / 31;
          colors[i * 4 + 3] = 255;
        }
        for (let channel = 0; channel < 3; channel++) {
          const a = colors[channel], b = colors[channel + 4];
          colors[channel + 8] = four ? (2 * a + b) / 3 : (a + b) / 2;
          colors[channel + 12] = four ? (a + 2 * b) / 3 : 0;
        }
        colors[11] = 255;
        colors[15] = four ? 255 : 0;
        let alphaLow, alphaHigh;
        if (format === "DXT5") {
          alphas[0] = view.getUint8(block);
          alphas[1] = view.getUint8(block + 1);
          const denominator = alphas[0] > alphas[1] ? 7 : 5;
          for (let i = 1; i < denominator; i++) {
            alphas[i + 1] = ((denominator - i) * alphas[0] + i * alphas[1]) / denominator;
          }
          if (denominator === 5) { alphas[6] = 0; alphas[7] = 255; }
          alphaLow = view.getUint32(block + 2, true) & 0xffffff;
          alphaHigh = view.getUint32(block + 4, true) >>> 8;
        }
        const lookup = view.getUint32(at + 4, true);
        for (let pixel = 0; pixel < 16; pixel++) {
          const x = bx + pixel % 4, y = by + (pixel >> 2);
          if (x >= width || y >= height) continue;
          const dest = (y * width + x) * 4;
          const src = 4 * ((lookup >>> (pixel * 2)) & 3);
          pixels[dest] = colors[src];
          pixels[dest + 1] = colors[src + 1];
          pixels[dest + 2] = colors[src + 2];
          let alpha = colors[src + 3];
          if (dxt3) alpha = 17 * ((view.getUint8(block + (pixel >> 1)) >> ((pixel & 1) * 4)) & 15);
          else if (!dxt1) alpha = alphas[((pixel < 8 ? alphaLow : alphaHigh) >>> ((pixel % 8) * 3)) & 7];
          pixels[dest + 3] = alpha;
        }
      }
    }
  }

  const api = { loadModel, readTexture, readReplacementTexture, canPaintTexture, writePaintedTexture, exportModelEdits,
    readModel, readMotion, rotation };
  if (typeof module !== "undefined") module.exports = api;
  else root.BalanceModels = api;
})(globalThis);
