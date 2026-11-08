"""Bytecode literal patching tests (synthetic chunks, no game install)."""
import contextlib
import io
import json
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import gres
import lua_data
import lua_patch
import story
import worldctl


def ins(op, a=0, b=0, c=0):
    return op | (a << 6) | (c << 14) | (b << 23)


def string(value):
    raw = value.encode('cp1251')
    return struct.pack('<I', len(raw) + 1) + raw + b'\0'


def proto():
    """Empty nested function: enough to prove prototypes survive a patch."""
    return (string('') + struct.pack('<ii', 1, 2) + struct.pack('<4B', 0, 0, 0, 2) +
            struct.pack('<I', 0) + struct.pack('<I', 0) + struct.pack('<I', 0) +
            struct.pack('<I', 0) + struct.pack('<I', 0) + struct.pack('<I', 0))


def chunk(instructions, constants, stack=8, protos=(), lineinfo=None, locals_=()):
    out = bytearray(lua_data.HEADER)
    out += struct.pack('<I', 0)
    out += struct.pack('<ii', 1, 1)
    out += struct.pack('<4B', 0, 0, 0, stack)
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
    out += b''.join(protos)
    lineinfo = lineinfo or []
    out += struct.pack('<I', len(lineinfo))
    if lineinfo:
        out += struct.pack('<%di' % len(lineinfo), *lineinfo)
    out += struct.pack('<I', len(locals_))
    for name, startpc, endpc in locals_:
        out += string(name) + struct.pack('<ii', startpc, endpc)
    out += struct.pack('<I', 0)                       # upvalue names
    return bytes(out)


def quest_chunk(debug=False):
    """Quest = {q1 = {DisplayName='Old', Description='Old', Level=1.0}}"""
    instructions = [
        ins(10, 0),                                   # NEWTABLE r0
        ins(10, 1),                                   # NEWTABLE r1
        ins(1, 2, 0, 3),                              # LOADK r2 "Old"
        ins(9, 1, 256 + 2, 2),                        # r1.DisplayName = r2
        ins(1, 2, 0, 3),                              # LOADK r2 "Old"
        ins(9, 1, 256 + 6, 2),                        # r1.Description = r2
        ins(1, 2, 0, 5),                              # LOADK r2 1.0
        ins(9, 1, 256 + 4, 2),                        # r1.Level = r2
        ins(9, 0, 256 + 1, 1),                        # r0.q1 = r1
        ins(7, 0, 0, 0),                              # Quest = r0
        ins(30, 0, 1),                                # RETURN 0 1
    ]
    extra = {}
    if debug:
        extra = {'lineinfo': [7] * len(instructions),
                 'locals_': [('quest', 0, len(instructions))]}
    return chunk(instructions, ['Quest', 'q1', 'DisplayName', 'Old', 'Level',
                                1.0, 'Description'], protos=(proto(),), **extra)


def quest_values(data):
    return lua_data.decode_chunk(data, allow_closures=True)['Quest']['q1']


