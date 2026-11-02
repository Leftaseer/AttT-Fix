"""Offline controls for Wine test isolation, screenshot conversion and service cleanup."""
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zlib

spec = importlib.util.spec_from_file_location('wine_game_test', Path(__file__).resolve().parents[1] / 'wine_game_test.py')
wine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wine)


class WineToolsTests(unittest.TestCase):
    def test_staging_copies_mutable_files_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root / 'assets'
            assets.mkdir()
            (assets / 'MSS').mkdir()
            (assets / 'MSS/plugin.asi').write_bytes(b'plugin')
            originals = {'Resource0.pak': b'archive', 'mss32.dll': b'audio', 'binkw32.dll': b'video',
                         'graphic.cfg': struct.pack('<4I', 1920, 1080, 32, 60) + b'\1config-tail'}
            for name, data in originals.items():
                (assets / name).write_bytes(data)
            exe = root / 'input.exe'
            exe.write_bytes(b'executable')
            saves = root / 'saves'
            saves.mkdir()
            (saves / 'game00').write_bytes(b'save')
            game = root / 'game'
            identities = wine.stage_game(assets, exe, game, 800, 600, saves)
            self.assertEqual(identities['Resource0.pak']['sha256'], wine.sha256(assets / 'Resource0.pak'))
            self.assertEqual((game / 'graphic.cfg').read_bytes(), struct.pack('<2I', 800, 600) + originals['graphic.cfg'][8:16] + b'\0config-tail')
            self.assertFalse((game / 'Resource0.pak').is_symlink())
            for name in originals:
                (game / name).write_bytes(b'changed by test program')
                self.assertEqual((assets / name).read_bytes(), originals[name])
            (game / 'MSS/plugin.asi').write_bytes(b'changed')
            (game / 'Saves/game00').write_bytes(b'changed')
            self.assertEqual((assets / 'MSS/plugin.asi').read_bytes(), b'plugin')
            self.assertEqual((saves / 'game00').read_bytes(), b'save')
            self.assertEqual(exe.read_bytes(), b'executable')

    def test_staging_refuses_existing_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaises(FileExistsError):
                wine.stage_game(directory, directory / 'unused.exe', directory, 800, 600)

    def test_environment_has_private_prefix_and_no_preload(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(wine.os.environ, {'LD_PRELOAD': '/unrelated.so'}):
            runtime = Path(temporary)
            env = wine.environment(runtime)
            self.assertEqual(env['WINEPREFIX'], str(runtime / 'prefix'))
            self.assertEqual(env['HOME'], wine.os.environ['HOME'])
            self.assertNotIn('LD_PRELOAD', env)
            self.assertEqual((runtime / 'runtime').stat().st_mode & 0o777, 0o700)

    def test_screenshot_pixels_and_row_padding_in_both_byte_orders(self):
        for order in (0, 1):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                header = [0] * 25
                header[:6] = [101, 7, 2, 24, 2, 1]
                header[7], header[11], header[12] = order, 32, 12
                header[14:17] = [0xff0000, 0xff00, 0xff]
                pixels = b''.join(p.to_bytes(4, 'little' if order == 0 else 'big') for p in (0xff123456, 0xffabcdef)) + b'pad!'
                source, target = root / 'screen.xwd', root / 'screen.png'
                source.write_bytes(struct.pack('>25I', *header) + b'\0' + pixels)
                wine.xwd_to_png(source, target)
                data = target.read_bytes()
                self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
                length = struct.unpack('>I', data[33:37])[0]
                self.assertEqual(data[37:41], b'IDAT')
                self.assertEqual(zlib.decompress(data[41:41+length]), b'\0\x12\x34\x56\xab\xcd\xef')

    def test_truncated_screenshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'bad.xwd'
            source.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'truncated'):
                wine.xwd_to_png(source, root / 'bad.png')

    def test_services_are_stopped_even_when_wineserver_times_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            services = wine.Services(runtime, runtime, 800, 600)
            process, stream = Mock(), io.StringIO()
            process.poll.return_value = None
            services.processes.append(process)
            services.streams.append(stream)
            with patch.object(wine.subprocess, 'run', side_effect=subprocess.TimeoutExpired('wineserver', 20)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    services.stop()
            process.terminate.assert_called_once()
            process.wait.assert_called_once()
            self.assertTrue(stream.closed)


if __name__ == '__main__':
    unittest.main()
