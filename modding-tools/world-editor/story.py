"""Quests, triggers and conversations as a JSON story index and patcher.

All three modules are Lua 5.1 bytecode that mixes data tables with nested
functions.  `lua_data` decodes the straight-line data part and represents each
nested function as an opaque `Closure`; this module turns that into a stable,
searchable document (function code is not exposed, only line/parameter counts).
`StoryPatch` edits literal fields, creates or removes whole records through
`lua_patch`, and exports the changed modules as an overlay PAK.  Function
values are preserved byte-for-byte, copied from another record with `$ref`, or
generated from a JSON expression with `$expr` (see `lua_expr`).

Layouts seen on all three retail continents::

    Quest[name]       = {DisplayName, Description, Level, SubQuest}
    SubQuest[sq][Start|Finish][trigger] = {Start, Action}
    Trigger[quest.sq.Start|Finish.trigger] = {WantLive, Condition, Action}
    Dialog[name][n][n]... = {who, speech, Condition, [Action], Do, replies...}

Trigger keys are ``<quest>.<subquest>.<Start|Finish>.<trigger>``; the stock
data has no unresolved keys, so a mismatch is reported as an error.
"""
import hashlib
import json
from pathlib import Path

import gres
import lua_data
import lua_expr
import lua_patch

FORMAT = 'attt-story/1'
PATCH_FORMAT = 'attt-story-patch/1'
MODULES = {
    'triggers': ('continent%dtriggers.lua', 'Trigger'),
    'quests': ('continent%dquests.lua', 'Quest'),
    'dialogues': ('continent%dconversations.lua', 'Dialog'),
}
PHASES = ('Start', 'Finish')

#: story-facing literal fields; Condition/Action/Do additionally take `$expr`
FIELDS = {
    'quest': {'display_name': 'DisplayName', 'description': 'Description',
              'level': 'Level'},
    'trigger': {'want_live': 'WantLive', 'condition': 'Condition',
                'action': 'Action'},
    'dialogue': {'who': 'who', 'speech': 'speech', 'condition': 'Condition',
                 'action': 'Action', 'do': 'Do'},
}
FUNCTION_FIELDS = {'Condition', 'Action', 'Do'}
KIND_MODULE = {'quest': 'quests', 'trigger': 'triggers', 'dialogue': 'dialogues'}


class StoryError(ValueError):
    pass


def _function(value):
    proto = value.proto
    result = {'line': proto.get('line'), 'lastline': proto.get('lastline'),
              'params': proto.get('nparams'), 'stack': proto.get('stack'),
              'upvalues': proto.get('nups'), 'instructions': len(proto.get('code', []))}
    names = proto.get('upnames') or []
    if names:
        result['upvalue_names'] = list(names)
    return {'function': result}


