"""Unit tests for the world data toolkit (no game installation required)."""
import json
import math
import os
import struct
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import gres
import heightmap
import lua_data
import world
import worldctl
import worldserve


def chunk(instructions, constants, stack=4, protos=()):
    """Build a minimal float32/size_t32 Lua 5.1 chunk for the evaluator."""
    def string(value):
        raw = value.encode('cp1251')
        return struct.pack('<I', len(raw) + 1) + raw + b'\0'

    out = bytearray(lua_data.HEADER)
    out += struct.pack('<I', 0)                       # source name
    out += struct.pack('<ii', 1, 1)                   # lines
    out += struct.pack('<4B', 0, 0, 0, stack)         # upvalues, params, vararg, stack
    out += struct.pack('<I', len(instructions))
    out += b''.join(struct.pack('<I', item) for item in instructions)
    out += struct.pack('<I', len(constants))
    for value in constants:
        if value is None:
            out += b'\0'
        elif isinstance(value, bool):
            out += b'\1' + bytes((1 if value else 0,))
        elif isinstance(value, float):
            out += b'\3' + struct.pack('<f', value)
        else:
            out += b'\4' + string(value)
    out += struct.pack('<I', len(protos))
    for proto in protos:
        out += proto
    out += struct.pack('<I', 0)                       # line info
    out += struct.pack('<I', 0)                       # locals
    out += struct.pack('<I', 0)                       # upvalue names
    return bytes(out)


def ins(op, a=0, b=0, c=0):
    return op | (a << 6) | (c << 14) | (b << 23)


def function(code, constants, params=0, stack=8, nups=0, protos=()):
    """Serialize one nested function body (no chunk header)."""
    def string(value):
        raw = value.encode('cp1251')
        return struct.pack('<I', len(raw) + 1) + raw + b'\0'

    out = bytearray()
    out += string('')
    out += struct.pack('<ii', 1, 1)
    out += struct.pack('<4B', nups, params, 0, stack)
    out += struct.pack('<I', len(code))
    out += b''.join(struct.pack('<I', item) for item in code)
    out += struct.pack('<I', len(constants))
    for value in constants:
        if value is None:
            out += b'\0'
        elif isinstance(value, bool):
            out += b'\1' + bytes((1 if value else 0,))
        elif isinstance(value, float):
            out += b'\3' + struct.pack('<f', value)
        else:
            out += b'\4' + string(value)
    out += struct.pack('<I', len(protos))
    out += b''.join(protos)
    out += struct.pack('<I', 0)                       # line info
    out += struct.pack('<I', 0)                       # locals
    out += struct.pack('<I', 0)                       # upvalue names
    return bytes(out)


class HeightmapTest(unittest.TestCase):
    def make(self):
        width, height = 5, 3
        samples = []
        for x in range(width):
            for y in range(height):
                samples.append(x * 1000 + y * 10)
        data = struct.pack('<4i', width, height, -10, -20)
        data += struct.pack('<%dH' % len(samples), *samples)
        data += struct.pack('<2f', 80.0, -300.0)
        return heightmap.Heightmap(data)

    def test_layout_and_elevation(self):
        map_ = self.make()
        self.assertEqual((map_.width, map_.height, map_.min_x, map_.min_z), (5, 3, -10, -20))
        self.assertEqual(map_.at(2, 1), 2010)
        self.assertAlmostEqual(map_.elevation(0), -300.0)
        self.assertAlmostEqual(map_.elevation(8000), -200.0)
        self.assertAlmostEqual(map_.min_elevation, -300.0)
        self.assertAlmostEqual(map_.max_elevation, 65535 / 80.0 - 300.0)
        self.assertAlmostEqual(map_.max_x, 10.0)
        self.assertAlmostEqual(map_.max_z, -10.0)

    def test_bilinear_sample(self):
        map_ = self.make()
        self.assertAlmostEqual(map_.sample(-10, -20), -300.0)
        self.assertAlmostEqual(map_.sample(0, -20), map_.elevation(2000))
        mid = map_.sample(-7.5, -20)
        self.assertAlmostEqual(mid, (map_.elevation(0) + map_.elevation(1000)) / 2)
        self.assertIsNone(map_.sample(100, -20))

    def test_render_shape_and_palette(self):
        map_ = self.make()
        width, height, rgb = map_.render(max_size=8, water=-250.0)
        self.assertEqual(len(rgb), height * (1 + width * 3))
        self.assertTrue(0 < width <= 8 and 0 < height <= 8)
        width, height, dry = map_.render(max_size=8, water=None)
        self.assertEqual(len(dry), height * (1 + width * 3))

    def test_truncated_and_bad_scale(self):
        with self.assertRaises(ValueError):
            heightmap.Heightmap(b'\0' * 8)
        data = struct.pack('<4i', 1, 1, 0, 0) + struct.pack('<H', 5) + struct.pack('<2f', 0.0, 0.0)
        map_ = heightmap.Heightmap(data)
        self.assertEqual((map_.scale, map_.offset), (1.0, 0.0))


