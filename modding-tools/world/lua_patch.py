"""Patch literals in Lua 5.1 logic chunks without touching nested functions.

Quest, trigger and conversation modules mix data tables with thousands of
function prototypes, so they cannot be re-emitted as source.  Instead of
rewriting the original construction code, edits are emitted as straight-line
assignments just before the main chunk's final ``RETURN``::

    GETGLOBAL rT, K("Quest")
    LOADK     rK, K("q1")
    GETTABLE  rT, rT, rK
    LOADK     rK, K("DisplayName")
    LOADK     rV, K("New title")
    SETTABLE  rT, rK, rV

New constants are appended, which is why the 256-slot RK addressing limit that
blocks bulk edits of shared literals does not apply.  No jump offset, function
prototype, local or upvalue changes; the final ``RETURN`` only moves down.

A field that does not exist yet may be given a JSON object or array.  Those
values are built with ``NEWTABLE`` plus ``SETTABLE``, which makes it possible to
add a whole quest, trigger or dialogue node.  Function values come from either
``{"$ref": [...]}``, which copies an existing function, or ``{"$expr": ...}``,
which ``lua_expr`` compiles into a new leaf prototype appended after the stock
ones.  A ``CLOSURE`` loads the new prototype and ``SETTABLE`` stores it.
"""
import math
import struct

import lua_data
import lua_expr
from luadis import R

HEADER = lua_data.HEADER
OPS = lua_data.OPS
OPCODE = {name: index for index, name in enumerate(OPS)}
MAX_CONSTANT = 1 << 18
MISSING = object()


class LuaPatchError(ValueError):
    pass


class Ref:
    """A function copied from another table path when the patch runs."""

    __slots__ = ('path', 'value')

    def __init__(self, path):
        self.path = tuple(path)
        self.value = MISSING

    def __repr__(self):
        return '<ref %s>' % '.'.join(str(part) for part in self.path)


def _read_constant(reader, data):
    start = reader.p
    tag = reader.u8()
    if tag == 0:
        value = None
    elif tag == 1:
        value = bool(reader.u8())
    elif tag == 3:
        value = struct.unpack('<f', reader.take(4))[0]
    elif tag == 4:
        value = reader.string()
    else:
        raise LuaPatchError('unsupported constant tag %d' % tag)
    return {'value': value, 'raw': bytes(data[start:reader.p])}


def encode_constant(value):
    if value is None:
        return b'\0'
    if isinstance(value, bool):
        return b'\1' + bytes((1 if value else 0,))
    if isinstance(value, float):
        return b'\3' + struct.pack('<f', value)
    if isinstance(value, str):
        raw = value.encode('cp1251')
        return b'\4' + struct.pack('<I', len(raw) + 1) + raw + b'\0'
    raise LuaPatchError('cannot encode constant %r' % (value,))


def _same(left, right):
    if isinstance(left, lua_expr.Expr) or isinstance(right, lua_expr.Expr):
        if isinstance(left, lua_expr.Expr):
            expression, other = left, right
        else:
            expression, other = right, left
        return (isinstance(other, lua_data.Closure) and
                expression.proto == other.proto)
    if isinstance(left, Ref) or isinstance(right, Ref):
        if isinstance(left, Ref):
            reference, other = left, right
        else:
            reference, other = right, left
        expected = reference.value
        if isinstance(expected, lua_data.Closure) and isinstance(other, lua_data.Closure):
            return expected.proto == other.proto
        return _same(expected, other)
    if isinstance(left, dict) or isinstance(right, dict):
        if not (isinstance(left, dict) and isinstance(right, dict)):
            return False
        if len(left) != len(right):
            return False
        for key, value in left.items():
            if key not in right or not _same(value, right[key]):
                return False
        return True
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return struct.pack('<f', float(left)) == struct.pack('<f', float(right))
    return type(left) is type(right) and left == right


def _float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _skip_function(reader):
    start = reader.p
    reader.string()
    reader.take(8)
    reader.take(4)
    reader.take(4 * reader.u32())
    for _ in range(reader.u32()):
        tag = reader.u8()
        if tag == 1:
            reader.take(1)
        elif tag == 3:
            reader.take(4)
        elif tag == 4:
            reader.take(reader.u32())
        elif tag != 0:
            raise LuaPatchError('unsupported constant tag %d in prototype' % tag)
    for _ in range(reader.u32()):
        _skip_function(reader)
    reader.take(4 * reader.u32())
    for _ in range(reader.u32()):
        reader.string()
        reader.take(8)
    for _ in range(reader.u32()):
        reader.string()
    return start, reader.p


