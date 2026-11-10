"""Project state for the browser's world, forest and story tools."""

from copy import deepcopy
import hashlib
from pathlib import Path
import os
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import forests
import gres
import story
from world import WorldError
from worldserve import State


def atomic_write(path, write):
    with TemporaryDirectory(dir=path.parent) as directory:
        staged = Path(directory) / path.name
        write(staged)
        os.replace(staged, path)


def verify_source(archives, source):
    name = source['file']
    entry = archives.resolve(name)
    if entry is None or hashlib.sha256(entry.read()).hexdigest() != source['sha256']:
        raise WorldError('%s differs from the project base. Open its original archives or use a new project.' % name)


class StoryArchives:
    """Give StoryPatch the previous draft's winning bytes while keeping archive metadata."""

    def __init__(self, base, entries):
        self.base = base
        self.entries = entries
        self.slots = base.slots
        self.archives = base.archives

    def resolve(self, name):
        entry = self.base.resolve(name)
        if name in self.entries:
            return SimpleNamespace(archive=entry.archive, read=lambda: self.entries[name])
        return entry


class Campaign(State):
    def __init__(self, world_path, archives, forests_path=None):
        super().__init__(world_path, archives=archives)
        self.forests_path = forests_path or self.world_path.with_suffix('.forests.json')
        self.story_path = self.world_path.with_suffix('.story.pak')
        self.story_entries = {}
        self.story_index = None
        self.terrain = {}
        if self.story_path.exists():
            identity = gres.read_identity(self.story_path)
            if not identity or gres.identity_differences(identity, gres.file_identity(archives, identity['files'])):
                raise WorldError('The saved story draft belongs to a different archive set.')
            with gres.Archive(self.story_path) as draft:
                self.story_entries = {entry.name: entry.read() for entry in draft}
        for continent in self.world.continents.values():
            for source in continent['sources'].values():
                verify_source(archives, source)

    def forest_model(self):
        if self.forests is None:
            if self.forests_path.exists():
                model = forests.Forests.load_json(self.forests_path, forests.ForestConfig.from_archive_set(self.archives))
                for zones in model.zones.values():
                    for entry in zones.values():
                        if 'source' in entry:
                            verify_source(self.archives, {**entry['source'], 'file': entry['file']})
            else:
                model = forests.Forests._from_set(self.archives, (1, 2, 3))
            self.forests = model
        return self.forests

    def get_story(self):
        if self.story_index is None:
            self.story_index = story.Story._from_set(StoryArchives(self.archives, self.story_entries), (1, 2, 3))
        return self.story_index

    def edit_forest(self, request):
        model = self.forest_model()
        operation, continent, zone = request['op'], request['continent'], request['zone']
        entry = model.zone(continent, zone)
        zones = {**model.zones, continent: {**model.zones[continent], zone: deepcopy(entry)}}
        candidate = forests.Forests(model.config, zones, model.archives)
        values = {name: request[name] for name in ('x', 'y', 'z', 'yaw', 'scale', 'y_scale') if name in request}
        if operation == 'add':
            index, record = candidate.add(continent, zone, model=request.get('model'),
                                          index=request.get('index'), heightmap=self.heightmap(continent), **values)
        elif operation == 'move':
            index = request['index']
            record = candidate.move(continent, zone, index, ground=request.get('ground', False),
                                    heightmap=self.heightmap(continent), **values)
        elif operation == 'remove':
            index = request['index']
            record = candidate.remove(continent, zone, index)
        else:
            raise WorldError('Unknown forest operation.')
        if not request.get('dry_run', True):
            atomic_write(self.forests_path, candidate.save_json)
            self.forests = candidate
            self.revision += 1
        return {'index': index, 'record': record}

    def edit_story(self, request):
        operations = request['operations']
        if not isinstance(operations, list) or not operations:
            raise WorldError('Provide at least one story operation.')
        patch = story.StoryPatch(StoryArchives(self.archives, self.story_entries))
        for operation in operations:
            patch.add(operation)
        entries = {**self.story_entries, **patch.documents()}
        # Decode the changed story before committing its draft.
        story.Story._from_set(StoryArchives(self.archives, entries), patch.continents)
        if not request.get('dry_run', True):
            identity = story.build_identity(self.archives, (1, 2, 3))
            atomic_write(self.story_path, lambda path: gres.write_pak(path, entries, identity=identity))
            self.story_entries = entries
            self.story_index = None
            self.revision += 1
        return {'changes': patch.changes}

    def export_entries(self):
        changed = self.world.changed_modules()
        for continent in sorted({number for number, _ in changed}):
            issues = self.world.validate(continent, self.archives, self.units)
            errors = [issue for issue in issues if issue['level'] == 'error']
            if errors:
                raise WorldError('World validation failed on continent %d (%d errors). Open Validate for details.'
                                 % (continent, len(errors)))
        entries = self.world.export_entries()
        if self.forests_path.exists() or self.forests is not None:
            model = self.forest_model()
            changes = model.changed_zones()
            if changes:
                errors = [issue for issue in model.validate(self.archives)
                          if issue['level'] == 'error' and (issue['continent'], issue['zone']) in changes]
                if errors:
                    raise WorldError('Forest validation failed (%d errors). Open Validate for details.' % len(errors))
                entries.update(model.export_entries())
        entries.update(self.story_entries)
        return entries
