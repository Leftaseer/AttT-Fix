"""GRES archive access for Ascension to the Throne Resource/Localization PAKs.

Format (little endian): b'GRES', u32 version 100, u32 entry count, then 136-byte
entries (128-byte cp1251 name, u32 offset, u32 size), then the payloads.
Overlays work by archive slot: Resource2.pak replaces entries from Resource0/1.
"""
import struct
from pathlib import Path

MAGIC = b'GRES'
VERSION = 100
ENTRY_SIZE = 136
NAME_SIZE = 128


class Entry:
    __slots__ = ('name', 'offset', 'size', 'archive')

    def __init__(self, name, offset, size, archive):
        self.name = name
        self.offset = offset
        self.size = size
        self.archive = archive

    def read(self):
        return self.archive.read(self)

    def __repr__(self):
        return 'Entry(%r, offset=%d, size=%d)' % (self.name, self.offset, self.size)


class Archive:
    def __init__(self, path):
        self.path = Path(path)
        self._stream = self.path.open('rb')
        try:
            header = self._stream.read(12)
            if len(header) != 12 or header[:4] != MAGIC:
                raise ValueError('%s is not a GRES archive' % self.path)
            version, count = struct.unpack('<II', header[4:])
            if version != VERSION:
                raise ValueError('%s has GRES version %d, expected %d' %
                                 (self.path, version, VERSION))
            table = self._stream.read(ENTRY_SIZE * count)
            if len(table) != ENTRY_SIZE * count:
                raise ValueError('%s has a truncated file table' % self.path)
            self.entries = {}
            end = 12 + ENTRY_SIZE * count
            for index in range(count):
                raw = table[ENTRY_SIZE * index:ENTRY_SIZE * (index + 1)]
                name = raw[:NAME_SIZE].split(b'\0', 1)[0].decode('cp1251')
                offset, size = struct.unpack('<II', raw[NAME_SIZE:])
                if not name or offset < end or offset + size > self.path.stat().st_size:
                    raise ValueError('%s entry %d has an invalid range' % (self.path, index))
                key = name.lower()
                if key in self.entries:
                    raise ValueError('%s contains duplicate entry %s' % (self.path, name))
                self.entries[key] = Entry(name, offset, size, self)
        except Exception:
            self._stream.close()
            raise

    @property
    def slot(self):
        return archive_slot(self.path.name)

    def read(self, entry):
        if isinstance(entry, str):
            entry = self.entries[entry.lower()]
        self._stream.seek(entry.offset)
        data = self._stream.read(entry.size)
        if len(data) != entry.size:
            raise ValueError('short read for %s in %s' % (entry.name, self.path))
        return data

    def __contains__(self, name):
        return name.lower() in self.entries

    def __iter__(self):
        return iter(self.entries.values())

    def close(self):
        self._stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def archive_slot(name):
    lowered = name.lower()
    if lowered.startswith('resource') and lowered.endswith('.pak'):
        digits = lowered[8:-4]
        if digits.isdigit():
            return int(digits)
    if lowered == 'localization.pak':
        return 1
    return None


class ArchiveSet:
    """Overlay of Resource0..N with higher slots winning, ordered by slot."""

    def __init__(self, paths, allow_gaps=False):
        archives = {}
        for path in paths:
            archive = Archive(path)
            slot = archive.slot
            if slot is None:
                archive.close()
                raise ValueError('%s is not a ResourceN.pak' % path)
            if slot in archives:
                raise ValueError('two archives for slot %d' % slot)
            archives[slot] = archive
        slots = sorted(archives)
        if not slots:
            raise ValueError('no Resource archives selected')
        if not allow_gaps and slots != list(range(slots[0], slots[-1] + 1)):
            raise ValueError('resource slots have gaps: %s' % slots)
        self.archives = archives
        self.slots = slots

    @classmethod
    def open_folder(cls, folder, allow_gaps=False):
        folder = Path(folder)
        paths = sorted(folder.glob('Resource*.pak'), key=lambda p: (archive_slot(p.name) or 0))
        localization = folder / 'Localization.pak'
        if localization.exists() and (archive_slot(localization.name) not in
                                      {archive_slot(p.name) for p in paths}):
            paths.append(localization)
        return cls(paths, allow_gaps=allow_gaps)

    def resolve(self, name):
        """Return the winning Entry for name, or None."""
        key = name.lower()
        for slot in reversed(self.slots):
            entry = self.archives[slot].entries.get(key)
            if entry is not None:
                return entry
        return None

    def has(self, name):
        return self.resolve(name) is not None

    def read(self, name):
        entry = self.resolve(name)
        if entry is None:
            raise KeyError(name)
        return entry.read()

    def names(self):
        seen = set()
        for slot in self.slots:
            for key in self.archives[slot].entries:
                if key not in seen:
                    seen.add(key)
                    yield key

    def close(self):
        for archive in self.archives.values():
            archive.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def write_pak(path, entries, overwrite=False):
    """Write name -> bytes entries as a deterministic GRES archive.

    Refuses to replace an existing file unless `overwrite` is set, and never
    writes through a symlink; an accidental slot collision must not clobber a
    game archive.
    """
    path = Path(path)
    if path.is_symlink():
        raise ValueError('refusing to write through symlink %s' % path)
    if path.exists() and not overwrite:
        raise FileExistsError('%s already exists; pass overwrite=True to replace it' % path)
    ordered = sorted(entries.items())
    for name, data in ordered:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError('entry %s is not bytes' % name)
        if not name or len(name.encode('cp1251')) > NAME_SIZE - 1:
            raise ValueError('invalid archive entry name %r' % name)
    table = bytearray(12 + ENTRY_SIZE * len(ordered))
    table[:4] = MAGIC
    struct.pack_into('<II', table, 4, VERSION, len(ordered))
    offset = len(table)
    for index, (name, data) in enumerate(ordered):
        at = 12 + ENTRY_SIZE * index
        encoded = name.encode('cp1251')
        table[at:at + len(encoded)] = encoded
        struct.pack_into('<II', table, at + NAME_SIZE, offset, len(data))
        offset += len(data)
    path.write_bytes(bytes(table) + b''.join(data for _, data in ordered))