class _Layout:
    """Section offsets of one main Lua function, for surgical rebuilds."""

    def __init__(self, data):
        if len(data) < 12 or data[:12] != HEADER:
            raise LuaPatchError('not a float32/size_t32 Lua 5.1 chunk')
        reader = R(data)
        reader.p = 12
        try:
            self.source = reader.string()
            self.line = reader.i32()
            self.lastline = reader.i32()
            flags = reader.take(4)
            self.nups, self.nparams, self.vararg, self.stack = flags
            self.prefix_end = reader.p
            self.code = [reader.u32() for _ in range(reader.u32())]
            self.k_count_pos = reader.p
            self.constants = [_read_constant(reader, data)
                              for _ in range(reader.u32())]
            self.k_end = reader.p
            self.protos_count_pos = reader.p
            self.prototype_count = reader.u32()
            self.protos = []
            for _ in range(self.prototype_count):
                start, end = _skip_function(reader)
                self.protos.append(bytes(data[start:end]))
            self.lineinfo = [reader.i32() for _ in range(reader.u32())]
            self.locals = []
            for _ in range(reader.u32()):
                name_start = reader.p
                reader.string()
                name_raw = bytes(data[name_start:reader.p])
                startpc = reader.i32()
                endpc = reader.i32()
                self.locals.append({'name_raw': name_raw, 'startpc': startpc,
                                    'endpc': endpc})
            self.upnames = bytes(data[reader.p:])
        except ValueError as error:
            raise LuaPatchError('truncated Lua chunk: %s' % error)
        self.data = data

    def rebuild(self, constants, code, lineinfo, locals_, extra_protos=()):
        out = bytearray(self.data[:self.prefix_end])
        out += struct.pack('<I', len(code))
        out += struct.pack('<%dI' % len(code), *code)
        out += struct.pack('<I', len(constants))
        for item in constants:
            out += item['raw']
        out += struct.pack('<I', len(self.protos) + len(extra_protos))
        for item in self.protos:
            out += item
        for item in extra_protos:
            out += item
        out += struct.pack('<I', len(lineinfo))
        if lineinfo:
            out += struct.pack('<%di' % len(lineinfo), *lineinfo)
        out += struct.pack('<I', len(locals_))
        for item in locals_:
            out += item['name_raw']
            out += struct.pack('<ii', item['startpc'], item['endpc'])
        out += self.upnames
        return bytes(out)


def _abc(op, a, b, c):
    return OPCODE[op] | (a << 6) | (c << 14) | (b << 23)


def _abx(op, a, bx):
    if not 0 <= bx < MAX_CONSTANT:
        raise LuaPatchError('constant index %d does not fit a Bx operand' % bx)
    return OPCODE[op] | (a << 6) | (bx << 14)


def actual_key(table, key):
    if key in table:
        return key
    if isinstance(key, str) and key.isdigit() and int(key) in table:
        return int(key)
    if isinstance(key, int) and str(key) in table:
        return str(key)
    raise LuaPatchError('key %r does not exist in table' % (key,))


def resolve(globals_, path):
    current = globals_
    for key in path:
        if not isinstance(current, dict):
            raise LuaPatchError('path %s runs through a non-table' % (path,))
        current = current[actual_key(current, key)]
    return current


def coerce(value, old, path):
    if value is None:
        return None
    if isinstance(old, (lua_data.Closure, bool)):
        if isinstance(value, lua_expr.Expr):
            return value
        if _is_expr(value):
            return _make_expr(value['$expr'], path)
        if _is_ref(value):
            return _make_ref(value['$ref'], path)
    if isinstance(old, bool):
        if not isinstance(value, bool):
            raise LuaPatchError('%s is a boolean; got %r' % (path, value))
        return value
    if isinstance(old, str):
        if not isinstance(value, str):
            raise LuaPatchError('%s is a string; got %r' % (path, value))
        try:
            value.encode('cp1251')
        except UnicodeEncodeError:
            raise LuaPatchError('string %r cannot be encoded as cp1251' % value)
        return value
    if isinstance(old, (int, float)) and not isinstance(old, bool):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise LuaPatchError('%s is a number; got %r' % (path, value))
        return _number(value, path)
    raise LuaPatchError(
        'cannot set %s: the existing value is a %s, only literal strings, '
        'numbers and booleans are editable' % (path, type(old).__name__))


def _number(value, path):
    if not math.isfinite(float(value)):
        raise LuaPatchError('%s cannot be non-finite' % (path,))
    rounded = _float32(float(value))
    if isinstance(value, int) and rounded != value:
        raise LuaPatchError('%d is not exactly representable as float32' % value)
    return rounded


