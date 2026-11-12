"""Local web workspace for the balance and campaign editors."""

import hashlib
from http.server import HTTPServer
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urlsplit
from uuid import uuid4
import webbrowser

from campaign import Campaign, atomic_write
import forests
import gres
import render
import story
from world import World, WorldError
from worldserve import Handler, MAX_BODY

BALANCE = Path(__file__).resolve().parent / 'balance-studio'
STATIC_TYPES = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.py': 'text/plain; charset=utf-8',
}
MAX_SLICE = 32 * 1024 * 1024
EDITIONS = ('attt', 'valkyrie')


def default_data_dir():
    base = os.environ.get('LOCALAPPDATA')
    return Path(base) / 'AttT Modding Studio' if base else Path.home() / '.attt-modding-studio'


class Workspace(HTTPServer):
    def __init__(self, port, data_dir):
        super().__init__(('127.0.0.1', port), WorkspaceHandler)
        self.data_dir = data_dir
        self.state = None
        self.settings = {}
        self.session = None
        self.start_error = None

    def open_project(self, settings, world_path=None, forests_path=None, remember=True):
        edition = settings['edition']
        game = Path(settings['game']).expanduser().resolve()
        name = settings.get('project', 'My mod').strip()
        localization = settings.get('preferLocalization', False)
        if edition not in EDITIONS or not name or len(name) > 80 or not isinstance(localization, bool):
            raise WorldError('Choose a game edition and a project name of up to 80 characters.')
        if not game.is_dir():
            raise WorldError('Choose the folder that contains Resource0.pak.')
        settings = {'edition': edition, 'game': str(game), 'project': name, 'preferLocalization': localization}
        archives = gres.ArchiveSet.open_folder(game, allow_gaps=True, prefer_localization=localization,
                                               fill_attfix_gap=edition == 'attt')
        try:
            for expected, actual in enumerate(archives.slots):
                if actual != expected:
                    raise WorldError('Resource%d.pak is missing before Resource%d.pak.' % (expected, actual))
            if len(archives.slots) > 255:
                raise WorldError('The workspace needs an available Resource export slot.')
            if world_path is None:
                key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()[:24]
                world_path = self.data_dir / 'projects' / key / 'world.json'
                world_path.parent.mkdir(parents=True, exist_ok=True)
            if world_path.suffix.lower() != '.json':
                raise WorldError('Choose a .json path for the world project.')
            if not world_path.exists():
                world = World._from_set(archives, (1, 2, 3))
                if not world.continents:
                    raise WorldError('The selected archives contain no world data.')
                atomic_write(world_path, world.save_json)
            try:
                candidate = Campaign(world_path, archives, forests_path)
            except SystemExit as error:
                raise WorldError(str(error)) from error
            if not candidate.world.continents:
                raise WorldError('The world project contains no continents.')
            if remember:
                self.data_dir.mkdir(parents=True, exist_ok=True)
                atomic_write(self.data_dir / 'last-project.json',
                             lambda path: path.write_text(json.dumps(settings), encoding='utf-8'))
        except Exception:
            archives.close()
            raise
        if self.state:
            self.state.close()
        self.state, self.settings, self.session = candidate, settings, uuid4().hex
        self.start_error = None

    def restore(self):
        try:
            settings = json.loads((self.data_dir / 'last-project.json').read_text(encoding='utf-8'))
            self.settings = settings
            self.open_project(settings, remember=False)
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.start_error = str(error)

    @property
    def revision(self):
        return '%s:%s' % (self.session, self.state.revision)

    def session_info(self):
        return {
            'active': self.state is not None, 'settings': self.settings, 'error': self.start_error,
            'folderPicker': os.name == 'nt',
            'edition': self.settings.get('edition'),
            'worldRevision': self.revision if self.state else None,
            'session': self.session,
            'archives': [
                {'slot': slot, 'name': archive.path.name, 'size': archive.path.stat().st_size}
                for slot, archive in self.state.archives.archives.items()
            ] if self.state else [],
        }

    def server_close(self):
        if self.state:
            self.state.close()
        super().server_close()


