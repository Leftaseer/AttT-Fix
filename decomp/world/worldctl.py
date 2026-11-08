#!/usr/bin/env python3
"""Command-line world editor for Ascension to the Throne data overlays.

The JSON model is the shared interface: humans can edit it with any tool, AI
agents can query and patch it, and this CLI applies typed operations, validates
references and exports a numbered ResourceN.pak overlay.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gres  # noqa: E402
import forests as forests_module  # noqa: E402
import heightmap as heightmap_module  # noqa: E402
import lua_data  # noqa: E402
import render  # noqa: E402
import story as story_module  # noqa: E402
import world as world_module  # noqa: E402


def open_game(folder, allow_gaps=False):
    folder = Path(folder)
    if not folder.is_dir():
        raise SystemExit('game folder does not exist: %s' % folder)
    return gres.ArchiveSet.open_folder(folder, allow_gaps=allow_gaps)


def load_world(path):
    return world_module.World.load_json(path)


def write_json(value, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=1, allow_nan=False, sort_keys=True)
        stream.write('\n')


def find_heightmap(archive_set, continent):
    name = 'continent%d_heightmap.nmph' % continent
    if not archive_set.has(name):
        raise SystemExit('%s is missing from the selected archives' % name)
    return heightmap_module.Heightmap(archive_set.read(name))


def load_units(archive_set):
    """Load the global Unit definitions used by army TroopList entries."""
    if archive_set is None or not archive_set.has('units.lua'):
        return None
    try:
        return lua_data.load_module(archive_set.read('units.lua'), 'Unit')
    except lua_data.LuaDataError as error:
        raise SystemExit('units.lua cannot be decoded: %s' % error)


def command_extract(args):
    continua = parse_continents(args.continents)
    archive_set = open_game(args.game)
    try:
        world = world_module.World._from_set(archive_set, continua)
        maps = {}
        for continent in continua:
            if archive_set.has('continent%d_heightmap.nmph' % continent):
                maps[continent] = find_heightmap(archive_set, continent)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        world.save_json(out / 'world.json')
        entities = {str(continent): world.flat_entities(continent) for continent in continua}
        write_json({'format': 'attt-world-entities/1', 'continents': entities}, out / 'entities.json')
        info = {'format': 'attt-world-info/1', 'archives': world.archives, 'continents': {}}
        for continent, entry in sorted(world.continents.items()):
            map_ = maps.get(continent)
            info['continents'][str(continent)] = {
                'modules': {name: len(table) for name, table in entry['modules'].items()},
                'sources': entry['sources'],
                'placements': sum(1 for _ in world.placements(continent)),
                'bounds': None if map_ is None else {
                    'minX': map_.min_x, 'minZ': map_.min_z, 'maxX': map_.max_x, 'maxZ': map_.max_z,
                    'step': map_.step, 'width': map_.width, 'height': map_.height,
                    'scale': map_.scale, 'offset': map_.offset,
                    'min_elevation': map_.min_elevation, 'max_elevation': map_.max_elevation,
                },
            }
        write_json(info, out / 'info.json')
        if args.map:
            for continent, map_ in maps.items():
                svg = render.render_svg(world, continent, map_, size=args.size)
                (out / ('continent%d.svg' % continent)).write_text(svg, encoding='utf-8')
        print('wrote %s (%d continents, %d placements)' %
              (out, len(world.continents), sum(1 for c in world.continents for _ in world.placements(c))))
    finally:
        archive_set.close()


def parse_continents(value):
    if not value:
        return (1, 2, 3)
    parts = []
    for item in value.split(','):
        item = item.strip()
        if '-' in item:
            start, end = item.split('-', 1)
            parts.extend(range(int(start), int(end) + 1))
        elif item:
            parts.append(int(item))
    if not parts:
        raise SystemExit('no continents selected')
    return tuple(sorted(set(parts)))


def command_info(args):
    world = load_world(args.world)
    result = {'archives': world.archives, 'source_modules': world.source_modules(),
              'continents': {}}
    for continent, entry in sorted(world.continents.items()):
        result['continents'][str(continent)] = {
            'modules': {name: len(table) for name, table in entry['modules'].items()},
            'placements': sum(1 for _ in world.placements(continent)),
            'changed': sorted(name for (item, name) in world.changed_modules() if item == continent),
        }
    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        for continent, entry in result['continents'].items():
            print('continent %s: %s' % (continent, ', '.join('%s=%d' % item for item in entry['modules'].items())))
            print('  placements: %d, changed modules: %s' %
                  (entry['placements'], ', '.join(entry['changed']) or 'none'))
        for source in result['source_modules']:
            print('source module: c%s %s from %s (slot %s)' %
                  (source['continent'], source['module'], source['archive'], source['slot']))


def command_find(args):
    world = load_world(args.world)
    archive_set = open_game(args.game) if args.game else None
    try:
        maps = {}
        if archive_set is not None:
            for continent in world.continents:
                if archive_set.has('continent%d_heightmap.nmph' % continent):
                    maps[continent] = find_heightmap(archive_set, continent)

        def add_elevation(continent, record, x, z):
            map_ = maps.get(continent)
            if map_ is not None:
                record['elevation'] = map_.sample(x, z)
            return record

        needle = (args.name or '').lower()
        results = []
        for continent in sorted(world.continents):
            if args.type in (None, 'entity', 'npc', 'object', 'tree'):
                kinds = (args.type,) if args.type in ('npc', 'object', 'tree') else ('npc', 'object', 'tree')
                for record in world.flat_entities(continent):
                    if kinds != ('npc', 'object', 'tree') and record['kind'] not in kinds:
                        continue
                    if needle and needle not in str(record.get('name') or '').lower():
                        continue
                    if args.town and args.town.lower() not in record['town'].lower():
                        continue
                    if args.house and args.house.lower() not in record['house'].lower():
                        continue
                    x, z = record['world'][0], record['world'][2]
                    results.append(add_elevation(continent, record, x, z))
            if args.type in (None, 'town'):
                for name in world.town_names(continent):
                    if needle and needle not in name.lower():
                        continue
                    position = world.towns(continent)[name].get('Pos') or {}
                    record = {'continent': continent, 'type': 'town', 'name': name,
                              'position': position}
                    results.append(add_elevation(continent, record,
                                                 position.get(1, 0.0), position.get(3, 0.0)))
            if args.type in (None, 'army', 'armypos'):
                modules = world.continents[continent]['modules']
                if args.type in (None, 'army'):
                    for name, army in modules.get('armies', {}).items():
                        if needle and needle not in str(name).lower():
                            continue
                        results.append({'continent': continent, 'type': 'army', 'name': name,
                                        'display': army.get('DisplayName') if isinstance(army, dict) else None})
                if args.type in (None, 'armypos'):
                    for name, position in modules.get('armypos', {}).items():
                        if needle and needle not in str(name).lower():
                            continue
                        if isinstance(position, dict):
                            x = position.get('x', 0.0)
                            z = position.get('z', 0.0)
                        else:
                            x = z = 0.0
                        record = {'continent': continent, 'type': 'armypos', 'name': name,
                                  'position': position}
                        results.append(add_elevation(continent, record, x, z))
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=1, sort_keys=True))
        else:
            for record in results:
                if record.get('type') == 'town':
                    print('c%s town   %-28s %s' % (record['continent'], record['name'],
                                                   record['position']))
                elif record.get('type') in ('army', 'armypos'):
                    print('c%s %-6s %-28s %s' % (record['continent'], record['type'], record['name'],
                                                 record.get('position') or record.get('display') or ''))
                else:
                    print('c%s %-6s %-10s %-20s %-30s (%.1f, %.1f)' %
                          (record['continent'], record['kind'], record['town'], record['house'],
                           record.get('name'), record['world'][0], record['world'][2]))
                if 'elevation' in record:
                    print('  elevation: %s' % record['elevation'])
        print('%d result(s)' % len(results), file=sys.stderr)
    finally:
        if archive_set is not None:
            archive_set.close()


def select_placement(world, args):
    try:
        return world.find_placement(args.continent, args.town, args.house, args.kind,
                                    index=args.index, name=args.name)
    except world_module.WorldError as error:
        raise SystemExit(str(error))


def command_move(args):
    world = load_world(args.world)
    placement = select_placement(world, args)
    if args.world_coords:
        placement = world.move_world(args.continent, placement.town_name, placement.house_name,
                                     placement.kind, placement.index, x=args.x, z=args.z)
    else:
        placement = world.move_local(args.continent, placement.town_name, placement.house_name,
                                     placement.kind, placement.index, x=args.x, y=args.y, z=args.z)
    world.save_json(args.world)
    print(json.dumps(placement.record(), ensure_ascii=False, indent=1, sort_keys=True))


def command_add(args):
    world = load_world(args.world)
    x = 0.0 if args.x is None else args.x
    y = 0.0 if args.y is None else args.y
    z = 0.0 if args.z is None else args.z
    if args.world_coords:
        x, z = world.local_from_world(args.continent, args.town, args.house, x, z)
    if not args.name:
        raise SystemExit('%s placements require --name' % args.kind)
    if args.kind == 'npc':
        entry = world_module.make_npc(args.name, x, y, z, rotation=args.rot or 0.0,
                                      kind=args.npc_kind)
    elif args.kind == 'object':
        entry = world_module.make_object(args.name, x, y, z, rotation=args.rot or 0.0,
                                         scale=args.scale, gizmo=args.gizmo,
                                         group=args.group, lod=args.lod)
    else:
        entry = world_module.make_tree(args.name, x, y, z, rotation=args.rot or 0.0)
    placement = world.add_placement(args.continent, args.town, args.house, args.kind, entry,
                                    index=args.index)
    world.save_json(args.world)
    print(json.dumps(placement.record(), ensure_ascii=False, indent=1, sort_keys=True))


def command_remove(args):
    world = load_world(args.world)
    placement = select_placement(world, args)
    removed = world.remove_placement(args.continent, placement.town_name, placement.house_name,
                                     placement.kind, placement.index)
    world.save_json(args.world)
    print(json.dumps({'removed': placement.record(), 'entry': world_module.to_jsonable(removed)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_clone(args):
    world = load_world(args.world)
    source = select_placement(world, args)
    placement = world.clone_placement(args.continent, source.town_name, source.house_name,
                                      source.kind, source.index, index_new=args.index_new)
    if args.x is not None or args.z is not None:
        if args.world_coords:
            placement = world.move_world(args.continent, placement.town_name, placement.house_name,
                                         placement.kind, placement.index, x=args.x, z=args.z)
        else:
            placement = world.move_local(args.continent, placement.town_name, placement.house_name,
                                         placement.kind, placement.index, x=args.x, z=args.z)
    if args.rot is not None:
        placement = world.set_rotation(args.continent, placement.town_name, placement.house_name,
                                       placement.kind, placement.index, args.rot)
    world.save_json(args.world)
    print(json.dumps(placement.record(), ensure_ascii=False, indent=1, sort_keys=True))


def command_add_town(args):
    world = load_world(args.world)
    entry = world.add_town(args.continent, args.name, args.x, args.y, args.z, rotation=args.rot)
    world.save_json(args.world)
    print(json.dumps({'name': args.name, 'entry': world_module.to_jsonable(entry)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_add_house(args):
    world = load_world(args.world)
    entry = world.add_house(args.continent, args.town, args.name, args.x, args.y, args.z,
                            rotation=args.rot)
    world.save_json(args.world)
    print(json.dumps({'town': args.town, 'name': args.name,
                      'entry': world_module.to_jsonable(entry)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_remove_town(args):
    world = load_world(args.world)
    try:
        removed = world.remove_town(args.continent, args.name, force=args.force)
    except world_module.WorldError as error:
        raise SystemExit(str(error))
    world.save_json(args.world)
    print(json.dumps({'name': args.name, 'entry': world_module.to_jsonable(removed)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_remove_house(args):
    world = load_world(args.world)
    try:
        removed = world.remove_house(args.continent, args.town, args.name, force=args.force)
    except world_module.WorldError as error:
        raise SystemExit(str(error))
    world.save_json(args.world)
    print(json.dumps({'town': args.town, 'name': args.name,
                      'entry': world_module.to_jsonable(removed)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def parse_troops(values):
    troops = []
    for value in values or []:
        unit, separator, quantity = value.partition(':')
        try:
            quantity = float(quantity)
        except ValueError:
            separator = ''
        if not separator or not unit:
            raise SystemExit('--troop must be UNIT:QUANTITY, got %r' % value)
        troops.append((unit, quantity))
    return troops


def command_add_army(args):
    world = load_world(args.world)
    try:
        entry = world.add_army(args.continent, args.name, world_module.make_army(
            display_name=args.display_name, attitude=args.attitude,
            standard=args.standard, troops=parse_troops(args.troop)),
            x=args.x, z=args.z, radius=args.radius)
    except world_module.WorldError as error:
        raise SystemExit(str(error))
    world.save_json(args.world)
    position = world.army_positions(args.continent).get(args.name)
    print(json.dumps({'name': args.name, 'entry': world_module.to_jsonable(entry),
                      'position': world_module.to_jsonable(position)},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_remove_army(args):
    world = load_world(args.world)
    try:
        removed = world.remove_army(args.continent, args.name)
    except world_module.WorldError as error:
        raise SystemExit(str(error))
    world.save_json(args.world)
    print(json.dumps({'name': args.name, 'army': world_module.to_jsonable(removed['army']),
                      'position': world_module.to_jsonable(removed['position'])},
                     ensure_ascii=False, indent=1, sort_keys=True))


def command_move_army(args):
    world = load_world(args.world)
    if args.x is None and args.z is None and args.radius is None:
        raise SystemExit('pass at least one of --x, --z or --radius')
    entry = world.move_army(args.continent, args.name, x=args.x, z=args.z, radius=args.radius)
    world.save_json(args.world)
    print(json.dumps(entry, ensure_ascii=False, indent=1, sort_keys=True))


def command_snap(args):
    world = load_world(args.world)
    archive_set = open_game(args.game)
    try:
        map_ = find_heightmap(archive_set, args.continent)
        kinds = (args.kind,) if args.kind else ('npc', 'object', 'tree')
        changed, skipped = world.snap_placements(
            args.continent, map_, offset=args.offset, kinds=kinds,
            town=args.town, house=args.house, dry_run=args.dry_run)
        if changed and not args.dry_run:
            world.save_json(args.world)
        print(json.dumps({'changed': len(changed), 'skipped': len(skipped),
                          'dry_run': args.dry_run, 'placements': changed[:args.limit],
                          'outside': skipped[:args.limit]},
                         ensure_ascii=False, indent=1, sort_keys=True))
    finally:
        archive_set.close()


def heightmap_issues(world, continent, map_, water=None):
    """Report towns, army positions and placements outside or below the map plane."""
    issues = []

    def check(base, x, z):
        if not (world_module._finite_number(x) and world_module._finite_number(z)):
            return
        elevation = map_.sample(x, z)
        if elevation is None:
            issues.append(dict(base, level='warning', kind='outside-heightmap'))
        elif water is not None and elevation < water:
            issues.append(dict(base, level='warning', kind='below-water',
                               elevation=elevation, water=water))

    for placement in world.placements(continent):
        world_x, world_z = placement.world_xz
        check({'entity': 'placement', 'town': placement.town_name,
               'house': placement.house_name, 'index': placement.index,
               'placement': placement.kind, 'world': [world_x, world_z]},
              world_x, world_z)
    for town_name, town in world.towns(continent).items():
        position = town.get('Pos') if isinstance(town, dict) else None
        if not isinstance(position, dict):
            continue
        check({'entity': 'town', 'town': town_name,
               'world': [position.get(1), position.get(3)]},
              position.get(1), position.get(3))
    for name, position in world.army_positions(continent).items():
        if not isinstance(position, dict):
            continue
        check({'entity': 'army', 'name': name,
               'world': [position.get('x'), position.get('z')]},
              position.get('x'), position.get('z'))
    return issues


def command_validate(args):
    world = load_world(args.world)
    archive_set = open_game(args.game) if args.game else None
    try:
        report = {}
        errors = 0
        units = load_units(archive_set)
        for continent in sorted(world.continents):
            issues = world.validate(continent, archive_set, units)
            if archive_set is not None and archive_set.has('continent%d_heightmap.nmph' % continent):
                map_ = find_heightmap(archive_set, continent)
                issues.extend(heightmap_issues(world, continent, map_, args.water))
            report[str(continent)] = issues
            errors += sum(1 for issue in issues if issue['level'] == 'error')
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
        else:
            for continent, issues in report.items():
                print('continent %s: %d issue(s)' % (continent, len(issues)))
                for issue in issues[:args.limit]:
                    print('  %-7s %-26s %s' % (issue['level'], issue['kind'],
                                               {key: value for key, value in issue.items()
                                                if key not in ('level', 'kind')}))
                if len(issues) > args.limit:
                    print('  ... %d more' % (len(issues) - args.limit))
        return 1 if errors else 0
    finally:
        if archive_set:
            archive_set.close()


def command_export(args):
    world = load_world(args.world)
    for source in world.source_modules():
        print('warning: c%s %s was loaded from Lua source in %s (slot %s); '
              'export re-emits data-only source' %
              (source['continent'], source['module'], source['archive'], source['slot']),
              file=sys.stderr)
    if args.game:
        archive_set = open_game(args.game)
        try:
            units = load_units(archive_set)
            for continent in world.continents:
                errors = [issue for issue in world.validate(continent, archive_set, units)
                          if issue['level'] == 'error']
                if errors:
                    raise SystemExit('refusing to export: %d validation error(s) on continent %d' %
                                     (len(errors), continent))
        finally:
            archive_set.close()
    destination, entries = world.export_pak(args.out, slot=args.slot, overwrite=args.overwrite)
    for name in sorted(entries):
        print('%s: %d bytes' % (name, len(entries[name])))
    print(destination)


def command_forest_extract(args):
    continents = parse_continents(args.continents)
    archive_set = open_game(args.game)
    try:
        model = forests_module.Forests._from_set(archive_set, continents)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        model.save_json(out / 'forests.json')
        info = {'format': 'attt-forests-info/1', 'archives': model.archives, 'continents': {}}
        for continent, zones in sorted(model.zones.items()):
            info['continents'][str(continent)] = {
                'zones': {
                    key: {
                        'file': entry['file'],
                        'set': model.config.zone(continent, key)['set'],
                        'records': len(entry['records']),
                        'types': sorted({record['type'] for record in entry['records']}),
                    }
                    for key, entry in sorted(zones.items())
                },
                'records': sum(len(entry['records']) for entry in zones.values()),
            }
        write_json(info, out / 'forests-info.json')
        print('wrote %s (%d zones, %d trees)' %
              (out, sum(len(zones) for zones in model.zones.values()),
               sum(len(entry['records']) for zones in model.zones.values()
                   for entry in zones.values())))
    finally:
        archive_set.close()


def load_forests(path):
    try:
        return forests_module.Forests.load_json(path)
    except forests_module.ForestError as error:
        raise SystemExit(str(error))


def forest_heightmap(args, continent, required):
    if not args.game:
        if required:
            raise SystemExit('--game is required to sample terrain elevation')
        return None
    archive_set = open_game(args.game)
    try:
        return find_heightmap(archive_set, continent)
    finally:
        archive_set.close()


def command_forest_info(args):
    model = load_forests(args.forests)
    result = {'archives': model.archives, 'continents': {}}
    for continent, zones in sorted(model.zones.items()):
        result['continents'][str(continent)] = {
            key: {'file': entry['file'],
                  'set': model.config.zone(continent, key)['set'],
                  'records': len(entry['records']),
                  'types': sorted({record['type'] for record in entry['records']})}
            for key, entry in sorted(zones.items())
        }
    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        for continent, zones in result['continents'].items():
            print('continent %s: %d zones, %d trees' %
                  (continent, len(zones), sum(zone['records'] for zone in zones.values())))
            for key, zone in zones.items():
                print('  %-32s set=%-8s records=%-4d types=%s' %
                      (key, zone['set'], zone['records'], zone['types']))
        changed = model.changed_zones()
        if changed:
            print('changed zones: %s' % ', '.join('%s/%s' % item for item in sorted(changed)))
    return 0


def command_forest_find(args):
    model = load_forests(args.forests)
    try:
        results = model.find(continent=args.continent, zone=args.zone, model=args.model,
                             type_id=args.type, x=args.x, z=args.z, radius=args.radius,
                             limit=args.limit)
    except forests_module.ForestError as error:
        raise SystemExit(str(error))
    print(json.dumps(results, indent=1, sort_keys=True))
    return 0


def command_forest_add(args):
    model = load_forests(args.forests)
    map_ = forest_heightmap(args, args.continent, args.y is None)
    try:
        index, record = model.add(args.continent, args.zone, type_id=args.type,
                                  model=args.model, x=args.x, y=args.y, z=args.z,
                                  yaw=args.yaw, scale=args.scale, y_scale=args.y_scale,
                                  index=args.index, heightmap=map_)
    except forests_module.ForestError as error:
        raise SystemExit(str(error))
    if not args.dry_run:
        model.save_json(args.forests)
    print(json.dumps({'dry_run': bool(args.dry_run), 'continent': args.continent,
                      'zone': args.zone.lower(), 'index': index,
                      'model': model.model(args.continent, args.zone, record),
                      'record': record}, indent=1, sort_keys=True))
    return 0


def command_forest_move(args):
    model = load_forests(args.forests)
    map_ = forest_heightmap(args, args.continent, args.ground)
    try:
        record = model.move(args.continent, args.zone, args.index, x=args.x, y=args.y,
                            z=args.z, yaw=args.yaw, scale=args.scale,
                            y_scale=args.y_scale, heightmap=map_, ground=args.ground)
    except forests_module.ForestError as error:
        raise SystemExit(str(error))
    if not args.dry_run:
        model.save_json(args.forests)
    print(json.dumps({'dry_run': bool(args.dry_run), 'continent': args.continent,
                      'zone': args.zone.lower(), 'index': args.index,
                      'model': model.model(args.continent, args.zone, record),
                      'record': record}, indent=1, sort_keys=True))
    return 0


def command_forest_remove(args):
    model = load_forests(args.forests)
    try:
        record = model.remove(args.continent, args.zone, args.index)
    except forests_module.ForestError as error:
        raise SystemExit(str(error))
    if not args.dry_run:
        model.save_json(args.forests)
    print(json.dumps({'dry_run': bool(args.dry_run), 'continent': args.continent,
                      'zone': args.zone.lower(), 'index': args.index,
                      'model': model.model(args.continent, args.zone, record),
                      'record': record}, indent=1, sort_keys=True))
    return 0


def command_forest_validate(args):
    model = load_forests(args.forests)
    archive_set = open_game(args.game) if args.game else None
    try:
        heightmaps = {}
        if archive_set is not None and not args.no_heightmap:
            for continent in model.zones:
                if archive_set.has('continent%d_heightmap.nmph' % continent):
                    heightmaps[continent] = find_heightmap(archive_set, continent)
        issues = model.validate(archive_set, heightmaps)
    finally:
        if archive_set is not None:
            archive_set.close()
    errors = [issue for issue in issues if issue['level'] == 'error']
    if args.json:
        print(json.dumps({'errors': len(errors), 'warnings': len(issues) - len(errors),
                          'issues': issues[:args.limit]}, indent=1, sort_keys=True))
    else:
        print('%d error(s), %d warning(s)' % (len(errors), len(issues) - len(errors)))
        for issue in issues[:args.limit]:
            location = ('c%s/%s/%s' % (issue.get('continent'), issue.get('zone'),
                                       issue.get('index'))
                        if 'zone' in issue else issue.get('file'))
            print('  %s %s %s' % (issue['level'], issue['kind'], location))
        if len(issues) > args.limit:
            print('  ... %d more' % (len(issues) - args.limit))
    return 1 if errors else 0


def command_forest_export(args):
    model = load_forests(args.forests)
    if args.game:
        archive_set = open_game(args.game)
        try:
            heightmaps = {}
            if not args.no_heightmap:
                for continent in model.zones:
                    if archive_set.has('continent%d_heightmap.nmph' % continent):
                        heightmaps[continent] = find_heightmap(archive_set, continent)
            errors = [issue for issue in model.validate(archive_set, heightmaps)
                      if issue['level'] == 'error']
            if errors:
                raise SystemExit('refusing to export: %d validation error(s)' % len(errors))
        finally:
            archive_set.close()
    destination, entries = model.export_pak(args.out, slot=args.slot, overwrite=args.overwrite)
    for name in sorted(entries):
        print('%s: %d bytes' % (name, len(entries[name])))
    print(destination)


def load_story(path):
    try:
        return story_module.Story.load_json(path)
    except story_module.StoryError as error:
        raise SystemExit(str(error))


def command_story_extract(args):
    continents = parse_continents(args.continents)
    try:
        model = story_module.Story.load_folder(args.game, continents)
    except story_module.StoryError as error:
        raise SystemExit(str(error))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model.save_json(out / 'story.json')
    info = {'format': 'attt-story-info/1', 'archives': model.archives,
            'continents': {'%s' % continent: {
                'summary': model.summary()[str(continent)],
                'sources': entry['sources']}
                for continent, entry in sorted(model.continents.items())}}
    write_json(info, out / 'story-info.json')
    counts = model.summary()
    print('wrote %s (%s)' % (out, ', '.join(
        'c%s: %d quests, %d triggers, %d dialogues, %d speech lines' %
        (continent, item['quests'], item['triggers'], item['dialogues'],
         item['speech_lines']) for continent, item in counts.items())))


def command_story_info(args):
    model = load_story(args.story)
    result = {'archives': model.archives, 'continents': model.summary()}
    if args.json:
        print(json.dumps(result, indent=1, sort_keys=True))
        return 0
    for continent, item in result['continents'].items():
        print('continent %s: %d quests, %d triggers, %d dialogues, %d speech lines' %
              (continent, item['quests'], item['triggers'], item['dialogues'],
               item['speech_lines']))
        entry = model.continents[int(continent)]
        for kind, source in sorted(entry['sources'].items()):
            print('  %-10s %s (slot %s)' % (kind, source['file'], source['slot']))
    issues = model.validate()
    errors = sum(1 for issue in issues if issue['level'] == 'error')
    warnings = len(issues) - errors
    if issues:
        print('%d error(s), %d warning(s); run story-validate for details' %
              (errors, warnings))
    return 0


def command_story_find(args):
    model = load_story(args.story)
    try:
        results = model.find(continent=args.continent, kind=args.kind, name=args.name,
                             text=args.text, limit=args.limit)
    except story_module.StoryError as error:
        raise SystemExit(str(error))
    print(json.dumps(results, indent=1, sort_keys=True))
    return 0


def command_story_dialogue(args):
    model = load_story(args.story)
    name = args.name
    continents = ([args.continent] if args.continent is not None
                  else sorted(model.continents))
    found = False
    output = []
    for continent in continents:
        dialogues = model.continents.get(int(continent), {}).get('dialogues', {})
        match = next((key for key in dialogues if key.lower() == name.lower()), None)
        if match is None:
            continue
        found = True
        lines = model.dialogue_lines(continent, match)
        output.append({'continent': continent, 'name': match, 'lines': lines[:args.limit]})
    if not found:
        raise SystemExit('dialogue %s was not found' % name)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    for block in output:
        print('continent %s: %s' % (block['continent'], block['name']))
        for line in block['lines']:
            speaker = line.get('who') or '?'
            print('%s[%s] %s' % ('  ' * line['depth'], speaker, line['speech']))
    return 0


def command_story_validate(args):
    model = load_story(args.story)
    issues = model.validate()
    errors = [issue for issue in issues if issue['level'] == 'error']
    if args.json:
        print(json.dumps({'errors': len(errors), 'warnings': len(issues) - len(errors),
                          'issues': issues[:args.limit]}, ensure_ascii=False,
                         indent=1, sort_keys=True))
    else:
        print('%d error(s), %d warning(s)' % (len(errors), len(issues) - len(errors)))
        for issue in issues[:args.limit]:
            print('  %s %s c%s %s%s' % (
                issue['level'], issue['kind'], issue.get('continent', '?'),
                issue.get('name', issue.get('file', '')),
                (': ' + issue['message']) if issue.get('message') else ''))
        if len(issues) > args.limit:
            print('  ... %d more' % (len(issues) - args.limit))
    return 1 if errors else 0


def command_story_patch(args):
    patch_path = Path(args.patch)
    try:
        document = json.loads(patch_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise SystemExit('cannot read %s: %s' % (patch_path, error))
    if not isinstance(document, dict) or document.get('format') != story_module.PATCH_FORMAT:
        raise SystemExit('%s is not an %s document' % (patch_path, story_module.PATCH_FORMAT))
    operations = document.get('operations')
    if not isinstance(operations, list) or not operations:
        raise SystemExit('patch has no operations')
    if not args.dry_run and not args.out:
        raise SystemExit('--out is required unless --dry-run is used')
    archive_set = open_game(args.game)
    try:
        patcher = story_module.StoryPatch(archive_set)
        try:
            for operation in operations:
                if isinstance(operation, dict) and 'value_file' in operation:
                    operation = dict(operation)
                    value_path = patch_path.parent / operation.pop('value_file')
                    operation['value'] = value_path.read_text(encoding='utf-8')
                patcher.add(operation)
        except story_module.StoryError as error:
            raise SystemExit('patch failed: %s' % error)
        except OSError as error:
            raise SystemExit('cannot read value file: %s' % error)
        result = {'dry_run': bool(args.dry_run), 'changes': patcher.changes}
        if args.dry_run:
            try:
                entries = patcher.documents()
            except story_module.StoryError as error:
                raise SystemExit('patch failed: %s' % error)
            result['files'] = {name: len(data) for name, data in sorted(entries.items())}
            print(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True))
            return 0
        try:
            destination, entries = patcher.export_pak(args.out, slot=args.slot,
                                                       overwrite=args.overwrite)
        except (story_module.StoryError, OSError, ValueError) as error:
            raise SystemExit('export failed: %s' % error)
        result['out'] = destination
        result['files'] = {name: len(data) for name, data in sorted(entries.items())}
        print(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    finally:
        archive_set.close()


def command_render(args):
    world = load_world(args.world)
    forests = load_forests(args.forests) if args.forests else None
    archive_set = open_game(args.game)
    try:
        map_ = find_heightmap(archive_set, args.continent)
        if args.out.lower().endswith('.png'):
            data = render.render_png(world, args.continent, map_, size=args.size, water=args.water)
            Path(args.out).write_bytes(data)
        else:
            svg = render.render_svg(world, args.continent, map_, size=args.size, water=args.water,
                                    show=tuple(args.show.split(',')), forests=forests,
                                    forest_limit=args.forest_limit)
            Path(args.out).write_text(svg, encoding='utf-8')
        print(args.out)
    finally:
        archive_set.close()


def command_patch(args):
    world = load_world(args.world)
    with open(args.patch, encoding='utf-8') as stream:
        document = json.load(stream)
    archive_set = open_game(args.game) if args.game else None
    try:
        heightmaps = {}
        if archive_set is not None:
            for continent in world.continents:
                if archive_set.has('continent%d_heightmap.nmph' % continent):
                    heightmaps[continent] = find_heightmap(archive_set, continent)
        before = world_module.to_jsonable(world.document())
        try:
            results = world_module.apply_patch(world, document, heightmaps)
        except world_module.WorldError as error:
            raise SystemExit('patch failed: %s' % error)
        changes = diff_documents(before, world_module.to_jsonable(world.document()), args.limit)
        if changes and not args.dry_run:
            world.save_json(args.world)
        print(json.dumps({'dry_run': bool(args.dry_run), 'operations': results,
                          'changes': changes},
                         ensure_ascii=False, indent=1, sort_keys=True))
    finally:
        if archive_set is not None:
            archive_set.close()


def diff_documents(left, right, limit):
    changes = []
    left_continents = left.get('continents', {})
    right_continents = right.get('continents', {})
    continents = sorted(set(left_continents) | set(right_continents), key=int)
    for key in continents:
        left_modules = left_continents.get(key, {}).get('modules', {})
        right_modules = right_continents.get(key, {}).get('modules', {})
        for name in sorted(set(left_modules) | set(right_modules)):
            before = left_modules.get(name)
            after = right_modules.get(name)
            if before is None or after is None:
                changes.append({'continent': int(key), 'module': name,
                                'change': 'added' if before is None else 'removed'})
            elif world_module.canonical(before) != world_module.canonical(after):
                paths = []
                compare_paths(before, after, '', paths, limit)
                changes.append({'continent': int(key), 'module': name, 'change': 'modified',
                                'paths': paths})
    return changes


def command_diff(args):
    left = load_world(args.world)
    right = load_world(args.right)
    changes = diff_documents(left.document(), right.document(), args.limit)
    if args.json:
        print(json.dumps(changes, ensure_ascii=False, indent=1, sort_keys=True))
    else:
        for change in changes:
            print('c%s %s: %s' % (change['continent'], change['module'], change['change']))
            for path in change.get('paths', []):
                print('  ' + path)
        if not changes:
            print('no differences')
    return 1 if changes else 0


def compare_paths(before, after, path, out, limit):
    if len(out) >= limit:
        return
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after), key=str):
            compare_paths(before.get(key), after.get(key), path + '/' + str(key), out, limit)
            if len(out) >= limit:
                return
    elif before != after:
        out.append('%s: %r -> %r' % (path or '/', before, after))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    extract = sub.add_parser('extract', help='decode archives into a JSON world model')
    extract.add_argument('--game', required=True)
    extract.add_argument('--continents', default='1,2,3')
    extract.add_argument('--out', required=True)
    extract.add_argument('--map', action='store_true', help='also render continent SVG maps')
    extract.add_argument('--size', type=int, default=1200)
    extract.set_defaults(func=command_extract)

    info = sub.add_parser('info', help='summarize a world model')
    info.add_argument('world')
    info.add_argument('--json', action='store_true')
    info.set_defaults(func=command_info)

    find = sub.add_parser('find', help='search entities, towns and armies')
    find.add_argument('world')
    find.add_argument('--name')
    find.add_argument('--type', choices=('entity', 'npc', 'object', 'tree', 'town', 'army', 'armypos'))
    find.add_argument('--town')
    find.add_argument('--house')
    find.add_argument('--game', help='also report terrain elevation from the archives')
    find.add_argument('--json', action='store_true')
    find.set_defaults(func=command_find)

    move = sub.add_parser('move', help='move a placement in local or world coordinates')
    move.add_argument('world')
    move.add_argument('--continent', type=int, required=True)
    move.add_argument('--town', required=True)
    move.add_argument('--house', required=True)
    move.add_argument('--kind', choices=('npc', 'object', 'tree'), required=True)
    move.add_argument('--index', type=int)
    move.add_argument('--name')
    move.add_argument('--x', type=float)
    move.add_argument('--y', type=float)
    move.add_argument('--z', type=float)
    move.add_argument('--world', dest='world_coords', action='store_true',
                      help='x/z are absolute world coordinates')
    move.set_defaults(func=command_move)

    add = sub.add_parser('add', help='create a placement')
    add.add_argument('world')
    add.add_argument('--continent', type=int, required=True)
    add.add_argument('--town', required=True)
    add.add_argument('--house', required=True)
    add.add_argument('--kind', choices=('npc', 'object', 'tree'), required=True)
    add.add_argument('--name', help='NPC definition name, object model or tree model')
    add.add_argument('--index', type=int)
    add.add_argument('--x', type=float)
    add.add_argument('--y', type=float)
    add.add_argument('--z', type=float)
    add.add_argument('--rot', type=float, help='rotation in degrees (Y axis for objects)')
    add.add_argument('--scale', type=float, default=1.0)
    add.add_argument('--gizmo', help='object gizmo model (default: <model>Gizmo; pass an '
                                     'empty string to omit the gizmo table)')
    add.add_argument('--group', default='Objects01')
    add.add_argument('--lod', default='farest')
    add.add_argument('--npc-kind', default='Creature')
    add.add_argument('--world', dest='world_coords', action='store_true',
                     help='x/z are absolute world coordinates')
    add.set_defaults(func=command_add)

    add_town = sub.add_parser('add-town', help='create a town')
    add_town.add_argument('world')
    add_town.add_argument('--continent', type=int, required=True)
    add_town.add_argument('--name', required=True)
    add_town.add_argument('--x', type=float, required=True)
    add_town.add_argument('--y', type=float, default=0.0)
    add_town.add_argument('--z', type=float, required=True)
    add_town.add_argument('--rot', type=float, default=0.0)
    add_town.set_defaults(func=command_add_town)

    add_house = sub.add_parser('add-house', help='create a house inside a town')
    add_house.add_argument('world')
    add_house.add_argument('--continent', type=int, required=True)
    add_house.add_argument('--town', required=True)
    add_house.add_argument('--name', required=True)
    add_house.add_argument('--x', type=float, required=True)
    add_house.add_argument('--y', type=float, default=0.0)
    add_house.add_argument('--z', type=float, required=True)
    add_house.add_argument('--rot', type=float, default=0.0)
    add_house.set_defaults(func=command_add_house)

    remove_town = sub.add_parser('remove-town', help='delete a town')
    remove_town.add_argument('world')
    remove_town.add_argument('--continent', type=int, required=True)
    remove_town.add_argument('--name', required=True)
    remove_town.add_argument('--force', action='store_true',
                             help='allow deleting a town that still contains houses or placements')
    remove_town.set_defaults(func=command_remove_town)

    remove_house = sub.add_parser('remove-house', help='delete a house')
    remove_house.add_argument('world')
    remove_house.add_argument('--continent', type=int, required=True)
    remove_house.add_argument('--town', required=True)
    remove_house.add_argument('--name', required=True)
    remove_house.add_argument('--force', action='store_true',
                              help='allow deleting a house that still contains placements')
    remove_house.set_defaults(func=command_remove_house)

    remove = sub.add_parser('remove', help='delete a placement')
    remove.add_argument('world')
    remove.add_argument('--continent', type=int, required=True)
    remove.add_argument('--town', required=True)
    remove.add_argument('--house', required=True)
    remove.add_argument('--kind', choices=('npc', 'object', 'tree'), required=True)
    remove.add_argument('--index', type=int)
    remove.add_argument('--name')
    remove.set_defaults(func=command_remove)

    clone = sub.add_parser('clone', help='duplicate a placement')
    clone.add_argument('world')
    clone.add_argument('--continent', type=int, required=True)
    clone.add_argument('--town', required=True)
    clone.add_argument('--house', required=True)
    clone.add_argument('--kind', choices=('npc', 'object', 'tree'), required=True)
    clone.add_argument('--index', type=int)
    clone.add_argument('--name')
    clone.add_argument('--index-new', type=int)
    clone.add_argument('--x', type=float)
    clone.add_argument('--z', type=float)
    clone.add_argument('--rot', type=float)
    clone.add_argument('--world', dest='world_coords', action='store_true',
                       help='x/z are absolute world coordinates')
    clone.set_defaults(func=command_clone)

    move_army = sub.add_parser('move-army', help='move an ArmyPos entry')
    move_army.add_argument('world')
    move_army.add_argument('--continent', type=int, required=True)
    move_army.add_argument('--name', required=True)
    move_army.add_argument('--x', type=float)
    move_army.add_argument('--z', type=float)
    move_army.add_argument('--radius', type=float)
    move_army.set_defaults(func=command_move_army)

    add_army = sub.add_parser('add-army', help='create an army definition')
    add_army.add_argument('world')
    add_army.add_argument('--continent', type=int, required=True)
    add_army.add_argument('--name', required=True)
    add_army.add_argument('--display-name', default='')
    add_army.add_argument('--attitude', default='Disabled',
                          choices=world_module.ARMY_ATTITUDES)
    add_army.add_argument('--standard', default='stSamael')
    add_army.add_argument('--troop', action='append', metavar='UNIT:QUANTITY',
                          help='add a troop entry (repeatable)')
    add_army.add_argument('--x', type=float, help='also create an ArmyPos entry at this X')
    add_army.add_argument('--z', type=float, help='also create an ArmyPos entry at this Z')
    add_army.add_argument('--radius', type=float)
    add_army.set_defaults(func=command_add_army)

    remove_army = sub.add_parser('remove-army',
                                 help='delete an army definition and its ArmyPos entry')
    remove_army.add_argument('world')
    remove_army.add_argument('--continent', type=int, required=True)
    remove_army.add_argument('--name', required=True)
    remove_army.set_defaults(func=command_remove_army)

    snap = sub.add_parser('snap', help='reset terrain-relative Y offsets (0 = on the ground)')
    snap.add_argument('world')
    snap.add_argument('--game', required=True)
    snap.add_argument('--continent', type=int, required=True)
    snap.add_argument('--town')
    snap.add_argument('--house')
    snap.add_argument('--kind', choices=('npc', 'object', 'tree'))
    snap.add_argument('--offset', type=float, default=0.0)
    snap.add_argument('--dry-run', action='store_true')
    snap.add_argument('--limit', type=int, default=20)
    snap.set_defaults(func=command_snap)

    validate = sub.add_parser('validate', help='check references and asset presence')
    validate.add_argument('world')
    validate.add_argument('--game')
    validate.add_argument('--water', type=float,
                          help='also warn about placements below this elevation')
    validate.add_argument('--json', action='store_true')
    validate.add_argument('--limit', type=int, default=30)
    validate.set_defaults(func=command_validate)

    export = sub.add_parser('export', help='write changed modules as a ResourceN.pak overlay')
    export.add_argument('world')
    export.add_argument('--out', required=True)
    export.add_argument('--slot', type=int)
    export.add_argument('--game')
    export.add_argument('--overwrite', action='store_true',
                        help='replace an existing ResourceN.pak instead of refusing')
    export.set_defaults(func=command_export)

    map_parser = sub.add_parser('render', help='render a hillshaded top-down map')
    map_parser.add_argument('world')
    map_parser.add_argument('--game', required=True)
    map_parser.add_argument('--continent', type=int, default=1)
    map_parser.add_argument('--out', required=True)
    map_parser.add_argument('--size', type=int, default=1200)
    map_parser.add_argument('--water', type=float, default=0.0)
    map_parser.add_argument('--show', default='town,npc,army',
                            help='comma list of town,npc,army,forest')
    map_parser.add_argument('--forests', help='forests.json to draw when show includes forest')
    map_parser.add_argument('--forest-limit', type=int, default=20000,
                            help='maximum forest dots before uniform subsampling')
    map_parser.set_defaults(func=command_render)

    patch = sub.add_parser('patch', help='apply a JSON batch of world edit operations')
    patch.add_argument('world')
    patch.add_argument('patch')
    patch.add_argument('--game', help='archives required for snap operations')
    patch.add_argument('--dry-run', action='store_true',
                       help='apply in memory, show the diff, do not save')
    patch.add_argument('--limit', type=int, default=20)
    patch.set_defaults(func=command_patch)

    diff = sub.add_parser('diff', help='compare two world models')
    diff.add_argument('world')
    diff.add_argument('right')
    diff.add_argument('--json', action='store_true')
    diff.add_argument('--limit', type=int, default=20)
    diff.set_defaults(func=command_diff)

    forest_extract = sub.add_parser('forest-extract',
                                    help='decode forest zones (.fst) into a JSON model')
    forest_extract.add_argument('--game', required=True)
    forest_extract.add_argument('--out', required=True)
    forest_extract.add_argument('--continents')
    forest_extract.set_defaults(func=command_forest_extract)

    forest_info = sub.add_parser('forest-info', help='summarize forest zones and tree counts')
    forest_info.add_argument('forests')
    forest_info.add_argument('--json', action='store_true')
    forest_info.set_defaults(func=command_forest_info)

    forest_find = sub.add_parser('forest-find', help='search trees by zone, model or position')
    forest_find.add_argument('forests')
    forest_find.add_argument('--continent', type=int)
    forest_find.add_argument('--zone')
    forest_find.add_argument('--model')
    forest_find.add_argument('--type', type=int)
    forest_find.add_argument('--x', type=float)
    forest_find.add_argument('--z', type=float)
    forest_find.add_argument('--radius', type=float)
    forest_find.add_argument('--limit', type=int, default=100)
    forest_find.set_defaults(func=command_forest_find)

    forest_add = sub.add_parser('forest-add', help='add a tree to a forest zone')
    forest_add.add_argument('forests')
    forest_add.add_argument('--continent', type=int, required=True)
    forest_add.add_argument('--zone', required=True)
    forest_add.add_argument('--type', type=int, help='tree type id from forest-info')
    forest_add.add_argument('--model', help='tree model name, e.g. Pine101')
    forest_add.add_argument('--x', type=float, required=True)
    forest_add.add_argument('--z', type=float, required=True)
    forest_add.add_argument('--y', type=float, help='defaults to terrain elevation')
    forest_add.add_argument('--yaw', type=float, default=0.0)
    forest_add.add_argument('--scale', type=float, default=1.0)
    forest_add.add_argument('--y-scale', type=float)
    forest_add.add_argument('--index', type=int)
    forest_add.add_argument('--game', help='archives used to sample terrain elevation')
    forest_add.add_argument('--dry-run', action='store_true')
    forest_add.set_defaults(func=command_forest_add)

    forest_move = sub.add_parser('forest-move', help='move or transform one tree record')
    forest_move.add_argument('forests')
    forest_move.add_argument('--continent', type=int, required=True)
    forest_move.add_argument('--zone', required=True)
    forest_move.add_argument('--index', type=int, required=True)
    forest_move.add_argument('--x', type=float)
    forest_move.add_argument('--y', type=float)
    forest_move.add_argument('--z', type=float)
    forest_move.add_argument('--yaw', type=float)
    forest_move.add_argument('--scale', type=float)
    forest_move.add_argument('--y-scale', type=float)
    forest_move.add_argument('--ground', action='store_true',
                             help='set y from the terrain heightmap')
    forest_move.add_argument('--game', help='archives used to sample terrain elevation')
    forest_move.add_argument('--dry-run', action='store_true')
    forest_move.set_defaults(func=command_forest_move)

    forest_remove = sub.add_parser('forest-remove', help='delete one tree record')
    forest_remove.add_argument('forests')
    forest_remove.add_argument('--continent', type=int, required=True)
    forest_remove.add_argument('--zone', required=True)
    forest_remove.add_argument('--index', type=int, required=True)
    forest_remove.add_argument('--dry-run', action='store_true')
    forest_remove.set_defaults(func=command_forest_remove)

    forest_validate = sub.add_parser('forest-validate',
                                     help='check tree types, models and map bounds')
    forest_validate.add_argument('forests')
    forest_validate.add_argument('--game')
    forest_validate.add_argument('--no-heightmap', action='store_true')
    forest_validate.add_argument('--json', action='store_true')
    forest_validate.add_argument('--limit', type=int, default=30)
    forest_validate.set_defaults(func=command_forest_validate)

    forest_export = sub.add_parser('forest-export',
                                   help='write changed forest zones as a ResourceN.pak overlay')
    forest_export.add_argument('forests')
    forest_export.add_argument('--out', required=True)
    forest_export.add_argument('--slot', type=int)
    forest_export.add_argument('--game')
    forest_export.add_argument('--no-heightmap', action='store_true')
    forest_export.add_argument('--overwrite', action='store_true')
    forest_export.set_defaults(func=command_forest_export)

    story_extract = sub.add_parser('story-extract',
                                   help='index quests, triggers and conversations')
    story_extract.add_argument('--game', required=True)
    story_extract.add_argument('--out', required=True)
    story_extract.add_argument('--continents', help='comma list, default 1,2,3')
    story_extract.set_defaults(func=command_story_extract)

    story_info = sub.add_parser('story-info', help='summarize a story index')
    story_info.add_argument('story')
    story_info.add_argument('--json', action='store_true')
    story_info.set_defaults(func=command_story_info)

    story_find = sub.add_parser('story-find',
                                help='search quests, triggers and dialogue lines')
    story_find.add_argument('story')
    story_find.add_argument('--continent', type=int)
    story_find.add_argument('--kind', choices=('quest', 'trigger', 'dialogue'))
    story_find.add_argument('--name', help='substring of a quest/trigger/dialogue name')
    story_find.add_argument('--text', help='substring of display text or dialogue speech')
    story_find.add_argument('--limit', type=int, default=50)
    story_find.set_defaults(func=command_story_find)

    story_dialogue = sub.add_parser('story-dialogue',
                                    help='print one dialogue tree with speakers')
    story_dialogue.add_argument('story')
    story_dialogue.add_argument('name')
    story_dialogue.add_argument('--continent', type=int)
    story_dialogue.add_argument('--json', action='store_true')
    story_dialogue.add_argument('--limit', type=int, default=500)
    story_dialogue.set_defaults(func=command_story_dialogue)

    story_validate = sub.add_parser('story-validate',
                                    help='check trigger keys and dialogue structure')
    story_validate.add_argument('story')
    story_validate.add_argument('--json', action='store_true')
    story_validate.add_argument('--limit', type=int, default=30)
    story_validate.set_defaults(func=command_story_validate)

    story_patch = sub.add_parser('story-patch',
                                 help='apply literal story edits as a ResourceN.pak overlay')
    story_patch.add_argument('patch', help='attt-story-patch/1 JSON document')
    story_patch.add_argument('--game', required=True,
                             help='game folder the edits are based on')
    story_patch.add_argument('--out', help='folder for the overlay PAK')
    story_patch.add_argument('--slot', type=int)
    story_patch.add_argument('--overwrite', action='store_true')
    story_patch.add_argument('--dry-run', action='store_true')
    story_patch.set_defaults(func=command_story_patch)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    return result or 0


if __name__ == '__main__':
    sys.exit(main())