def _is_ref(value):
    return isinstance(value, dict) and set(value) == {'$ref'}


def _is_expr(value):
    return isinstance(value, dict) and set(value) == {'$expr'}


def _make_ref(value, path):
    if not isinstance(value, list) or not value:
        raise LuaPatchError('%s.$ref must be a non-empty array of table keys' % path)
    keys = [_table_key(key, path + '.$ref') for key in value]
    return Ref(keys)


def _make_expr(value, path):
    try:
        return lua_expr.compile_expression(value, path)
    except lua_expr.ExprError as error:
        raise LuaPatchError(str(error))


def validate_new(value, path):
    """Check a literal, nested table or function value for a new field."""
    if isinstance(value, (Ref, lua_expr.Expr)):
        return value
    if _is_ref(value):
        return _make_ref(value['$ref'], path)
    if _is_expr(value):
        return _make_expr(value['$expr'], path)
    if isinstance(value, (dict, list)):
        return normalize_table(value, path)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            value.encode('cp1251')
        except UnicodeEncodeError:
            raise LuaPatchError('string %r cannot be encoded as cp1251' % value)
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value, path)
    raise LuaPatchError('cannot add %s = %r: expected a string, number or boolean'
                        % (path, value))


def _table_key(key, path):
    if isinstance(key, bool):
        raise LuaPatchError('%s has a boolean table key' % path)
    if isinstance(key, int):
        if not -2 ** 24 < key < 2 ** 24:
            raise LuaPatchError('%s has an integer key outside the float32 range' % path)
        return key
    if isinstance(key, str):
        if not key:
            raise LuaPatchError('%s has an empty table key' % path)
        if key.isdigit():
            value = int(key)
            if value >= 2 ** 24:
                raise LuaPatchError('%s has an integer key outside the float32 range' % path)
            return value
        return key
    raise LuaPatchError('%s has an unsupported table key %r' % (path, key))


def normalize_table(value, path):
    """Validate a JSON table, converting digit-only keys to Lua integers."""
    if isinstance(value, list):
        value = {index + 1: item for index, item in enumerate(value)}
    if not isinstance(value, dict):
        raise LuaPatchError('%s must be a JSON object or array' % path)
    result = {}
    for raw_key, item in value.items():
        key = _table_key(raw_key, path)
        item_path = '%s[%s]' % (path, key)
        if item is None:
            raise LuaPatchError('%s cannot be nil inside a new table' % item_path)
        if isinstance(item, (Ref, lua_expr.Expr)):
            result[key] = item
        elif _is_ref(item):
            result[key] = _make_ref(item['$ref'], item_path)
        elif _is_expr(item):
            result[key] = _make_expr(item['$expr'], item_path)
        elif isinstance(item, (dict, list)):
            result[key] = normalize_table(item, item_path)
        else:
            result[key] = validate_new(item, item_path)
    return result


def resolve_refs(globals_, value, path):
    """Resolve ``$ref`` placeholders to the functions they copy."""
    if isinstance(value, lua_expr.Expr):
        return
    if isinstance(value, Ref):
        if value.value is not MISSING:
            return
        try:
            target = resolve(globals_, value.path)
        except LuaPatchError:
            raise LuaPatchError('%s: $ref path %s does not exist' %
                                (path, '.'.join(str(part) for part in value.path)))
        if not isinstance(target, lua_data.Closure):
            raise LuaPatchError('%s: $ref must point at a function, not a %s' %
                                (path, type(target).__name__))
        value.value = target
    elif isinstance(value, dict):
        for key, item in value.items():
            resolve_refs(globals_, item, '%s[%s]' % (path, key))


def lookup(globals_, path):
    """Return (parent, key, old) for a path; old is MISSING for a new field."""
    parent = resolve(globals_, path[:-1])
    key = path[-1]
    try:
        key = actual_key(parent, key)
    except LuaPatchError:
        if not isinstance(key, (str, int)) or isinstance(key, bool):
            raise LuaPatchError('invalid field name %r' % (key,))
        return parent, key, MISSING
    return parent, key, parent[key]


