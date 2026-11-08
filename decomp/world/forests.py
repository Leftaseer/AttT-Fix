"""Forest zones (.fst), WorldLevel forest config and overlay export.

An .fst file is an array of 68-byte records::

    u32 tree_type_id
    16 floats: 4x4 row-major D3DX matrix (rows 0..2 = rotation/scale,
               row 3 = world x, y, z, 1.0)

`CForests.cpp` `FUN_00558ac0` confirms the 0x44 stride.  The type id is a
0-based index into `WorldLevel.TreesProperties[<forest set>]`; the resulting
entry's first value is the tree name, whose model file is
`<lowercase name>.gdl` (e.g. `Dry101` -> `dry101.gdl`).  Each zone entry in
`WorldLevel.Forest[<continent>]` names the matching `fzone*.fst` file and the
property set it uses.

All 203 configured zones and 24,684 stock records resolve this way; the
unreferenced `fzone4fill1.fst` (162 records) is reported as unconfigured.
"""
import hashlib
import json
import math
import struct
from pathlib import Path

import gres
import lua_data

FORMAT = 'attt-forests/1'
RECORD = struct.Struct('<I16f')
RECORD_SIZE = RECORD.size
CONFIG_FILE = 'worldlevel.lua'


class ForestError(ValueError):
    pass


def _finite(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool) and
            math.isfinite(value))


def _number(value, label):
    if not _finite(value):
        raise ForestError('%s must be a finite number' % label)
    return float(value)


def tree_model(name):
    return str(name).lower() + '.gdl'


def matrix_yaw(matrix):
    """Yaw in degrees for the D3DXMatrixRotationY row-vector convention."""
    return math.degrees(math.atan2(matrix[8], matrix[0]))


def matrix_scale(matrix):
    """Return (horizontal_scale, vertical_scale) from the 3x3 part."""
    return (math.hypot(matrix[0], matrix[8]), abs(matrix[5]))


def make_matrix(yaw=0.0, scale=1.0, y_scale=None):
    if y_scale is None:
        y_scale = scale
    radians = math.radians(yaw)
    cos, sin = math.cos(radians), math.sin(radians)
    return [
        cos * scale, 0.0, -sin * scale, 0.0,
        0.0, y_scale, 0.0, 0.0,
        sin * scale, 0.0, cos * scale, 0.0,
    ]


def make_record(type_id, x, y, z, yaw=0.0, scale=1.0, y_scale=None):
    if not isinstance(type_id, int) or isinstance(type_id, bool) or type_id < 0:
        raise ForestError('tree type must be a non-negative integer')
    return {
        'type': type_id,
        'matrix': make_matrix(yaw, _number(scale, 'scale'),
                              None if y_scale is None else _number(y_scale, 'y_scale')),
        'x': _number(x, 'x'),
        'y': _number(y, 'y'),
        'z': _number(z, 'z'),
    }


def parse_fst(data):
    if len(data) % RECORD_SIZE:
        raise ForestError('%d bytes is not a whole number of %d-byte .fst records' %
                          (len(data), RECORD_SIZE))
    records = []
    for offset in range(0, len(data), RECORD_SIZE):
        values = RECORD.unpack_from(data, offset)
        type_id = values[0]
        matrix = list(values[1:13])
        x, y, z, tail = values[13:17]
        if not all(_finite(value) for value in matrix + [x, y, z]):
            raise ForestError('record at offset %d contains non-finite values' % offset)
        if abs(tail - 1.0) > 1e-5:
            raise ForestError('record at offset %d has matrix row 3 w=%r, expected 1.0' %
                              (offset, tail))
        records.append({'type': type_id, 'matrix': matrix, 'x': x, 'y': y, 'z': z})
    return records


