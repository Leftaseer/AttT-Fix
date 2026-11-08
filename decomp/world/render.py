"""Top-down world map rendering for humans; the JSON model remains the AI interface."""
import base64
import html
import math

import heightmap as heightmap_module

COLORS = {
    'npc': '#e0574a',
    'object': '#b9b9b9',
    'tree': '#4f9d55',
    'forest': '#2f7d3a',
    'army': '#4a7fd0',
    'town': '#f0c040',
}


def world_to_pixel(x, z, map_, width, height):
    px = (x - map_.min_x) / (map_.max_x - map_.min_x) * width
    py = (z - map_.min_z) / (map_.max_z - map_.min_z) * height
    return px, py


def render_svg(world, continent, map_, size=1200, water=0.0, show=('town', 'npc', 'army'),
               forests=None, forest_limit=20000):
    width = max(2, int(map_.width / max(map_.width, map_.height) * size))
    height = max(2, int(map_.height / max(map_.width, map_.height) * size))
    rgb_width, rgb_height, rgb = map_.render(max_size=size, water=water)
    image = base64.b64encode(heightmap_module.png_bytes(rgb_width, rgb_height, rgb)).decode('ascii')

    def point(x, z):
        return world_to_pixel(x, z, map_, width, height)

    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height),
        '<image x="0" y="0" width="%d" height="%d" xlink:href="data:image/png;base64,%s"/>' %
        (width, height, image),
    ]
    for x in range(int(map_.min_x // 1000 * 1000), int(map_.max_x) + 1, 1000):
        px, _ = point(x, map_.min_z)
        parts.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%d" stroke="#00000033" stroke-width="0.5"/>' %
                     (px, px, height))
        parts.append('<text x="%.1f" y="12" font-size="10" fill="#ffffffaa">%d</text>' % (px + 2, x))
    for z in range(int(map_.min_z // 1000 * 1000), int(map_.max_z) + 1, 1000):
        _, py = point(map_.min_x, z)
        parts.append('<line x1="0" y1="%.1f" x2="%d" y2="%.1f" stroke="#00000033" stroke-width="0.5"/>' %
                     (py, width, py))
        parts.append('<text x="2" y="%.1f" font-size="10" fill="#ffffffaa">%d</text>' % (py - 2, z))

    if 'town' in show:
        for name, town in sorted(world.towns(continent).items()):
            position = town.get('Pos') or {}
            x = position.get(1, 0.0)
            z = position.get(3, 0.0)
            if not (map_.min_x <= x <= map_.max_x and map_.min_z <= z <= map_.max_z):
                continue
            px, py = point(x, z)
            parts.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="#000" stroke-width="0.8"/>' %
                         (px, py, COLORS['town']))
            parts.append('<text x="%.1f" y="%.1f" font-size="11" font-weight="bold" fill="#fff" '
                         'stroke="#000" stroke-width="2.5" paint-order="stroke">%s</text>' %
                         (px + 6, py - 4, html.escape(str(name))))
    if 'npc' in show:
        for placement in world.placements(continent, kinds=('npc',)):
            x, z = placement.world_xz
            if not (map_.min_x <= x <= map_.max_x and map_.min_z <= z <= map_.max_z):
                continue
            px, py = point(x, z)
            parts.append('<circle cx="%.1f" cy="%.1f" r="1.8" fill="%s"/>' % (px, py, COLORS['npc']))
    if 'forest' in show and forests is not None:
        points = []
        for _, _, _, record in forests.records(continent):
            x, z = record['x'], record['z']
            if map_.min_x <= x <= map_.max_x and map_.min_z <= z <= map_.max_z:
                points.append(point(x, z))
        if len(points) > forest_limit:
            points = points[::int(math.ceil(len(points) / float(forest_limit)))]
        if points:
            path = ' '.join('M%.1f %.1f h0' % position for position in points)
            parts.append('<path d="%s" stroke="%s" stroke-width="1.6" stroke-linecap="round" '
                         'fill="none" opacity="0.85"/>' % (path, COLORS['forest']))
    if 'army' in show:
        for name, army in sorted(world.continents[continent]['modules'].get('armypos', {}).items()):
            if not isinstance(army, dict):
                continue
            x, z = army.get('x'), army.get('z')
            if not isinstance(x, (int, float)) or not isinstance(z, (int, float)):
                continue
            if not (map_.min_x <= x <= map_.max_x and map_.min_z <= z <= map_.max_z):
                continue
            px, py = point(x, z)
            parts.append('<rect x="%.1f" y="%.1f" width="4" height="4" fill="%s"/>' %
                         (px - 2, py - 2, COLORS['army']))
    footer = ('continent %d: %d towns, %d placements' %
              (continent, len(world.towns(continent)),
               sum(1 for _ in world.placements(continent))))
    if forests is not None and 'forest' in show:
        footer += ', %d trees' % sum(len(entry['records']) for entry
                                     in forests.zones.get(continent, {}).values())
    parts.append('<text x="8" y="%d" font-size="11" fill="#fff" stroke="#000" stroke-width="2.5" '
                 'paint-order="stroke">%s</text>' % (height - 8, footer))
    parts.append('</svg>')
    return '\n'.join(parts)


def render_png(world, continent, map_, size=1200, water=0.0):
    del world, continent
    width, height, rgb = map_.render(max_size=size, water=water)
    return heightmap_module.png_bytes(width, height, rgb)