class ArchiveTest(unittest.TestCase):
    def test_write_read_and_overlay(self):
        with tempfile.TemporaryDirectory() as folder:
            base = {'a.lua': b'A', 'b.lua': b'B', 'sub/c.lua': b'C'}
            gres.write_pak(os.path.join(folder, 'Resource0.pak'), base)
            gres.write_pak(os.path.join(folder, 'Resource1.pak'),
                           {'b.lua': b'B2', 'd.lua': b'D'})
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                self.assertEqual(archive_set.slots, [0, 1])
                self.assertEqual(archive_set.read('a.lua'), b'A')
                self.assertEqual(archive_set.read('b.lua'), b'B2')
                self.assertEqual(archive_set.read('sub/c.lua'), b'C')
                self.assertEqual(sorted(archive_set.names()),
                                 ['a.lua', 'b.lua', 'd.lua', 'sub/c.lua'])
                self.assertTrue(archive_set.has('d.lua'))
                self.assertFalse(archive_set.has('missing.lua'))
                resolved = archive_set.resolve('b.lua')
                self.assertEqual(resolved.archive.path.name, 'Resource1.pak')
            finally:
                archive_set.close()

    def test_write_pak_refuses_existing_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'Resource0.pak')
            gres.write_pak(path, {'a': b'A'})
            with self.assertRaises(FileExistsError):
                gres.write_pak(path, {'a': b'B'})
            gres.write_pak(path, {'a': b'B'}, overwrite=True)
            archive = gres.Archive(path)
            try:
                self.assertEqual(archive.read('a'), b'B')
            finally:
                archive.close()
            target = os.path.join(folder, 'target.bin')
            with open(target, 'wb') as stream:
                stream.write(b'x')
            link = os.path.join(folder, 'Resource1.pak')
            os.symlink(target, link)
            with self.assertRaises(ValueError):
                gres.write_pak(link, {'a': b'A'})

    def test_identity_trailer_and_overlay_check(self):
        with tempfile.TemporaryDirectory() as folder:
            base = os.path.join(folder, 'Resource0.pak')
            entries = {'a.lua': b'A', 'b.lua': b'B'}
            gres.write_pak(base, entries)
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                identity = gres.file_identity(archive_set, entries)
            finally:
                archive_set.close()
            overlay = os.path.join(folder, 'Resource1.pak')
            gres.write_pak(overlay, {'b.lua': b'B2'}, identity=identity)
            with gres.Archive(overlay) as archive:
                self.assertEqual(archive.read('b.lua'), b'B2')
            self.assertEqual(gres.read_identity(overlay), identity)
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                self.assertEqual(gres.check_overlay(overlay, archive_set),
                                 (identity, []))
            finally:
                archive_set.close()
            gres.write_pak(base, {'a.lua': b'AX', 'b.lua': b'B'}, overwrite=True)
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                built_for, differences = gres.check_overlay(overlay, archive_set)
            finally:
                archive_set.close()
            self.assertEqual(built_for, identity)
            self.assertEqual(len(differences), 1)
            self.assertIn('a.lua differs', differences[0])
            plain = os.path.join(folder, 'Resource2.pak')
            gres.write_pak(plain, {'c.lua': b'C'})
            self.assertIsNone(gres.read_identity(plain))
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                self.assertIsNone(gres.check_overlay(plain, archive_set))
            finally:
                archive_set.close()
            malformed = os.path.join(folder, 'Resource3.pak')
            gres.write_pak(malformed, {'c.lua': b'C'},
                           identity={'format': gres.IDENTITY_FORMAT,
                                     'files': {'c.lua': 'not-a-record'}})
            self.assertIsNone(gres.read_identity(malformed))

    def test_localization_slot_and_bad_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            gres.write_pak(os.path.join(folder, 'Localization.pak'), {'t.txt': b'hello'})
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                self.assertEqual(archive_set.read('t.txt'), b'hello')
            finally:
                archive_set.close()
            path = os.path.join(folder, 'Resource9.pak')
            with open(path, 'wb') as stream:
                stream.write(b'NOPE' + b'\0' * 8)
            with self.assertRaises(ValueError):
                gres.Archive(path).close()

    def test_source_overlay_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'Resource0.pak')
            source = (b'Town = {Town1 = {Pos = {1.0, 0.0, 2.0}, Rot = 0.0, '
                      b'Houses = {}}}\n')
            gres.write_pak(path, {'continent1towns.lua': source})
            data = world.World.load_archives([path], continents=(1,))
            self.assertEqual(data.source_modules(),
                             [{'continent': 1, 'module': 'towns',
                               'archive': 'Resource0.pak', 'slot': 0}])
            self.assertEqual(list(data.towns(1)), ['Town1'])
            gres.write_pak(path, {'continent1towns.lua': b'Town = {}\nfunction f() end\n'},
                           overwrite=True)
            with self.assertRaises(world.WorldError) as caught:
                world.World.load_archives([path], continents=(1,))
            self.assertIn('continent1towns.lua', str(caught.exception))