class LuaPatchTest(unittest.TestCase):
    def test_noop_rebuild_is_identical(self):
        data = quest_chunk()
        self.assertEqual(lua_patch.patch(data, []), data)

    def test_edit_literals_and_keep_shared_constant(self):
        data = quest_chunk()
        patched = lua_patch.patch(data, [
            (['Quest', 'q1', 'DisplayName'], 'New title'),
            (['Quest', 'q1', 'Level'], 42),
        ])
        values = quest_values(patched)
        self.assertEqual(values['DisplayName'], 'New title')
        self.assertEqual(values['Description'], 'Old')
        self.assertEqual(values['Level'], 42.0)
        before = lua_data.parse_chunk(data)
        after = lua_data.parse_chunk(patched)
        self.assertEqual(len(before['protos']), len(after['protos']))
        self.assertEqual(len(after['code']), len(before['code']) + 12)
        self.assertEqual(lua_patch.OPS[after['code'][-1] & 63], 'RETURN')

    def test_create_and_remove_fields(self):
        data = quest_chunk()
        patched = lua_patch.patch(data, [
            (['Quest', 'q1', 'Active'], True),
            (['Quest', 'q1', 'Description'], None),
        ])
        values = quest_values(patched)
        self.assertIs(values['Active'], True)
        self.assertNotIn('Description', values)
        self.assertEqual(values['DisplayName'], 'Old')

    def test_lineinfo_and_locals_follow_insertion(self):
        data = quest_chunk(debug=True)
        self.assertEqual(lua_patch.patch(data, []), data)
        patched = lua_patch.patch(data, [(['Quest', 'q1', 'Level'], 3)])
        layout = lua_patch._Layout(patched)
        self.assertEqual(len(layout.lineinfo), len(layout.code))
        self.assertEqual(set(layout.lineinfo), {7})
        self.assertEqual(layout.locals[0]['endpc'], len(layout.code))

    def test_rejects_wrong_types(self):
        editor = lua_patch.ChunkEditor(quest_chunk())
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'DisplayName'], 5)
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'Level'], 'high')
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'NewField'], {'nested': True})
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'Missing'], None)
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'nope', 'DisplayName'], 'x')

    def test_rejects_return_with_values(self):
        data = chunk([ins(30, 0, 2)], [])
        with self.assertRaises(lua_patch.LuaPatchError):
            lua_patch.ChunkEditor(data)

    def test_rejects_early_return(self):
        data = chunk([ins(30, 0, 1), ins(30, 0, 1)], [])
        with self.assertRaises(lua_patch.LuaPatchError):
            lua_patch.ChunkEditor(data)

    def test_non_latin1_string_fails(self):
        editor = lua_patch.ChunkEditor(quest_chunk())
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'DisplayName'], '日本語')


class StoryPatchTest(unittest.TestCase):
    def test_bytecode_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            gres.write_pak(os.path.join(tmp, 'Resource0.pak'),
                           {'continent1quests.lua': quest_chunk()})
            archives = gres.ArchiveSet.open_folder(tmp)
            try:
                patcher = story.StoryPatch(archives)
                patcher.add({'kind': 'quest', 'continent': 1, 'name': 'q1',
                             'field': 'display_name', 'value': 'Renamed'})
                patcher.add({'kind': 'quest', 'continent': 1, 'name': 'q1',
                             'field': 'level', 'value': 7})
                entries = patcher.documents()
                self.assertEqual(list(entries), ['continent1quests.lua'])
                values = quest_values(entries['continent1quests.lua'])
                self.assertEqual(values['DisplayName'], 'Renamed')
                self.assertEqual(values['Level'], 7.0)
                self.assertEqual(patcher.changes[0]['old'], 'Old')
            finally:
                archives.close()

    def test_missing_targets_report_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            gres.write_pak(os.path.join(tmp, 'Resource0.pak'),
                           {'continent1quests.lua': quest_chunk()})
            archives = gres.ArchiveSet.open_folder(tmp)
            try:
                patcher = story.StoryPatch(archives)
                cases = [
                    {'kind': 'quest', 'continent': 1, 'name': 'qNope',
                     'field': 'display_name', 'value': 'x'},
                    {'kind': 'quest', 'continent': 1, 'name': 'q1',
                     'field': 'condition', 'value': 'x'},
                    {'kind': 'dialogue', 'continent': 1, 'name': 'q1',
                     'path': 'root.1', 'field': 'speech', 'value': 'x'},
                ]
                for case in cases:
                    with self.assertRaises(story.StoryError):
                        patcher.add(case)
            finally:
                archives.close()


class StoryPatchCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.temp.name, 'game')
        self.out = os.path.join(self.temp.name, 'out')
        os.makedirs(self.game)
        os.makedirs(self.out)
        tables = {
            'quests': {'q1': {'DisplayName': 'Quest One', 'Description': 'Find it',
                              'Level': 2.0, 'SubQuest': {}}},
            'triggers': {'q1.sq.Start.trigger': {'WantLive': True,
                                                 'Condition': True, 'Action': False}},
            'dialogues': {'cIntro': {1: {'who': 'HERO', 'speech': 'Hello',
                                         'Condition': True,
                                         1: {'who': 'OWNER', 'speech': 'Hi'}}}},
        }
        entries = {
            'continent1quests.lua': lua_data.emit_source(
                {'Quest': tables['quests']}, order=['Quest']),
            'continent1triggers.lua': lua_data.emit_source(
                {'Trigger': tables['triggers']}, order=['Trigger']),
            'continent1conversations.lua': lua_data.emit_source(
                {'Dialog': tables['dialogues']}, order=['Dialog']),
        }
        gres.write_pak(os.path.join(self.game, 'Resource0.pak'), entries)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = worldctl.main(argv)
        return code, output.getvalue()

    def test_dry_run_does_not_write(self):
        patch = os.path.join(self.temp.name, 'patch.json')
        with open(patch, 'w', encoding='utf-8') as stream:
            json.dump({'format': story.PATCH_FORMAT, 'operations': [
                {'kind': 'quest', 'continent': 1, 'name': 'q1',
                 'field': 'display_name', 'value': 'Renamed'}]}, stream)
        code, output = self.run_cli(['story-patch', patch, '--game', self.game,
                                     '--dry-run'])
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertTrue(result['dry_run'])
        self.assertEqual(result['changes'][0]['new'], 'Renamed')
        self.assertEqual(os.listdir(self.out), [])

    def test_apply_all_kinds_and_value_file(self):
        text = os.path.join(self.temp.name, 'line.txt')
        with open(text, 'w', encoding='utf-8') as stream:
            stream.write('A longer welcome')
        patch = os.path.join(self.temp.name, 'patch.json')
        with open(patch, 'w', encoding='utf-8') as stream:
            json.dump({'format': story.PATCH_FORMAT, 'operations': [
                {'kind': 'quest', 'continent': 1, 'name': 'q1',
                 'field': 'level', 'value': 9},
                {'kind': 'trigger', 'continent': 1, 'name': 'q1.sq.Start.trigger',
                 'field': 'want_live', 'value': False},
                {'kind': 'dialogue', 'continent': 1, 'name': 'cIntro',
                 'path': 'root.1.1', 'field': 'speech', 'value_file': 'line.txt'},
                {'kind': 'dialogue', 'continent': 1, 'name': 'cIntro',
                 'path': 'root.1.1', 'field': 'who', 'value': 'GUARD'},
                {'kind': 'dialogue', 'continent': 1, 'name': 'cIntro',
                 'path': 'root.1', 'field': 'condition', 'value': False},
            ]}, stream)
        code, output = self.run_cli(['story-patch', patch, '--game', self.game,
                                     '--out', self.out])
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertTrue(result['out'].endswith('Resource1.pak'))
        archives = gres.ArchiveSet.open_folder(self.out)
        try:
            quests = lua_data.parse_source(archives.read('continent1quests.lua'))
            triggers = lua_data.parse_source(archives.read('continent1triggers.lua'))
            dialogues = lua_data.parse_source(archives.read('continent1conversations.lua'))
        finally:
            archives.close()
        self.assertEqual(quests['Quest']['q1']['Level'], 9.0)
        self.assertIs(triggers['Trigger']['q1.sq.Start.trigger']['WantLive'], False)
        self.assertEqual(dialogues['Dialog']['cIntro'][1][1]['speech'],
                         'A longer welcome')
        self.assertEqual(dialogues['Dialog']['cIntro'][1][1]['who'], 'GUARD')
        self.assertIs(dialogues['Dialog']['cIntro'][1]['Condition'], False)

    def test_bad_patch_document(self):
        patch = os.path.join(self.temp.name, 'patch.json')
        with open(patch, 'w', encoding='utf-8') as stream:
            json.dump({'format': 'wrong', 'operations': []}, stream)
        with self.assertRaises(SystemExit):
            self.run_cli(['story-patch', patch, '--game', self.game, '--dry-run'])


if __name__ == '__main__':
    unittest.main()
