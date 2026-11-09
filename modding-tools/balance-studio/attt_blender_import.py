"""Import a Balance Studio rig template with its shared edges welded."""

bl_info = {
    "name": "AttT Rig Template",
    "author": "Balance Studio",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "File > Import > AttT Rig Template (.glb)",
    "category": "Import-Export",
}

import bpy
import json
import struct
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper


def template_frame_count(filepath):
    try:
        with open(filepath, "rb") as stream:
            header = stream.read(20)
            if len(header) != 20:
                return None
            magic, version, _, length, kind = struct.unpack("<4sIII4s", header)
            if magic != b"glTF" or version != 2 or kind != b"JSON" or length > 4 * 1024 * 1024:
                return None
            asset = json.loads(stream.read(length))
        extras = asset["scenes"][asset.get("scene", 0)].get("extras", {})
        frames = extras.get("att_animation_frames")
        if extras.get("rig") and extras.get("att_animation_fps") == 30 and type(frames) is int and 1 < frames <= 30000:
            return frames
    except (OSError, ValueError, IndexError, KeyError, TypeError, AttributeError):
        pass
    return None


def weld_template_mesh(obj):
    original = obj.data
    ids = original.attributes.get("_ATT_WELD")
    if ids is None or ids.domain != "POINT" or ids.data_type != "FLOAT":
        return 0

    representatives = {}
    kept = []
    remap = []
    weights = []
    for vertex, value in zip(original.vertices, ids.data):
        groups = tuple(sorted((group.group, round(group.weight, 5)) for group in vertex.groups))
        key = (round(value.value), groups)
        index = representatives.get(key)
        if index is None or (original.vertices[kept[index]].co - vertex.co).length > 0.00003:
            index = len(kept)
            representatives[key] = index
            kept.append(vertex.index)
            weights.append([(group.group, group.weight) for group in vertex.groups])
        remap.append(index)
    removed = len(original.vertices) - len(kept)
    if removed == 0:
        original.attributes.remove(ids)
        return 0

    faces = [[remap[i] for i in polygon.vertices] for polygon in original.polygons]
    if any(len(face) != len(set(face)) for face in faces):
        return 0

    mesh = bpy.data.meshes.new(original.name + " welded")
    mesh.from_pydata([original.vertices[i].co for i in kept], [], faces)
    for material in original.materials:
        mesh.materials.append(material)
    for source, target in zip(original.polygons, mesh.polygons):
        target.material_index = source.material_index
        target.use_smooth = source.use_smooth
    for layer in original.uv_layers:
        copied = mesh.uv_layers.new(name=layer.name)
        for source, target in zip(layer.uv, copied.uv):
            target.vector = source.vector
    if original.uv_layers:
        mesh.uv_layers.active_index = original.uv_layers.active_index

    # UVs and split normals belong to corners. Face order and corner order
    # are unchanged by the vertex remap, including at hard edges.
    normals = [entry.vector.copy() for entry in original.corner_normals]
    sharp = {tuple(sorted(remap[i] for i in edge.vertices)) for edge in original.edges if edge.use_edge_sharp}
    seams = {tuple(sorted(remap[i] for i in edge.vertices)) for edge in original.edges if edge.use_seam}
    uv = mesh.uv_layers.active
    if uv:
        first = {}
        for polygon in mesh.polygons:
            loops = list(polygon.loop_indices)
            for a, b in zip(loops, loops[1:] + loops[:1]):
                va, vb = mesh.loops[a].vertex_index, mesh.loops[b].vertex_index
                if va > vb:
                    va, vb, a, b = vb, va, b, a
                edge = (va, vb)
                corners = tuple(tuple(uv.uv[i].vector) for i in (a, b))
                if edge in first and corners != first[edge]:
                    seams.add(edge)
                first.setdefault(edge, corners)
    for edge in mesh.edges:
        key = tuple(sorted(edge.vertices))
        if key in sharp:
            edge.use_edge_sharp = True
        if key in seams:
            edge.use_seam = True
    if normals:
        mesh.normals_split_custom_set(normals)

    group_names = [group.name for group in obj.vertex_groups]
    obj.data = mesh
    for name in group_names:
        obj.vertex_groups.new(name=name)
    for index, groups in enumerate(weights):
        for group, weight in groups:
            obj.vertex_groups[group].add([index], weight, "REPLACE")
    if original.users == 0:
        name = original.name
        bpy.data.meshes.remove(original)
        mesh.name = name
    mesh.update()
    return removed


def display_rig(context, armature, connect=True):
    lengths = {bone.name: bone.get("att_length") for bone in armature.data.bones}
    if not any(lengths.values()):
        return
    previous = context.view_layer.objects.active
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        for bone in armature.data.edit_bones:
            length = lengths[bone.name]
            if isinstance(length, (int, float)) and length > 0:
                bone.length = length
        if connect:
            for bone in armature.data.edit_bones:
                if bone.parent and (bone.head - bone.parent.tail).length < 0.00001:
                    bone.use_connect = True
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
        context.view_layer.objects.active = previous
    armature.data.display_type = "STICK"
    armature.show_in_front = True
    for bone in armature.data.bones:
        bone.hide = bool(bone.get("att_unused", False))


class IMPORT_SCENE_OT_attt_rig(bpy.types.Operator, ImportHelper):
    """Import an AttT template and join the matching boundary edges"""

    bl_idname = "import_scene.attt_rig"
    bl_label = "Import AttT Rig Template"
    bl_options = {"REGISTER", "UNDO"}
    filename_ext = ".glb"
    filter_glob: StringProperty(default="*.glb", options={"HIDDEN"})

    def execute(self, context):
        existing = set(bpy.data.objects)
        scene = context.scene
        frames = template_frame_count(self.filepath)
        timing = (scene.render.fps, scene.render.fps_base, scene.frame_start, scene.frame_end, scene.frame_current)
        if frames:
            scene.render.fps = 30
            scene.render.fps_base = 1
            scene.frame_start = 0
            scene.frame_end = frames - 1
            scene.frame_set(0)
        options = {"filepath": self.filepath, "merge_vertices": False}
        properties = bpy.ops.import_scene.gltf.get_rna_type().properties
        if "bone_heuristic" in properties:
            options["bone_heuristic"] = "BLENDER"
        if "disable_bone_shape" in properties:
            options["disable_bone_shape"] = True
        try:
            result = bpy.ops.import_scene.gltf(**options)
        except RuntimeError as error:
            self.report({"ERROR"}, str(error))
            result = {"CANCELLED"}
        if "FINISHED" not in result:
            if frames:
                scene.render.fps, scene.render.fps_base, scene.frame_start, scene.frame_end, frame = timing
                scene.frame_set(frame)
            return {"CANCELLED"}
        imported = set(bpy.data.objects) - existing
        removed = sum(weld_template_mesh(obj) for obj in imported if obj.type == "MESH")
        for obj in imported:
            if obj.type == "ARMATURE":
                # Connected edit bones drop the imported pose's local translation.
                display_rig(context, obj, connect=not frames)
        self.report({"INFO"}, f"AttT template imported. Welded {removed} duplicate vertices.")
        return {"FINISHED"}


def menu_import(self, _context):
    self.layout.operator(IMPORT_SCENE_OT_attt_rig.bl_idname, text="AttT Rig Template (.glb)")


def register():
    bpy.utils.register_class(IMPORT_SCENE_OT_attt_rig)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.utils.unregister_class(IMPORT_SCENE_OT_attt_rig)


if __name__ == "__main__":
    register()