class LuaDataTest(unittest.TestCase):
    def test_decode_handcrafted_chunk(self):
        instructions = [
            ins(10, 0),                       # NEWTABLE r0
            ins(1, 1, 0, 0),                  # LOADK r1 "a"
            ins(9, 0, 256 + 1, 1),            # SETTABLE r0[1.0] = r1
            ins(1, 2, 0, 3),                  # LOADK r2 2.5
            ins(9, 0, 256 + 2, 2),            # SETTABLE r0["x"] = r2
            ins(2, 3, 1, 0),                  # LOADBOOL r3 true
            ins(9, 0, 256 + 1, 3),            # SETTABLE r0[1.0] = r3
            ins(7, 0, 0, 4),                  # SETGLOBAL r0 "T"
            ins(30),                          # RETURN
        ]
        data = chunk(instructions, ['a', 1.0, 'x', 2.5, 'T'])
        self.assertEqual(lua_data.decode_global(data, 'T'), {1: True, 'x': 2.5})

    def test_source_round_trip(self):
        table = {
            'Town1': {
                'Pos': {1: 10.0, 2: 0.0, 3: -4.5},
                'Rot': 45.0,
                'Houses': {
                    'H1': {'Pos': {1: 0.0, 2: 0.0, 3: 2.0},
                           'Npcs': {1: {1: 'npc', 2: 3.0, 3: 'x'}}},
                },
            },
            'город': {'name': 'юникод'},
        }
        source = lua_data.emit_source({'Town': table}, order=['Town'])
        self.assertIn('Town = {'.encode('cp1251'), source)
        self.assertEqual(lua_data.load_module(source, 'Town'), table)
        self.assertEqual(world.canonical(lua_data.load_module(source, 'Town')),
                         world.canonical(table))

    def test_calls_need_closure_mode(self):
        instructions = [
            ins(5, 0),                        # GETGLOBAL r0 "using"
            ins(1, 1, 0, 1),                  # LOADK r1 "dialogUtils"
            ins(28, 0, 2, 1),                 # CALL r0 2 1 (no results)
            ins(10, 1),                       # NEWTABLE r1
            ins(7, 1, 0, 2),                  # SETGLOBAL r1 "Dialog"
            ins(30),                          # RETURN
        ]
        data = chunk(instructions, ['using', 'dialogUtils', 'Dialog'])
        with self.assertRaises(lua_data.LuaDataError):
            lua_data.decode_chunk(data)
        self.assertEqual(lua_data.decode_chunk(data, allow_closures=True)['Dialog'], {})

    def test_numeric_for_loop(self):
        instructions = [
            ins(10, 0),                        # NEWTABLE r0
            ins(1, 1, 0, 1),                   # LOADK r1 1.0
            ins(1, 2, 0, 2),                   # LOADK r2 3.0
            ins(1, 3, 0, 3),                   # LOADK r3 1.0
            ins(32, 1, 0, 2 + 131071),         # FORPREP r1 -> FORLOOP
            ins(1, 5, 0, 0),                   # LOADK r5 "v"
            ins(9, 0, 4, 5),                   # r0[r4] = r5
            ins(31, 1, 0, -3 + 131071),        # FORLOOP r1 -> body
            ins(7, 0, 0, 4),                   # SETGLOBAL r0 "T"
            ins(30),                           # RETURN
        ]
        data = chunk(instructions, ['v', 1.0, 3.0, 1.0, 'T'])
        self.assertEqual(lua_data.decode_global(data, 'T'),
                         {1: 'v', 2: 'v', 3: 'v'})

    def test_generic_for_with_pairs(self):
        instructions = [
            ins(10, 0),                        # NEWTABLE r0
            ins(1, 2, 0, 0),                   # LOADK r2 "a"
            ins(1, 3, 0, 1),                   # LOADK r3 1.0
            ins(9, 0, 2, 3),                   # r0["a"] = 1.0
            ins(1, 2, 0, 2),                   # LOADK r2 "b"
            ins(1, 3, 0, 3),                   # LOADK r3 2.0
            ins(9, 0, 2, 3),                   # r0["b"] = 2.0
            ins(10, 7),                        # NEWTABLE r7
            ins(5, 1, 0, 4),                   # GETGLOBAL r1 "pairs"
            ins(0, 2, 0, 0),                   # MOVE r2 r0
            ins(28, 1, 2, 4),                  # CALL r1 2 4
            ins(22, 0, 0, 1 + 131071),         # JMP -> TFORLOOP
            ins(9, 7, 4, 5),                   # r7[r4] = r5
            ins(33, 1, 0, 2),                  # TFORLOOP r1 2
            ins(22, 0, 0, -3 + 131071),        # JMP -> body
            ins(7, 7, 0, 5),                   # SETGLOBAL r7 "Out"
            ins(30),                           # RETURN
        ]
        data = chunk(instructions, ['a', 1.0, 'b', 2.0, 'pairs', 'Out'])
        self.assertEqual(lua_data.decode_chunk(data, allow_closures=True)['Out'],
                         {'a': 1.0, 'b': 2.0})

    def test_closure_call_and_upvalue_binding(self):
        concat = function([ins(21, 2, 0, 1), ins(30, 2, 2)], [], params=2)
        upvalue = function([ins(4, 0, 0, 0), ins(30, 0, 2)], [], nups=1)
        instructions = [
            ins(10, 1),                        # NEWTABLE r1
            ins(36, 0, 0, 0),                  # CLOSURE r0 proto 0
            ins(1, 1, 0, 1),                   # LOADK r1 "a"
            ins(1, 2, 0, 2),                   # LOADK r2 "b"
            ins(28, 0, 3, 2),                  # CALL r0 3 2
            ins(7, 0, 0, 0),                   # SETGLOBAL r0 "F"
            ins(10, 1),                        # NEWTABLE r1
            ins(36, 0, 0, 1),                  # CLOSURE r0 proto 1 (1 upvalue)
            ins(0, 0, 1, 0),                   # upvalue 0 = r1
            ins(28, 0, 1, 2),                  # CALL r0 1 2
            ins(7, 0, 0, 3),                   # SETGLOBAL r0 "G"
            ins(30),                           # RETURN
        ]
        data = chunk(instructions, ['F', 'a', 'b', 'G'],
                     protos=(concat, upvalue))
        values = lua_data.decode_chunk(data, allow_closures=True)
        self.assertEqual(values['F'], 'ab')
        self.assertEqual(values['G'], {})

    def test_rejects_non_data_chunks(self):
        with self.assertRaises(lua_data.LuaDataError):
            lua_data.decode_chunk(b'not a chunk')
        data = chunk([ins(10, 0), ins(12, 0, 1, 2), ins(30)], [])
        with self.assertRaises(lua_data.LuaDataError):
            lua_data.decode_global(data, 'T')