def pick_folder():
    if os.name != 'nt':
        raise WorldError('Paste the game folder path into the field.')
    script = r'''
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()
$dialog = New-Object Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Select the game folder containing Resource0.pak'
$dialog.ShowNewFolderButton = $false
if ($dialog.ShowDialog() -eq 'OK') { Write-Output $dialog.SelectedPath }
$dialog.Dispose()
'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-STA', '-Command', script],
                            capture_output=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise WorldError('The folder picker could not open. Paste the game folder path instead.')
    return result.stdout.decode('utf-8').strip()


class WorkspaceHandler(Handler):
    def local_request(self):
        origin = 'http://127.0.0.1:%d' % self.server.server_port
        if self.headers.get('Host') != origin[7:] or self.headers.get('Origin', origin) != origin:
            self.error('Use the workspace URL printed by the launcher.', 403)
            return False
        return True

    def world_request(self, handle):
        path = self.path
        try:
            self.path = path[len('/world'):]
            handle()
        finally:
            self.path = path

    def do_GET(self):
        if not self.local_request():
            return
        route = urlsplit(self.path)
        try:
            if route.path == '/api/session':
                return self.send_json(self.server.session_info())
            if route.path.startswith(('/api/', '/world/')) and not self.state:
                return self.error('Open a game project first.', 409)
            if route.path.startswith('/world/'):
                return self.world_request(super().do_GET)
            query = {key: value[0] for key, value in parse_qs(route.query).items()}
            if route.path == '/api/world-overlay':
                return self.world_overlay(validate=query.get('preview') != '1')
            if route.path == '/api/campaign/check-export':
                if query.get('revision') != self.server.revision:
                    return self.error('The campaign draft changed. Open Review combined export again.', 409)
                self.state.export_entries()
                return self.send_json({'revision': self.server.revision})
            if route.path.startswith('/api/archive/'):
                return self.archive_slice(route, query)
            if route.path.startswith('/api/campaign/'):
                return self.campaign_data(route.path.rsplit('/', 1)[-1], query)
            name = unquote(route.path[1:]) if route.path != '/' else 'Balance Studio.html'
            if name == Path(name).name:
                path = BALANCE / name
                if path.suffix in STATIC_TYPES and path.is_file():
                    return self.send_bytes(path.read_bytes(), STATIC_TYPES[path.suffix])
            return self.error('not found', 404)
        except (ValueError, TypeError, KeyError, OSError) as error:
            self.error(str(error))

    def do_POST(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        if self.headers.get_content_type() != 'application/json':
            return self.error('Expected a JSON request.', 415)
        if path == '/world/patch' and self.state:
            return self.world_request(super().do_POST)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.error('Invalid JSON request length.', 413)
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                return self.error('Expected a JSON object.')
            if path == '/api/pick-folder':
                return self.send_json({'folder': pick_folder()})
            if path == '/api/project':
                self.server.open_project(request)
                return self.send_json(self.server.session_info())
            if not self.state or request.get('revision') != self.server.revision:
                return self.error('The project changed. Reload this editor before applying another edit.', 409)
            if path == '/api/campaign/world':
                result = self.state.patch(request, dry_run=request.get('dry_run', True), save=True)
            elif path == '/api/campaign/forests':
                result = self.state.edit_forest(request)
            elif path == '/api/campaign/story':
                result = self.state.edit_story(request)
            else:
                return self.error('not found', 404)
            return self.send_json({**result, 'revision': self.server.revision})
        except (ValueError, TypeError, KeyError, OSError, subprocess.TimeoutExpired) as error:
            self.error(str(error))

    def archive_slice(self, route, query):
        if query.get('session', self.server.session) != self.server.session:
            return self.error('The game project has changed.', 409)
        try:
            slot = int(route.path.rsplit('/', 1)[-1])
            archive = self.state.archives.archives[slot]
            start, end = int(query['start']), int(query['end'])
            if not 0 <= start <= end <= archive.path.stat().st_size or end - start > MAX_SLICE:
                raise ValueError()
        except (KeyError, ValueError):
            return self.error('Invalid archive slice.', 416)
        with archive.path.open('rb') as stream:
            stream.seek(start)
            data = stream.read(end - start)
        return self.send_bytes(data, 'application/octet-stream')

    def campaign_data(self, kind, query):
        state = self.state
        continent = int(query.get('continent', min(state.world.continents)))
        if continent not in state.world.continents:
            return self.error('Unknown continent.', 404)
        world = state.world
        map_ = state.heightmap(continent) if kind in ('world', 'terrain') else None
        data = {'revision': self.server.revision, 'continents': sorted(world.continents)}
        if kind == 'terrain':
            if map_ is None:
                return self.error('This continent has no terrain map.', 404)
            if continent not in state.terrain:
                state.terrain[continent] = render.render_png(world, continent, map_, size=900)
            return self.send_bytes(state.terrain[continent], 'image/png')
        if kind == 'world':
            modules = world.continents[continent]['modules']
            data.update(
                bounds=[map_.min_x, map_.max_x, map_.min_z, map_.max_z] if map_ else None,
                towns={name: list((town.get('Houses') or {}).keys()) for name, town in world.towns(continent).items()},
                armies=[{'name': name, 'title': army.get('DisplayName') or name,
                         'position': modules.get('armypos', {}).get(name)}
                        for name, army in modules.get('armies', {}).items() if isinstance(army, dict)],
                npcs=sorted(name for name in modules.get('npcs', {}) if isinstance(name, str)),
                placements=world.flat_entities(continent), units=sorted(state.units or []),
            )
        elif kind == 'forests':
            model = state.forest_model()
            zones = model.zones.get(continent, {})
            zone = query.get('zone') or next(iter(sorted(zones)), '')
            rows = []
            models = []
            if zone:
                zone_data = model.zone(continent, zone)
                models = sorted(set(model.config.models(continent, zone).values()))
                offset = max(0, int(query.get('offset', 0)))
                rows = model.find(continent, zone, model=query.get('model'), limit=offset + 101)[offset:]
                for row in rows:
                    record = zone_data['records'][row['index']]
                    row.update(yaw=forests.matrix_yaw(record['matrix']),
                               scale=forests.matrix_scale(record['matrix'])[0],
                               y_scale=forests.matrix_scale(record['matrix'])[1])
                data['more'] = len(rows) > 100
                data['total'] = len(zone_data['records'])
            data.update(zones=sorted(zones), zone=zone, models=models, rows=rows[:100])
        elif kind == 'story':
            model = state.get_story()
            category = query.get('kind', 'quest')
            name = query.get('name')
            if name:
                records = model.entry(continent)[story.KIND_MODULE[category]]
                data['record'] = records.get(name)
                if category == 'dialogue' and name in records:
                    data['nodes'] = model.dialogue_nodes(continent, name)
            else:
                data['rows'] = model.find(continent, category, text=query.get('search'), limit=150)
        elif kind == 'validate':
            if query.get('kind') == 'forests':
                issues = state.forest_model().validate(state.archives, {continent: state.heightmap(continent)})
            elif query.get('kind') == 'story':
                issues = state.get_story().validate()
            else:
                issues = state.validate(continent)
            data['issues'] = issues[:200]
            data['total'] = len(issues)
        else:
            return self.error('not found', 404)
        return self.send_json(data)

    def world_overlay(self, validate=True):
        state, archives = self.state, self.state.archives
        headers = [('X-World-Revision', self.server.revision)]
        entries = state.export_entries(validate)
        if not entries:
            return self.send_bytes(b'', 'application/octet-stream', 204, headers)
        with TemporaryDirectory(prefix='attt-campaign-export-') as folder:
            path = Path(folder) / 'draft.pak'
            identity = gres.file_identity(archives, entries)
            gres.write_pak(path, entries, identity=identity)
            return self.send_bytes(path.read_bytes(), 'application/octet-stream', headers=headers)


def serve_workspace(args):
    if bool(args.game) != bool(args.world):
        raise WorldError('Provide both --game and --world, or launch without either to choose in the browser.')
    with Workspace(args.port, args.data_dir or default_data_dir()) as server:
        if args.game:
            server.open_project({'game': args.game, 'edition': args.edition,
                                 'project': args.world.stem, 'preferLocalization': args.prefer_localization},
                                world_path=args.world, forests_path=args.forests, remember=False)
        else:
            server.restore()
        url = 'http://127.0.0.1:%d/' % server.server_port
        print('AttT Modding Studio at %s' % url, flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
