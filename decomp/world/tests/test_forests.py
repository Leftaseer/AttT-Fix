"""Unit tests for forest zones (.fst) and the forest CLI (no game needed)."""
import json
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import forests
import gres
import heightmap
import lua_data
import render
import worldctl


def sample_level():
    return {
        'Forest': {
            1: {
                1: {1: 'fZone1Test', 2: 'SetTest', 3: 1.0, 4: 10.0, 5: 20.0,
                    6: {1: 'Pine101', 2: 10.0, 3: 'Oak101', 4: 5.0}},
            },
        },
        'TreesProperties': {
            'SetTest': {
                1: {1: 'Pine101', 2: 1.0, 3: 2.0, 4: 3.0, 5: 4.0, 6: 5.0},
                2: {1: 'Oak101', 2: 6.0, 3: 7.0, 4: 8.0, 5: 9.0, 6: 10.0},
            },
        },
    }


def sample_records():
    return [
        forests.make_record(0, 10.0, 100.0, 20.0, yaw=90.0, scale=2.0),
        forests.make_record(1, 30.0, 50.0, 40.0),
    ]


def fake_heightmap(value=100.0):
    width, height = 4, 4
    data = struct.pack('<4i', width, height, 0, 0)
    data += struct.pack('<%dH' % (width * height), *([1000] * (width * height)))
    data += struct.pack('<2f', 10.0, 0.0)
    return heightmap.Heightmap(data)


class FstTest(unittest.TestCase):
    def test_record_roundtrip(self):
        records = sample_records()
        data = forests.build_fst(records)
        self.assertEqual(len(data), 2 * forests.RECORD_SIZE)
        parsed = forests.parse_fst(data)
        self.assertEqual(forests.build_fst(parsed), data)
        self.assertEqual([record['type'] for record in parsed], [0, 1])
        self.assertEqual([(record['x'], record['y'], record['z']) for record in parsed],
                         [(10.0, 100.0, 20.0), (30.0, 50.0, 40.0)])

    def test_matrix_helpers(self):
        record = forests.make_record(0, 0, 0, 0, yaw=90.0, scale=2.0, y_scale=3.0)
        parsed = forests.parse_fst(forests.build_fst([record]))[0]
        self.assertAlmostEqual(forests.matrix_yaw(parsed['matrix']), 90.0, places=4)
        self.assertAlmostEqual(forests.matrix_scale(parsed['matrix'])[0], 2.0, places=5)
        self.assertAlmostEqual(forests.matrix_scale(parsed['matrix'])[1], 3.0, places=5)
        self.assertAlmostEqual(parsed['matrix'][5], 3.0, places=5)

    def test_reject_bad_files(self):
        with self.assertRaises(forests.ForestError):
            forests.parse_fst(b'\0' * 10)
        bad = bytearray(forests.build_fst(sample_records()[:1]))
        struct.pack_into('<f', bad, 4 + 15 * 4, 0.5)
        with self.assertRaises(forests.ForestError):
            forests.parse_fst(bytes(bad))
        with self.assertRaises(forests.ForestError):
            forests.build_fst([{'type': 0, 'matrix': [0.0] * 11, 'x': 0, 'y': 0, 'z': 0}])
        with self.assertRaises(forests.ForestError):
            forests.make_record(-1, 0, 0, 0)

    def test_model_name(self):
        self.assertEqual(forests.tree_model('Dry101'), 'dry101.gdl')


class ForestConfigTest(unittest.TestCase):
    def test_types_are_zero_based(self):
        config = forests.ForestConfig(sample_level())
        self.assertEqual(config.zone(1, 'FZONE1TEST')['set'], 'SetTest')
        self.assertEqual(config.tree(1, 'fzone1test', 0)['model'], 'Pine101')
        self.assertEqual(config.tree(1, 'fzone1test', 1)['model'], 'Oak101')
        self.assertEqual(config.type_for_model(1, 'fzone1test', 'oak101.gdl'), 1)
        self.assertEqual(config.type_for_model(1, 'fzone1test', 'Pine101'), 0)
        self.assertEqual(config.models(1, 'fzone1test'), {0: 'Pine101', 1: 'Oak101'})
        with self.assertRaises(forests.ForestError):
            config.tree(1, 'fzone1test', 2)

    def test_snapshot_roundtrip(self):
        config = forests.ForestConfig(sample_level())
        restored = forests.ForestConfig.from_snapshot(config.snapshot())
        self.assertEqual(restored.tree(1, 'fzone1test', 1)['model'], 'Oak101')
        self.assertEqual(restored.zone(1, 'fzone1test')['trees'],
                         config.zone(1, 'fzone1test')['trees'])