def build_fst(records):
    out = bytearray()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ForestError('record %d is not an object' % index)
        type_id = record.get('type')
        if not isinstance(type_id, int) or isinstance(type_id, bool) or type_id < 0:
            raise ForestError('record %d has an invalid type' % index)
        matrix = record.get('matrix')
        if not isinstance(matrix, list) or len(matrix) != 12:
            raise ForestError('record %d matrix must contain 12 numbers' % index)
        matrix = [_number(value, 'record %d matrix' % index) for value in matrix]
        position = [_number(record.get(key), 'record %d %s' % (index, key))
                    for key in ('x', 'y', 'z')]
        out += RECORD.pack(type_id, *(matrix + position + [1.0]))
    return bytes(out)


class ForestConfig:
    """Typed view of WorldLevel.Forest and WorldLevel.TreesProperties."""

    def __init__(self, world_level):
        if not isinstance(world_level, dict):
            raise ForestError('WorldLevel is not a table')
        raw_forest = world_level.get('Forest')
        raw_properties = world_level.get('TreesProperties')
        if not isinstance(raw_forest, dict) or not isinstance(raw_properties, dict):
            raise ForestError('WorldLevel has no Forest/TreesProperties tables')
        self.properties = {}
        for set_name, entries in raw_properties.items():
            if not isinstance(entries, dict):
                raise ForestError('TreesProperties.%s is not a table' % set_name)
            parsed = {}
            for key, entry in entries.items():
                if (not isinstance(entry, dict) or not isinstance(entry.get(1), str) or
                        not all(_finite(entry.get(i)) for i in (2, 3, 4, 5))):
                    raise ForestError('TreesProperties.%s[%s] is malformed' % (set_name, key))
                parsed[int(key)] = {
                    'model': entry[1],
                    'params': [entry[2], entry[3], entry[4], entry[5], entry.get(6, 0.0)],
                }
            self.properties[str(set_name)] = parsed
        self.continents = {}
        for continent, entries in raw_forest.items():
            if not isinstance(entries, dict):
                raise ForestError('Forest[%s] is not a table' % continent)
            zones = {}
            for key, entry in entries.items():
                if (not isinstance(entry, dict) or not isinstance(entry.get(1), str) or
                        not isinstance(entry.get(2), str)):
                    raise ForestError('Forest[%s][%s] is malformed' % (continent, key))
                trees = []
                weighted = entry.get(6)
                if isinstance(weighted, dict):
                    keys = sorted((k for k in weighted if isinstance(k, int)))
                    for position in range(0, len(keys) - 1, 2):
                        name, weight = weighted.get(keys[position]), weighted.get(keys[position + 1])
                        if isinstance(name, str) and _finite(weight):
                            trees.append((name, float(weight)))
                zones[entry[1].lower()] = {
                    'name': entry[1],
                    'set': entry[2],
                    'scale': float(entry.get(3, 1.0)),
                    'x': float(entry.get(4, 0.0)),
                    'z': float(entry.get(5, 0.0)),
                    'trees': trees,
                }
            self.continents[int(continent)] = zones
        for continent, zones in self.continents.items():
            for zone in zones.values():
                if zone['set'] not in self.properties:
                    raise ForestError('zone %s uses unknown TreesProperties set %s' %
                                      (zone['name'], zone['set']))

    @classmethod
    def from_archive_set(cls, archive_set):
        if not archive_set.has(CONFIG_FILE):
            raise ForestError('%s is missing from the selected archives' % CONFIG_FILE)
        data = archive_set.read(CONFIG_FILE)
        try:
            if data[:4] == b'\x1bLua':
                globals_ = lua_data.decode_chunk(data, allow_closures=True)
            else:
                globals_ = lua_data.parse_source(data)
        except lua_data.LuaDataError as error:
            raise ForestError('%s cannot be decoded: %s' % (CONFIG_FILE, error))
        return cls(globals_.get('WorldLevel'))

    def zone(self, continent, zone):
        zones = self.continents.get(int(continent))
        if zones is None:
            raise ForestError('continent %s has no forest configuration' % continent)
        entry = zones.get(str(zone).lower())
        if entry is None:
            raise ForestError('continent %s has no forest zone %s' % (continent, zone))
        return entry

    def tree(self, continent, zone, type_id):
        entry = self.zone(continent, zone)
        properties = self.properties[entry['set']]
        if not isinstance(type_id, int) or type_id + 1 not in properties:
            raise ForestError('zone %s (%s) has no tree type %s' %
                              (entry['name'], entry['set'], type_id))
        return properties[type_id + 1]

    def type_for_model(self, continent, zone, model):
        target = str(model).lower()
        if target.endswith('.gdl'):
            target = target[:-4]
        properties = self.properties[self.zone(continent, zone)['set']]
        matches = [key for key, entry in sorted(properties.items())
                   if entry['model'].lower() == target]
        if not matches:
            raise ForestError('zone %s has no tree model %s' % (zone, model))
        return matches[0] - 1

    def models(self, continent, zone):
        properties = self.properties[self.zone(continent, zone)['set']]
        return {key - 1: entry['model'] for key, entry in sorted(properties.items())}

    def snapshot(self):
        return {
            'properties': {
                str(set_name): {str(key): dict(entry) for key, entry in sorted(entries.items())}
                for set_name, entries in sorted(self.properties.items())
            },
            'continents': {
                str(continent): {key: dict(zone) for key, zone in sorted(zones.items())}
                for continent, zones in sorted(self.continents.items())
            },
        }

    @classmethod
    def from_snapshot(cls, snapshot):
        level = {'Forest': {}, 'TreesProperties': {}}
        for set_name, entries in snapshot['properties'].items():
            level['TreesProperties'][set_name] = {
                int(key): {1: entry['model'],
                           2: entry['params'][0], 3: entry['params'][1],
                           4: entry['params'][2], 5: entry['params'][3],
                           6: entry['params'][4]}
                for key, entry in entries.items()
            }
        for continent, zones in snapshot['continents'].items():
            level['Forest'][continent] = {}
            for number, (key, zone) in enumerate(sorted(zones.items()), 1):
                weighted = {}
                for position, item in enumerate(zone['trees'], 1):
                    weighted[position * 2 - 1] = item[0]
                    weighted[position * 2] = item[1]
                level['Forest'][continent][number] = {
                    1: zone['name'], 2: zone['set'], 3: zone['scale'],
                    4: zone['x'], 5: zone['z'], 6: weighted,
                }
        return cls(level)