class ChunkEditor:
    def __init__(self, data):
        self.layout = _Layout(data)
        if not self.layout.code:
            raise LuaPatchError('main chunk has no instructions')
        returns = [index for index, instruction in enumerate(self.layout.code)
                   if OPS[instruction & 63] == 'RETURN']
        if returns != [len(self.layout.code) - 1]:
            raise LuaPatchError('main chunk must have exactly one final RETURN')
        if ((self.layout.code[-1] >> 23) & 511) != 1:
            raise LuaPatchError('final RETURN yields values; refusing to clobber them')
        if self.layout.stack < 3:
            raise LuaPatchError('main chunk frame has fewer than 3 registers')
        if self.layout.lineinfo and len(self.layout.lineinfo) != len(self.layout.code):
            raise LuaPatchError('line info does not match the instruction count')
        self.globals = lua_data.decode_chunk(data, allow_closures=True)
        self.constants = [dict(item) for item in self.layout.constants]
        self.added_protos = []
        self.edits = []

    def _constant(self, value):
        if value is None:
            raise LuaPatchError('nil does not need a constant')
        if isinstance(value, bool):
            value = bool(value)
        elif isinstance(value, (int, float)):
            value = _float32(float(value))
        elif not isinstance(value, str):
            raise LuaPatchError('cannot add constant %r' % (value,))
        for index, item in enumerate(self.constants):
            if _same(item['value'], value):
                return index
        if len(self.constants) >= MAX_CONSTANT:
            raise LuaPatchError('constant table is full')
        self.constants.append({'value': value, 'raw': encode_constant(value)})
        return len(self.constants) - 1

    def set(self, path, value):
        path = list(path)
        if len(path) < 2:
            raise LuaPatchError('path %s must name a global and a field' % (path,))
        parent, key, old = lookup(self.globals, path)
        keys = path[:-1] + [key]
        if any(edit['keys'] == keys for edit in self.edits):
            raise LuaPatchError('path %s is edited twice' % (path,))
        label = '.'.join(str(part) for part in path)
        if old is MISSING:
            new = validate_new(value, label)
            resolve_refs(self.globals, new, label)
        else:
            new = coerce(value, old, label)
        self.edits.append({'path': path, 'keys': keys, 'old': old, 'new': new})
        return old, new

    def _instructions(self, edit):
        if isinstance(edit['new'], lua_expr.Expr):
            return self._expr_instructions(edit['keys'], edit['new'])
        if isinstance(edit['new'], Ref):
            return self._ref_instructions(edit['keys'], edit['new'])
        if isinstance(edit['new'], dict):
            return self._table_instructions(edit['keys'], edit['new'])
        return self._literal_instructions(edit['keys'], edit['new'])

    def _add_proto(self, expression):
        index = len(self.layout.protos) + len(self.added_protos)
        self.added_protos.append(expression.raw)
        return index

    def _expr_instructions(self, keys, expression):
        if self.layout.stack < 3:
            raise LuaPatchError('main chunk frame has fewer than 3 registers')
        table = self.layout.stack - 1
        key_register = self.layout.stack - 2
        value = self.layout.stack - 3
        code = [_abx('GETGLOBAL', table, self._constant(keys[0]))]
        for key in keys[1:-1]:
            code.append(_abx('LOADK', key_register, self._constant(key)))
            code.append(_abc('GETTABLE', table, table, key_register))
        code.append(_abx('LOADK', key_register, self._constant(keys[-1])))
        code.append(_abx('CLOSURE', value, self._add_proto(expression)))
        code.append(_abc('SETTABLE', table, key_register, value))
        return code

    def _literal_instructions(self, keys, new):
        table = self.layout.stack - 1
        key_register = self.layout.stack - 2
        value = self.layout.stack - 3
        code = [_abx('GETGLOBAL', table, self._constant(keys[0]))]
        for key in keys[1:-1]:
            code.append(_abx('LOADK', key_register, self._constant(key)))
            code.append(_abc('GETTABLE', table, table, key_register))
        code.append(_abx('LOADK', key_register, self._constant(keys[-1])))
        code.append(self._literal(value, new))
        code.append(_abc('SETTABLE', table, key_register, value))
        return code

    def _literal(self, register, value):
        if value is None:
            return _abc('LOADNIL', register, 0, 0)
        if isinstance(value, bool):
            return _abc('LOADBOOL', register, 1 if value else 0, 0)
        return _abx('LOADK', register, self._constant(value))

    @staticmethod
    def _table_depth(value):
        if not isinstance(value, dict):
            return 0
        return 1 + max((ChunkEditor._table_depth(item) for item in value.values()),
                       default=0)

    def _ref_load(self, code, register, key_register, reference):
        code.append(_abx('GETGLOBAL', register, self._constant(reference.path[0])))
        for part in reference.path[1:]:
            code.append(_abx('LOADK', key_register, self._constant(part)))
            code.append(_abc('GETTABLE', register, register, key_register))

    def _ref_instructions(self, keys, reference):
        if self.layout.stack < 3:
            raise LuaPatchError('main chunk frame has fewer than 3 registers')
        table = self.layout.stack - 1
        key_register = self.layout.stack - 2
        value = self.layout.stack - 3
        code = []
        self._ref_load(code, value, key_register, reference)
        code.append(_abx('GETGLOBAL', table, self._constant(keys[0])))
        for key in keys[1:-1]:
            code.append(_abx('LOADK', key_register, self._constant(key)))
            code.append(_abc('GETTABLE', table, table, key_register))
        code.append(_abx('LOADK', key_register, self._constant(keys[-1])))
        code.append(_abc('SETTABLE', table, key_register, value))
        return code

    def _emit_table(self, code, register, value, key_register, value_register):
        code.append(_abc('NEWTABLE', register, 0, 0))
        for key, item in value.items():
            if isinstance(item, dict):
                child = register - 1
                self._emit_table(code, child, item, key_register, value_register)
                code.append(_abx('LOADK', key_register, self._constant(key)))
                code.append(_abc('SETTABLE', register, key_register, child))
            elif isinstance(item, lua_expr.Expr):
                code.append(_abx('CLOSURE', value_register,
                                 self._add_proto(item)))
                code.append(_abx('LOADK', key_register, self._constant(key)))
                code.append(_abc('SETTABLE', register, key_register, value_register))
            elif isinstance(item, Ref):
                code.append(_abx('LOADK', key_register, self._constant(key)))
                self._ref_load(code, value_register, key_register, item)
                code.append(_abc('SETTABLE', register, key_register, value_register))
            else:
                code.append(_abx('LOADK', key_register, self._constant(key)))
                code.append(self._literal(value_register, item))
                code.append(_abc('SETTABLE', register, key_register, value_register))

    def _table_instructions(self, keys, new):
        depth = self._table_depth(new)
        needed = depth + 2
        if self.layout.stack < needed:
            raise LuaPatchError('building this table needs %d registers, but the '
                                'main chunk frame has %d' % (needed, self.layout.stack))
        top = self.layout.stack - 1
        key_register = top
        value_register = top - (depth + 1)
        root_register = top - 1
        code = []
        self._emit_table(code, root_register, new, key_register, value_register)
        table = value_register
        code.append(_abx('GETGLOBAL', table, self._constant(keys[0])))
        for key in keys[1:-1]:
            code.append(_abx('LOADK', key_register, self._constant(key)))
            code.append(_abc('GETTABLE', table, table, key_register))
        code.append(_abx('LOADK', key_register, self._constant(keys[-1])))
        code.append(_abc('SETTABLE', table, key_register, root_register))
        return code

    def build(self):
        insert = len(self.layout.code) - 1
        added = []
        for edit in self.edits:
            added.extend(self._instructions(edit))
        code = self.layout.code[:insert] + added + self.layout.code[insert:]
        if self.layout.lineinfo:
            line = self.layout.lineinfo[insert]
            lineinfo = (self.layout.lineinfo[:insert] + [line] * len(added) +
                        self.layout.lineinfo[insert:])
        else:
            lineinfo = []
        delta = len(added)
        locals_ = []
        for item in self.layout.locals:
            startpc, endpc = item['startpc'], item['endpc']
            if startpc >= insert:
                startpc += delta
            if endpc >= insert:
                endpc += delta
            locals_.append({'name_raw': item['name_raw'], 'startpc': startpc,
                            'endpc': endpc})
        data = self.layout.rebuild(self.constants, code, lineinfo, locals_,
                                   extra_protos=self.added_protos)
        self._verify(data)
        return data

    def _verify(self, data):
        function = lua_data.parse_chunk(data)
        before = lua_data.parse_chunk(self.layout.data)
        expected = len(before['protos']) + len(self.added_protos)
        if len(function['protos']) != expected:
            raise LuaPatchError('function prototype count changed')
        if not function['code'] or OPS[function['code'][-1] & 63] != 'RETURN':
            raise LuaPatchError('patched chunk does not end with RETURN')
        globals_ = lua_data.decode_chunk(data, allow_closures=True)
        for edit in self.edits:
            if edit['new'] is None:
                parent = resolve(globals_, edit['keys'][:-1])
                if edit['keys'][-1] in parent:
                    raise LuaPatchError('verification failed to remove %s' %
                                        ('.'.join(str(part) for part in edit['path']),))
                continue
            current = resolve(globals_, edit['keys'])
            if not _same(current, edit['new']):
                raise LuaPatchError('verification failed for %s' %
                                    ('.'.join(str(part) for part in edit['path']),))


def patch(data, edits):
    """Apply `(path, value)` pairs to one bytecode chunk; return new bytes."""
    editor = ChunkEditor(data)
    for path, value in edits:
        editor.set(path, value)
    return editor.build()