class ForestModelTest(unittest.TestCase):
    def make(self):
        config = forests.ForestConfig(sample_level())
        data = forests.build_fst(sample_records())
        zones = {1: {'fzone1test': {
            'file': 'fzone1test.fst',
            'records': forests.parse_fst(data),
            'source': {'slot': 0, 'sha256': __import__('hashlib').sha256(data).hexdigest()},
        }}}
        return forests.Forests(config, zones, [{'slot': 0, 'path': 'Resource0.pak'}])

    def test_find(self):
        model = self.make()
        self.assertEqual([item['index'] for item in model.find(1, model='Oak101')], [1])
        self.assertEqual([item['index'] for item in model.find(1, type_id=0)], [0])
        near = model.find(1, x=10.0, z=20.0, radius=1.0)
        self.assertEqual([item['model'] for item in near], ['Pine101'])

    def test_add_move_remove(self):
        model = self.make()
        map_ = fake_heightmap()
        zone = model.zone(1, 'fzone1test')
        index, record = model.add(1, 'fzone1test', model='Pine101', x=5.0, z=5.0,
                                  heightmap=map_, yaw=45.0)
        self.assertEqual(index, 2)
        self.assertEqual(record['type'], 0)
        self.assertAlmostEqual(record['y'], 100.0)
        moved = model.move(1, 'fzone1test', index, x=6.0, z=8.0, ground=True, heightmap=map_)
        self.assertAlmostEqual(moved['x'], 6.0)
        self.assertAlmostEqual(moved['y'], 100.0)
        removed = model.remove(1, 'fzone1test', index)
        self.assertEqual(removed['type'], 0)
        self.assertEqual(len(zone['records']), 2)
        self.assertEqual(model.changed_zones(), {})
        with self.assertRaises(forests.ForestError):
            model.move(1, 'fzone1test', 99, x=1.0)
        with self.assertRaises(forests.ForestError):
            model.add(1, 'fzone1test', model='Nope', x=1.0, z=1.0, heightmap=map_)
        with self.assertRaises(forests.ForestError):
            model.add(1, 'fzone1test', model='Pine101', x=99.0, z=99.0, heightmap=map_)

    def test_changed_and_export(self):
        model = self.make()
        zone = model.zone(1, 'fzone1test')
        zone['records'][0]['x'] = 12.0
        self.assertEqual(list(model.changed_zones()), [(1, 'fzone1test')])
        entries = model.export_entries()
        self.assertEqual(list(entries), ['fzone1test.fst'])
        self.assertAlmostEqual(forests.parse_fst(entries['fzone1test.fst'])[0]['x'], 12.0)
        with tempfile.TemporaryDirectory() as tmp:
            destination, exported = model.export_pak(tmp)
            self.assertTrue(destination.endswith('Resource1.pak'))
            with gres.ArchiveSet([destination]) as archive_set:
                self.assertEqual(forests.parse_fst(archive_set.read('fzone1test.fst'))[0]['x'], 12.0)

    def test_json_roundtrip(self):
        model = self.make()
        zone = model.zone(1, 'fzone1test')
        zone['records'][1]['z'] = 45.0
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'forests.json')
            model.save_json(path)
            restored = forests.Forests.load_json(path)
            self.assertEqual(restored.zone(1, 'fzone1test')['records'][1]['z'], 45.0)
            self.assertEqual(restored.config.tree(1, 'fzone1test', 0)['model'], 'Pine101')

    def test_validate(self):
        class Names:
            def __init__(self, names):
                self._names = set(names)

            def has(self, name):
                return name in self._names

            def names(self):
                return iter(self._names)

        model = self.make()
        issues = model.validate(Names({'pine101.gdl', 'oak101.gdl'}))
        self.assertEqual(issues, [])
        issues = model.validate(Names(set()))
        self.assertEqual([issue['kind'] for issue in issues],
                         ['missing-model', 'missing-model'])
        issues = model.validate(heightmaps={1: fake_heightmap()})
        self.assertEqual({issue['kind'] for issue in issues}, {'outside-heightmap'})
        model.zone(1, 'fzone1test')['records'][0]['type'] = 7
        issues = model.validate()
        self.assertEqual(issues[0]['kind'], 'unknown-tree-type')
        model.config.continents[1]['missingzone'] = {
            'name': 'MissingZone', 'set': 'SetTest', 'scale': 1.0,
            'x': 0.0, 'z': 0.0, 'trees': []}
        issues = model.validate(Names({'pine101.gdl', 'oak101.gdl', 'stray.fst'}))
        kinds = [issue['kind'] for issue in issues]
        self.assertIn('unconfigured-zone', kinds)
        self.assertIn('missing-zone-file', kinds)