def sample_world():
    towns = {
        'Town1': {
            'Pos': {1: 100.0, 2: 0.0, 3: 200.0},
            'Rot': 90.0,
            'Houses': {
                'H1': {
                    'Pos': {1: 10.0, 2: 0.0, 3: 0.0},
                    'Rot': 0.0,
                    'Npcs': {1: {1: 'npc_a', 2: {1: 1.0, 2: 0.0, 3: 0.0}, 3: 0.0, 4: 1}},
                    'Objs': {1: {1: 'chair', 3: {1: -1.0, 2: 0.0, 3: 0.0}, 4: 0.0,
                                 5: {1: 1.0, 2: 1.0, 3: 1.0}}},
                    'Trees': {1: {1: 'oak', 2: {1: 0.0, 2: 0.0, 3: 5.0}, 3: 1.5}},
                },
            },
        },
    }
    modules = {'towns': towns, 'npcs': {'npc_a': {}},
               'armies': {'aGuard': world.make_army('Guard', 'Neutral', 'stSamael',
                                                    [('uGuard', 2)])},
               'armypos': {'aGuard': {'x': 1.0, 'z': 2.0, 'radius': 10.0}}}
    entry = {
        'modules': modules,
        'sources': {name: {'emitted_sha256': world.hash_emitted(world.MODULES[name][1], table)}
                    for name, table in modules.items()},
    }
    return world.World({1: entry})


