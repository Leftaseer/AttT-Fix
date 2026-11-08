"""Heightmap (.nmph) access and a dependency-free PNG hillshade renderer.

Layout observed in all three continents: four int32 (width, height, minX, minZ),
width*height uint16 samples stored column-major (x * height + y), then two floats
`scale` and `offset`.  Sample spacing is 5 world units.

Elevation mapping confirmed against CMapHeight::Sample (00473110) and the
continent terrain mesh: `elevation = sample / scale + offset`.  For continent 1
that is `sample / 81.10927 - 302.0936`, giving a terrain range of about
-302..+506 world units; the ocean plane sits exactly at y = 0.
"""
import math
import struct
import zlib

STEP = 5.0


class Heightmap:
    def __init__(self, data):
        if len(data) < 24:
            raise ValueError('heightmap is truncated')
        self.width, self.height, self.min_x, self.min_z = struct.unpack('<4i', data[:16])
        count = self.width * self.height
        if count <= 0 or len(data) not in (16 + count * 2, 16 + count * 2 + 8):
            raise ValueError('heightmap size %d does not match %dx%d samples' %
                             (len(data), self.width, self.height))
        self.samples = struct.unpack('<%dH' % count, data[16:16 + count * 2])
        if len(data) == 16 + count * 2 + 8:
            self.scale, self.offset = struct.unpack('<2f', data[16 + count * 2:])
        else:
            self.scale, self.offset = 1.0, 0.0
        if not (math.isfinite(self.scale) and math.isfinite(self.offset) and self.scale):
            self.scale, self.offset = 1.0, 0.0
        self.step = STEP

    def at(self, x, y):
        """Sample at column x, row y (column-major storage)."""
        return self.samples[x * self.height + y]

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as stream:
            return cls(stream.read())

    @property
    def max_x(self):
        return self.min_x + (self.width - 1) * self.step

    @property
    def max_z(self):
        return self.min_z + (self.height - 1) * self.step

    def elevation(self, sample):
        return sample / self.scale + self.offset

    @property
    def min_elevation(self):
        return self.elevation(0)

    @property
    def max_elevation(self):
        return self.elevation(65535)

    def sample(self, x, z):
        fx = (x - self.min_x) / self.step
        fz = (z - self.min_z) / self.step
        if not (0 <= fx <= self.width - 1 and 0 <= fz <= self.height - 1):
            return None
        x0, z0 = int(fx), int(fz)
        x1, z1 = min(x0 + 1, self.width - 1), min(z0 + 1, self.height - 1)
        tx, tz = fx - x0, fz - z0
        top = self.at(x0, z0) * (1 - tx) + self.at(x1, z0) * tx
        bottom = self.at(x0, z1) * (1 - tx) + self.at(x1, z1) * tx
        return self.elevation(top * (1 - tz) + bottom * tz)

    def render(self, max_size=1200, hillshade=1.0, water=None):
        """Return (width, height, RGB bytes) for a downsampled hillshade."""
        scale = max(self.width, self.height) / float(max_size)
        width = max(2, int(self.width / scale))
        height = max(2, int(self.height / scale))
        grid = []
        for row in range(height):
            y0 = int(row * self.height / height)
            y1 = max(y0 + 1, int((row + 1) * self.height / height))
            values = []
            for column in range(width):
                x0 = int(column * self.width / width)
                x1 = max(x0 + 1, int((column + 1) * self.width / width))
                total = 0
                count = 0
                for sy in range(y0, min(y1, self.height)):
                    base = sy
                    for sx in range(x0, min(x1, self.width)):
                        total += self.samples[sx * self.height + base]
                        count += 1
                values.append(self.elevation(total / count))
            grid.append(values)
        span = self.max_elevation - self.min_elevation or 1.0
        dx = (self.width - 1) * self.step / max(1, width - 1)
        dz = (self.height - 1) * self.step / max(1, height - 1)
        light = (-0.55, -0.7, 0.45)
        raw = bytearray()
        for row in range(height):
            raw.append(0)
            for column in range(width):
                elevation = grid[row][column]
                east = grid[row][min(column + 1, width - 1)]
                south = grid[min(row + 1, height - 1)][column]
                normal = (-(east - elevation) / dx, -(south - elevation) / dz, 1.0)
                length = math.sqrt(sum(component * component for component in normal)) or 1.0
                shade = (normal[0] * light[0] + normal[1] * light[1] + normal[2] * light[2]) / length
                shade = 0.65 + 0.55 * shade * hillshade
                if water is not None and elevation < water:
                    depth = min(1.0, (water - elevation) / 80.0)
                    color = (int(40 + 70 * (1 - depth)), int(90 + 90 * (1 - depth)), int(150 + 70 * (1 - depth)))
                else:
                    base = max(0.0, min(1.0, (elevation - self.min_elevation) / span)) ** 0.8
                    color = (int(70 + 110 * base), int(95 + 95 * base), int(60 + 70 * base))
                raw.extend(max(0, min(255, int(channel * shade))) for channel in color)
        return width, height, bytes(raw)


def png_bytes(width, height, rgb):
    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload +
                struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff))

    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) +
            chunk(b'IDAT', zlib.compress(rgb, 6)) + chunk(b'IEND', b''))