class RenderTest(unittest.TestCase):
    def test_forest_layer(self):
        class EmptyWorld:
            continents = {1: {'modules': {}, 'sources': {}}}

            def towns(self, continent):
                return {}

            def placements(self, continent, kinds=None):
                return []

        width, height = 12, 12
        data = struct.pack('<4i', width, height, 0, 0)
        data += struct.pack('<%dH' % (width * height), *([1000] * (width * height)))
        data += struct.pack('<2f', 10.0, 0.0)
        map_ = heightmap.Heightmap(data)
        zones = {1: {'fzone1test': {
            'file': 'fzone1test.fst',
            'records': forests.parse_fst(forests.build_fst(sample_records())),
            'source': {},
        }}}
        model = forests.Forests(forests.ForestConfig(sample_level()), zones)
        svg = render.render_svg(EmptyWorld(), 1, map_, size=200, show=('forest',),
                                forests=model)
        self.assertIn(render.COLORS['forest'], svg)
        self.assertIn('h0', svg)
        self.assertIn('2 trees', svg)


class ForestCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.temp.name, 'game')
        self.out = os.path.join(self.temp.name, 'out')
        os.makedirs(self.game)
        os.makedirs(self.out)
        level = sample_level()
        entries = {
            'worldlevel.lua': lua_data.emit_source({'WorldLevel': level}, order=['WorldLevel']),
            'continent1_heightmap.nmph': self.heightmap_bytes(),
            'fzone1test.fst': forests.build_fst(sample_records()),
            'pine101.gdl': b'model',
            'oak101.gdl': b'model',
        }
        gres.write_pak(os.path.join(self.game, 'Resource0.pak'), entries)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def heightmap_bytes():
        width, height = 4, 4
        data = struct.pack('<4i', width, height, 0, 0)
        data += struct.pack('<%dH' % (width * height), *([1000] * (width * height)))
        data += struct.pack('<2f', 10.0, 0.0)
        return data

    def test_extract_add_validate_export(self):
        document = os.path.join(self.out, 'forests.json')
        self.assertEqual(worldctl.main(['forest-extract', '--game', self.game,
                                        '--out', self.out]), 0)
        self.assertTrue(os.path.exists(document))
        self.assertEqual(worldctl.main(['forest-find', document, '--model', 'Oak101']), 0)
        self.assertEqual(worldctl.main(['forest-add', document, '--game', self.game,
                                        '--continent', '1', '--zone', 'fzone1test',
                                        '--model', 'Pine101', '--x', '5', '--z', '5']), 0)
        self.assertEqual(worldctl.main(['forest-validate', document, '--game', self.game]), 0)
        self.assertEqual(worldctl.main(['forest-export', document, '--game', self.game,
                                        '--out', self.out]), 0)
        overlay = os.path.join(self.out, 'Resource1.pak')
        self.assertTrue(os.path.exists(overlay))
        with gres.ArchiveSet([os.path.join(self.game, 'Resource0.pak'), overlay]) as archive_set:
            loaded = forests.Forests._from_set(archive_set, (1,))
            self.assertEqual(len(loaded.zone(1, 'fzone1test')['records']), 3)


if __name__ == '__main__':
    unittest.main()