class Forests:
    def __init__(self, config, zones=None, archives=None):
        self.config = config
        self.zones = zones or {}
        self.archives = archives or []

    @classmethod
    def load_archives(cls, paths, continents=(1, 2, 3)):
        archive_set = gres.ArchiveSet(paths)
        try:
            return cls._from_set(archive_set, continents)
        finally:
            archive_set.close()

    @classmethod
    def _from_set(cls, archive_set, continents):
        config = ForestConfig.from_archive_set(archive_set)
        model = cls(config, archives=[{'slot': slot,
                                       'path': str(archive_set.archives[slot].path)}
                                      for slot in archive_set.slots])
        for continent in continents:
            zones = config.continents.get(continent, {})
            entry = {}
            for key, zone in zones.items():
                filename = key + '.fst'
                resolved = archive_set.resolve(filename)
                if resolved is None:
                    continue
                data = resolved.read()
                entry[key] = {
                    'file': filename,
                    'records': parse_fst(data),
                    'source': {
                        'archive': resolved.archive.path.name,
                        'slot': resolved.archive.slot,
                        'sha256': hashlib.sha256(data).hexdigest(),
                    },
                }
            if entry:
                model.zones[continent] = entry
        return model

    @classmethod
    def load_json(cls, path, config=None):
        with open(path, encoding='utf-8') as stream:
            document = json.load(stream)
        if document.get('format') != FORMAT:
            raise ForestError('%s is not an %s document' % (path, FORMAT))
        if config is None:
            if not isinstance(document.get('config'), dict):
                raise ForestError('%s has no config snapshot' % path)
            config = ForestConfig.from_snapshot(document['config'])
        zones = {}
        for continent, entries in document['zones'].items():
            parsed = {}
            for key, entry in entries.items():
                parsed[key] = {
                    'file': entry['file'],
                    'records': entry['records'],
                    'source': entry.get('source', {}),
                }
            zones[int(continent)] = parsed
        return cls(config, zones, document.get('archives', []))

    def document(self):
        return {
            'format': FORMAT,
            'archives': self.archives,
            'config': self.config.snapshot(),
            'zones': {str(continent): entry for continent, entry in sorted(self.zones.items())},
        }

    def save_json(self, path):
        with open(path, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(self.document(), stream, ensure_ascii=False, indent=1,
                      allow_nan=False, sort_keys=True)
            stream.write('\n')

    # --- access -----------------------------------------------------------
    def zone(self, continent, zone):
        entry = self.zones.get(int(continent), {}).get(str(zone).lower())
        if entry is None:
            raise ForestError('continent %s has no loaded forest zone %s' % (continent, zone))
        return entry

    def records(self, continent=None, zone=None):
        continents = self.zones if continent is None else {int(continent): self.zones.get(int(continent), {})}
        for number, zones in sorted(continents.items()):
            for key, entry in sorted(zones.items()):
                if zone is not None and key != str(zone).lower():
                    continue
                for index, record in enumerate(entry['records']):
                    yield number, key, index, record

    def model(self, continent, zone, record):
        return self.config.tree(continent, zone, record['type'])['model']

    def find(self, continent=None, zone=None, model=None, type_id=None,
             x=None, z=None, radius=None, limit=100):
        target = str(model).lower() if model is not None else None
        if target and target.endswith('.gdl'):
            target = target[:-4]
        results = []
        for number, key, index, record in self.records(continent, zone):
            if type_id is not None and record['type'] != int(type_id):
                continue
            try:
                name = self.model(number, key, record)
            except ForestError:
                name = None
            if target and (name is None or name.lower() != target):
                continue
            if x is not None or z is not None:
                if x is None or z is None:
                    raise ForestError('x and z must be given together')
                if radius is not None and math.hypot(record['x'] - float(x),
                                                     record['z'] - float(z)) > float(radius):
                    continue
            results.append({'continent': number, 'zone': key, 'index': index,
                            'type': record['type'], 'model': name,
                            'x': record['x'], 'y': record['y'], 'z': record['z']})
            if len(results) >= int(limit):
                break
        return results

    # --- editing ----------------------------------------------------------
    def add(self, continent, zone, type_id=None, model=None, x=0.0, y=None, z=0.0,
            yaw=0.0, scale=1.0, y_scale=None, index=None, heightmap=None):
        entry = self.zone(continent, zone)
        if type_id is None:
            if model is None:
                raise ForestError('either a type id or a tree model is required')
            type_id = self.config.type_for_model(continent, zone, model)
        else:
            self.config.tree(continent, zone, int(type_id))
        if y is None:
            if heightmap is None:
                raise ForestError('y is required without a heightmap')
            sample = heightmap.sample(float(x), float(z))
            if sample is None:
                raise ForestError('(%s, %s) is outside the heightmap' % (x, z))
            y = sample
        record = make_record(int(type_id), x, y, z, yaw, scale, y_scale)
        records = entry['records']
        if index is None:
            index = len(records)
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index <= len(records):
            raise ForestError('index must be between 0 and %d' % len(records))
        records.insert(index, record)
        return index, record

    def move(self, continent, zone, index, x=None, y=None, z=None, yaw=None,
             scale=None, y_scale=None, heightmap=None, ground=False):
        records = self.zone(continent, zone)['records']
        if not 0 <= index < len(records):
            raise ForestError('record index %s is out of range' % index)
        record = records[index]
        if x is not None:
            record['x'] = _number(x, 'x')
        if z is not None:
            record['z'] = _number(z, 'z')
        if ground:
            if heightmap is None:
                raise ForestError('ground requires a heightmap')
            sample = heightmap.sample(record['x'], record['z'])
            if sample is None:
                raise ForestError('(%s, %s) is outside the heightmap' %
                                  (record['x'], record['z']))
            record['y'] = sample
        elif y is not None:
            record['y'] = _number(y, 'y')
        if yaw is not None or scale is not None or y_scale is not None:
            old_yaw = matrix_yaw(record['matrix']) if yaw is None else float(yaw)
            old_scale, old_y_scale = matrix_scale(record['matrix'])
            record['matrix'] = make_matrix(old_yaw,
                                           old_scale if scale is None else float(scale),
                                           old_y_scale if y_scale is None else float(y_scale))
        return record

    def remove(self, continent, zone, index):
        records = self.zone(continent, zone)['records']
        if not 0 <= index < len(records):
            raise ForestError('record index %s is out of range' % index)
        return records.pop(index)

    def canonical_records(self, record):
        return json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)

    # --- checks and export ------------------------------------------------
    def changed_zones(self):
        changed = {}
        for continent, zones in self.zones.items():
            for key, entry in zones.items():
                source = entry.get('source', {})
                if source.get('sha256') != hashlib.sha256(build_fst(entry['records'])).hexdigest():
                    changed[(continent, key)] = entry
        return changed

    def validate(self, archive_set=None, heightmaps=None):
        issues = []
        for continent, zones in sorted(self.zones.items()):
            for key, entry in sorted(zones.items()):
                map_ = (heightmaps or {}).get(continent)
                for index, record in enumerate(entry['records']):
                    try:
                        tree = self.config.tree(continent, key, record['type'])
                    except ForestError as error:
                        issues.append({'level': 'error', 'kind': 'unknown-tree-type',
                                       'continent': continent, 'zone': key,
                                       'index': index, 'type': record['type'],
                                       'message': str(error)})
                        continue
                    if archive_set is not None:
                        model = tree_model(tree['model'])
                        if not archive_set.has(model):
                            issues.append({'level': 'error', 'kind': 'missing-model',
                                           'continent': continent, 'zone': key,
                                           'index': index, 'model': model})
                    if map_ is not None:
                        if not (map_.min_x <= record['x'] <= map_.max_x and
                                map_.min_z <= record['z'] <= map_.max_z):
                            issues.append({'level': 'warning', 'kind': 'outside-heightmap',
                                           'continent': continent, 'zone': key,
                                           'index': index, 'x': record['x'], 'z': record['z']})
        if archive_set is not None:
            for continent, zones in sorted(self.zones.items()):
                for key in sorted(set(self.config.continents.get(continent, {})) - set(zones)):
                    issues.append({'level': 'warning', 'kind': 'missing-zone-file',
                                   'continent': continent, 'zone': key,
                                   'file': key + '.fst'})
            known = {key for zones in self.config.continents.values() for key in zones}
            for name in sorted(archive_set.names()):
                if name.endswith('.fst') and name[:-4] not in known:
                    issues.append({'level': 'warning', 'kind': 'unconfigured-zone',
                                   'file': name})
        return issues

    def export_entries(self):
        entries = {}
        for (continent, key), entry in self.changed_zones().items():
            entries[entry['file']] = build_fst(entry['records'])
        return entries

    def export_pak(self, path, slot=None, overwrite=False):
        entries = self.export_entries()
        if not entries:
            raise ForestError('no forest zones changed')
        folder = Path(path)
        if not folder.is_dir():
            raise ForestError('output folder does not exist: %s' % folder)
        if slot is None:
            used = {source['slot'] for zones in self.zones.values()
                    for entry in zones.values() for source in [entry.get('source', {})]}
            used.update(archive.get('slot') for archive in self.archives)
            for candidate in folder.glob('Resource*.pak'):
                used.add(gres.archive_slot(candidate.name))
            used.discard(None)
            slot = max(used, default=0) + 1
        destination = folder / ('Resource%d.pak' % slot)
        gres.write_pak(destination, entries, overwrite=overwrite)
        return str(destination), entries
