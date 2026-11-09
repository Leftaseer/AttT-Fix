#!/usr/bin/env python3
"""Local preview and patch server for the JSON world model.

The CLI and JSON model remain the canonical interfaces; this server is a thin
human-friendly layer: browse the rendered map, inspect entities and validation,
and apply batch patches with an explicit dry-run step.

It binds to localhost, never touches the game archives, and only writes the
JSON model when a patch request asks for ``save=1``.
"""
import argparse
import html
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import heightmap as heightmap_module  # noqa: E402
import forests as forests_module  # noqa: E402
import render  # noqa: E402
import world as world_module  # noqa: E402
import worldctl  # noqa: E402

MAX_BODY = 5 * 1024 * 1024


def copy_world(world):
    return world_module.World(
        {continent: {'modules': world_module.clone(entry.get('modules', {})),
                     'sources': world_module.clone(entry.get('sources', {}))}
         for continent, entry in world.continents.items()},
        world_module.clone(world.archives))


class State:
    def __init__(self, world_path, game=None, forests_path=None, *, archives=None):
        self.world_path = Path(world_path)
        self.world = world_module.World.load_json(world_path)
        self.archives = archives if archives is not None else (worldctl.open_game(game) if game else None)
        self.units = worldctl.load_units(self.archives)
        self.forests = (forests_module.Forests.load_json(forests_path)
                        if forests_path else None)
        self.forests_path = Path(forests_path) if forests_path else None
        self._maps = {}
        self.revision = 0
        self._project_stat = self.world_path.stat()

    def close(self):
        if self.archives is not None:
            self.archives.close()

    def heightmap(self, continent):
        if continent in self._maps:
            return self._maps[continent]
        map_ = None
        if self.archives is not None:
            name = 'continent%d_heightmap.nmph' % continent
            if self.archives.has(name):
                map_ = heightmap_module.Heightmap(self.archives.read(name))
        self._maps[continent] = map_
        return map_

    def info(self):
        result = {'world': str(self.world_path), 'archives': self.world.archives,
                  'game': self.archives is not None, 'continents': {}}
        if self.forests is not None:
            result['forests'] = {
                'path': str(self.forests_path),
                'continents': {str(continent): sum(len(entry['records'])
                                                   for entry in zones.values())
                               for continent, zones in sorted(self.forests.zones.items())},
            }
        changed = self.world.changed_modules()
        for continent in sorted(self.world.continents):
            result['continents'][str(continent)] = {
                'modules': {name: len(table) for name, table in
                            self.world.continents[continent]['modules'].items()},
                'placements': sum(1 for _ in self.world.placements(continent)),
                'changed': sorted(name for (item, name) in changed if item == continent),
                'heightmap': self.heightmap(continent) is not None,
            }
        return result

    def validate(self, continent):
        issues = self.world.validate(continent, self.archives, self.units)
        map_ = self.heightmap(continent)
        if map_ is not None:
            issues.extend(worldctl.heightmap_issues(self.world, continent, map_))
        return issues

    def patch(self, document, dry_run=False, save=False):
        before = world_module.to_jsonable(self.world.document())
        candidate = copy_world(self.world)
        heightmaps = {continent: map_ for continent in candidate.continents
                      if (map_ := self.heightmap(continent)) is not None}
        results = world_module.apply_patch(candidate, document, heightmaps)
        after = world_module.to_jsonable(candidate.document())
        changes = worldctl.diff_documents(before, after, 50)
        if not dry_run:
            if save:
                current = self.world_path.stat()
                if (current.st_ino, current.st_size, current.st_mtime_ns) != (
                        self._project_stat.st_ino, self._project_stat.st_size, self._project_stat.st_mtime_ns):
                    raise world_module.WorldError('The world project changed on disk. Restart the workspace to load it.')
                with TemporaryDirectory(dir=self.world_path.parent) as folder:
                    staged = Path(folder) / self.world_path.name
                    candidate.save_json(staged)
                    os.replace(staged, self.world_path)
                self._project_stat = self.world_path.stat()
            self.world = candidate
            self.revision += 1
        return {'dry_run': bool(dry_run), 'saved': bool(save and not dry_run),
                'results': world_module.to_jsonable(results), 'changes': changes}


