"""Serve both editors with a single, read-only game archive selection."""

import hashlib
from http.server import HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

import gres
from world import World, WorldError
from worldserve import Handler, State

BALANCE = Path(__file__).resolve().parent / 'balance-studio'
STATIC_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.py': 'text/plain; charset=utf-8',
}
MAX_SLICE = 32 * 1024 * 1024


def validate_base(world, archives):
    for continent in world.continents.values():
        for source in continent['sources'].values():
            name = source['file']
            entry = archives.resolve(name)
            if entry is None or hashlib.sha256(entry.read()).hexdigest() != source['sha256']:
                raise WorldError('%s differs from the world project base. Open the original archive set '
                                 'or create a new world project.' % name)


class WorkspaceHandler(Handler):
    def local_request(self):
        origin = 'http://127.0.0.1:%d' % self.server.server_port
        if (self.headers.get('Host') != origin[7:] or
                self.headers.get('Origin', origin) != origin):
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
        if route.path.startswith('/world/'):
            return self.world_request(super().do_GET)
        if route.path == '/api/session':
            return self.send_json({
                'edition': self.server.edition,
                'worldRevision': self.state.revision,
                'archives': [
                    {'slot': slot, 'name': archive.path.name, 'size': archive.path.stat().st_size}
                    for slot, archive in self.state.archives.archives.items()
                ],
            })
        if route.path == '/api/world-overlay':
            return self.world_overlay()
        if route.path.startswith('/api/archive/'):
            return self.archive_slice(route)
        name = unquote(route.path[1:]) if route.path != '/' else 'Balance Studio.html'
        if name == Path(name).name:
            path = BALANCE / name
            if path.suffix in STATIC_TYPES and path.is_file():
                return self.send_bytes(path.read_bytes(), STATIC_TYPES[path.suffix])
        return self.error('not found', 404)

    def do_POST(self):
        if not self.local_request():
            return
        if (urlsplit(self.path).path != '/world/patch' or
                self.headers.get_content_type() != 'application/json'):
            return self.error('Expected a JSON world patch.', 404)
        return self.world_request(super().do_POST)

    def archive_slice(self, route):
        query = parse_qs(route.query)
        try:
            slot = int(route.path.rsplit('/', 1)[-1])
            archive = self.state.archives.archives[slot]
            start = int(query['start'][0])
            end = int(query['end'][0])
            if not 0 <= start <= end <= archive.path.stat().st_size or end - start > MAX_SLICE:
                raise ValueError()
        except (KeyError, ValueError):
            return self.error('Invalid archive slice.', 416)
        with archive.path.open('rb') as stream:
            stream.seek(start)
            data = stream.read(end - start)
        return self.send_bytes(data, 'application/octet-stream')

    def world_overlay(self):
        world, archives = self.state.world, self.state.archives
        headers = [('X-World-Revision', str(self.state.revision))]
        changed = world.changed_modules()
        if not changed:
            return self.send_bytes(b'', 'application/octet-stream', 204, headers)
        try:
            validate_base(world, archives)
            for continent in sorted({number for number, _ in changed}):
                issues = world.validate(continent, archives, self.state.units)
                errors = [issue for issue in issues if issue['level'] == 'error']
                if errors:
                    return self.error('World validation failed on continent %d (%d errors). Open Validate for details.'
                                      % (continent, len(errors)))
            with TemporaryDirectory(prefix='attt-world-export-') as folder:
                path, _ = world.export_pak(folder, slot=max(archives.slots) + 1, archive_set=archives)
                data = Path(path).read_bytes()
        except (ValueError, OSError) as error:
            return self.error(str(error))
        return self.send_bytes(data, 'application/octet-stream', headers=headers)


def serve_workspace(args):
    if args.world.suffix.lower() != '.json':
        raise ValueError('Choose a .json path for the world project.')
    if not args.game.is_dir():
        raise ValueError('Game folder does not exist: %s' % args.game)
    with gres.ArchiveSet.open_folder(args.game, allow_gaps=True, prefer_localization=args.prefer_localization,
                                     fill_attfix_gap=args.edition == 'attt') as archives:
        for expected, actual in enumerate(archives.slots):
            if actual != expected:
                raise ValueError('Resource%d.pak is missing before Resource%d.pak.' % (expected, actual))
        if len(archives.slots) > 255:
            raise ValueError('The workspace needs an available Resource export slot.')
        if not args.world.exists():
            world = World._from_set(archives, (1, 2, 3))
            if not world.continents:
                raise ValueError('The selected archives contain no world data.')
            world.save_json(args.world)
        state = State(args.world, forests_path=args.forests, archives=archives)
        if not state.world.continents:
            raise ValueError('The world project contains no continents.')
        validate_base(state.world, archives)
        with HTTPServer(('127.0.0.1', args.port), WorkspaceHandler) as server:
            server.state = state
            server.edition = args.edition
            url = 'http://127.0.0.1:%d/' % server.server_port
            print('AttT Modding Studio at %s' % url, flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    return 0
