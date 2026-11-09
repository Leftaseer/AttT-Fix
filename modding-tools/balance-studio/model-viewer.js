"use strict";

window.openUnitViewer = (() => {
  const model = window.BalanceModels;
  const element = (name) => document.getElementById("model-" + name);
  const dialog = element("dialog");
  const canvas = element("canvas");
  const clipSelect = element("clip");
  const outfitSelect = element("outfit");
  const partSelect = element("part");
  const boneSelect = element("bone");
  const lodSelect = element("lod");
  const surfaceSelect = element("surface");
  const markerToggle = element("markers");
  const partInfo = element("part-info");
  const inspectionNote = element("inspection-note");
  const frameInput = element("frame");
  const frameLabel = element("frame-label");
  const status = element("status");
  const play = element("play");
  const exportButton = element("export");
  const exportStatus = element("export-status");
  const fps = window.BalanceAnimation.fps;
  let renderer;
  let game, unit, clips, pose, textureCache, save, outfits;
  let request = 0;
  let timer = 0;
  const editor = window.createModelEditor({
    redraw: () => setFrame(frameInput.valueAsNumber),
    previewTexture,
    activeClip: () => clips[Number(clipSelect.value)],
    activeClips: () => clips,
    reload: () => loadClip(Number(clipSelect.value), false, pose.lod, frameInput.valueAsNumber),
    exportRig: async (loaded, reference, motion) => {
      const source = { unit, edition: loaded.edition, mesh: reference.scene.mesh, motion: reference.motion,
        frame: 0, rig: reference.id };
      const names = new Set(reference.scene.parts.flatMap((part) => part.materials.map(({ texture }) => texture)).filter(Boolean));
      const textures = await Promise.all([...names].map(async (name) => {
        const image = await editor.readTexture(loaded, name);
        return [name, image && await encodeTexture(image)];
      }));
      return window.BalanceGlb.makeGlb(reference.scene.parts, new Map(textures), source, reference.bindings, motion);
    },
    drawPaint(name, image, area) {
      if (!pose) return;
      textureCache.set(name, Promise.resolve(image));
      renderer.drawPaint(name, image, area);
    },
    paintState(active) {
      canvas.classList.toggle("painting", active);
      element("camera-hint").hidden = active;
      if (active) {
        stop();
        markerToggle.checked = false;
        updateInspection();
      }
    },
    enterEditMode() {
      if (!pose) return;
      partSelect.value = "-1";
      surfaceSelect.value = "0";
      updateInspection(true);
    },
  });

  function createRenderer(selectBone) {
    const gl = canvas.getContext("webgl", { alpha: false, antialias: true });
    if (!gl) throw new Error("3D preview needs WebGL. Check that hardware acceleration is available in your browser.");
    const vertex = `
      attribute vec3 position;
      attribute vec3 normal;
      attribute vec2 uv;
      attribute float influence;
      uniform mat3 orbit;
      uniform vec3 center;
      uniform vec3 scale;
      uniform vec2 panOffset;
      varying vec2 texCoord;
      varying vec3 surface;
      varying float weight;
      void main() {
        gl_Position = vec4((orbit * (position - center)) * scale, 1.0);
        gl_Position.xy += panOffset;
        gl_PointSize = 8.0;
        surface = orbit * normal;
        texCoord = uv;
        weight = influence;
      }
    `;
    const fragment = `
      precision mediump float;
      uniform sampler2D albedo;
      uniform int style;
      varying vec2 texCoord;
      varying vec3 surface;
      varying float weight;
      void main() {
        if (style == 4) {
          gl_FragColor = vec4(0.12, 0.24, 0.34, 1.0);
          return;
        }
        if (style == 7) {
          gl_FragColor = vec4(0.30, 0.79, 0.73, 1.0);
          return;
        }
        if (style == 5 || style == 6) {
          if (distance(gl_PointCoord, vec2(0.5)) > 0.46) discard;
          gl_FragColor = style == 6 ? vec4(1.0, 0.77, 0.24, 1.0) : vec4(0.25, 0.9, 0.83, 1.0);
          return;
        }
        vec3 color = vec3(0.69, 0.76, 0.8);
        if (style == 0) {
          vec4 texel = texture2D(albedo, texCoord);
          if (texel.a < 0.35) discard;
          color = texel.rgb;
        } else if (style == 3) {
          color = mix(vec3(0.25, 0.37, 0.49), vec3(1.0, 0.51, 0.13), clamp(weight, 0.0, 1.0));
        }
        float facing = max(0.0, dot(normalize(surface), normalize(vec3(-0.45, 0.65, -0.7))));
        gl_FragColor = vec4(color * (0.56 + 0.52 * facing), 1.0);
      }
    `;
    const program = gl.createProgram();
    for (const [type, source] of [[gl.VERTEX_SHADER, vertex], [gl.FRAGMENT_SHADER, fragment]]) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error("The preview shader could not be compiled.");
      gl.attachShader(program, shader);
      gl.deleteShader(shader);
    }
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error("The preview shader could not be linked.");
    gl.useProgram(program);
    gl.enable(gl.DEPTH_TEST);
    gl.clearColor(0.105, 0.14, 0.18, 1);
    const uniforms = Object.fromEntries(["orbit", "center", "scale", "panOffset", "style"].map(
      (name) => [name, gl.getUniformLocation(program, name)]));
    const attributes = ["position", "normal", "uv"].map((name) => gl.getAttribLocation(program, name));
    const influenceAttribute = gl.getAttribLocation(program, "influence");
    const weightBuffer = gl.createBuffer();
    const markerBuffer = gl.createBuffer();

    let buffers = [];
    let textures = new Map();
    let images = new Map();
    let center = [0, 0, 0], radius = 1;
    let focus, projection;
    let partIndex = -1, surface = 0, bone, weightedPart, showMarkers = false;
    const front = -0.42;
    let yaw = front, pitch = 0.08, zoom = 1;
    let panX = 0, panY = 0;

    function aboveGround(part) {
      // Several clips stow unused weapons and accessories below the terrain.
      for (let i = 1; i < part.vertices.length; i += 8) {
        if (part.vertices[i] >= 0) return true;
      }
      return false;
    }

    function uploadTexture({ width, height, pixels }) {
      const texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      const powerOfTwo = (n) => (n & (n - 1)) === 0;
      if (powerOfTwo(width) && powerOfTwo(height)) {
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      } else {
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      }
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      return texture;
    }

    function setTexture(name, image) {
      if (textures.has(name)) gl.deleteTexture(textures.get(name));
      if (image) textures.set(name, uploadTexture(image));
      else textures.delete(name);
      images.set(name, image);
      draw();
    }

    function drawPaint(name, image, area) {
      const texture = textures.get(name);
      if (!texture) return;
      gl.bindTexture(gl.TEXTURE_2D, texture);
      images.set(name, image);
      if (area) {
        const { left, top, right, bottom } = area;
        const width = right - left, height = bottom - top;
        const patch = new Uint8Array(width * height * 4);
        for (let y = 0; y < height; y++) {
          const start = ((top + y) * image.width + left) * 4;
          patch.set(image.pixels.subarray(start, start + width * 4), y * width * 4);
        }
        gl.texSubImage2D(gl.TEXTURE_2D, 0, left, top, width, height, gl.RGBA, gl.UNSIGNED_BYTE, patch);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      } else {
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      }
      draw(true);
    }

    function materialsOf(part) {
      return part.materials.length ? part.materials : [{ start: 0, texture: "" }];
    }

    function projectedGeometry() {
      const { origin, rotation, scale, visible } = projection;
      return visible.map(({ part }) => {
        const points = new Float32Array(part.vertices.length / 8 * 3);
        for (let at = 0, out = 0; at < part.vertices.length; at += 8, out += 3) {
          const x = part.vertices[at] - origin[0];
          const y = part.vertices[at + 1] - origin[1];
          const z = part.vertices[at + 2] - origin[2];
          points[out] = (rotation[0] * x + rotation[3] * y + rotation[6] * z) * scale[0] + panX;
          points[out + 1] = (rotation[1] * x + rotation[4] * y + rotation[7] * z) * scale[1] + panY;
          points[out + 2] = (rotation[2] * x + rotation[5] * y + rotation[8] * z) * scale[2];
        }
        return { part, points, materials: materialsOf(part) };
      });
    }

    function textureAlpha(image, u, v) {
      if (!image) return 1;
      const { width, height, pixels } = image;
      const wrap = (width & (width - 1)) === 0 && (height & (height - 1)) === 0;
      const coordinate = (pixel, size) => wrap ? (pixel + size) % size : Math.max(0, Math.min(size - 1, pixel));
      const x = (wrap ? u - Math.floor(u) : Math.max(0, Math.min(1, u))) * width - 0.5;
      const y = (wrap ? v - Math.floor(v) : Math.max(0, Math.min(1, v))) * height - 0.5;
      const left = Math.floor(x), top = Math.floor(y);
      const dx = x - left, dy = y - top;
      const alpha = (col, row) => pixels[(coordinate(row, height) * width + coordinate(col, width)) * 4 + 3];
      return ((alpha(left, top) * (1 - dx) + alpha(left + 1, top) * dx) * (1 - dy) +
        (alpha(left, top + 1) * (1 - dx) + alpha(left + 1, top + 1) * dx) * dy) / 255;
    }

    function pickTexture(x, y) {
      if (Math.abs(x) > 1 || Math.abs(y) > 1) return;
      projection.geometry ??= projectedGeometry();
      let hit, depth = Infinity;
      for (const { part, points, materials } of projection.geometry) {
        const { vertices, indices } = part;
        for (const [i, { texture, start }] of materials.entries()) {
          const end = materials[i + 1]?.start ?? indices.length;
          for (let at = start; at + 2 < end; at += 3) {
            const a = indices[at] * 3, b = indices[at + 1] * 3, c = indices[at + 2] * 3;
            const ax = points[a], bx = points[b], cx = points[c];
            const ay = points[a + 1], by = points[b + 1], cy = points[c + 1];
            if (x < Math.min(ax, bx, cx) || x > Math.max(ax, bx, cx) ||
                y < Math.min(ay, by, cy) || y > Math.max(ay, by, cy)) continue;
            const determinant = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);
            if (!determinant) continue;
            const p = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / determinant;
            const q = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / determinant;
            const r = 1 - p - q;
            if (p < 0 || q < 0 || r < 0) continue;
            const z = points[a + 2] * p + points[b + 2] * q + points[c + 2] * r;
            if (z < -1 || z > 1 || z >= depth) continue;
            const va = indices[at] * 8, vb = indices[at + 1] * 8, vc = indices[at + 2] * 8;
            const u = vertices[va + 6] * p + vertices[vb + 6] * q + vertices[vc + 6] * r;
            const v = vertices[va + 7] * p + vertices[vb + 7] * q + vertices[vc + 7] * r;
            if (textureAlpha(images.get(texture), u, v) < 0.35) continue;
            hit = { name: texture, u, v };
            depth = z;
          }
        }
      }
      return hit;
    }

    function paintBetween(fromX, fromY, toX, toY) {
      if (!projection) return;
      const rect = canvas.getBoundingClientRect();
      const count = Math.max(1, Math.min(48, Math.ceil(Math.hypot(toX - fromX, toY - fromY) / 2)));
      const hits = [];
      for (let i = 1; i <= count; i++) {
        const x = fromX + (toX - fromX) * i / count;
        const y = fromY + (toY - fromY) * i / count;
        hits.push(pickTexture((x - rect.left) * 2 / rect.width - 1, 1 - (y - rect.top) * 2 / rect.height));
      }
      editor.paintStroke(hits);
    }

    function drawEdges(buffer) {
      const { indices } = buffer.part;
      if (!buffer.edgeBuffer) {
        const edges = new Uint16Array(indices.length * 2);
        for (let i = 0; i + 2 < indices.length; i += 3) {
          const a = indices[i], b = indices[i + 1], c = indices[i + 2];
          edges.set([a, b, b, c, c, a], i * 2);
        }
        buffer.edgeBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer.edgeBuffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edges, gl.STATIC_DRAW);
      } else {
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer.edgeBuffer);
      }
      gl.drawElements(gl.LINES, indices.length * 2, gl.UNSIGNED_SHORT, 0);
    }

    function drawMarkers(visible) {
      gl.disable(gl.DEPTH_TEST);
      gl.disableVertexAttribArray(attributes[1]);
      gl.disableVertexAttribArray(attributes[2]);
      gl.bindBuffer(gl.ARRAY_BUFFER, markerBuffer);
      gl.vertexAttribPointer(attributes[0], 3, gl.FLOAT, false, 0, 0);
      for (const buffer of visible) {
        const { part } = buffer;
        if (!part.boneIds?.length) continue;
        gl.bufferData(gl.ARRAY_BUFFER, part.markers, gl.DYNAMIC_DRAW);
        if (buffer.linkCount === undefined) {
          const links = part.links();
          buffer.linkCount = links.length;
          if (links.length) {
            buffer.linkBuffer = gl.createBuffer();
            gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer.linkBuffer);
            gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, links, gl.STATIC_DRAW);
          }
        }
        if (buffer.linkCount) {
          gl.uniform1i(uniforms.style, 7);
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffer.linkBuffer);
          gl.drawElements(gl.LINES, buffer.linkCount, gl.UNSIGNED_SHORT, 0);
        }
        gl.uniform1i(uniforms.style, 5);
        gl.drawArrays(gl.POINTS, 0, part.boneIds.length);
      }
      const selected = visible.some(({ part }) => part === weightedPart) ? weightedPart.boneIds.indexOf(bone) : -1;
      if (selected !== -1) {
        const at = selected * 3;
        gl.bufferData(gl.ARRAY_BUFFER, weightedPart.markers.subarray(at, at + 3), gl.DYNAMIC_DRAW);
        gl.uniform1i(uniforms.style, 6);
        gl.drawArrays(gl.POINTS, 0, 1);
      }
      gl.enable(gl.DEPTH_TEST);
    }

    function pickBone(clientX, clientY) {
      if (!showMarkers || !projection) return;
      const rect = canvas.getBoundingClientRect();
      const mouseX = clientX - rect.left, mouseY = clientY - rect.top;
      if (mouseX < 0 || mouseY < 0 || mouseX >= rect.width || mouseY >= rect.height) return;
      const { origin, rotation, scale, visible } = projection;
      let nearest, distance = 8 ** 2, depth = Infinity;
      for (const { part } of visible) {
        for (const [index, boneId] of (part.boneIds ?? []).entries()) {
          const at = index * 3;
          const x = part.markers[at] - origin[0];
          const y = part.markers[at + 1] - origin[1];
          const z = part.markers[at + 2] - origin[2];
          const clipX = (rotation[0] * x + rotation[3] * y + rotation[6] * z) * scale[0] + panX;
          const clipY = (rotation[1] * x + rotation[4] * y + rotation[7] * z) * scale[1] + panY;
          const clipZ = (rotation[2] * x + rotation[5] * y + rotation[8] * z) * scale[2];
          if (Math.abs(clipX) > 1 || Math.abs(clipY) > 1 || Math.abs(clipZ) > 1) continue;
          const dx = (clipX + 1) * rect.width / 2 - mouseX;
          const dy = (1 - clipY) * rect.height / 2 - mouseY;
          const squared = dx * dx + dy * dy;
          if (squared < distance || (squared === distance && clipZ < depth)) {
            distance = squared;
            depth = clipZ;
            nearest = { part, boneId };
          }
        }
      }
      if (nearest) selectBone(nearest.part, nearest.boneId);
    }

    function draw(preserveProjection = false) {
      if (!canvas.clientWidth || !canvas.clientHeight) return;
      const pixelRatio = Math.min(devicePixelRatio, 2);
      const width = Math.round(canvas.clientWidth * pixelRatio);
      const height = Math.round(canvas.clientHeight * pixelRatio);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
        preserveProjection = false;
      }
      gl.viewport(0, 0, width, height);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      if (!buffers.length) return;
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const cp = Math.cos(pitch), sp = Math.sin(pitch);
      const rotation = [cy, sp * sy, -cp * sy, 0, cp, sp, sy, -sp * cy, cp * cy];
      const viewRadius = focus?.radius ?? radius;
      const size = 0.88 * zoom / viewRadius;
      const aspect = width / height;
      const scale = [size / Math.max(1, aspect), size * Math.min(1, aspect), 0.25 / viewRadius];
      const origin = focus?.center ?? center;
      gl.uniformMatrix3fv(uniforms.orbit, false, rotation);
      gl.uniform3fv(uniforms.scale, scale);
      gl.uniform3fv(uniforms.center, origin);
      gl.uniform2f(uniforms.panOffset, panX, panY);
      const active = buffers[partIndex];
      const above = buffers.filter(({ part }) => aboveGround(part));
      const visible = active ? [active] : (above.length ? above : buffers);
      if (preserveProjection !== true) projection = { rotation, scale, origin, visible };
      for (const attribute of attributes) gl.enableVertexAttribArray(attribute);
      for (const buffer of visible) {
        const { vertexBuffer, indexBuffer, part } = buffer;
        gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
        gl.vertexAttribPointer(attributes[0], 3, gl.FLOAT, false, 32, 0);
        gl.vertexAttribPointer(attributes[1], 3, gl.FLOAT, false, 32, 12);
        gl.vertexAttribPointer(attributes[2], 2, gl.FLOAT, false, 32, 24);
        gl.uniform1i(uniforms.style, surface);
        if (surface === 0) {
          const materials = materialsOf(part);
          for (const [i, { texture, start }] of materials.entries()) {
            const end = materials[i + 1]?.start ?? part.indices.length;
            gl.bindTexture(gl.TEXTURE_2D, textures.get(texture) ?? textures.get(""));
            gl.drawElements(gl.TRIANGLES, end - start, gl.UNSIGNED_SHORT, start * 2);
          }
        } else {
          gl.bindTexture(gl.TEXTURE_2D, textures.get(""));
          if (surface === 3 && part === weightedPart) {
            gl.enableVertexAttribArray(influenceAttribute);
            gl.bindBuffer(gl.ARRAY_BUFFER, weightBuffer);
            gl.vertexAttribPointer(influenceAttribute, 1, gl.FLOAT, false, 0, 0);
          }
          if (surface === 2) {
            gl.enable(gl.POLYGON_OFFSET_FILL);
            gl.polygonOffset(1, 1);
          }
          gl.drawElements(gl.TRIANGLES, part.indices.length, gl.UNSIGNED_SHORT, 0);
          gl.disableVertexAttribArray(influenceAttribute);
          if (surface === 2) gl.disable(gl.POLYGON_OFFSET_FILL);
        }
      }
      if (surface === 2) {
        gl.uniform1i(uniforms.style, 4);
        for (const buffer of visible) {
          gl.bindBuffer(gl.ARRAY_BUFFER, buffer.vertexBuffer);
          gl.vertexAttribPointer(attributes[0], 3, gl.FLOAT, false, 32, 0);
          gl.vertexAttribPointer(attributes[1], 3, gl.FLOAT, false, 32, 12);
          gl.vertexAttribPointer(attributes[2], 2, gl.FLOAT, false, 32, 24);
          drawEdges(buffer);
        }
      }
      if (showMarkers) drawMarkers(visible);
    }

    function clear() {
      for (const { vertexBuffer, indexBuffer, edgeBuffer, linkBuffer } of buffers) {
        gl.deleteBuffer(vertexBuffer);
        gl.deleteBuffer(indexBuffer);
        if (edgeBuffer) gl.deleteBuffer(edgeBuffer);
        if (linkBuffer) gl.deleteBuffer(linkBuffer);
      }
      for (const texture of textures.values()) gl.deleteTexture(texture);
      textures.clear();
      images.clear();
      buffers = [];
      weightedPart = undefined;
      partIndex = -1;
      focus = projection = undefined;
      draw();
    }

    function setFrame() {
      for (const { vertexBuffer, part } of buffers) {
        gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, part.vertices);
      }
      updateFocus();
      draw();
    }

    function updateFocus() {
      const vertices = buffers[partIndex]?.part.vertices;
      focus = undefined;
      if (vertices?.length) {
        const min = [Infinity, Infinity, Infinity];
        const max = [-Infinity, -Infinity, -Infinity];
        extendBounds(vertices, min, max);
        const partBounds = bounds(min, max);
        if (partBounds.radius > 0) focus = partBounds;
      }
    }

    function inspect(index, style, markers, part, boneId) {
      partIndex = index;
      surface = style;
      showMarkers = markers;
      weightedPart = part;
      bone = boneId;
      if (surface === 3 && weightedPart) {
        gl.bindBuffer(gl.ARRAY_BUFFER, weightBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, weightedPart.influence(bone), gl.STATIC_DRAW);
      }
      updateFocus();
      draw();
    }

    function extendBounds(vertices, min, max) {
      for (let i = 0; i < vertices.length; i += 8) {
        for (let axis = 0; axis < 3; axis++) {
          min[axis] = Math.min(min[axis], vertices[i + axis]);
          max[axis] = Math.max(max[axis], vertices[i + axis]);
        }
      }
    }

    function bounds(min, max) {
      const center = min.map((bound, axis) => (bound + max[axis]) / 2);
      return { center, radius: Math.hypot(...max.map((bound, axis) => bound - center[axis])) };
    }

    function setScene(scene, sourceImages) {
      const { parts, frameCount } = scene;
      const min = [Infinity, Infinity, Infinity];
      const max = [-Infinity, -Infinity, -Infinity];
      // Frame the clip once so tall or lunging poses stay visible without camera motion.
      const samples = Math.min(frameCount, 9);
      for (let sample = 0; sample < samples; sample++) {
        scene.setFrame(Math.round(sample * (frameCount - 1) / Math.max(1, samples - 1)));
        // Include held projectiles at the start without framing their full flight path.
        const visible = parts.filter((part) => (sample === 0 || !part.projectile) && aboveGround(part));
        for (const { vertices } of visible.length ? visible : parts) {
          extendBounds(vertices, min, max);
        }
      }
      scene.setFrame(0);
      ({ center, radius } = bounds(min, max));
      if (!Number.isFinite(radius) || !radius) throw new Error("This pose has invalid geometry.");
      clear();
      images = new Map(sourceImages);
      textures = new Map([...images].filter(([, image]) => image).map(([name, image]) => [name, uploadTexture(image)]));
      textures.set("", uploadTexture({ width: 1, height: 1, pixels: new Uint8Array([178, 185, 191, 255]) }));
      buffers = parts.map((part) => {
        const vertexBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, part.vertices, gl.DYNAMIC_DRAW);
        const indexBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, part.indices, gl.STATIC_DRAW);
        return { part, vertexBuffer, indexBuffer };
      });
      draw();
    }

    let pointer = null;
    const clickSlop = 4;
    const orbit = (dx, dy) => {
      yaw = (yaw + dx * 0.012) % (2 * Math.PI);
      pitch = Math.min(1.35, Math.max(-1.35, pitch + dy * 0.012));
      draw();
    };
    function pan(dx, dy) {
      panX += 2 * dx / canvas.clientWidth;
      panY -= 2 * dy / canvas.clientHeight;
      draw();
    }
    function changeZoom(factor) {
      zoom = Math.min(5, Math.max(0.35, zoom * factor));
      draw();
    }
    function reset() {
      yaw = front;
      pitch = 0.08;
      zoom = 1;
      panX = panY = 0;
      draw();
    }
    canvas.addEventListener("pointerdown", (event) => {
      if (!buffers.length || pointer || (event.button !== 0 && event.button !== 2)) return;
      const { pointerId, clientX, clientY, button } = event;
      const painting = button === 0 && !event.altKey && editor.painting();
      pointer = { pointerId, clientX, clientY, button, painting, clicking: button === 0 && showMarkers && !painting };
      canvas.setPointerCapture(event.pointerId);
      if (painting) {
        stop();
        editor.beginStroke();
        paintBetween(clientX, clientY, clientX, clientY);
      }
    });
    canvas.addEventListener("pointermove", (event) => {
      if (event.pointerId !== pointer?.pointerId) return;
      if (!(event.buttons & (pointer.button === 2 ? 2 : 1))) {
        canvas.releasePointerCapture(event.pointerId);
        endDrag(event);
        return;
      }
      const dx = event.clientX - pointer.clientX, dy = event.clientY - pointer.clientY;
      if (pointer.clicking && Math.hypot(dx, dy) < clickSlop) return;
      pointer.clicking = false;
      if (pointer.painting) paintBetween(pointer.clientX, pointer.clientY, event.clientX, event.clientY);
      else if (pointer.button === 2) pan(dx, dy);
      else orbit(dx, dy);
      pointer.clientX = event.clientX;
      pointer.clientY = event.clientY;
    });
    function endDrag(event) {
      if (event.pointerId !== pointer?.pointerId) return;
      if (pointer.painting) editor.endStroke();
      pointer = null;
    }
    canvas.addEventListener("pointerup", (event) => {
      if (event.pointerId !== pointer?.pointerId) return;
      const click = pointer.clicking && Math.hypot(event.clientX - pointer.clientX, event.clientY - pointer.clientY) < clickSlop;
      endDrag(event);
      if (click) pickBone(event.clientX, event.clientY);
    });
    canvas.addEventListener("lostpointercapture", endDrag);
    canvas.addEventListener("contextmenu", (event) => event.preventDefault());
    canvas.addEventListener("wheel", (event) => {
      if (!buffers.length) return;
      event.preventDefault();
      changeZoom(event.deltaY < 0 ? 1.12 : 1 / 1.12);
    }, { passive: false });
    canvas.addEventListener("keydown", (event) => {
      if (!buffers.length) return;
      const drag = event.shiftKey ? pan : orbit;
      const action = {
        ArrowLeft: () => drag(-16, 0), ArrowRight: () => drag(16, 0),
        ArrowUp: () => drag(0, -16), ArrowDown: () => drag(0, 16),
        "+": () => changeZoom(1.2), "=": () => changeZoom(1.2),
        "-": () => changeZoom(1 / 1.2), Home: reset,
      }[event.key];
      if (action) { event.preventDefault(); action(); }
    });
    new ResizeObserver(draw).observe(canvas);
    return { setScene, setFrame, setTexture, drawPaint, clear, reset, changeZoom, inspect };
  }

  function previewTexture(name, image) {
    const cache = textureCache;
    if (!cache.has(name)) return;
    if (image) {
      cache.set(name, Promise.resolve(image));
      renderer.setTexture(name, image);
      return;
    }
    const pending = editor.readTexture(game, name);
    cache.set(name, pending);
    pending.then((image) => {
      if (cache === textureCache && cache.get(name) === pending && pose) renderer.setTexture(name, image);
    });
  }

  function setFrame(frame) {
    pose.setFrame(frame);
    renderer.setFrame();
    frameInput.value = frame;
    frameLabel.textContent = `Frame ${frame + 1} / ${pose.frameCount}`;
  }

  function stop() {
    cancelAnimationFrame(timer);
    timer = 0;
    play.textContent = "Play";
    play.setAttribute("aria-pressed", "false");
  }

  function controls(ready) {
    for (const name of ["zoom-in", "zoom-out", "reset", "export"]) element(name).disabled = !ready;
    frameInput.disabled = play.disabled = !ready || pose.frameCount < 2;
    surfaceSelect.disabled = partSelect.disabled = !ready;
    lodSelect.disabled = !ready || pose.lods.length < 2;
    if (!ready) {
      boneSelect.disabled = markerToggle.disabled = true;
      partInfo.textContent = "";
      editor.setScene(undefined);
    }
  }

  function updateInspection(partChanged = false) {
    const partIndex = Number(partSelect.value);
    const part = pose.parts[partIndex];
    if (partChanged) {
      const previousBone = boneSelect.value;
      boneSelect.replaceChildren();
      for (const [index, entry] of pose.parts.entries()) {
        if (!entry.boneIds?.length || (part && entry !== part)) continue;
        const name = entry.name || "Unnamed part";
        const group = part ? boneSelect : document.createElement("optgroup");
        if (!part) {
          group.label = `${index + 1}. ${name}`;
          boneSelect.append(group);
        }
        group.append(...entry.boneIds.map((bone) =>
          new Option(`Bone ${bone}${part ? "" : ` · ${name}`}`, `${index}:${bone}`)));
      }
      if (!boneSelect.options.length) boneSelect.add(new Option("No weighted bones", ""));
      if ([...boneSelect.options].some(({ value }) => value === previousBone)) boneSelect.value = previousBone;
    }
    const hasBones = Boolean(boneSelect.value);
    const [weightedIndex, bone] = boneSelect.value.split(":").map(Number);
    boneSelect.disabled = markerToggle.disabled = surfaceSelect.options[3].disabled = !hasBones;
    if (!hasBones && surfaceSelect.value === "3") surfaceSelect.value = "1";
    const style = Number(surfaceSelect.value);
    const showMarkers = markerToggle.checked && !markerToggle.disabled;
    inspectionNote.textContent = [
      style === 3 && "Blue to orange shows increasing influence from the selected bone.",
      showMarkers && "Click a marker to select its bone. Lines link bones that influence the same vertices.",
    ].filter(Boolean).join(" ");
    const inspected = part ? [part] : pose.parts;
    const vertices = inspected.reduce((total, entry) => total + entry.vertices.length / 8, 0);
    const triangles = inspected.reduce((total, entry) => total + entry.indices.length / 3, 0);
    const materials = part && [...new Set(part.materials.map(({ texture }) => texture).filter(Boolean))].join(", ");
    partInfo.textContent = [
      `${vertices.toLocaleString()} vertices · ${triangles.toLocaleString()} triangles`,
      part && (part.boneIds ? `${part.boneIds.length} weighted bones / ${part.boneCount} mesh bones` : "Rigid part"),
      part && `Track ${part.trackIndex} · ${part.trackFrames} frames · ${part.trackBoneCount} transforms per frame`,
      part && (materials || "No texture assigned"),
    ].filter(Boolean).join(" · ");
    renderer.inspect(partIndex, style, showMarkers, hasBones ? pose.parts[weightedIndex] : undefined, bone);
  }

  function selectBone(part, boneId) {
    boneSelect.value = `${pose.parts.indexOf(part)}:${boneId}`;
    updateInspection();
  }

  async function loadClip(index, tryOthers = false, lod = 0, frame = 0) {
    const ticket = ++request;
    const loadedGame = game;
    const cache = textureCache;
    stop();
    controls(false);
    exportStatus.textContent = "Exports the current frame as a textured mesh.";
    clipSelect.disabled = clips.length < 2;
    pose = null;
    renderer.clear();
    status.textContent = "Reading mesh and animation…";
    const candidates = tryOthers ? clips.map((_, i) => i).slice(index) : [index];
    let error;
    for (const candidate of candidates) {
      const clip = clips[candidate];
      try {
        const scene = await model.loadModel(loadedGame, clip, lod, editor.overrides(loadedGame));
        if (ticket !== request) return;
        editor.apply(loadedGame, scene);
        const names = new Set(scene.parts.flatMap((part) => part.materials.map((material) => material.texture)).filter(Boolean));
        // Keep the decoded images for the active mesh, which most clips share.
        for (const name of cache.keys()) if (!names.has(name)) cache.delete(name);
        const images = await Promise.all([...names].map(async (name) => {
          if (!cache.has(name)) {
            cache.set(name, editor.readTexture(loadedGame, name));
          }
          return [name, await cache.get(name)];
        }));
        if (ticket !== request) return;
        renderer.setScene(scene, images);
        pose = scene;
        clipSelect.value = candidate;
        frameInput.max = scene.frameCount - 1;
        lodSelect.replaceChildren(...scene.lods.map((level) => new Option(level === 0 ? "Highest detail" : `LOD ${level}`, level)));
        lodSelect.value = lod;
        partSelect.replaceChildren(new Option("All visible parts", -1), ...scene.parts.map(
          (part, i) => new Option(`${i + 1}. ${part.name || "Unnamed part"}`, i)));
        setFrame(Math.min(frame, scene.frameCount - 1));
        controls(true);
        updateInspection(true);
        editor.setScene(scene);
        const unavailable = images.filter(([, image]) => !image).length;
        status.textContent = [scene.descriptor, scene.mesh, clip.motion, `${scene.parts.length} mesh parts`,
          unavailable && `${unavailable} textures unavailable`].filter(Boolean).join(" · ");
        return;
      } catch (failure) {
        if (ticket !== request) return;
        error ??= failure;
      }
    }
    status.textContent = error?.message ?? "No model animation was found for this unit.";
    if (lod !== 0 && lodSelect.options.length > 1) lodSelect.disabled = false;
  }

  async function encodeTexture(image) {
    const bitmap = document.createElement("canvas");
    bitmap.width = image.width;
    bitmap.height = image.height;
    bitmap.getContext("2d").putImageData(new ImageData(
      new Uint8ClampedArray(image.pixels.buffer), image.width, image.height), 0, 0);
    const blob = await new Promise((resolve) => bitmap.toBlob(resolve, "image/png"));
    if (!blob) throw new Error("A texture could not be encoded as PNG.");
    const masked = image.pixels.some((value, index) => index % 4 === 3 && value < 90);
    return { png: new Uint8Array(await blob.arrayBuffer()), masked };
  }

  exportButton.addEventListener("click", async () => {
    const ticket = request;
    const download = save;
    const clip = clips[Number(clipSelect.value)];
    const source = { unit, edition: game.edition, mesh: pose.mesh, motion: clip.motion, frame: frameInput.valueAsNumber };
    stop();
    const parts = pose.parts.map((part) => ({ ...part, vertices: part.vertices.slice() }));
    const textures = [...textureCache];
    exportButton.disabled = true;
    exportStatus.textContent = "Preparing GLB…";
    try {
      const images = new Map(await Promise.all(textures.map(async ([name, pending]) => {
        const image = await pending;
        return [name, image && await encodeTexture(image)];
      })));
      const bytes = window.BalanceGlb.makeGlb(parts, images, source);
      const clipName = source.motion.replace(/\.ska$/i, "");
      const name = `${source.edition}-${source.unit}-${clipName}-frame-${source.frame + 1}.glb`;
      download(name, new Blob([bytes], { type: "model/gltf-binary" }));
      if (request === ticket) exportStatus.textContent = `Downloaded frame ${source.frame + 1} as GLB.`;
    } catch (error) {
      if (request === ticket) exportStatus.textContent = error.message;
    } finally {
      if (request === ticket) exportButton.disabled = false;
    }
  });

  play.addEventListener("click", () => {
    if (timer) { stop(); return; }
    const start = performance.now() - frameInput.valueAsNumber * 1000 / fps;
    play.textContent = "Pause";
    play.setAttribute("aria-pressed", "true");
    function tick(now) {
      const frame = Math.floor((now - start) * fps / 1000) % pose.frameCount;
      if (frame !== frameInput.valueAsNumber) setFrame(frame);
      timer = requestAnimationFrame(tick);
    }
    timer = requestAnimationFrame(tick);
  });
  frameInput.addEventListener("input", () => { stop(); setFrame(frameInput.valueAsNumber); });
  clipSelect.addEventListener("change", () => loadClip(Number(clipSelect.value)));
  outfitSelect.addEventListener("change", () => showRecord(outfits[Number(outfitSelect.value)]));
  lodSelect.addEventListener("change", () => loadClip(Number(clipSelect.value), false,
    Number(lodSelect.value), frameInput.valueAsNumber));
  partSelect.addEventListener("change", () => updateInspection(true));
  for (const control of [surfaceSelect, boneSelect, markerToggle]) {
    control.addEventListener("change", () => updateInspection());
  }
  element("zoom-in").addEventListener("click", () => renderer.changeZoom(1.2));
  element("zoom-out").addEventListener("click", () => renderer.changeZoom(1 / 1.2));
  element("reset").addEventListener("click", () => renderer.reset());
  dialog.addEventListener("close", () => {
    if (dialog.open) return;
    request++;
    stop();
    renderer?.clear();
    editor.close();
    status.textContent = "";
    pose = game = unit = clips = textureCache = save = outfits = null;
  });

  function showRecord(record) {
    unit = record.id;
    clips = record.clips;
    element("title").textContent = record.title;
    element("edition").textContent = `${game.edition === "attt" ? "Original game" : "Valkyrie"} · ${record.id}`;
    clipSelect.replaceChildren(...clips.map(({ label }, i) => new Option(label, i)));
    frameLabel.textContent = "Frame";
    clipSelect.disabled = true;
    controls(false);
    try {
      renderer ??= createRenderer(selectBone);
      renderer.reset();
      loadClip(0, true);
    } catch (error) {
      status.textContent = error.message;
    }
  }

  return (loaded, record, download, collection) => {
    game = loaded;
    save = download;
    outfits = collection;
    textureCache = new Map();
    editor.open(game, save);
    surfaceSelect.value = "0";
    markerToggle.checked = false;
    element("outfit-picker").hidden = !outfits;
    outfitSelect.replaceChildren();
    const groups = new Map();
    for (const [i, outfit] of (outfits ?? []).entries()) {
      if (!groups.has(outfit.group)) {
        const group = document.createElement("optgroup");
        group.label = outfit.group;
        outfitSelect.append(group);
        groups.set(outfit.group, group);
      }
      groups.get(outfit.group).append(new Option(outfit.title, i));
    }
    dialog.showModal();
    showRecord(record);
  };
})();
