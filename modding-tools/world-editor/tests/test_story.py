"""Unit tests for the quest/trigger/conversation index (no game needed)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import gres
import lua_data
import story
import worldctl


def sample_tables():
    return {
        'quests': {
            'q1': {'DisplayName': 'Quest One', 'Description': 'Find the mill',
                   'Level': 2.0, 'SubQuest': {
                       'sqStart': {'Start': {'trigger': {'Start': True, 'Action': False}},
                                   'Finish': {}},
                   }},
            '-------': {'DisplayName': '', 'Description': '', 'Level': 0.0,
                        'SubQuest': {}},
        },
        'triggers': {
            'q1.sqStart.Start.trigger': {'WantLive': True, 'Condition': True,
                                         'Action': False},
        },
        'dialogues': {
            'cIntro': {1: {'who': 'HERO', 'speech': 'Hello there', 'Condition': True,
                           'Do': False,
                           1: {'who': 'OWNER', 'speech': 'Welcome to Windrose',
                               'Condition': True}}},
            '------': {},
        },
    }


def make_story(tables=None):
    return story.Story.from_tables({1: tables or sample_tables()})


class StoryModelTest(unittest.TestCase):
    def test_summary_and_dialogue_lines(self):
        model = make_story()
        self.assertEqual(model.summary(),
                         {'1': {'quests': 1, 'triggers': 1, 'dialogues': 1,
                                'speech_lines': 2}})
        lines = model.dialogue_lines(1, 'cIntro')
        self.assertEqual([line['path'] for line in lines], ['root.1', 'root.1.1'])
        self.assertEqual([line['who'] for line in lines], ['HERO', 'OWNER'])
        with self.assertRaises(story.StoryError):
            model.dialogue_lines(1, 'cMissing')

    def test_find(self):
        model = make_story()
        self.assertEqual(model.find(kind='quest')[0]['name'], 'q1')
        self.assertEqual(model.find(kind='quest')[0]['level'], 2.0)
        matches = model.find(kind='dialogue', text='windrose')
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['name'], 'cIntro')
        self.assertEqual(matches[0]['path'], 'root.1.1')
        self.assertEqual(model.find(kind='trigger', name='sqStart')[0]['name'],
                         'q1.sqStart.Start.trigger')

    def test_validate(self):
        self.assertEqual(make_story().validate(), [])
        tables = sample_tables()
        tables['triggers']['q1.sqNope.Start.trigger'] = {
            'WantLive': False, 'Condition': True, 'Action': False}
        tables['triggers']['broken'] = {'WantLive': False, 'Condition': True,
                                        'Action': False}
        kinds = [issue['kind'] for issue in make_story(tables).validate()]
        self.assertEqual(kinds, ['malformed-trigger', 'unresolved-trigger'])
        tables = sample_tables()
        tables['dialogues']['cIntro'][1].pop('who')
        kinds = [issue['kind'] for issue in make_story(tables).validate()]
        self.assertIn('dialogue-without-speaker', kinds)

    def test_json_roundtrip(self):
        model = make_story()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'story.json')
            model.save_json(path)
            restored = story.Story.load_json(path)
            self.assertEqual(restored.summary(), model.summary())
            self.assertEqual(restored.dialogue_lines(1, 'cIntro'),
                             model.dialogue_lines(1, 'cIntro'))
            self.assertEqual(restored.validate(), [])


class StoryCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.temp.name, 'game')
        self.out = os.path.join(self.temp.name, 'out')
        os.makedirs(self.game)
        tables = sample_tables()
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

    def test_extract_find_dialogue_validate(self):
        document = os.path.join(self.out, 'story.json')
        code, _ = self.run_cli(['story-extract', '--game', self.game,
                                '--out', self.out])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(document))
        self.assertTrue(os.path.exists(os.path.join(self.out, 'story-info.json')))

        code, output = self.run_cli(['story-info', document, '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)['continents']['1']['quests'], 1)

        code, output = self.run_cli(['story-find', document, '--kind', 'dialogue',
                                     '--text', 'windrose'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)[0]['name'], 'cIntro')

        code, output = self.run_cli(['story-dialogue', document, 'cIntro', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)[0]['lines']), 2)

        code, output = self.run_cli(['story-validate', document])
        self.assertEqual(code, 0)
        self.assertIn('0 error(s)', output)


if __name__ == '__main__':
    unittest.main()
