"""Expression compiler and `$expr` story patching tests (no game install)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import lua_data
import lua_expr
import lua_patch
import story
from test_lua_patch import quest_chunk, trigger_chunk


class ExpressionTest(unittest.TestCase):
    def check(self, spec, expected, globals_=None):
        expression = lua_expr.compile_expression(spec)
        self.assertEqual(lua_expr.evaluate(expression, globals_ or {}), expected)

    def test_literals(self):
        self.check(True, True)
        self.check(False, False)
        self.check(7, 7.0)
        self.check('text', 'text')
        self.check(None, None)

    def test_logic(self):
        self.check({'op': 'and', 'args': [True, 'value']}, 'value')
        self.check({'op': 'and', 'args': [False, 'value']}, False)
        self.check({'op': 'or', 'args': [False, 0]}, 0.0)
        self.check({'op': 'or', 'args': ['first', 'second']}, 'first')
        self.check({'op': 'not', 'args': [False]}, True)
        self.check({'op': 'not', 'args': [0]}, False)
        self.check({'op': 'and', 'args': [True, True, False]}, False)

    def test_comparisons(self):
        self.check({'op': 'eq', 'args': [2, 2]}, True)
        self.check({'op': 'eq', 'args': [2, 3]}, False)
        self.check({'op': 'ne', 'args': [2, 3]}, True)
        self.check({'op': 'lt', 'args': [2, 3]}, True)
        self.check({'op': 'le', 'args': [3, 3]}, True)
        self.check({'op': 'gt', 'args': [3, 2]}, True)
        self.check({'op': 'ge', 'args': [2, 3]}, False)

    def test_arithmetic_and_if(self):
        self.check({'op': 'add', 'args': [2, 3]}, 5.0)
        self.check({'op': 'sub', 'args': [2, 3]}, -1.0)
        self.check({'op': 'mul', 'args': [2, 3]}, 6.0)
        self.check({'op': 'div', 'args': [6, 3]}, 2.0)
        self.check({'op': 'neg', 'args': [4]}, -4.0)
        self.check({'op': 'len', 'args': ['abcd']}, 4.0)
        self.check({'op': 'concat', 'args': ['a', 2, 'b']}, 'a2b')
        self.check({'if': {'op': 'lt', 'args': [1, 2]},
                    'then': 'yes', 'else': 'no'}, 'yes')
        self.check({'if': {'op': 'lt', 'args': [3, 2]},
                    'then': 'yes', 'else': 'no'}, 'no')

    def test_sequence_keeps_last_result(self):
        seen = []

        def record(value):
            seen.append(value)
            return value

        expression = lua_expr.compile_expression(
            {'op': 'seq', 'args': [{'call': ['record'], 'args': [1]},
                                   {'call': ['record'], 'args': [2]},
                                   {'call': ['record'], 'args': [3]}]})
        self.assertEqual(lua_expr.evaluate(expression, {'record': record}), 3.0)
        self.assertEqual(seen, [1.0, 2.0, 3.0])

    def test_globals_and_calls(self):
        self.check({'global': 'Flag'}, True, {'Flag': True})
        self.check({'global': ['Table', 'field']}, 4.5,
                   {'Table': {'field': 4.5}})
        self.check({'call': ['add'], 'args': [1, 2]}, 3.0,
                   {'add': lambda left, right: left + right})
        self.check({'call': 'T.add', 'method': True, 'args': [1, 2]}, 3.0,
                   {'T': {'add': lambda self, left, right: left + right}})

    def test_prototype_shape(self):
        expression = lua_expr.compile_expression(
            {'op': 'and', 'args': [{'global': 'A'}, {'global': 'B'}]})
        proto = expression.proto
        self.assertEqual(proto['nparams'], 0)
        self.assertEqual(proto['nups'], 0)
        self.assertEqual(proto['protos'], [])
        self.assertEqual(proto['locals'], [])
        self.assertEqual(lua_patch.OPS[proto['code'][-1] & 63], 'RETURN')
        self.assertTrue(proto['stack'] >= 2)

    def test_rejects_bad_expressions(self):
        bad = [
            {'op': 'and', 'args': [True]},
            {'op': 'eq', 'args': [1]},
            {'op': 'nope', 'args': [1, 2]},
            {'op': 'eq', 'args': [1, 2], 'extra': True},
            {'global': ''},
            {'global': ['Good', True]},
            {'call': 'fn', 'method': True},
            {'call': ['fn'], 'args': 'no'},
            {'if': True, 'then': 1},
            {'unknown': 1},
            [1, 2],
            '日本語',
            {'op': 'add', 'args': [1, 16777217]},
        ]
        for spec in bad:
            with self.assertRaises(lua_expr.ExprError):
                lua_expr.compile_expression(spec)


class ExpressionPatchTest(unittest.TestCase):
    def test_replaces_existing_function(self):
        data = trigger_chunk()
        expression = {'$expr': {'op': 'and', 'args': [
            {'call': ['Conditions', 'Check'], 'method': True,
             'args': ['Quest', 'q1', 'sq', 'Start', 'trigger']},
            {'global': 'Extra'}]}}
        patched = lua_patch.patch(
            data, [(['Trigger', 'a', 'Condition'], expression)])
        function = lua_data.parse_chunk(patched)
        self.assertEqual(len(function['protos']),
                         len(lua_data.parse_chunk(data)['protos']) + 1)
        trigger = lua_data.decode_chunk(patched, allow_closures=True)['Trigger']
        condition = trigger['a']['Condition']
        self.assertIsInstance(condition, lua_data.Closure)
        self.assertEqual(trigger['a']['Action'].proto,
                         lua_data.decode_chunk(data, allow_closures=True)
                         ['Trigger']['a']['Action'].proto)
        seen = []

        def check(*arguments):
            seen.append(arguments)
            return True

        self.assertTrue(lua_expr.evaluate(
            lua_expr.Expr(expression['$expr'], condition.proto, b''),
            {'Conditions': {'Check': check}, 'Extra': True}))
        self.assertEqual(seen[0][1:], ('Quest', 'q1', 'sq', 'Start', 'trigger'))

    def test_creates_record_with_two_functions(self):
        data = trigger_chunk()
        patched = lua_patch.patch(data, [
            (['Trigger', 'b'], {
                'WantLive': True,
                'Condition': {'$expr': {'global': 'Flag'}},
                'Action': {'$expr': {'call': 'Actions.DoAction', 'method': True,
                                     'args': ['q1', 'sq', 'Start']}},
            }),
        ])
        function = lua_data.parse_chunk(patched)
        self.assertEqual(len(function['protos']),
                         len(lua_data.parse_chunk(data)['protos']) + 2)
        trigger = lua_data.decode_chunk(patched, allow_closures=True)['Trigger']
        self.assertIsInstance(trigger['b']['Condition'], lua_data.Closure)
        self.assertIsInstance(trigger['b']['Action'], lua_data.Closure)
        self.assertEqual(trigger['b']['Condition'].proto['nparams'], 0)
        self.assertEqual(trigger['b']['Action'].proto['nparams'], 0)

    def test_expression_stays_rejected_for_literal_fields(self):
        editor = lua_patch.ChunkEditor(quest_chunk())
        with self.assertRaises(lua_patch.LuaPatchError):
            editor.set(['Quest', 'q1', 'DisplayName'], {'$expr': True})


class StoryExpressionTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        import gres
        self.temp = tempfile.TemporaryDirectory()
        self.gres = gres
        folder = self.temp.name
        gres.write_pak(os.path.join(folder, 'Resource0.pak'),
                       {'continent1triggers.lua': trigger_chunk()})
        self.archives = gres.ArchiveSet.open_folder(folder)

    def tearDown(self):
        self.archives.close()
        self.temp.cleanup()

    def test_field_condition_expression(self):
        patcher = story.StoryPatch(self.archives)
        patcher.add({
            'kind': 'trigger', 'continent': 1, 'name': 'a',
            'field': 'condition',
            'value': {'$expr': {'op': 'and', 'args': [
                {'global': 'Flag'}, {'global': ['Quest', 'Active']}]}},
        })
        entries = patcher.documents()
        trigger = lua_data.decode_chunk(entries['continent1triggers.lua'],
                                        allow_closures=True)['Trigger']['a']
        self.assertIsInstance(trigger['Condition'], lua_data.Closure)
        self.assertEqual(trigger['Condition'].proto['nparams'], 0)
        self.assertEqual(patcher.changes[0]['new'],
                         {'$expr': {'op': 'and', 'args': [
                             {'global': 'Flag'},
                             {'global': ['Quest', 'Active']}]}})

    def test_create_trigger_with_expression(self):
        patcher = story.StoryPatch(self.archives)
        patcher.add({
            'kind': 'trigger', 'continent': 1, 'name': 'b',
            'create': {'WantLive': False,
                       'Condition': {'$expr': {'global': 'Flag'}},
                       'Action': {'$expr': {'call': 'Actions.DoAction',
                                            'method': True,
                                            'args': ['q1', 'sq', 'Start']}}},
        })
        entries = patcher.documents()
        trigger = lua_data.decode_chunk(entries['continent1triggers.lua'],
                                        allow_closures=True)['Trigger']['b']
        self.assertIsInstance(trigger['Condition'], lua_data.Closure)
        self.assertIsInstance(trigger['Action'], lua_data.Closure)

    def test_expression_outside_function_fields_is_rejected(self):
        patcher = story.StoryPatch(self.archives)
        with self.assertRaises(story.StoryError):
            patcher.add({'kind': 'trigger', 'continent': 1, 'name': 'a',
                         'field': 'want_live',
                         'value': {'$expr': {'global': 'Flag'}}})
        with self.assertRaises(story.StoryError):
            patcher.add({'kind': 'trigger', 'continent': 1, 'name': 'b',
                         'create': {'WantLive': {'$expr': {'global': 'Flag'}},
                                    'Condition': True}})


class StoryExpressionCliTest(unittest.TestCase):
    def setUp(self):
        import contextlib
        import io
        import json
        import tempfile
        import gres
        import worldctl
        self.contextlib = contextlib
        self.io = io
        self.json = json
        self.gres = gres
        self.worldctl = worldctl
        self.temp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.temp.name, 'game')
        self.out = os.path.join(self.temp.name, 'out')
        os.makedirs(self.game)
        os.makedirs(self.out)
        gres.write_pak(os.path.join(self.game, 'Resource0.pak'), {
            'continent1quests.lua': quest_chunk(),
            'continent1triggers.lua': trigger_chunk(),
        })

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, argv):
        output = self.io.StringIO()
        with self.contextlib.redirect_stdout(output):
            code = self.worldctl.main(argv)
        return code, output.getvalue()

    def test_export_expression_and_overlay_check(self):
        patch = os.path.join(self.temp.name, 'patch.json')
        expression = {'$expr': {'op': 'and', 'args': [
            {'call': 'Conditions.Check', 'method': True,
             'args': ['Current Hero', 'Warrior']},
            {'op': 'eq', 'args': [1, 1]}]}}
        with open(patch, 'w', encoding='utf-8') as stream:
            self.json.dump({'format': story.PATCH_FORMAT, 'operations': [
                {'kind': 'quest', 'continent': 1, 'name': 'q1',
                 'field': 'display_name', 'value': 'Demo'},
                {'kind': 'trigger', 'continent': 1, 'name': 'a',
                 'field': 'condition', 'value': expression},
            ]}, stream, ensure_ascii=False)
        code, output = self.run_cli(['story-patch', patch, '--game', self.game,
                                     '--out', self.out, '--slot', '1'])
        self.assertEqual(code, 0)
        result = self.json.loads(output)
        destination = result['out']
        self.assertTrue(destination.endswith('Resource1.pak'))

        code, output = self.run_cli(['overlay-check', destination,
                                     '--game', self.game, '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(self.json.loads(output)['status'], 'match')

        with self.gres.ArchiveSet([destination]) as overlays:
            triggers = lua_data.decode_chunk(
                overlays.read('continent1triggers.lua'),
                allow_closures=True)['Trigger']
            quests = lua_data.decode_chunk(
                overlays.read('continent1quests.lua'),
                allow_closures=True)['Quest']
            function = lua_data.parse_chunk(
                overlays.read('continent1triggers.lua'))
        self.assertEqual(quests['q1']['DisplayName'], 'Demo')
        condition = triggers['a']['Condition']
        self.assertIsInstance(condition, lua_data.Closure)
        self.assertEqual(len(function['protos']), 2)
        self.assertTrue(lua_expr.evaluate(
            lua_expr.Expr(expression['$expr'], condition.proto, b''),
            {'Conditions': {'Check': lambda self, *args: True}}))


if __name__ == '__main__':
    unittest.main()