PAGE = """<!DOCTYPE html>
<meta charset="utf-8">
<title>AttT world preview</title>
<style>
 body {{ background:#181a1d; color:#ddd; font:14px system-ui,sans-serif; margin:16px; }}
 a {{ color:#7cb7ff; }}
 #map {{ display:block; max-width:100%; background:#000; margin:8px 0; }}
 textarea {{ width:100%; height:180px; background:#101214; color:#ddd;
             border:1px solid #333; font:12px monospace; }}
 pre {{ background:#101214; border:1px solid #333; padding:8px; overflow:auto; }}
 button {{ background:#2d4a6b; color:#fff; border:1px solid #456; padding:4px 10px; }}
</style>
<h2>AttT world preview</h2>
<p>{info}</p>
<p><img id="map" alt="world map" src="map/{continent}.svg?size=1100&water=0&show={layers}"></p>
<p><label>Continent <select id="continent">{options}</select></label>
   <a href="world.json">world.json</a> |
   <a href="entities.json">entities.json</a> |
   <a href="info.json">info.json</a> |
   <a href="validate/{continent}.json">validate</a></p>
<h3>Batch patch</h3>
<textarea id="patch">{{"format": "attt-world-patch/1", "operations": []}}</textarea>
<p><button onclick="run(1)">Dry run</button>
   <button onclick="run(0)">Apply and save</button></p>
<pre id="out">No request yet.</pre>
<script>
const continent = document.getElementById('continent');
const map = document.getElementById('map');
const patch = document.getElementById('patch');
const out = document.getElementById('out');
function show() {{ map.src = 'map/' + continent.value + '.svg?size=1100&water=0&show={layers}'; }}
continent.addEventListener('change', show);
async function run(dry) {{
  const response = await fetch('patch?dry_run=' + dry + '&save=' + (dry ? 0 : 1), {{
    method: 'POST', headers: {{'content-type': 'application/json'}}, body: patch.value}});
  const data = await response.json();
  out.textContent = JSON.stringify(data, null, 1);
  if (response.ok && !dry) {{
    if (window.parent !== window) window.parent.postMessage('attt-world-updated', location.origin);
    setTimeout(() => location.reload(), 600);
  }}
}}
</script>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = 'attt-worldserve/1'

    def log_message(self, format, *args):
        sys.stderr.write('%s %s\n' % (self.address_string(), format % args))

    @property
    def state(self):
        return self.server.state

    def send_bytes(self, data, content_type, status=200, headers=()):
        self.send_response(status)
        self.send_header('content-type', content_type)
        if status != 204:
            self.send_header('content-length', str(len(data)))
        self.send_header('cache-control', 'no-store')
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, value, status=200):
        self.send_bytes(json.dumps(value, ensure_ascii=False, indent=1,
                                   sort_keys=True).encode('utf-8'),
                        'application/json; charset=utf-8', status)

    def error(self, message, status=400):
        self.send_json({'error': message}, status)

    def do_GET(self):
        parsed = urlsplit(self.path)
        parts = [part for part in parsed.path.split('/') if part]
        query = parse_qs(parsed.query)
        if not parts:
            return self.page(int(query.get('continent', ['1'])[0]))
        if parts == ['world.json']:
            return self.send_json(world_module.to_jsonable(self.state.world.document()))
        if parts == ['info.json']:
            return self.send_json(self.state.info())
        if parts == ['entities.json']:
            return self.send_json({'format': 'attt-world-entities/1', 'continents': {
                str(continent): self.state.world.flat_entities(continent)
                for continent in sorted(self.state.world.continents)}})
        if len(parts) == 2 and parts[0] in ('entities', 'validate'):
            value = parts[1][:-5] if parts[1].endswith('.json') else parts[1]
            continent = self.continent(value)
            if continent is None:
                return
            if parts[0] == 'entities':
                return self.send_json(self.state.world.flat_entities(continent))
            return self.send_json({'continent': continent,
                                   'issues': self.state.validate(continent)})
        if len(parts) == 2 and parts[0] == 'map' and parts[1].endswith('.svg'):
            continent = self.continent(parts[1][:-4])
            if continent is None:
                return
            map_ = self.state.heightmap(continent)
            if map_ is None:
                return self.error('continent %s has no heightmap in the selected archives' %
                                  continent, 404)
            show = tuple(item for item in query.get('show', ['town,npc,army'])[0].split(',')
                         if item)
            try:
                size = max(200, min(3000, int(query.get('size', ['1100'])[0])))
                water = float(query.get('water', ['0'])[0])
            except ValueError:
                return self.error('size and water must be numbers')
            svg = render.render_svg(self.state.world, continent, map_, size=size,
                                    water=water, show=show, forests=self.state.forests)
            return self.send_bytes(svg.encode('utf-8'), 'image/svg+xml; charset=utf-8')
        return self.error('not found', 404)

    def do_POST(self):
        parsed = urlsplit(self.path)
        if parsed.path != '/patch':
            return self.error('not found', 404)
        try:
            length = int(self.headers.get('content-length', '0'))
        except ValueError:
            return self.error('bad content-length')
        if length <= 0 or length > MAX_BODY:
            return self.error('patch body must be between 1 and %d bytes' % MAX_BODY, 413)
        try:
            document = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError) as error:
            return self.error('invalid JSON: %s' % error)
        query = parse_qs(parsed.query)
        dry_run = query.get('dry_run', ['1'])[0] not in ('0', 'false', 'no')
        save = query.get('save', ['0'])[0] in ('1', 'true', 'yes')
        try:
            result = self.state.patch(document, dry_run=dry_run, save=save)
        except (OSError, world_module.WorldError) as error:
            return self.error(str(error))
        return self.send_json(result)

    def continent(self, value):
        try:
            continent = int(value)
        except ValueError:
            self.error('continent must be an integer', 404)
            return None
        if continent not in self.state.world.continents:
            self.error('unknown continent %s' % continent, 404)
            return None
        return continent

    def page(self, continent):
        if continent not in self.state.world.continents:
            continent = min(self.state.world.continents)
        options = ''.join('<option value="%d"%s>%d</option>' %
                          (item, ' selected' if item == continent else '', item)
                          for item in sorted(self.state.world.continents))
        info = '%d continents from %s; game archives %s' % (
            len(self.state.world.continents), self.state.world_path.name,
            'loaded' if self.state.archives is not None else 'not loaded (map disabled)')
        if self.state.forests is not None:
            info += '; forests loaded'
        layers = 'town,npc,army,forest' if self.state.forests is not None else 'town,npc,army'
        body = PAGE.format(info=html.escape(info), continent=continent, options=options,
                           layers=layers)
        self.send_bytes(body.encode('utf-8'), 'text/html; charset=utf-8')


class Server(HTTPServer):
    allow_reuse_address = True

    def __init__(self, address, world_path, game=None, forests_path=None):
        self.state = State(world_path, game, forests_path)
        super().__init__(address, Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world')
    parser.add_argument('--game', help='game folder for maps and validation')
    parser.add_argument('--forests', help='forests.json to draw on the map')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    server = Server((args.host, args.port), args.world, args.game, args.forests)
    host, port = server.server_address[:2]
    print('serving http://%s:%d/ (%s)' % (host, port, args.world))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.state.close()
        server.server_close()


if __name__ == '__main__':
    main()
