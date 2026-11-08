"""Continent world model: modules, placements, transforms, validation and export."""
import copy
import hashlib
import json
import math
from pathlib import Path

import gres
import lua_data

FORMAT = 'attt-world/1'
MODULES = {
    'towns': ('continent%dtowns.lua', 'Town'),
    'npcs': ('continent%dnpcs.lua', 'NPC'),
    'saos': ('continent%dsaos.lua', 'SAO'),
    'armies': ('continent%darmies.lua', 'Army'),
    'armypos': ('continent%darmypos.lua', 'ArmyPos'),
}
POSITION_KINDS = {'npc': 2, 'object': 3, 'tree': 2}
SECTIONS = {'npc': 'Npcs', 'object': 'Objs', 'tree': 'Trees'}
ROTATION_KEYS = {'npc': 3, 'tree': 3, 'object': 4}


class WorldError(ValueError):
    pass


def _int_key(key):
    if isinstance(key, str):
        try:
            value = int(key, 10)
        except ValueError:
            return key
        if str(value) == key:
            return value
    return key


def to_jsonable(value):
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def from_jsonable(value):
    if isinstance(value, dict):
        return {_int_key(key): from_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [from_jsonable(item) for item in value]
    return value


def canonical(value):
    return json.dumps(to_jsonable(value), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


class World:
    def __init__(self, continents=None, archives=None):
        self.continents = continents or {}
        self.archives = archives or []

    # --- loading -----------------------------------------------------------
    @classmethod
    def load_archives(cls, paths, continents=(1, 2, 3)):
        archive_set = gres.ArchiveSet(paths)
        try:
            return cls._from_set(archive_set, continents)
        finally:
            archive_set.close()

    @classmethod
    def _from_set(cls, archive_set, continents):
        world = cls(archives=[{'slot': archive_set.slots and slot,
                               'path': str(archive_set.archives[slot].path)}
                              for slot in archive_set.slots])
        for continent in continents:
            entry = {'sources': {}, 'modules': {}}
            for module, (pattern, global_name) in MODULES.items():
                filename = pattern % continent
                resolved = archive_set.resolve(filename)
                if resolved is None:
                    continue
                data = resolved.read()
                try:
                    table = lua_data.load_module(data, global_name)
                except lua_data.LuaDataError as error:
                    raise WorldError('%s from %s cannot be decoded as data: %s' %
                                     (filename, resolved.archive.path.name, error))
                if not isinstance(table, dict):
                    raise WorldError('%s does not define a table' % filename)
                entry['modules'][module] = table
                entry['sources'][module] = {
                    'file': filename,
                    'archive': resolved.archive.path.name,
                    'slot': resolved.archive.slot,
                    'source_format': 'bytecode' if data[:4] == b'\x1bLua' else 'source',
                    'global': global_name,
                    'sha256': hashlib.sha256(data).hexdigest(),
                    'emitted_sha256': hash_emitted(global_name, table),
                }
            if entry['modules']:
                world.continents[continent] = entry
        return world

    @classmethod
    def load_json(cls, path):
        with open(path, encoding='utf-8') as stream:
            document = json.load(stream)
        if document.get('format') != FORMAT:
            raise WorldError('%s is not an %s document' % (path, FORMAT))
        continents = {}
        for key, entry in document['continents'].items():
            continents[int(key)] = {
                'modules': {name: from_jsonable(table) for name, table in entry['modules'].items()},
                'sources': entry.get('sources', {}),
            }
        return cls(continents, document.get('archives', []))

    def document(self):
        return {
            'format': FORMAT,
            'archives': self.archives,
            'continents': {str(key): entry for key, entry in sorted(self.continents.items())},
        }

    def save_json(self, path):
        with open(path, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(to_jsonable(self.document()), stream, ensure_ascii=False, indent=1,
                      allow_nan=False, sort_keys=True)
            stream.write('\n')

    # --- access ------------------------------------------------------------
    def module(self, continent, name):
        try:
            return self.continents[continent]['modules'][name]
        except KeyError:
            raise WorldError('continent %s has no %s module' % (continent, name))

    def towns(self, continent):
        return self.module(continent, 'towns')

    def army_positions(self, continent):
        return self.module(continent, 'armypos')

    def army_position(self, continent, name):
        try:
            entry = self.army_positions(continent)[name]
        except KeyError:
            raise WorldError('unknown army position %s on continent %s' % (name, continent))
        if not isinstance(entry, dict):
            raise WorldError('army position %s is not a table' % name)
        return entry

    def house_entry(self, continent, town, house):
        town_entry = self.towns(continent).get(town)
        if town_entry is None:
            raise WorldError('unknown town %s' % town)
        house_entry = (town_entry.get('Houses') or {}).get(house)
        if house_entry is None:
            raise WorldError('unknown house %s in %s' % (house, town))
        return town_entry, house_entry

    def placements(self, continent, kinds=('npc', 'object', 'tree')):
        towns = self.towns(continent)
        for town_name, town in towns.items():
            for house_name, house in (town.get('Houses') or {}).items():
                sections = {'npc': 'Npcs', 'object': 'Objs', 'tree': 'Trees'}
                for kind in kinds:
                    for index, placement in (house.get(sections[kind]) or {}).items():
                        yield Placement(continent, town_name, town, house_name, house, kind, index, placement)

    def town_names(self, continent):
        return sorted(self.towns(continent))

    def source_modules(self):
        result = []
        for continent, entry in sorted(self.continents.items()):
            for name, source in entry.get('sources', {}).items():
                if source.get('source_format') == 'source':
                    result.append({'continent': continent, 'module': name,
                                   'archive': source.get('archive'),
                                   'slot': source.get('slot')})
        return result

    def identity_files(self):
        """Source module names that make up this model's base build."""
        return [source['file']
                for _, entry in sorted(self.continents.items())
                for source in entry.get('sources', {}).values()
                if source.get('file')]

    def placement(self, continent, town, house, kind, index):
        town_entry, house_entry = self.house_entry(continent, town, house)
        section = SECTIONS[kind]
        try:
            return Placement(continent, town, town_entry, house, house_entry, kind, index,
                             house_entry[section][index])
        except (KeyError, TypeError):
            raise WorldError('unknown %s %s in %s/%s' % (kind, index, town, house))

    def find_placement(self, continent, town, house, kind, index=None, name=None):
        if kind not in SECTIONS:
            raise WorldError('unknown placement kind %s' % kind)
        self.house_entry(continent, town, house)
        if index is not None:
            return self.placement(continent, town, house, kind, index)
        if name is None:
            raise WorldError('pass an index or a name')
        candidates = [placement for placement in self.placements(continent, kinds=(kind,))
                      if placement.town_name == town and placement.house_name == house and
                      str(placement.name) == str(name)]
        if len(candidates) != 1:
            raise WorldError('%d placements named %s in %s/%s' %
                             (len(candidates), name, town, house))
        return candidates[0]

    def flat_entities(self, continent):
        result = []
        for placement in self.placements(continent):
            result.append(placement.record())
        return result

    # --- edits -------------------------------------------------------------
    def move_local(self, continent, town, house, kind, index, x=None, y=None, z=None):
        placement = self.placement(continent, town, house, kind, index)
        position = placement.position
        for key, value in ((1, x), (2, y), (3, z)):
            if value is not None:
                position[key] = float(value)
        return placement

    def move_world(self, continent, town, house, kind, index, x=None, z=None):
        placement = self.placement(continent, town, house, kind, index)
        world_x, world_z = placement.world_xz
        offset_x = 0.0 if x is None else float(x) - world_x
        offset_z = 0.0 if z is None else float(z) - world_z
        local_x, local_z = placement.to_local_offset(offset_x, offset_z)
        position = placement.position
        position[1] = position.get(1, 0.0) + local_x
        position[3] = position.get(3, 0.0) + local_z
        return placement

    def local_from_world(self, continent, town, house, x, z):
        town_entry, house_entry = self.house_entry(continent, town, house)
        town_pos = town_entry.get('Pos') or {}
        house_pos = house_entry.get('Pos') or {}
        town_rot = float(town_entry.get('Rot', 0.0))
        house_rot = float(house_entry.get('Rot', 0.0))
        house_x, house_z = rotate(house_pos.get(1, 0.0), house_pos.get(3, 0.0), town_rot)
        offset_x = float(x) - (town_pos.get(1, 0.0) + house_x)
        offset_z = float(z) - (town_pos.get(3, 0.0) + house_z)
        return rotate(offset_x, offset_z, -(town_rot + house_rot))

    def add_placement(self, continent, town, house, kind, entry, index=None):
        town_entry, house_entry = self.house_entry(continent, town, house)
        if not isinstance(entry, dict):
            raise WorldError('%s placement must be a table' % kind)
        if _position(entry, kind) is None:
            raise WorldError('%s placement needs a position at key %d' % (kind, POSITION_KINDS[kind]))
        section = house_entry.get(SECTIONS[kind])
        if section is None:
            section = {}
            house_entry[SECTIONS[kind]] = section
        if not isinstance(section, dict):
            raise WorldError('%s in %s/%s is not a table' % (SECTIONS[kind], town, house))
        if index is None:
            index = max((key for key in section if isinstance(key, int)), default=0) + 1
        elif not isinstance(index, int) or isinstance(index, bool) or index < 1:
            raise WorldError('index must be a positive integer')
        elif index in section:
            raise WorldError('%s index %s already exists in %s/%s' % (kind, index, town, house))
        section[index] = entry
        return Placement(continent, town, town_entry, house, house_entry, kind, index, entry)

    def remove_placement(self, continent, town, house, kind, index):
        _, house_entry = self.house_entry(continent, town, house)
        section = house_entry.get(SECTIONS[kind])
        if not isinstance(section, dict) or index not in section:
            raise WorldError('unknown %s %s in %s/%s' % (kind, index, town, house))
        return section.pop(index)

    def clone_placement(self, continent, town, house, kind, index, index_new=None):
        source = self.placement(continent, town, house, kind, index)
        return self.add_placement(continent, town, house, kind, clone(source.entry), index=index_new)

    def set_rotation(self, continent, town, house, kind, index, rotation):
        placement = self.placement(continent, town, house, kind, index)
        if kind == 'object':
            entry = placement.entry.get(4)
            if not isinstance(entry, dict):
                entry = {1: 0.0, 2: 0.0, 3: 0.0}
                placement.entry[4] = entry
            entry[2] = float(rotation)
        else:
            placement.entry[3] = float(rotation)
        return placement

    def add_town(self, continent, name, x, y, z, rotation=0.0):
        towns = self.towns(continent)
        if not isinstance(name, str) or not name:
            raise WorldError('town name must be a non-empty string')
        if name in towns:
            raise WorldError('town %s already exists' % name)
        for key, value in (('x', x), ('y', y), ('z', z), ('rotation', rotation)):
            if not _finite_number(value):
                raise WorldError('%s must be a finite number' % key)
        entry = {'Pos': {1: float(x), 2: float(y), 3: float(z)},
                 'Rot': float(rotation), 'Houses': {}}
        towns[name] = entry
        return entry

    def add_house(self, continent, town, name, x, y, z, rotation=0.0, sections=None):
        town_entry = self.towns(continent).get(town)
        if town_entry is None:
            raise WorldError('unknown town %s' % town)
        if not isinstance(name, str) or not name:
            raise WorldError('house name must be a non-empty string')
        houses = town_entry.get('Houses')
        if houses is None:
            houses = {}
            town_entry['Houses'] = houses
        if not isinstance(houses, dict):
            raise WorldError('Houses in %s is not a table' % town)
        if name in houses:
            raise WorldError('house %s already exists in %s' % (name, town))
        for key, value in (('x', x), ('y', y), ('z', z), ('rotation', rotation)):
            if not _finite_number(value):
                raise WorldError('%s must be a finite number' % key)
        entry = {'Pos': {1: float(x), 2: float(y), 3: float(z)}, 'Rot': float(rotation)}
        for section, table in (sections or {}).items():
            if section not in SECTIONS.values():
                raise WorldError('unsupported house section %s' % section)
            if not isinstance(table, dict):
                raise WorldError('house section %s must be a table' % section)
            entry[section] = table
        houses[name] = entry
        return entry

    def remove_town(self, continent, name, force=False):
        towns = self.towns(continent)
        if name not in towns:
            raise WorldError('unknown town %s' % name)
        houses = towns[name].get('Houses') if isinstance(towns[name], dict) else None
        houses = houses if isinstance(houses, dict) else {}
        placements = sum(_placement_count(house) for house in houses.values())
        if (houses or placements) and not force:
            raise WorldError('town %s still contains %d house(s) and %d placement(s); '
                             'pass force to remove it' % (name, len(houses), placements))
        return towns.pop(name)

    def remove_house(self, continent, town, name, force=False):
        town_entry = self.towns(continent).get(town)
        if town_entry is None:
            raise WorldError('unknown town %s' % town)
        if not isinstance(town_entry, dict):
            raise WorldError('town %s is not a table' % town)
        houses = town_entry.get('Houses')
        if not isinstance(houses, dict) or name not in houses:
            raise WorldError('unknown house %s in %s' % (name, town))
        placements = _placement_count(houses[name])
        if placements and not force:
            raise WorldError('house %s in %s still contains %d placement(s); '
                             'pass force to remove it' % (name, town, placements))
        return houses.pop(name)

    def add_army(self, continent, name, definition=None, x=None, z=None, radius=None):
        armies = self.module(continent, 'armies')
        if not isinstance(name, str) or not name:
            raise WorldError('army name must be a non-empty string')
        if name in armies:
            raise WorldError('army %s already exists' % name)
        definition = make_army() if definition is None else clone(definition)
        if not isinstance(definition, dict):
            raise WorldError('army definition must be a table')
        position = None
        if x is not None or z is not None or radius is not None:
            if x is None or z is None:
                raise WorldError('army position needs both x and z')
            if not (_finite_number(x) and _finite_number(z)):
                raise WorldError('army position needs finite x and z')
            if radius is not None and (not _finite_number(radius) or radius < 0):
                raise WorldError('army radius must be a non-negative number')
            positions = self.continents[continent]['modules'].get('armypos')
            if positions is None:
                positions = {}
                self.continents[continent]['modules']['armypos'] = positions
            if not isinstance(positions, dict):
                raise WorldError('armypos module is not a table')
            if name in positions:
                raise WorldError('army position %s already exists' % name)
            position = {'x': float(x), 'z': float(z)}
            if radius is not None:
                position['radius'] = float(radius)
            positions[name] = position
        armies[name] = definition
        return definition

    def remove_army(self, continent, name):
        armies = self.module(continent, 'armies')
        if name not in armies:
            raise WorldError('unknown army %s' % name)
        position = None
        positions = self.continents[continent]['modules'].get('armypos')
        if isinstance(positions, dict):
            position = positions.pop(name, None)
        return {'army': armies.pop(name), 'position': position}

    def move_army(self, continent, name, x=None, z=None, radius=None):
        entry = self.army_position(continent, name)
        for key, value in (('x', x), ('z', z), ('radius', radius)):
            if value is None:
                continue
            if not _finite_number(value):
                raise WorldError('army position %s: %s must be a finite number' % (name, key))
            entry[key] = float(value)
        if 'radius' in entry and (not _finite_number(entry['radius']) or entry['radius'] < 0):
            raise WorldError('army position %s: radius must be a non-negative number' % name)
        return entry

    def snap_placements(self, continent, map_, offset=0.0, kinds=('npc', 'object', 'tree'),
                        town=None, house=None, dry_run=False):
        """Reset placement Y offsets; the engine adds the terrain height at runtime."""
        changed, skipped = [], []
        for placement in self.placements(continent, kinds=kinds):
            if town is not None and placement.town_name != town:
                continue
            if house is not None and placement.house_name != house:
                continue
            world_x, world_z = placement.world_xz
            elevation = map_.sample(world_x, world_z)
            if elevation is None:
                skipped.append({'id': placement.record()['id'], 'world': [world_x, world_z]})
                continue
            position = placement.position
            current = float(position.get(2, 0.0))
            if abs(current - offset) < 1e-4:
                continue
            if not dry_run:
                position[2] = float(offset)
            changed.append({'id': placement.record()['id'], 'world': [world_x, world_z],
                            'elevation': elevation, 'from': current, 'to': float(offset)})
        return changed, skipped

    # --- validation --------------------------------------------------------
    def validate(self, continent, archive_set=None, units=None):
        issues = []
        npcs = self.continents[continent]['modules'].get('npcs', {})
        towns = self.towns(continent)
        seen_towns = set()
        for town_name, town in towns.items():
            if town_name in seen_towns:
                issues.append({'level': 'error', 'kind': 'duplicate-town', 'town': town_name})
            seen_towns.add(town_name)
            if not isinstance(town.get('Pos'), dict):
                issues.append({'level': 'error', 'kind': 'town-without-position', 'town': town_name})
            elif not _transform_values(town['Pos'], town.get('Rot', 0.0)):
                issues.append({'level': 'error', 'kind': 'bad-town-transform', 'town': town_name})
            houses = town.get('Houses')
            if not isinstance(houses, dict):
                issues.append({'level': 'warning', 'kind': 'town-without-houses', 'town': town_name})
                continue
            for house_name, house in houses.items():
                if not isinstance(house, dict):
                    issues.append({'level': 'error', 'kind': 'bad-house', 'town': town_name,
                                   'house': house_name})
                    continue
                if not _transform_values(house.get('Pos'), house.get('Rot', 0.0)):
                    issues.append({'level': 'error', 'kind': 'bad-house-transform',
                                   'town': town_name, 'house': house_name})
                for index, placement in (house.get('Npcs') or {}).items():
                    name = placement.get(1) if isinstance(placement, dict) else None
                    if isinstance(name, str) and name not in npcs and name != 'OWNER':
                        issues.append({'level': 'error', 'kind': 'undefined-npc', 'town': town_name,
                                       'house': house_name, 'index': index, 'name': name})
                    if not _position(placement, 'npc'):
                        issues.append({'level': 'warning', 'kind': 'npc-without-position',
                                       'town': town_name, 'house': house_name, 'index': index})
                for index, placement in (house.get('Objs') or {}).items():
                    model = placement.get(1) if isinstance(placement, dict) else None
                    if not isinstance(model, str):
                        issues.append({'level': 'error', 'kind': 'object-without-model',
                                       'town': town_name, 'house': house_name, 'index': index})
                    elif archive_set is not None and not _model_present(archive_set, model):
                        issues.append({'level': 'error', 'kind': 'missing-model', 'town': town_name,
                                       'house': house_name, 'index': index, 'model': model})
                    gizmo = None
                    if isinstance(placement, dict) and isinstance(placement.get(2), dict):
                        gizmo = placement[2].get(1)
                    if (archive_set is not None and isinstance(gizmo, str) and
                            not _model_present(archive_set, gizmo)):
                        issues.append({'level': 'error', 'kind': 'missing-gizmo', 'town': town_name,
                                       'house': house_name, 'index': index, 'gizmo': gizmo})
                    if not _position(placement, 'object'):
                        issues.append({'level': 'warning', 'kind': 'object-without-position',
                                       'town': town_name, 'house': house_name, 'index': index})
                for index, placement in (house.get('Trees') or {}).items():
                    model = placement.get(1) if isinstance(placement, dict) else None
                    if not isinstance(model, str):
                        issues.append({'level': 'error', 'kind': 'tree-without-model',
                                       'town': town_name, 'house': house_name, 'index': index})
                    elif archive_set is not None and not _model_present(archive_set, model):
                        issues.append({'level': 'error', 'kind': 'missing-model', 'town': town_name,
                                       'house': house_name, 'index': index, 'model': model})
                    if not _position(placement, 'tree'):
                        issues.append({'level': 'warning', 'kind': 'tree-without-position',
                                       'town': town_name, 'house': house_name, 'index': index})
        armies = self.continents[continent]['modules'].get('armies', {})
        positions = self.continents[continent]['modules'].get('armypos', {})
        for name, position in positions.items():
            if isinstance(name, str) and name not in armies:
                issues.append({'level': 'warning', 'kind': 'army-position-without-army', 'name': name})
            if not isinstance(position, dict):
                issues.append({'level': 'error', 'kind': 'bad-army-position', 'name': name})
                continue
            if not all(_finite_number(position.get(key)) for key in ('x', 'z')):
                issues.append({'level': 'error', 'kind': 'bad-army-position', 'name': name})
            radius = position.get('radius')
            if radius is not None and (not _finite_number(radius) or radius < 0):
                issues.append({'level': 'error', 'kind': 'bad-army-position', 'name': name})
        for name, army in armies.items():
            if not isinstance(army, dict):
                issues.append({'level': 'error', 'kind': 'bad-army', 'name': name})
                continue
            attitude = army.get('Attitude')
            if not isinstance(attitude, str):
                issues.append({'level': 'error', 'kind': 'bad-army', 'name': name})
            elif attitude not in ARMY_ATTITUDES:
                issues.append({'level': 'warning', 'kind': 'unknown-army-attitude',
                               'name': name, 'attitude': attitude})
            if not isinstance(army.get('DisplayName'), str):
                issues.append({'level': 'error', 'kind': 'bad-army', 'name': name})
            if not isinstance(army.get('Standard'), str) or not army.get('Standard'):
                issues.append({'level': 'error', 'kind': 'bad-army', 'name': name})
            elif archive_set is not None and not _standard_present(archive_set, army['Standard']):
                issues.append({'level': 'error', 'kind': 'missing-standard', 'name': name,
                               'standard': army['Standard']})
            troops = army.get('TroopList')
            if not isinstance(troops, dict):
                issues.append({'level': 'error', 'kind': 'bad-army-trooplist', 'name': name})
                continue
            for index, troop in troops.items():
                unit = troop.get('Unit') if isinstance(troop, dict) else None
                quantity = troop.get('Quantity') if isinstance(troop, dict) else None
                if (not isinstance(unit, str) or not unit or
                        not _finite_number(quantity) or quantity <= 0):
                    issues.append({'level': 'error', 'kind': 'bad-army-troop',
                                   'name': name, 'index': index})
                elif units is not None and unit not in units:
                    issues.append({'level': 'error', 'kind': 'missing-unit', 'name': name,
                                   'index': index, 'unit': unit})
        return issues

    # --- export ------------------------------------------------------------
    def changed_modules(self):
        changed = {}
        for continent, entry in self.continents.items():
            modules = entry.get('modules', {})
            sources = entry.get('sources', {})
            for name, table in modules.items():
                global_name = MODULES[name][1]
                current = hash_emitted(global_name, table)
                if sources.get(name, {}).get('emitted_sha256') != current:
                    changed[(continent, name)] = table
        return changed

    def export_entries(self):
        changed = self.changed_modules()
        entries = {}
        for (continent, name), table in changed.items():
            filename = MODULES[name][0] % continent
            global_name = MODULES[name][1]
            entries[filename] = lua_data.emit_source({global_name: table}, order=[global_name])
        return entries

    def export_pak(self, path, slot=None, overwrite=False, archive_set=None):
        entries = self.export_entries()
        if not entries:
            raise WorldError('no modules changed')
        folder = Path(path)
        if not folder.is_dir():
            raise WorldError('output folder does not exist: %s' % folder)
        if slot is None:
            used = {source.get('slot') for entry in self.continents.values()
                    for source in entry.get('sources', {}).values()}
            used.update(archive.get('slot') for archive in self.archives)
            for candidate in folder.glob('Resource*.pak'):
                used.add(gres.archive_slot(candidate.name))
            used.discard(None)
            slot = max(used, default=0) + 1
        destination = folder / ('Resource%d.pak' % slot)
        identity = None
        if archive_set is not None:
            identity = gres.file_identity(archive_set,
                                          self.identity_files() or list(entries))
            if not identity['files']:
                identity = None
        gres.write_pak(destination, entries, overwrite=overwrite, identity=identity)
        return str(destination), entries


def hash_emitted(global_name, table):
    return hashlib.sha256(lua_data.emit_source({global_name: table}, order=[global_name])).hexdigest()


def _position(placement, kind):
    if not isinstance(placement, dict):
        return None
    position = placement.get(POSITION_KINDS[kind])
    if isinstance(position, dict) and all(key in position for key in (1, 3)):
        return position
    return None


def _finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool) and
            math.isfinite(value))


def _transform_values(position, rotation):
    return (isinstance(position, dict) and
            all(_finite_number(position.get(key, 0.0)) for key in (1, 2, 3)) and
            _finite_number(rotation))


def make_npc(name, x, y, z, rotation=0.0, kind='Creature'):
    return {1: name, 2: {1: float(x), 2: float(y), 3: float(z)},
            3: float(rotation), 4: kind}


def make_tree(model, x, y, z, rotation=0.0):
    return {1: model, 2: {1: float(x), 2: float(y), 3: float(z)}, 3: float(rotation)}


def make_object(model, x, y, z, rotation=0.0, scale=1.0, gizmo=None,
                group='Objects01', lod='farest', flag=False):
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    scale_x, scale_y, scale_z = scale
    entry = {
        1: model,
        3: {1: float(x), 2: float(y), 3: float(z)},
        4: {1: 0.0, 2: float(rotation), 3: 0.0},
        5: {1: float(scale_x), 2: float(scale_y), 3: float(scale_z)},
        6: lod,
        7: bool(flag),
        8: group,
    }
    if gizmo != '':
        entry[2] = {1: gizmo or (model + 'Gizmo'), 2: group, 3: 'medium'}
    return entry


ARMY_ATTITUDES = ('Disabled', 'Neutral', 'Agressive', 'Dead')


def make_army(display_name='', attitude='Disabled', standard='stSamael', troops=()):
    if not isinstance(display_name, str):
        raise WorldError('display name must be a string')
    if attitude not in ARMY_ATTITUDES:
        raise WorldError('attitude must be one of %s' % ', '.join(ARMY_ATTITUDES))
    if not isinstance(standard, str) or not standard:
        raise WorldError('standard must be a non-empty string')
    troop_list = {}
    for index, item in enumerate(troops, 1):
        try:
            unit, quantity = item
        except (TypeError, ValueError):
            raise WorldError('troops must be (unit, quantity) pairs')
        if not isinstance(unit, str) or not unit:
            raise WorldError('troop unit must be a non-empty string')
        if not _finite_number(quantity) or quantity <= 0:
            raise WorldError('troop quantity must be a positive number')
        troop_list[index] = {'Unit': unit, 'Quantity': float(quantity)}
    return {'Attitude': attitude, 'DisplayName': display_name,
            'Standard': standard, 'TroopList': troop_list}


def _placement_count(house):
    if not isinstance(house, dict):
        return 0
    return sum(len(section) for section in (house.get(name) or {}
                                            for name in SECTIONS.values())
               if isinstance(section, dict))


def _model_present(archive_set, model):
    lowered = model.lower()
    for extension in ('.gdl', '.skm', '.lskm', '.ef'):
        if archive_set.has(lowered + extension):
            return True
    return False


def _standard_present(archive_set, standard):
    suffix = standard[2:].lower() if standard.lower().startswith('st') else standard.lower()
    return any(archive_set.has('standard' + suffix + extension)
               for extension in ('.lskm', '.lgdl', '.gdl'))


class Placement:
    def __init__(self, continent, town_name, town, house_name, house, kind, index, entry):
        self.continent = continent
        self.town_name = town_name
        self.town = town
        self.house_name = house_name
        self.house = house
        self.kind = kind
        self.index = index
        self.entry = entry

    @property
    def position(self):
        position = _position(self.entry, self.kind)
        if position is None:
            raise WorldError('%s %s in %s/%s has no position' %
                             (self.kind, self.index, self.town_name, self.house_name))
        return position

    @property
    def name(self):
        if self.kind == 'npc':
            return self.entry.get(1)
        if self.kind in ('object', 'tree'):
            return self.entry.get(1)
        return None

    @property
    def local_xz(self):
        position = self.position
        return float(position.get(1, 0.0)), float(position.get(3, 0.0))

    def _components(self):
        town_pos = self.town.get('Pos') or {}
        house_pos = self.house.get('Pos') or {}
        town_rot = float(self.town.get('Rot', 0.0))
        house_rot = float(self.house.get('Rot', 0.0))
        return town_pos, house_pos, town_rot, house_rot

    @property
    def world_xz(self):
        town_pos, house_pos, town_rot, house_rot = self._components()
        house_x, house_z = rotate(house_pos.get(1, 0.0), house_pos.get(3, 0.0), town_rot)
        local_x, local_z = rotate(self.position.get(1, 0.0), self.position.get(3, 0.0),
                                  town_rot + house_rot)
        return (town_pos.get(1, 0.0) + house_x + local_x,
                town_pos.get(3, 0.0) + house_z + local_z)

    @property
    def town_y(self):
        return float((self.town.get('Pos') or {}).get(2, 0.0))

    @property
    def house_y(self):
        return float((self.house.get('Pos') or {}).get(2, 0.0))

    @property
    def world_y(self):
        return self.town_y + self.house_y + float(self.position.get(2, 0.0))

    @property
    def world_position(self):
        x, z = self.world_xz
        return (x, self.world_y, z)

    def to_local_offset(self, offset_x, offset_z):
        _, _, town_rot, house_rot = self._components()
        return rotate(offset_x, offset_z, -(town_rot + house_rot))

    def record(self):
        x, z = self.world_xz
        return {
            'id': 'c%d/%s/%s/%s/%s' % (self.continent, self.town_name, self.house_name,
                                       self.kind, self.index),
            'continent': self.continent,
            'town': self.town_name,
            'house': self.house_name,
            'kind': self.kind,
            'index': self.index,
            'name': self.name,
            'local': [self.position.get(1, 0.0), self.position.get(2, 0.0), self.position.get(3, 0.0)],
            'world': [x, self.world_y, z],
        }


def rotate(x, z, degrees):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    return x * cosine - z * sine, x * sine + z * cosine


def clone(value):
    return copy.deepcopy(value)


PATCH_FORMAT = 'attt-world-patch/1'


def apply_patch(world, document, heightmaps=None):
    if not isinstance(document, dict):
        raise WorldError('patch must be a JSON object')
    if document.get('format') not in (None, PATCH_FORMAT):
        raise WorldError('unsupported patch format %r' % document.get('format'))
    operations = document.get('operations')
    if not isinstance(operations, list):
        raise WorldError('patch must contain an operations list')
    results = []
    for number, operation in enumerate(operations, 1):
        name = operation.get('op') if isinstance(operation, dict) else None
        handler = _PATCH_OPERATIONS.get(name)
        try:
            if handler is None:
                raise WorldError('unknown operation %r' % name)
            results.append(handler(world, operation, heightmaps or {}))
        except WorldError as error:
            raise WorldError('operation %d (%s): %s' % (number, name, error))
    return results


def _operation_int(operation, key, minimum=None):
    value = operation.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise WorldError('%s must be an integer' % key)
    if minimum is not None and value < minimum:
        raise WorldError('%s must be at least %d' % (key, minimum))
    return value


def _operation_number(operation, key, default=None, required=False):
    value = operation.get(key, default)
    if value is None:
        if required:
            raise WorldError('%s is required' % key)
        return None
    if not _finite_number(value):
        raise WorldError('%s must be a finite number' % key)
    return float(value)


def _operation_string(operation, key):
    value = operation.get(key)
    if not isinstance(value, str) or not value:
        raise WorldError('%s must be a non-empty string' % key)
    return value


def _operation_placement(world, operation):
    continent = _operation_int(operation, 'continent', 1)
    town = _operation_string(operation, 'town')
    house = _operation_string(operation, 'house')
    kind = _operation_string(operation, 'kind')
    if kind not in SECTIONS:
        raise WorldError('kind must be one of %s' % ', '.join(sorted(SECTIONS)))
    index = operation.get('index')
    if index is not None:
        _operation_int(operation, 'index', 1)
    return world.find_placement(continent, town, house, kind, index=index,
                                name=operation.get('name'))


def _patch_move(world, operation, _heightmaps):
    placement = _operation_placement(world, operation)
    if operation.get('world'):
        if operation.get('x') is None and operation.get('z') is None:
            raise WorldError('move needs x or z')
        placement = world.move_world(
            placement.continent, placement.town_name, placement.house_name, placement.kind,
            placement.index, x=_operation_number(operation, 'x'),
            z=_operation_number(operation, 'z'))
    else:
        if all(operation.get(key) is None for key in ('x', 'y', 'z')):
            raise WorldError('move needs x, y or z')
        placement = world.move_local(
            placement.continent, placement.town_name, placement.house_name, placement.kind,
            placement.index, x=_operation_number(operation, 'x'),
            y=_operation_number(operation, 'y'), z=_operation_number(operation, 'z'))
    return placement.record()


def _patch_add(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    town = _operation_string(operation, 'town')
    house = _operation_string(operation, 'house')
    kind = _operation_string(operation, 'kind')
    if kind not in SECTIONS:
        raise WorldError('kind must be one of %s' % ', '.join(sorted(SECTIONS)))
    name = _operation_string(operation, 'name')
    x = _operation_number(operation, 'x', 0.0)
    y = _operation_number(operation, 'y', 0.0)
    z = _operation_number(operation, 'z', 0.0)
    if operation.get('world'):
        x, z = world.local_from_world(continent, town, house, x, z)
    rotation = _operation_number(operation, 'rot', 0.0)
    if kind == 'npc':
        entry = make_npc(name, x, y, z, rotation=rotation,
                         kind=operation.get('npc_kind', 'Creature'))
    elif kind == 'object':
        entry = make_object(name, x, y, z, rotation=rotation,
                            scale=_operation_number(operation, 'scale', 1.0),
                            gizmo=operation.get('gizmo'),
                            group=operation.get('group', 'Objects01'),
                            lod=operation.get('lod', 'farest'),
                            flag=bool(operation.get('flag', False)))
    else:
        entry = make_tree(name, x, y, z, rotation=rotation)
    index = operation.get('index')
    if index is not None:
        _operation_int(operation, 'index', 1)
    placement = world.add_placement(continent, town, house, kind, entry, index=index)
    return placement.record()


def _patch_remove(world, operation, _heightmaps):
    placement = _operation_placement(world, operation)
    removed = world.remove_placement(placement.continent, placement.town_name,
                                     placement.house_name, placement.kind, placement.index)
    return {'id': placement.record()['id'], 'entry': to_jsonable(removed)}


def _patch_clone(world, operation, _heightmaps):
    source = _operation_placement(world, operation)
    index_new = operation.get('index_new')
    if index_new is not None:
        _operation_int(operation, 'index_new', 1)
    placement = world.clone_placement(source.continent, source.town_name, source.house_name,
                                      source.kind, source.index, index_new=index_new)
    if operation.get('x') is not None or operation.get('z') is not None:
        if operation.get('world'):
            placement = world.move_world(
                placement.continent, placement.town_name, placement.house_name, placement.kind,
                placement.index, x=_operation_number(operation, 'x'),
                z=_operation_number(operation, 'z'))
        else:
            placement = world.move_local(
                placement.continent, placement.town_name, placement.house_name, placement.kind,
                placement.index, x=_operation_number(operation, 'x'),
                z=_operation_number(operation, 'z'))
    if operation.get('rot') is not None:
        placement = world.set_rotation(
            placement.continent, placement.town_name, placement.house_name, placement.kind,
            placement.index, _operation_number(operation, 'rot'))
    return placement.record()


def _patch_rotate(world, operation, _heightmaps):
    placement = _operation_placement(world, operation)
    rotation = _operation_number(operation, 'rot', required=True)
    world.set_rotation(placement.continent, placement.town_name, placement.house_name,
                      placement.kind, placement.index, rotation)
    return placement.record()


def _patch_move_army(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    name = _operation_string(operation, 'name')
    if all(operation.get(key) is None for key in ('x', 'z', 'radius')):
        raise WorldError('move-army needs x, z or radius')
    return world.move_army(continent, name, x=_operation_number(operation, 'x'),
                           z=_operation_number(operation, 'z'),
                           radius=_operation_number(operation, 'radius'))


def _patch_add_town(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    name = _operation_string(operation, 'name')
    entry = world.add_town(continent, name,
                           _operation_number(operation, 'x', required=True),
                           _operation_number(operation, 'y', 0.0),
                           _operation_number(operation, 'z', required=True),
                           rotation=_operation_number(operation, 'rot', 0.0))
    return {'name': name, 'entry': to_jsonable(entry)}


def _patch_add_house(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    town = _operation_string(operation, 'town')
    name = _operation_string(operation, 'name')
    sections = operation.get('sections') or {}
    if not isinstance(sections, dict):
        raise WorldError('sections must be an object')
    entry = world.add_house(continent, town, name,
                            _operation_number(operation, 'x', required=True),
                            _operation_number(operation, 'y', 0.0),
                            _operation_number(operation, 'z', required=True),
                            rotation=_operation_number(operation, 'rot', 0.0),
                            sections=sections)
    return {'town': town, 'name': name, 'entry': to_jsonable(entry)}


def _patch_remove_town(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    name = _operation_string(operation, 'name')
    removed = world.remove_town(continent, name, force=bool(operation.get('force')))
    return {'name': name, 'entry': to_jsonable(removed)}


def _patch_remove_house(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    town = _operation_string(operation, 'town')
    name = _operation_string(operation, 'name')
    removed = world.remove_house(continent, town, name, force=bool(operation.get('force')))
    return {'town': town, 'name': name, 'entry': to_jsonable(removed)}


def _operation_troops(operation):
    value = operation.get('troops')
    if value is None:
        return []
    if not isinstance(value, list):
        raise WorldError('troops must be a list')
    troops = []
    for item in value:
        if isinstance(item, dict):
            unit = item.get('unit', item.get('Unit'))
            quantity = item.get('quantity', item.get('Quantity'))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            unit, quantity = item
        else:
            raise WorldError('each troop must be [unit, quantity] or an object')
        troops.append((unit, quantity))
    return troops


def _patch_add_army(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    name = _operation_string(operation, 'name')
    x = _operation_number(operation, 'x')
    z = _operation_number(operation, 'z')
    radius = _operation_number(operation, 'radius')
    entry = world.add_army(continent, name, make_army(
        display_name=operation.get('display_name', ''),
        attitude=operation.get('attitude', 'Disabled'),
        standard=operation.get('standard', 'stSamael'),
        troops=_operation_troops(operation)), x=x, z=z, radius=radius)
    position = world.army_positions(continent).get(name)
    return {'name': name, 'entry': to_jsonable(entry),
            'position': to_jsonable(position)}


def _patch_remove_army(world, operation, _heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    name = _operation_string(operation, 'name')
    removed = world.remove_army(continent, name)
    return {'name': name, 'army': to_jsonable(removed['army']),
            'position': to_jsonable(removed['position'])}


def _patch_snap(world, operation, heightmaps):
    continent = _operation_int(operation, 'continent', 1)
    map_ = heightmaps.get(continent)
    if map_ is None:
        raise WorldError('snap requires a heightmap for continent %s (pass --game)' % continent)
    kind = operation.get('kind')
    if kind is not None and kind not in SECTIONS:
        raise WorldError('kind must be one of %s' % ', '.join(sorted(SECTIONS)))
    changed, skipped = world.snap_placements(
        continent, map_, offset=_operation_number(operation, 'offset', 0.0),
        kinds=(kind,) if kind else tuple(SECTIONS), town=operation.get('town'),
        house=operation.get('house'))
    limit = operation.get('limit', 50)
    return {'changed': len(changed), 'skipped': len(skipped),
            'placements': changed[:limit], 'outside': skipped[:limit]}


_PATCH_OPERATIONS = {
    'move': _patch_move,
    'add': _patch_add,
    'remove': _patch_remove,
    'clone': _patch_clone,
    'rotate': _patch_rotate,
    'move-army': _patch_move_army,
    'add-town': _patch_add_town,
    'add-house': _patch_add_house,
    'remove-town': _patch_remove_town,
    'remove-house': _patch_remove_house,
    'add-army': _patch_add_army,
    'remove-army': _patch_remove_army,
    'snap': _patch_snap,
}