class WorldTest(unittest.TestCase):
    def test_transform_and_move(self):
        data = sample_world()
        placement = data.placement(1, 'Town1', 'H1', 'npc', 1)
        self.assertEqual(placement.local_xz, (1.0, 0.0))
        self.assertAlmostEqual(placement.world_xz[0], 100.0)
        self.assertAlmostEqual(placement.world_xz[1], 211.0)
        record = placement.record()
        self.assertEqual(record['id'], 'c1/Town1/H1/npc/1')
        self.assertAlmostEqual(record['world'][2], 211.0)
        data.move_world(1, 'Town1', 'H1', 'npc', 1, x=110.0, z=211.0)
        self.assertAlmostEqual(placement.world_xz[0], 110.0)
        self.assertAlmostEqual(placement.world_xz[1], 211.0)
        self.assertAlmostEqual(placement.position[1], 1.0)
        self.assertAlmostEqual(placement.position[3], -10.0)

    def test_placements_and_validation(self):
        data = sample_world()
        kinds = [(item.kind, item.index) for item in data.placements(1)]
        self.assertEqual(kinds, [('npc', 1), ('object', 1), ('tree', 1)])
        self.assertEqual(data.validate(1), [])
        data.module(1, 'npcs').clear()
        issues = data.validate(1)
        self.assertIn('undefined-npc', [issue['kind'] for issue in issues])

    def test_changed_modules_and_export(self):
        data = sample_world()
        self.assertEqual(data.changed_modules(), {})
        data.move_local(1, 'Town1', 'H1', 'tree', 1, x=2.0)
        self.assertEqual(list(data.changed_modules()), [(1, 'towns')])
        entries = data.export_entries()
        self.assertEqual(list(entries), ['continent1towns.lua'])
        loaded = lua_data.load_module(entries['continent1towns.lua'], 'Town')
        self.assertAlmostEqual(loaded['Town1']['Houses']['H1']['Trees'][1][2][1], 2.0)
        with tempfile.TemporaryDirectory() as folder:
            path, written = data.export_pak(folder, slot=3)
            self.assertEqual(os.path.basename(path), 'Resource3.pak')
            archive_set = gres.ArchiveSet.open_folder(folder)
            try:
                self.assertEqual(archive_set.read('continent1towns.lua'), entries['continent1towns.lua'])
            finally:
                archive_set.close()
        with self.assertRaises(world.WorldError):
            sample_world().export_pak('/tmp')

    def test_export_stamps_build_identity(self):
        data = sample_world()
        base = {}
        for name, source in data.continents[1]['sources'].items():
            source['file'] = world.MODULES[name][0] % 1
            global_name = world.MODULES[name][1]
            base[source['file']] = lua_data.emit_source(
                {global_name: data.module(1, name)}, order=[global_name])
        data.move_local(1, 'Town1', 'H1', 'tree', 1, x=2.0)
        with tempfile.TemporaryDirectory() as folder:
            game = os.path.join(folder, 'game')
            out = os.path.join(folder, 'out')
            os.makedirs(game)
            os.makedirs(out)
            gres.write_pak(os.path.join(game, 'Resource0.pak'), base)
            with gres.ArchiveSet.open_folder(game) as archive_set:
                expected = gres.file_identity(archive_set, data.identity_files())
                path, _ = data.export_pak(out, archive_set=archive_set)
            self.assertEqual(gres.read_identity(path), expected)
            self.assertEqual(set(expected['files']), set(base))
            with gres.ArchiveSet.open_folder(game) as archive_set:
                self.assertEqual(gres.check_overlay(path, archive_set), (expected, []))

    def test_export_slot_skips_existing_archives(self):
        data = sample_world()
        data.move_local(1, 'Town1', 'H1', 'tree', 1, x=2.0)
        with tempfile.TemporaryDirectory() as folder:
            for number in (0, 1, 2):
                open(os.path.join(folder, 'Resource%d.pak' % number), 'wb').close()
            path, _ = data.export_pak(folder)
            self.assertEqual(os.path.basename(path), 'Resource3.pak')
            with self.assertRaises(FileExistsError):
                data.export_pak(folder, slot=2)
            path, _ = data.export_pak(folder, slot=2, overwrite=True)
            self.assertEqual(os.path.basename(path), 'Resource2.pak')

    def test_json_round_trip(self):
        data = sample_world()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'world.json')
            data.save_json(path)
            loaded = world.World.load_json(path)
        self.assertEqual(world.canonical(loaded.document()), world.canonical(data.document()))
        tree = loaded.placement(1, 'Town1', 'H1', 'tree', 1)
        self.assertAlmostEqual(tree.world_xz[0], 95.0)
        self.assertAlmostEqual(tree.world_xz[1], 210.0)

    def test_army_positions_and_move(self):
        data = sample_world()
        entry = data.army_position(1, 'aGuard')
        self.assertEqual(entry, {'x': 1.0, 'z': 2.0, 'radius': 10.0})
        moved = data.move_army(1, 'aGuard', x=30.0, z=-40.0, radius=5.0)
        self.assertEqual(moved, {'x': 30.0, 'z': -40.0, 'radius': 5.0})
        self.assertIn((1, 'armypos'), data.changed_modules())
        self.assertEqual(data.validate(1), [])
        with self.assertRaises(world.WorldError):
            data.move_army(1, 'missing', x=0.0)
        with self.assertRaises(world.WorldError):
            data.move_army(1, 'aGuard', radius=-1.0)
        with self.assertRaises(world.WorldError):
            data.move_army(1, 'aGuard', x=float('nan'))

    def test_add_remove_armies_and_towns(self):
        data = sample_world()
        army = data.add_army(1, 'aNew', world.make_army(
            'New', 'Neutral', 'stVagrant', [('uWolf', 2), ('uOgre', 1)]))
        self.assertEqual(army['TroopList'][1], {'Unit': 'uWolf', 'Quantity': 2.0})
        self.assertEqual(data.validate(1), [])
        with self.assertRaises(world.WorldError):
            data.add_army(1, 'aNew')
        with self.assertRaises(world.WorldError):
            world.make_army(attitude='Friendly')
        with self.assertRaises(world.WorldError):
            world.make_army(troops=[('uWolf', 0)])
        data.add_army(1, 'aEmpty')
        data.add_army(1, 'aPlaced', x=5.0, z=6.0, radius=7.0)
        self.assertEqual(data.army_position(1, 'aPlaced'),
                         {'x': 5.0, 'z': 6.0, 'radius': 7.0})
        with self.assertRaises(world.WorldError):
            data.add_army(1, 'aPartial', x=1.0)
        self.assertEqual(data.army_positions(1).get('aNew'), None)
        data.module(1, 'armypos')['aNew'] = {'x': 0.0, 'z': 0.0, 'radius': 1.0}
        removed = data.remove_army(1, 'aNew')
        self.assertEqual(removed['army']['Attitude'], 'Neutral')
        self.assertEqual(removed['position']['radius'], 1.0)
        self.assertNotIn('aNew', data.army_positions(1))
        self.assertEqual(data.validate(1), [])
        with self.assertRaises(world.WorldError):
            data.remove_army(1, 'aNew')
        with self.assertRaises(world.WorldError):
            data.remove_house(1, 'Town1', 'H1')
        with self.assertRaises(world.WorldError):
            data.remove_town(1, 'Town1')
        empty = data.add_house(1, 'Town1', 'Empty', 0, 0, 0)
        self.assertEqual(data.remove_house(1, 'Town1', 'Empty'), empty)
        self.assertEqual(data.remove_town(1, 'Town1', force=True)['Rot'], 90.0)
        self.assertEqual(data.towns(1), {})
        data.module(1, 'armies')['aEmpty'] = {'Attitude': 'Neutral'}
        self.assertIn('bad-army-trooplist',
                      [issue['kind'] for issue in data.validate(1)])

    def test_add_remove_clone_placements(self):
        data = sample_world()
        tree = world.make_tree('oak', 0.0, 0.0, -5.0, rotation=45.0)
        placement = data.add_placement(1, 'Town1', 'H1', 'tree', tree)
        self.assertEqual(placement.index, 2)
        self.assertAlmostEqual(placement.world_xz[0], 105.0)
        self.assertAlmostEqual(placement.world_xz[1], 210.0)
        self.assertEqual(data.placement(1, 'Town1', 'H1', 'tree', 2).entry[3], 45.0)
        with self.assertRaises(world.WorldError):
            data.add_placement(1, 'Town1', 'H1', 'tree', tree, index=2)
        with self.assertRaises(world.WorldError):
            data.add_placement(1, 'Town1', 'H1', 'tree', {1: 'oak'})
        clone = data.clone_placement(1, 'Town1', 'H1', 'tree', 1, index_new=7)
        self.assertEqual(clone.index, 7)
        self.assertIsNot(clone.entry, data.placement(1, 'Town1', 'H1', 'tree', 1).entry)
        data.move_world(1, 'Town1', 'H1', 'tree', 7, x=120.0, z=220.0)
        self.assertAlmostEqual(data.placement(1, 'Town1', 'H1', 'tree', 7).world_xz[0], 120.0)
        self.assertAlmostEqual(data.placement(1, 'Town1', 'H1', 'tree', 1).world_xz[0], 95.0)
        removed = data.remove_placement(1, 'Town1', 'H1', 'tree', 2)
        self.assertEqual(removed[1], 'oak')
        with self.assertRaises(world.WorldError):
            data.remove_placement(1, 'Town1', 'H1', 'tree', 2)

    def test_local_from_world_and_rotation(self):
        data = sample_world()
        local_x, local_z = data.local_from_world(1, 'Town1', 'H1', 120.0, 220.0)
        self.assertAlmostEqual(local_x, 10.0)
        self.assertAlmostEqual(local_z, -20.0)
        data.set_rotation(1, 'Town1', 'H1', 'npc', 1, 90.0)
        self.assertEqual(data.placement(1, 'Town1', 'H1', 'npc', 1).entry[3], 90.0)
        data.set_rotation(1, 'Town1', 'H1', 'object', 1, 45.0)
        self.assertEqual(data.placement(1, 'Town1', 'H1', 'object', 1).entry[4],
                         {1: 0.0, 2: 45.0, 3: 0.0})
        entry = world.make_object('Altar', 0.0, 0.0, 0.0, rotation=90.0, scale=2.0,
                                  group='Objects02')
        self.assertEqual(entry[2], {1: 'AltarGizmo', 2: 'Objects02', 3: 'medium'})
        self.assertEqual(entry[4], {1: 0.0, 2: 90.0, 3: 0.0})
        self.assertEqual(entry[5], {1: 2.0, 2: 2.0, 3: 2.0})
        self.assertEqual(entry[8], 'Objects02')
        self.assertNotIn(2, world.make_object('SteelbergTrainer', 0.0, 0.0, 0.0, gizmo=''))

    def test_snap_placements(self):
        width = height = 51
        data = struct.pack('<4i', width, height, 0, 0)
        data += struct.pack('<%dH' % (width * height), *([40000] * (width * height)))
        data += struct.pack('<2f', 80.0, -300.0)
        map_ = heightmap.Heightmap(data)
        world_data = sample_world()
        world_data.add_placement(1, 'Town1', 'H1', 'tree',
                                 world.make_tree('oak', 1000.0, 0.0, 0.0))
        changed, skipped = world_data.snap_placements(1, map_, offset=2.5, dry_run=True)
        self.assertEqual(len(changed), 3)
        self.assertEqual(len(skipped), 1)
        self.assertAlmostEqual(changed[0]['elevation'], 200.0)
        self.assertEqual(world_data.placement(1, 'Town1', 'H1', 'tree', 1).position[2], 0.0)
        changed, _ = world_data.snap_placements(1, map_, offset=2.5)
        self.assertEqual(len(changed), 3)
        self.assertAlmostEqual(world_data.placement(1, 'Town1', 'H1', 'tree', 1).position[2], 2.5)
        changed, skipped = world_data.snap_placements(1, map_, town='Missing')
        self.assertEqual((changed, skipped), ([], []))

    def test_validate_assets_and_army_positions(self):
        class Archives:
            def __init__(self, names):
                self.names = set(names)

            def has(self, name):
                return name in self.names

        data = sample_world()
        issues = data.validate(1, Archives({'chair.gdl', 'chairgizmo.gdl'}))
        self.assertEqual([issue['kind'] for issue in issues],
                         ['missing-model', 'missing-standard'])
        issues = data.validate(1, Archives({'chair.gdl', 'chairgizmo.gdl', 'oak.gdl',
                                            'standardsamael.lskm'}))
        self.assertEqual(issues, [])
        data.add_army(1, 'aUnits', world.make_army(troops=[('uWolf', 1)]))
        issues = data.validate(1, None, {'uGuard': {}})
        self.assertEqual([issue['kind'] for issue in issues], ['missing-unit'])
        self.assertEqual(data.validate(1, None, {'uWolf': {}, 'uGuard': {}}), [])
        data.army_position(1, 'aGuard')['radius'] = -5.0
        issues = data.validate(1, None, {'uWolf': {}, 'uGuard': {}})
        self.assertEqual([issue['kind'] for issue in issues], ['bad-army-position'])

    def test_apply_patch(self):
        data = sample_world()
        document = {
            'format': world.PATCH_FORMAT,
            'operations': [
                {'op': 'move', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'npc', 'index': 1, 'x': 2.0, 'z': 1.0},
                {'op': 'add', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'tree', 'name': 'oak', 'x': 120.0, 'z': 220.0, 'world': True,
                 'rot': 30.0, 'index': 5},
                {'op': 'clone', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'tree', 'index': 1, 'index_new': 8, 'x': 130.0, 'z': 230.0,
                 'world': True},
                {'op': 'rotate', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'object', 'index': 1, 'rot': 90.0},
                {'op': 'move-army', 'continent': 1, 'name': 'aGuard', 'x': 7.0,
                 'radius': 3.0},
                {'op': 'remove', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'npc', 'index': 1},
            ],
        }
        results = world.apply_patch(data, document)
        self.assertEqual([result.get('id') for result in results[:2]],
                         ['c1/Town1/H1/npc/1', 'c1/Town1/H1/tree/5'])
        self.assertAlmostEqual(results[0]['local'][0], 2.0)
        self.assertAlmostEqual(results[0]['local'][2], 1.0)
        with self.assertRaises(world.WorldError):
            data.placement(1, 'Town1', 'H1', 'npc', 1)
        added = data.placement(1, 'Town1', 'H1', 'tree', 5)
        self.assertAlmostEqual(added.world_xz[0], 120.0)
        self.assertAlmostEqual(added.world_xz[1], 220.0)
        self.assertEqual(added.entry[3], 30.0)
        clone_ = data.placement(1, 'Town1', 'H1', 'tree', 8)
        self.assertAlmostEqual(clone_.world_xz[0], 130.0)
        self.assertAlmostEqual(clone_.world_xz[1], 230.0)
        self.assertEqual(data.placement(1, 'Town1', 'H1', 'object', 1).entry[4][2], 90.0)
        self.assertEqual(data.army_position(1, 'aGuard'),
                         {'x': 7.0, 'z': 2.0, 'radius': 3.0})
        self.assertEqual(set(data.changed_modules()), {(1, 'towns'), (1, 'armypos')})

    def test_add_town_and_house(self):
        data = sample_world()
        data.add_town(1, 'Town2', 0.0, 0.0, 0.0, rotation=45.0)
        data.add_house(1, 'Town2', 'H1', 5.0, 0.0, 5.0, rotation=90.0)
        placement = data.add_placement(1, 'Town2', 'H1', 'tree',
                                       world.make_tree('oak', 0.0, 0.0, 0.0))
        self.assertAlmostEqual(placement.world_xz[0], 0.0)
        self.assertAlmostEqual(placement.world_xz[1], 2 ** 0.5 * 5.0)
        self.assertIn((1, 'towns'), data.changed_modules())
        self.assertEqual(data.validate(1), [])
        with self.assertRaises(world.WorldError):
            data.add_town(1, 'Town2', 0.0, 0.0, 0.0)
        with self.assertRaises(world.WorldError):
            data.add_town(1, 'Bad', float('nan'), 0.0, 0.0)
        with self.assertRaises(world.WorldError):
            data.add_house(1, 'Town2', 'H1', 0.0, 0.0, 0.0)
        with self.assertRaises(world.WorldError):
            data.add_house(1, 'Missing', 'H1', 0.0, 0.0, 0.0)
        with self.assertRaises(world.WorldError):
            data.add_house(1, 'Town2', 'H2', 0.0, 0.0, 0.0, sections={'Objs': []})

    def test_apply_patch_town_house(self):
        data = sample_world()
        results = world.apply_patch(data, {'operations': [
            {'op': 'add-town', 'continent': 1, 'name': 'Town2', 'x': 0.0, 'z': 0.0,
             'rot': 45.0},
            {'op': 'add-house', 'continent': 1, 'town': 'Town2', 'name': 'H1',
             'x': 5.0, 'z': 5.0, 'rot': 90.0},
            {'op': 'add', 'continent': 1, 'town': 'Town2', 'house': 'H1',
             'kind': 'tree', 'name': 'oak', 'x': 0.0, 'z': 0.0},
        ]})
        self.assertEqual(results[0]['name'], 'Town2')
        self.assertEqual(results[1]['name'], 'H1')
        self.assertEqual(results[2]['id'], 'c1/Town2/H1/tree/1')
        self.assertEqual(set(data.changed_modules()), {(1, 'towns')})

    def test_apply_patch_snap_and_errors(self):
        width = height = 51
        data = struct.pack('<4i', width, height, 0, 0)
        data += struct.pack('<%dH' % (width * height), *([40000] * (width * height)))
        data += struct.pack('<2f', 80.0, -300.0)
        map_ = heightmap.Heightmap(data)
        world_data = sample_world()
        results = world.apply_patch(world_data, {'operations': [
            {'op': 'snap', 'continent': 1, 'town': 'Town1', 'house': 'H1',
             'offset': 1.0, 'limit': 2}]}, {1: map_})
        self.assertEqual(results[0]['changed'], 3)
        self.assertEqual(len(results[0]['placements']), 2)
        self.assertAlmostEqual(world_data.placement(1, 'Town1', 'H1', 'tree', 1).position[2], 1.0)
        with self.assertRaises(world.WorldError):
            world.apply_patch(world_data, {'operations': [{'op': 'bogus'}]})
        with self.assertRaises(world.WorldError):
            world.apply_patch(world_data, {'operations': [{'op': 'snap', 'continent': 1}]}, {})
        with self.assertRaises(world.WorldError):
            world.apply_patch(world_data, {'format': 'wrong', 'operations': []})
        with self.assertRaises(world.WorldError):
            world.apply_patch(world_data, {'operations': [
                {'op': 'move', 'continent': 1, 'town': 'Town1', 'house': 'H1',
                 'kind': 'tree', 'index': 1}]})

    def test_apply_patch_towns_and_armies(self):
        data = sample_world()
        results = world.apply_patch(data, {'operations': [
            {'op': 'add-army', 'continent': 1, 'name': 'aPatch', 'attitude': 'Neutral',
             'standard': 'stVagrant', 'troops': [['uWolf', 3]],
             'x': 4.0, 'z': 5.0, 'radius': 9.0},
            {'op': 'add-town', 'continent': 1, 'name': 'NewTown', 'x': 0.0, 'z': 0.0},
            {'op': 'add-house', 'continent': 1, 'town': 'NewTown', 'name': 'H1',
             'x': 0.0, 'z': 0.0},
            {'op': 'add', 'continent': 1, 'town': 'NewTown', 'house': 'H1',
             'kind': 'tree', 'name': 'oak', 'x': 0.0, 'z': 0.0},
            {'op': 'remove-house', 'continent': 1, 'town': 'NewTown', 'name': 'H1',
             'force': True},
            {'op': 'remove-town', 'continent': 1, 'name': 'NewTown'},
            {'op': 'remove-army', 'continent': 1, 'name': 'aGuard'},
            {'op': 'remove-army', 'continent': 1, 'name': 'aPatch'},
        ]})
        self.assertEqual(results[0]['entry']['TroopList']['1']['Unit'], 'uWolf')
        self.assertEqual(results[0]['position'], {'x': 4.0, 'z': 5.0, 'radius': 9.0})
        self.assertEqual(results[4]['name'], 'H1')
        self.assertEqual(results[6]['position']['radius'], 10.0)
        self.assertEqual(list(data.towns(1)), ['Town1'])
        self.assertEqual(data.army_positions(1), {})
        self.assertEqual(data.module(1, 'armies'), {})
        self.assertEqual(data.validate(1), [])


class WorldServerTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, 'world.json')
        sample_world().save_json(self.path)
        self.server = worldserve.Server(('127.0.0.1', 0), self.path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:%d' % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.state.close()
        self.folder.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as response:
            return response.status, response.headers.get_content_type(), response.read()

    def request(self, path, body):
        request = urllib.request.Request(
            self.base + path, data=json.dumps(body).encode('utf-8'),
            headers={'content-type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_read_endpoints(self):
        status, content_type, body = self.get('/')
        self.assertEqual((status, content_type), (200, 'text/html'))
        self.assertIn(b'AttT world preview', body)
        status, _, body = self.get('/world.json')
        self.assertEqual(status, 200)
        self.assertIn('continents', json.loads(body))
        status, _, body = self.get('/entities.json')
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)['continents']['1']), 3)
        status, _, body = self.get('/validate/1.json')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['issues'], [])
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get('/map/1.svg')
        self.assertEqual(caught.exception.code, 404)
        caught.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get('/validate/9.json')
        self.assertEqual(caught.exception.code, 404)
        caught.exception.close()

    def test_patch_dry_run_apply_and_save(self):
        operation = {'format': world.PATCH_FORMAT, 'operations': [
            {'op': 'move', 'continent': 1, 'town': 'Town1', 'house': 'H1',
             'kind': 'npc', 'index': 1, 'x': 2.0, 'z': 0.0}]}
        status, result = self.request('/patch?dry_run=1', operation)
        self.assertEqual(status, 200)
        self.assertTrue(result['dry_run'])
        self.assertTrue(result['changes'])
        self.assertFalse(result['saved'])
        _, _, body = self.get('/world.json')
        self.assertEqual(json.loads(body)['continents']['1']['modules']['towns']
                         ['Town1']['Houses']['H1']['Npcs']['1']['2']['1'], 1.0)
        status, result = self.request('/patch?dry_run=0&save=1', operation)
        self.assertEqual((status, result['saved']), (200, True))
        _, _, body = self.get('/world.json')
        self.assertEqual(json.loads(body)['continents']['1']['modules']['towns']
                         ['Town1']['Houses']['H1']['Npcs']['1']['2']['1'], 2.0)
        saved = world.World.load_json(self.path)
        self.assertAlmostEqual(saved.placement(1, 'Town1', 'H1', 'npc', 1).position[1], 2.0)
        status, result = self.request('/patch?dry_run=1', {'operations': [{'op': 'bogus'}]})
        self.assertEqual(status, 400)
        self.assertIn('operation 1 (bogus)', result['error'])