def _plain(value):
    if isinstance(value, lua_data.Closure):
        return _function(value)
    if isinstance(value, lua_expr.Expr):
        return {'$expr': value.spec}
    if isinstance(value, lua_patch.Ref):
        return {'$ref': list(value.path)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()
                if isinstance(key, (str, int))}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _contains_function(value):
    if isinstance(value, dict):
        if set(value) in ({'$expr'}, {'$ref'}):
            return True
        return any(_contains_function(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_function(item) for item in value)
    return False


def _check_expression_keys(value, path, key=None):
    if isinstance(value, dict):
        if set(value) in ({'$expr'}, {'$ref'}):
            if key not in FUNCTION_FIELDS:
                raise StoryError('%s: function values are only allowed for '
                                 'Condition, Action or Do' % path)
            return
        for name, item in value.items():
            _check_expression_keys(item, '%s.%s' % (path, name), str(name))
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            _check_expression_keys(item, '%s[%d]' % (path, index), key)


def _quests(raw):
    quests = {}
    for name, quest in raw.items():
        if not isinstance(quest, dict):
            raise StoryError('Quest.%s is not a table' % name)
        subquests = {}
        for sub_name, sub in (quest.get('SubQuest') or {}).items():
            if not isinstance(sub, dict):
                raise StoryError('Quest.%s.SubQuest.%s is not a table' % (name, sub_name))
            phases = {}
            for phase in PHASES:
                entries = sub.get(phase) or {}
                if not isinstance(entries, dict):
                    raise StoryError('Quest.%s.SubQuest.%s.%s is not a table' %
                                     (name, sub_name, phase))
                phases[phase.lower()] = {
                    trigger: {key: _plain(value) for key, value in entry.items()}
                    for trigger, entry in entries.items() if isinstance(entry, dict)}
            subquests[sub_name] = phases
        quests[name] = {
            'display_name': quest.get('DisplayName', ''),
            'description': quest.get('Description', ''),
            'level': quest.get('Level', 0.0),
            'subquests': subquests,
        }
    return quests


def _triggers(raw):
    triggers = {}
    for key, trigger in raw.items():
        if not isinstance(trigger, dict):
            raise StoryError('Trigger.%s is not a table' % key)
        triggers[key] = {
            'want_live': bool(trigger.get('WantLive', False)),
            'condition': _plain(trigger.get('Condition')),
            'action': _plain(trigger.get('Action')),
        }
    return triggers


def _dialogue_node(raw, path='root'):
    if not isinstance(raw, dict):
        raise StoryError('dialog node %s is not a table' % path)
    node = {}
    for key, field in (('who', 'who'), ('speech', 'speech'),
                       ('Condition', 'condition'), ('Action', 'action'), ('Do', 'do')):
        if key in raw:
            node[field] = _plain(raw[key])
    extra = {str(key): _plain(value) for key, value in raw.items()
             if isinstance(key, str) and key not in ('who', 'speech', 'Condition',
                                                     'Action', 'Do')}
    if extra:
        node['extra'] = extra
    replies = []
    for index in sorted(key for key in raw if isinstance(key, int)):
        replies.append(_dialogue_node(raw[index], '%s.%d' % (path, index)))
    if replies:
        node['replies'] = replies
    return node


def _dialogues(raw):
    dialogues = {}
    for name, node in raw.items():
        if str(name).startswith('-'):
            continue
        dialogues[name] = _dialogue_node(node, str(name))
    return dialogues


def _load_table(archive_set, filename, global_name):
    resolved = archive_set.resolve(filename)
    if resolved is None:
        return None, None
    data = resolved.read()
    source = {'file': filename, 'archive': resolved.archive.path.name,
              'slot': resolved.archive.slot,
              'sha256': hashlib.sha256(data).hexdigest()}
    try:
        if data[:4] == b'\x1bLua':
            globals_ = lua_data.decode_chunk(data, allow_closures=True)
        else:
            globals_ = lua_data.parse_source(data)
    except lua_data.LuaDataError as error:
        raise StoryError('%s cannot be decoded: %s' % (filename, error))
    if global_name not in globals_:
        raise StoryError('%s does not define %s' % (filename, global_name))
    return globals_[global_name], source


def build_identity(archive_set, continents):
    """Fingerprint every story module an overlay is based on."""
    names = [MODULES[kind][0] % continent
             for continent in sorted(set(continents)) for kind in MODULES]
    return gres.file_identity(archive_set, names)


class Story:
    def __init__(self, continents=None, archives=None):
        self.continents = continents or {}
        self.archives = archives or []

    @classmethod
    def from_tables(cls, tables, archives=None):
        """Build from already-decoded module tables.

        `tables` maps a continent to any of `quests`, `triggers`, `dialogues`.
        """
        story = cls(archives=archives)
        for continent, modules in sorted(tables.items()):
            entry = {'quests': {}, 'triggers': {}, 'dialogues': {}, 'sources': {}}
            if modules.get('quests') is not None:
                entry['quests'] = _quests(modules['quests'])
            if modules.get('triggers') is not None:
                entry['triggers'] = _triggers(modules['triggers'])
            if modules.get('dialogues') is not None:
                entry['dialogues'] = _dialogues(modules['dialogues'])
            entry['sources'] = dict(modules.get('sources') or {})
            story.continents[int(continent)] = entry
        return story

    @classmethod
    def load_archives(cls, paths, continents=(1, 2, 3)):
        archive_set = gres.ArchiveSet(paths)
        try:
            return cls._from_set(archive_set, continents)
        finally:
            archive_set.close()

    @classmethod
    def load_folder(cls, folder, continents=(1, 2, 3)):
        archive_set = gres.ArchiveSet.open_folder(folder, allow_gaps=True)
        try:
            return cls._from_set(archive_set, continents)
        finally:
            archive_set.close()

    @classmethod
    def _from_set(cls, archive_set, continents):
        archives = [{'slot': slot, 'path': str(archive_set.archives[slot].path)}
                    for slot in archive_set.slots]
        tables = {}
        for continent in continents:
            modules = {'sources': {}}
            found = False
            for kind, (pattern, global_name) in MODULES.items():
                filename = pattern % continent
                raw, source = _load_table(archive_set, filename, global_name)
                if raw is None:
                    continue
                modules[kind] = raw
                modules['sources'][kind] = source
                found = True
            if found:
                tables[continent] = modules
        return cls.from_tables(tables, archives)

    @classmethod
    def load_json(cls, path):
        with open(path, encoding='utf-8') as stream:
            document = json.load(stream)
        if document.get('format') != FORMAT:
            raise StoryError('%s is not an %s document' % (path, FORMAT))
        story = cls(archives=document.get('archives', []))
        for continent, entry in document['continents'].items():
            story.continents[int(continent)] = {
                'quests': entry.get('quests', {}),
                'triggers': entry.get('triggers', {}),
                'dialogues': entry.get('dialogues', {}),
                'sources': entry.get('sources', {}),
            }
        return story

    def document(self):
        return {'format': FORMAT, 'archives': self.archives,
                'continents': {str(continent): entry
                               for continent, entry in sorted(self.continents.items())}}

    def save_json(self, path):
        with open(path, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(self.document(), stream, ensure_ascii=False, indent=1,
                      allow_nan=False, sort_keys=True)
            stream.write('\n')

    # --- access -----------------------------------------------------------
    def summary(self):
        result = {}
        for continent, entry in sorted(self.continents.items()):
            speech = sum(1 for dialogue in entry['dialogues'].values()
                         for _, node in _iter_nodes(dialogue) if 'speech' in node)
            result[str(continent)] = {
                'quests': sum(1 for name in entry['quests'] if not name.startswith('-')),
                'triggers': len(entry['triggers']),
                'dialogues': len(entry['dialogues']),
                'speech_lines': speech,
            }
        return result

    def entry(self, continent):
        entry = self.continents.get(int(continent))
        if entry is None:
            raise StoryError('continent %s has no story modules' % continent)
        return entry

    def dialogue_nodes(self, continent, name):
        entry = self.entry(continent)
        node = entry['dialogues'].get(name)
        if node is None:
            raise StoryError('continent %s has no dialogue %s' % (continent, name))
        return list(_iter_nodes(node))

    def dialogue_lines(self, continent, name):
        lines = []
        for path, node in self.dialogue_nodes(continent, name):
            if 'speech' not in node:
                continue
            lines.append({'path': path, 'depth': path.count('.'),
                          'who': node.get('who'), 'speech': node['speech'],
                          'condition': node.get('condition')})
        return lines

    def find(self, continent=None, kind=None, name=None, text=None, limit=100):
        target = str(name).lower() if name else None
        content = str(text).lower() if text else None
        results = []
        for number, entry in sorted(self.continents.items()):
            if continent is not None and number != int(continent):
                continue
            if kind in (None, 'quest'):
                for quest_name, quest in sorted(entry['quests'].items()):
                    if quest_name.startswith('-'):
                        continue
                    if target and target not in quest_name.lower():
                        continue
                    haystack = ' '.join((quest_name, str(quest.get('display_name', '')),
                                         str(quest.get('description', '')))).lower()
                    if content and content not in haystack:
                        continue
                    results.append({'continent': number, 'kind': 'quest',
                                    'name': quest_name,
                                    'display_name': quest.get('display_name', ''),
                                    'description': quest.get('description', ''),
                                    'level': quest.get('level', 0.0),
                                    'subquests': len(quest.get('subquests', {}))})
                    if len(results) >= limit:
                        return results
            if kind in (None, 'trigger'):
                for trigger_name, trigger in sorted(entry['triggers'].items()):
                    if target and target not in trigger_name.lower():
                        continue
                    haystack = ' '.join((trigger_name,
                                         _describe(trigger.get('condition')),
                                         _describe(trigger.get('action')))).lower()
                    if content and content not in haystack:
                        continue
                    results.append({'continent': number, 'kind': 'trigger',
                                    'name': trigger_name,
                                    'want_live': trigger.get('want_live', False),
                                    'condition': trigger.get('condition'),
                                    'action': trigger.get('action')})
                    if len(results) >= limit:
                        return results
            if kind in (None, 'dialogue'):
                for dialogue_name, node in sorted(entry['dialogues'].items()):
                    if target and target not in dialogue_name.lower():
                        continue
                    matches = _match_dialogue(dialogue_name, node, content)
                    for match in matches:
                        results.append({'continent': number, 'kind': 'dialogue',
                                        'name': dialogue_name, **match})
                        if len(results) >= limit:
                            return results
        return results

    # --- checks -----------------------------------------------------------
    def validate(self):
        issues = []
        for continent, entry in sorted(self.continents.items()):
            quests = entry['quests']
            for key, trigger in sorted(entry['triggers'].items()):
                parts = key.split('.')
                if len(parts) != 4:
                    issues.append({'level': 'error', 'kind': 'malformed-trigger',
                                   'continent': continent, 'name': key,
                                   'message': 'expected quest.subquest.phase.trigger'})
                    continue
                quest_name, sub_name, phase, trigger_name = parts
                quest = quests.get(quest_name)
                if quest is None:
                    issues.append({'level': 'error', 'kind': 'unresolved-trigger',
                                   'continent': continent, 'name': key,
                                   'message': 'quest %s is missing' % quest_name})
                    continue
                sub = quest.get('subquests', {}).get(sub_name)
                if sub is None:
                    issues.append({'level': 'error', 'kind': 'unresolved-trigger',
                                   'continent': continent, 'name': key,
                                   'message': 'subquest %s is missing' % sub_name})
                    continue
                if phase.lower() not in sub:
                    issues.append({'level': 'error', 'kind': 'unresolved-trigger',
                                   'continent': continent, 'name': key,
                                   'message': 'phase %s is missing' % phase})
                    continue
                if trigger_name not in sub[phase.lower()]:
                    issues.append({'level': 'error', 'kind': 'unresolved-trigger',
                                   'continent': continent, 'name': key,
                                   'message': 'trigger %s is missing from the quest' %
                                              trigger_name})
            for name, node in sorted(entry['dialogues'].items()):
                if _node_count(node) == 0:
                    issues.append({'level': 'warning', 'kind': 'empty-dialogue',
                                   'continent': continent, 'name': name})
                for path, item in _iter_nodes(node):
                    speech = item.get('speech')
                    if isinstance(speech, str) and speech and not item.get('who'):
                        issues.append({'level': 'warning', 'kind': 'dialogue-without-speaker',
                                       'continent': continent, 'name': '%s:%s' % (name, path),
                                       'speech': speech})
        return issues


class StoryPatch:
    """Apply literal edits to quest, trigger and conversation modules.

    Operations use story-facing names and fields; the class translates them to
    the raw table paths used by ``lua_patch``::

        {"kind": "quest", "continent": 1, "name": "q1",
         "field": "display_name", "value": "New title"}
        {"kind": "trigger", "continent": 1,
         "name": "q1.sq.Start.trigger5", "field": "want_live", "value": true}
        {"kind": "dialogue", "continent": 1, "name": "cIntro",
         "path": "root.1.2", "field": "speech", "value": "..."}

    Whole records are created with ``"create": {...}`` and removed with
    ``"remove": true``::

        {"kind": "quest", "continent": 1, "name": "qNew",
         "create": {"DisplayName": "New quest", "Level": 1, "SubQuest": {}}}
        {"kind": "dialogue", "continent": 1, "name": "cIntro",
         "path": "root.1", "create": {"who": "HERO", "speech": "Hi"}}
        {"kind": "dialogue", "continent": 1, "name": "cIntro",
         "path": "root.1.2", "remove": true}

    A dialogue ``create`` without ``path`` makes a new dialogue record; with a
    path it appends a reply (the next free integer key, or ``"key"``).  Nested
    tables are supported.

    ``condition``, ``action`` and ``do`` fields (and the matching
    ``Condition``/``Action``/``Do`` keys inside a ``create`` payload) accept a
    function value: ``{"$ref": [...]}`` copies an existing one and
    ``{"$expr": ...}`` compiles a new one.  ``$expr`` is rejected in every
    other field.
    """

    def __init__(self, archive_set):
        self.archive_set = archive_set
        self._modules = {}
        self._edits = {}
        self.changes = []

    @property
    def continents(self):
        return sorted({continent for continent, _ in self._modules})

    def _module(self, continent, kind):
        kind = KIND_MODULE[kind]
        key = (continent, kind)
        if key in self._modules:
            return self._modules[key]
        pattern, global_name = MODULES[kind]
        filename = pattern % continent
        entry = self.archive_set.resolve(filename)
        if entry is None:
            raise StoryError('%s is missing from the selected archives' % filename)
        data = entry.read()
        try:
            if data[:4] == b'\x1bLua':
                globals_ = lua_data.decode_chunk(data, allow_closures=True)
            else:
                globals_ = lua_data.parse_source(data)
        except lua_data.LuaDataError as error:
            raise StoryError('%s cannot be decoded: %s' % (filename, error))
        if global_name not in globals_:
            raise StoryError('%s does not define %s' % (filename, global_name))
        module = {'file': filename, 'data': data, 'globals': globals_,
                  'bytecode': data[:4] == b'\x1bLua',
                  'source': {'file': filename, 'slot': entry.archive.slot,
                             'archive': entry.archive.path.name}}
        self._modules[key] = module
        return module

    def _table(self, module, kind):
        table_name = MODULES[KIND_MODULE[kind]][1]
        table = module['globals'].get(table_name)
        if not isinstance(table, dict):
            raise StoryError('%s does not define a %s table' % (module['file'], table_name))
        return table_name, table

    def _dialogue_node(self, continent, module, name, dialogue_path):
        table_name, table = self._table(module, 'dialogue')
        try:
            actual = lua_patch.actual_key(table, name)
        except lua_patch.LuaPatchError:
            raise StoryError('continent %d has no dialogue %s' % (continent, name))
        node = table[actual]
        if not isinstance(node, dict):
            raise StoryError('dialogue %s is not a table' % name)
        path = [table_name, actual]
        segments = (dialogue_path or 'root').split('.')
        if segments[0] != 'root':
            raise StoryError('dialogue path must start with root: %r' % dialogue_path)
        for segment in segments[1:]:
            if not segment.isdigit() or int(segment) < 1:
                raise StoryError('dialogue path segment %r is not a reply index' %
                                 segment)
            replies = sorted(key for key in node if isinstance(key, int))
            index = int(segment)
            if index > len(replies):
                raise StoryError('dialogue %s has no reply %d (only %d)' %
                                 (name, index, len(replies)))
            key = replies[index - 1]
            node = node[key]
            if not isinstance(node, dict):
                raise StoryError('dialogue %s reply %s is not a table' %
                                 (name, segment))
            path.append(key)
        return node, path

    def _path(self, continent, module, kind, name, field, dialogue_path):
        if kind == 'dialogue':
            _, path = self._dialogue_node(continent, module, name, dialogue_path)
        else:
            table_name, table = self._table(module, kind)
            try:
                actual = lua_patch.actual_key(table, name)
            except lua_patch.LuaPatchError:
                raise StoryError('continent %d has no %s %s' % (continent, kind, name))
            path = [table_name, actual]
        path.append(FIELDS[kind][field])
        return path

    def _next_reply_key(self, node_path, node):
        used = {key for key in node if isinstance(key, int)}
        for group in self._edits.values():
            for edit in group:
                if edit['path'][:-1] == node_path and isinstance(edit['path'][-1], int):
                    used.add(edit['path'][-1])
        return max(used, default=0) + 1

    def _record_edit(self, kind, continent, module_kind, keys, new, label, name,
                     field=None, dialogue_path=None, old=None,
                     created=False, removed=False):
        group = self._edits.setdefault((continent, module_kind), [])
        if any(edit['path'] == keys for edit in group):
            raise StoryError('%s is edited twice' % label)
        group.append({'path': keys, 'new': new})
        self.changes.append({
            'continent': continent, 'kind': kind, 'name': name, 'field': field,
            'path': dialogue_path, 'old': _plain(old) if old is not None else None,
            'new': _plain(new), 'created': created, 'removed': removed,
        })

    def _create(self, operation, kind, continent, name):
        module = self._module(continent, kind)
        table_name, table = self._table(module, kind)
        payload = operation.get('create')
        if not isinstance(payload, (dict, list)):
            raise StoryError('create for %s must be a JSON object or array' % kind)
        dialogue_path = operation.get('path')
        if kind == 'dialogue' and dialogue_path is not None:
            node, node_path = self._dialogue_node(continent, module, name, dialogue_path)
            key = operation.get('key')
            if key is None:
                key = self._next_reply_key(node_path, node)
            elif (not isinstance(key, int) or isinstance(key, bool) or key < 1):
                raise StoryError('dialogue reply key must be a positive integer')
            elif key in node:
                raise StoryError('dialogue %s already has reply %d at %s' %
                                 (name, key, dialogue_path))
            keys = node_path + [key]
            label = 'dialogue/%s/%s' % (name, dialogue_path)
        else:
            if dialogue_path not in (None, 'root'):
                raise StoryError('%s records have no dialogue reply path' % kind)
            try:
                lua_patch.actual_key(table, name)
            except lua_patch.LuaPatchError:
                pass
            else:
                raise StoryError('continent %d already has %s %s' %
                                 (continent, kind, name))
            keys = [table_name, name]
            label = '%s/%s' % (kind, name)
        try:
            _check_expression_keys(payload, label)
            if _contains_function(payload) and not module['bytecode']:
                raise StoryError('%s: function values need a bytecode module' % label)
            new = lua_patch.validate_new(payload, label)
            lua_patch.resolve_refs(module['globals'], new, label)
        except lua_patch.LuaPatchError as error:
            raise StoryError(str(error))
        if isinstance(new, (lua_patch.Ref, lua_expr.Expr)):
            raise StoryError('%s must be a table, not a function value' % label)
        self._record_edit(kind, continent, KIND_MODULE[kind], keys, new, label, name,
                          dialogue_path=dialogue_path, created=True)

    def _remove(self, operation, kind, continent, name):
        module = self._module(continent, kind)
        table_name, table = self._table(module, kind)
        dialogue_path = operation.get('path')
        if kind == 'dialogue' and dialogue_path not in (None, 'root'):
            node, keys = self._dialogue_node(continent, module, name, dialogue_path)
            old = node
            label = 'dialogue/%s/%s' % (name, dialogue_path)
        else:
            if dialogue_path not in (None, 'root'):
                raise StoryError('%s records have no dialogue reply path' % kind)
            try:
                actual = lua_patch.actual_key(table, name)
            except lua_patch.LuaPatchError:
                raise StoryError('continent %d has no %s %s' % (continent, kind, name))
            keys = [table_name, actual]
            old = table[actual]
            label = '%s/%s' % (kind, name)
        self._record_edit(kind, continent, KIND_MODULE[kind], keys, None, label, name,
                          dialogue_path=dialogue_path, old=old, removed=True)

    def add(self, operation):
        if not isinstance(operation, dict):
            raise StoryError('each operation must be a JSON object')
        kind = operation.get('kind')
        if kind not in FIELDS:
            raise StoryError('unknown story kind %r' % (kind,))
        field = operation.get('field')
        if field is not None and field not in FIELDS[kind]:
            raise StoryError('%s field %r is not editable; choose one of %s' %
                             (kind, field, ', '.join(sorted(FIELDS[kind]))))
        try:
            continent = int(operation['continent'])
        except (KeyError, TypeError, ValueError):
            raise StoryError('operation %s needs an integer continent' % (kind,))
        name = operation.get('name')
        if not isinstance(name, str) or not name:
            raise StoryError('operation %s needs a name' % (kind,))
        creating = 'create' in operation
        removing = bool(operation.get('remove'))
        if creating and removing:
            raise StoryError('operation %s/%s cannot create and remove at once' %
                             (kind, name))
        if creating or removing:
            if field is not None:
                raise StoryError('%s operations take a create/remove payload, '
                                 'not a field' % kind)
            if creating:
                self._create(operation, kind, continent, name)
            else:
                self._remove(operation, kind, continent, name)
            return
        if field is None:
            raise StoryError('%s operations need a field, create or remove' % kind)
        if 'value' not in operation:
            raise StoryError('operation %s/%s needs a value' % (kind, name))
        module = self._module(continent, kind)
        path = self._path(continent, module, kind, name, field,
                          operation.get('path'))
        label = '%s/%s/%s' % (kind, name, field)
        if (_contains_function(operation['value']) and
                FIELDS[kind][field] not in FUNCTION_FIELDS):
            raise StoryError('%s: function values are only allowed for '
                             'Condition, Action or Do' % label)
        if _contains_function(operation['value']) and not module['bytecode']:
            raise StoryError('%s: function values need a bytecode module' % label)
        try:
            parent, key, old = lua_patch.lookup(module['globals'], path)
            if old is lua_patch.MISSING:
                new = lua_patch.validate_new(operation['value'], label)
            else:
                new = lua_patch.coerce(operation['value'], old, label)
        except lua_patch.LuaPatchError as error:
            raise StoryError(str(error))
        if new is None and old is lua_patch.MISSING:
            raise StoryError('%s does not exist; cannot remove it' % label)
        keys = path[:-1] + [key]
        group = self._edits.setdefault((continent, KIND_MODULE[kind]), [])
        if any(edit['path'] == keys for edit in group):
            raise StoryError('%s is edited twice' % label)
        edit = {'path': keys, 'new': new}
        group.append(edit)
        self.changes.append({
            'continent': continent, 'kind': kind, 'name': name, 'field': field,
            'path': operation.get('path'),
            'old': None if old is lua_patch.MISSING else _plain(old),
            'new': _plain(new), 'created': old is lua_patch.MISSING,
            'removed': new is None,
        })

    def documents(self):
        """Return patched module bytes keyed by archive entry name."""
        result = {}
        for (continent, kind), edits in sorted(self._edits.items()):
            module = self._modules[(continent, kind)]
            if module['bytecode']:
                try:
                    data = lua_patch.patch(module['data'],
                                           [(edit['path'], edit['new']) for edit in edits])
                except lua_patch.LuaPatchError as error:
                    raise StoryError('%s cannot be patched: %s' %
                                     (module['file'], error))
            else:
                globals_ = lua_data.parse_source(module['data'])
                for edit in edits:
                    parent = lua_patch.resolve(globals_, edit['path'][:-1])
                    key = edit['path'][-1]
                    if key in parent:
                        key = lua_patch.actual_key(parent, key)
                    if edit['new'] is None:
                        parent.pop(key, None)
                    else:
                        parent[key] = edit['new']
                data = lua_data.emit_source(globals_)
            result[module['file']] = data
        return result

    def export_pak(self, path, slot=None, overwrite=False):
        entries = self.documents()
        if not entries:
            raise StoryError('no story fields changed')
        folder = Path(path)
        if not folder.is_dir():
            raise StoryError('output folder does not exist: %s' % folder)
        if slot is None:
            used = set(self.archive_set.slots)
            used.update(module['source']['slot'] for module in self._modules.values())
            used.update(gres.archive_slot(candidate.name)
                        for candidate in folder.glob('Resource*.pak'))
            used.discard(None)
            slot = max(used, default=0) + 1
        destination = folder / ('Resource%d.pak' % slot)
        identity = build_identity(self.archive_set, self.continents)
        gres.write_pak(destination, entries, overwrite=overwrite, identity=identity)
        return str(destination), entries


def _describe(value):
    if isinstance(value, dict) and 'function' in value:
        return 'function line %s' % value['function'].get('line')
    return str(value)


def _iter_nodes(node, path='root'):
    yield path, node
    for index, child in enumerate(node.get('replies', []), 1):
        child_path = '%s.%d' % (path, index)
        yield from _iter_nodes(child, child_path)


def _node_count(node):
    return sum(1 for _ in _iter_nodes(node))


def _match_dialogue(name, node, content):
    if content is None:
        for path, item in _iter_nodes(node):
            if 'speech' in item:
                return [{'path': path, 'who': item.get('who'),
                         'speech': item['speech']}]
        return []
    matches = []
    for path, item in _iter_nodes(node):
        speech = item.get('speech')
        who = item.get('who')
        haystack = ' '.join(str(value) for value in (name, who, speech)
                            if value is not None).lower()
        if content in haystack:
            matches.append({'path': path, 'who': who, 'speech': speech})
    return matches