class CliTest(unittest.TestCase):
    def test_heightmap_issues_cover_towns_and_armies(self):
        data = sample_world()
        width = height = 101
        raw = struct.pack('<4i', width, height, -100, -100)
        raw += struct.pack('<%dH' % (width * height), *([40000] * (width * height)))
        raw += struct.pack('<2f', 80.0, -300.0)
        map_ = heightmap.Heightmap(raw)
        issues = worldctl.heightmap_issues(data, 1, map_, water=300.0)
        self.assertEqual([issue['entity'] for issue in issues],
                         ['placement'] * 3 + ['town', 'army'])
        self.assertEqual([issue['kind'] for issue in issues], ['below-water'] * 5)
        data.army_position(1, 'aGuard')['x'] = 1000.0
        issues = worldctl.heightmap_issues(data, 1, map_, water=300.0)
        self.assertIn(('army', 'outside-heightmap'),
                      [(issue['entity'], issue['kind']) for issue in issues])
        self.assertEqual(len(issues), 5)
        self.assertEqual(worldctl.heightmap_issues(data, 1, map_), [
            {'entity': 'army', 'name': 'aGuard', 'world': [1000.0, 2.0],
             'level': 'warning', 'kind': 'outside-heightmap'}])

    def test_move_flag_does_not_shadow_model_path(self):
        parser = worldctl.build_parser()
        base = ['move', 'model.json', '--continent', '1', '--town', 'T', '--house', 'H',
                '--kind', 'npc', '--index', '1', '--x', '1', '--z', '2']
        args = parser.parse_args(base)
        self.assertEqual(args.world, 'model.json')
        self.assertFalse(args.world_coords)
        args = parser.parse_args(base + ['--world'])
        self.assertEqual(args.world, 'model.json')
        self.assertTrue(args.world_coords)

    def test_edit_command_parsers(self):
        parser = worldctl.build_parser()
        args = parser.parse_args(['add', 'model.json', '--continent', '1', '--town', 'T',
                                  '--house', 'H', '--kind', 'object', '--name', 'Altar',
                                  '--x', '1', '--y', '2', '--z', '3', '--world'])
        self.assertEqual(args.world, 'model.json')
        self.assertTrue(args.world_coords)
        self.assertEqual(args.scale, 1.0)
        args = parser.parse_args(['clone', 'model.json', '--continent', '1', '--town', 'T',
                                  '--house', 'H', '--kind', 'tree', '--index', '1',
                                  '--index-new', '9', '--x', '10', '--z', '20', '--world'])
        self.assertEqual(args.index_new, 9)
        self.assertTrue(args.world_coords)
        args = parser.parse_args(['move-army', 'model.json', '--continent', '2', '--name', 'a1',
                                  '--x', '4', '--radius', '50'])
        self.assertEqual((args.continent, args.name, args.x, args.radius), (2, 'a1', 4.0, 50.0))
        args = parser.parse_args(['remove', 'model.json', '--continent', '1', '--town', 'T',
                                  '--house', 'H', '--kind', 'npc', '--name', 'npc_a'])
        self.assertEqual((args.kind, args.name), ('npc', 'npc_a'))
        args = parser.parse_args(['snap', 'model.json', '--game', 'g', '--continent', '1',
                                  '--dry-run'])
        self.assertTrue(args.dry_run)
        args = parser.parse_args(['patch', 'model.json', 'ops.json', '--game', 'g',
                                  '--dry-run'])
        self.assertEqual((args.patch, args.game, args.dry_run), ('ops.json', 'g', True))
        args = parser.parse_args(['add-army', 'model.json', '--continent', '1',
                                  '--name', 'a1', '--attitude', 'Neutral',
                                  '--troop', 'uWolf:3', '--troop', 'uOgre:1'])
        self.assertEqual((args.name, args.attitude, args.troop),
                         ('a1', 'Neutral', ['uWolf:3', 'uOgre:1']))
        args = parser.parse_args(['remove-army', 'model.json', '--continent', '1',
                                  '--name', 'a1'])
        self.assertEqual(args.name, 'a1')
        args = parser.parse_args(['remove-town', 'model.json', '--continent', '1',
                                  '--name', 'T', '--force'])
        self.assertTrue(args.force)
        args = parser.parse_args(['remove-house', 'model.json', '--continent', '1',
                                  '--town', 'T', '--name', 'H'])
        self.assertFalse(args.force)


if __name__ == '__main__':
    unittest.main()
