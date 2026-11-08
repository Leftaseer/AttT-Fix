"""Read and write the game's data-only Lua 5.1 chunks.

The engine's Lua is built with 4-byte size_t and float lua_Number, so stock luac
cannot read its bytecode.  This module interprets the straight-line constructors
used by the world data modules (towns, NPC/SAO definitions, armies, positions)
and emits equivalent cp1251 Lua source, which the game also loads.

Tables keep numeric keys as ints and string keys as strings.  Numeric values stay
floats, matching the engine's LUA_NUMBER.
"""
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import luadis  # noqa: E402

HEADER = b'\x1bLua\x51\x00\x01\x04\x04\x04\x04\x00'
OPS = luadis.OPS


class LuaDataError(ValueError):
    pass


class Closure:
    """Opaque stand-in for a nested function when decoding logic chunks."""

    def __init__(self, proto, upvalues=None):
        self.proto = proto
        self.upvalues = list(upvalues or [])

    def __repr__(self):
        return '<function line %s>' % self.proto.get('line')


def normalize_key(value):
    if isinstance(value, float) and value.is_integer() and abs(value) < 2 ** 31:
        return int(value)
    return value


def parse_chunk(data):
    if len(data) < 12 or data[:12] != HEADER:
        raise LuaDataError('not a little-endian float32/size_t32 Lua 5.1 chunk')
    reader = luadis.R(data)
    reader.p = 12
    function = luadis.function(reader)
    if reader.p != len(data):
        raise LuaDataError('trailing bytes after the Lua chunk')
    return function


def decode_chunk(data, allow_closures=False):
    """Interpret a data-only chunk and return its globals.

    With allow_closures the straight-line part of a logic chunk is still
    evaluated; nested functions become opaque Closure values.  This is enough
    to recover embedded configuration tables such as WorldLevel.
    """
    function = parse_chunk(data)
    if function['protos'] and not allow_closures:
        raise LuaDataError('chunk defines functions and is not data-only')
    return evaluate(function, allow_closures=allow_closures)


def evaluate(function, allow_closures=False):
    globals_ = {}
    budget = {'left': 2000000 if allow_closures else len(function['code']) * 4 + 16}
    _execute(function, (), (), globals_, allow_closures, 0, budget)
    return globals_


class _PairsIterator:
    """Iterator returned by the built-in pairs() and driven by TFORLOOP."""

    def __init__(self, source):
        self.keys = list(source)

    def __call__(self, state, control):
        if control is None:
            index = 0
        else:
            try:
                index = self.keys.index(control) + 1
            except ValueError:
                raise LuaDataError('invalid key to next')
        if index >= len(self.keys):
            return ()
        key = self.keys[index]
        return (key, state[key])


def _lua_type(value):
    if value is None:
        return 'nil'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, (int, float)):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, dict):
        return 'table'
    if isinstance(value, Closure) or callable(value):
        return 'function'
    return 'userdata'


def _string_format(fmt, *args):
    if not isinstance(fmt, str):
        raise LuaDataError('string.format expects a format string')
    converted = [int(value) if isinstance(value, float) and value.is_integer() else value
                 for value in args]
    try:
        return fmt % tuple(converted)
    except (TypeError, ValueError) as error:
        raise LuaDataError('string.format: %s' % error)


def _pairs(value):
    if not isinstance(value, dict):
        raise LuaDataError('pairs expects a table')
    return (_PairsIterator(value), value, None)


class _TableIdentity:
    """Hash-by-identity stand-in for Lua table keys.

    Lua allows tables as keys; the clone helper in stock scripts uses one as a
    memo.  Such keys never leave the internal tables we evaluate.
    """

    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return id(self.value)

    def __eq__(self, other):
        return isinstance(other, _TableIdentity) and other.value is self.value


def _table_key(value):
    value = normalize_key(value)
    if isinstance(value, dict):
        return _TableIdentity(value)
    return value


BUILTINS = {
    'type': _lua_type,
    'pairs': _pairs,
    'string': {'format': _string_format},
}


def _call(callee, arguments, globals_, allow_closures, depth, budget):
    if isinstance(callee, Closure):
        return _execute(callee.proto, arguments, callee.upvalues, globals_,
                        allow_closures, depth + 1, budget)
    if callable(callee):
        try:
            result = callee(*arguments)
        except LuaDataError:
            raise
        except (TypeError, ValueError, ZeroDivisionError) as error:
            raise LuaDataError('Lua function failed: %s' % error)
        if isinstance(result, tuple):
            return list(result)
        return [] if result is None else [result]
    return []


def _number(value, what='number'):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LuaDataError('%s is not a number: %r' % (what, value))
    return value


def _concat_string(value):
    if isinstance(value, str):
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LuaDataError('cannot concatenate %r' % (value,))
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return repr(float(value))


def _execute(function, arguments, upvalues, globals_, allow_closures, depth, budget):
    if depth > 64:
        raise LuaDataError('Lua call depth exceeded')
    registers = [None] * (function['stack'] + 8)
    for index, value in enumerate(arguments[:function['nparams']]):
        registers[index] = value
    upvalues = list(upvalues)
    constants = function['k']
    code = function['code']

    def rk(index):
        if index >= 256:
            return constants[index - 256]
        if index >= len(registers):
            raise LuaDataError('register %d is out of range' % index)
        return registers[index]

    def table(register):
        value = registers[register]
        if not isinstance(value, dict):
            raise LuaDataError('register %d is not a table' % register)
        return value

    def put(target, key, value):
        key = _table_key(key)
        if isinstance(key, float) or not isinstance(key, (str, int, _TableIdentity)):
            raise LuaDataError('unsupported Lua table key %r' % (key,))
        if value is None:
            target.pop(key, None)
        else:
            target[key] = value

    pc = 0
    while pc < len(code):
        budget['left'] -= 1
        if budget['left'] < 0:
            raise LuaDataError('Lua chunk does not terminate')
        instruction = code[pc]
        pc += 1
        op = instruction & 63
        a = (instruction >> 6) & 255
        c = (instruction >> 14) & 511
        b = (instruction >> 23) & 511
        bx = instruction >> 14
        name = OPS[op] if op < len(OPS) else 'INVALID'
        if name == 'MOVE':
            registers[a] = registers[b]
        elif name == 'LOADK':
            registers[a] = constants[bx]
        elif name == 'LOADBOOL':
            registers[a] = bool(b)
            if c:
                pc += 1
        elif name == 'LOADNIL':
            for register in range(a, min(a + b + 1, len(registers))):
                registers[register] = None
        elif name == 'GETUPVAL':
            registers[a] = upvalues[b] if b < len(upvalues) else None
        elif name == 'SETUPVAL':
            if b < len(upvalues):
                upvalues[b] = registers[a]
        elif name == 'GETGLOBAL':
            key = constants[bx]
            if key in globals_:
                registers[a] = globals_[key]
            elif allow_closures and key in BUILTINS:
                registers[a] = BUILTINS[key]
            else:
                registers[a] = None
        elif name == 'SETGLOBAL':
            globals_[constants[bx]] = registers[a]
        elif name == 'GETTABLE':
            source = table(b)
            registers[a] = source.get(_table_key(rk(c)))
        elif name == 'SETTABLE':
            put(table(a), rk(b), rk(c))
        elif name == 'NEWTABLE':
            registers[a] = {}
        elif name == 'CLOSURE':
            if not allow_closures:
                raise LuaDataError('unsupported instruction CLOSURE at %d' % (pc - 1))
            proto = function['protos'][bx]
            closure = Closure(proto, [])
            registers[a] = closure
            for _ in range(proto['nups']):
                if pc >= len(code):
                    raise LuaDataError('truncated closure upvalues')
                pseudo = code[pc]
                pc += 1
                binding = OPS[pseudo & 63]
                index = (pseudo >> 23) & 511
                if binding == 'MOVE':
                    closure.upvalues.append(registers[index])
                elif binding == 'GETUPVAL':
                    closure.upvalues.append(upvalues[index] if index < len(upvalues) else None)
                else:
                    raise LuaDataError('unsupported closure binding %s at %d' %
                                       (binding, pc - 1))
        elif name == 'CALL':
            if not allow_closures:
                raise LuaDataError('unsupported instruction CALL at %d' % (pc - 1))
            # Import helpers such as using("dialogUtils") return nothing we need;
            # unknown globals are stubbed the same way.
            arguments = [registers[a + offset] for offset in range(1, b)]
            results = _call(registers[a], arguments, globals_, allow_closures,
                            depth, budget)
            for offset in range(c - 1):
                registers[a + offset] = results[offset] if offset < len(results) else None
        elif name == 'JMP':
            pc += bx - 131071
        elif name == 'EQ':
            outcome = rk(b) == rk(c)
            if outcome != bool(a):
                pc += 1
        elif name == 'LT':
            try:
                outcome = rk(b) < rk(c)
            except TypeError:
                raise LuaDataError('cannot compare %r and %r' % (rk(b), rk(c)))
            if outcome != bool(a):
                pc += 1
        elif name == 'LE':
            try:
                outcome = rk(b) <= rk(c)
            except TypeError:
                raise LuaDataError('cannot compare %r and %r' % (rk(b), rk(c)))
            if outcome != bool(a):
                pc += 1
        elif name == 'CONCAT':
            registers[a] = ''.join(_concat_string(rk(index)) for index in range(b, c + 1))
        elif name == 'TEST':
            truthy = not (registers[a] is None or registers[a] is False)
            if (not truthy) == bool(c):
                pc += 1
        elif name == 'FORPREP':
            registers[a] = (_number(registers[a], 'for start') -
                            _number(registers[a + 2], 'for step'))
            pc += bx - 131071
        elif name == 'FORLOOP':
            step = _number(registers[a + 2], 'for step')
            index = _number(registers[a], 'for index') + step
            limit = _number(registers[a + 1], 'for limit')
            registers[a] = index
            if (step > 0 and index <= limit) or (step <= 0 and index >= limit):
                pc += bx - 131071
                registers[a + 3] = index
        elif name == 'TFORLOOP':
            if not allow_closures:
                raise LuaDataError('unsupported instruction TFORLOOP at %d' % (pc - 1))
            values = _call(registers[a], [registers[a + 1], registers[a + 2]],
                           globals_, allow_closures, depth, budget)
            for offset in range(c):
                registers[a + 3 + offset] = values[offset] if offset < len(values) else None
            if pc >= len(code) or OPS[code[pc] & 63] != 'JMP':
                raise LuaDataError('TFORLOOP is not followed by JMP')
            jump = code[pc]
            pc += 1
            if registers[a + 3] is not None:
                registers[a + 2] = registers[a + 3]
                pc += (jump >> 14) - 131071
        elif name == 'SETLIST':
            block = c
            if block == 0:
                block = code[pc]
                pc += 1
            target = table(a)
            for index in range(1, b + 1):
                put(target, (block - 1) * 50 + index, registers[a + index])
        elif name == 'RETURN':
            if not allow_closures and pc != len(code):
                raise LuaDataError('unexpected early return')
            if b == 0:
                return []
            return [registers[a + offset] for offset in range(b - 1)]
        else:
            raise LuaDataError('unsupported instruction %s at %d' % (name, pc - 1))
    raise LuaDataError('Lua chunk ended without return')


def decode_global(data, name):
    globals_ = decode_chunk(data)
    if name not in globals_:
        raise LuaDataError('chunk does not define %s' % name)
    return globals_[name]


def _quote_string(value):
    out = ['"']
    for char in value:
        code = ord(char)
        if char == '"':
            out.append('\\"')
        elif char == '\\':
            out.append('\\\\')
        elif char == '\n':
            out.append('\\n')
        elif char == '\r':
            out.append('\\r')
        elif char == '\t':
            out.append('\\t')
        elif code < 32 or code == 127:
            out.append('\\%03d' % code)
        else:
            try:
                char.encode('cp1251')
            except UnicodeEncodeError:
                raise LuaDataError('string %r cannot be encoded as cp1251' % value)
            out.append(char)
    out.append('"')
    return ''.join(out)


def _format_number(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise LuaDataError('cannot emit non-finite number %r' % value)
    return repr(float(value))


IDENTIFIER = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
RESERVED = frozenset('and break do else elseif end false for function if in local nil not or '
                     'repeat return then true until while'.split())


def _valid_identifier(key):
    return (isinstance(key, str) and key and key.isascii() and key not in RESERVED and
            all(char in IDENTIFIER for char in key) and not key[0].isdigit())


def _format_key(key):
    if isinstance(key, int):
        return '[%d]' % key
    if _valid_identifier(key):
        return key
    return '[%s]' % _quote_string(key)


def _dense_array(table):
    keys = [key for key in table if isinstance(key, int)]
    return (len(keys) == len(table) == (max(keys) if keys else 0) and
            all(isinstance(key, int) and 1 <= key <= len(table) for key in table))


def _emit_value(value, indent):
    pad = '  ' * indent
    if value is None:
        return 'nil'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _format_number(value)
    if isinstance(value, str):
        return _quote_string(value)
    if not isinstance(value, dict):
        raise LuaDataError('cannot emit value %r' % (value,))
    if not value:
        return '{}'
    if _dense_array(value):
        items = [value[key] for key in sorted(value)]
        if len(items) <= 8 and all(not isinstance(item, dict) for item in items):
            return '{' + ', '.join(_emit_value(item, indent + 1) for item in items) + '}'
        body = ',\n'.join('%s  %s' % (pad, _emit_value(item, indent + 1)) for item in items)
        return '{\n%s,\n%s}' % (body, pad)
    keys = sorted(value, key=lambda item: (isinstance(item, str), item))
    body = ',\n'.join('%s  %s = %s' % (pad, _format_key(key), _emit_value(value[key], indent + 1))
                      for key in keys)
    return '{\n%s,\n%s}' % (body, pad)


def emit_table(value, indent=0):
    return _emit_value(value, indent)


def emit_source(globals_, order=None):
    """Render globals as cp1251 Lua source bytes."""
    names = list(order) if order is not None else list(globals_)
    text = []
    for name in names:
        value = globals_[name]
        if not _valid_identifier(name):
            raise LuaDataError('invalid global name %r' % name)
        text.append('%s = %s\n' % (name, emit_table(value)))
    return ''.join(text).encode('cp1251')


# --- data source parser -----------------------------------------------------
# Only assignment chunks of literal tables are accepted, which is what the game
# uses for these modules and for source overlays such as the King's Daughter mod.

class _Tokens:
    def __init__(self, text):
        self.tokens = []
        position = 0
        length = len(text)
        while position < length:
            char = text[position]
            if char in ' \t\r\n\f\v':
                position += 1
            elif text.startswith('--', position):
                end = text.find('\n', position)
                position = length if end < 0 else end + 1
            elif char in '{}[]=.,;-':
                self.tokens.append(char)
                position += 1
            elif char in '"\'':
                quote = char
                position += 1
                value = []
                while True:
                    if position >= length:
                        raise LuaDataError('unterminated string')
                    char = text[position]
                    position += 1
                    if char == quote:
                        break
                    if char != '\\':
                        value.append(char)
                        continue
                    if position >= length:
                        raise LuaDataError('unterminated escape')
                    escape = text[position]
                    position += 1
                    simple = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r',
                              't': '\t', 'v': '\v'}
                    if escape in simple:
                        value.append(simple[escape])
                    elif escape.isdigit():
                        digits = escape
                        while len(digits) < 3 and position < length and text[position].isdigit():
                            digits += text[position]
                            position += 1
                        value.append(chr(int(digits)))
                    else:
                        value.append(escape)
                self.tokens.append(('str', ''.join(value)))
            elif char.isalpha() or char == '_':
                end = position + 1
                while end < length and (text[end].isalnum() or text[end] == '_'):
                    end += 1
                self.tokens.append(('name', text[position:end]))
                position = end
            elif char.isdigit() or (char == '.' and position + 1 < length and text[position + 1].isdigit()):
                end = position
                while end < length and text[end].isdigit():
                    end += 1
                if end < length and text[end] == '.':
                    end += 1
                    while end < length and text[end].isdigit():
                        end += 1
                if end < length and text[end] in 'eE':
                    end += 1
                    if end < length and text[end] in '+-':
                        end += 1
                    while end < length and text[end].isdigit():
                        end += 1
                literal = text[position:end]
                try:
                    value = float(literal)
                except ValueError:
                    raise LuaDataError('unsupported number %r' % literal)
                self.tokens.append(('num', value))
                position = end
            else:
                raise LuaDataError('unsupported character %r' % char)
        self.position = 0

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self, expected=None):
        token = self.peek()
        if token is None:
            raise LuaDataError('unexpected end of source')
        if expected is not None and token != expected:
            raise LuaDataError('expected %r, found %r' % (expected, token))
        self.position += 1
        return token


def parse_source(data, encoding='cp1251'):
    text = data.decode(encoding) if isinstance(data, bytes) else data
    tokens = _Tokens(text)
    globals_ = {}

    def value():
        token = tokens.peek()
        if token == '{':
            return table()
        if token == '-':
            tokens.take()
            return -value()
        if isinstance(token, tuple) and token[0] == 'num':
            tokens.take()
            return token[1]
        if isinstance(token, tuple) and token[0] == 'str':
            tokens.take()
            return token[1]
        if isinstance(token, tuple) and token[0] == 'name':
            tokens.take()
            if token[1] == 'true':
                return True
            if token[1] == 'false':
                return False
            if token[1] == 'nil':
                return None
            raise LuaDataError('unsupported expression %r' % token[1])
        raise LuaDataError('unexpected token %r' % (token,))

    def table():
        tokens.take('{')
        result = {}
        array_index = 1
        while tokens.peek() != '}':
            token = tokens.peek()
            if token == '[':
                tokens.take()
                key = value()
                tokens.take(']')
                tokens.take('=')
                item = value()
                result[normalize_key(key)] = item
            elif isinstance(token, tuple) and token[0] == 'name' and tokens.tokens[tokens.position + 1:tokens.position + 2] == ['=']:
                key = tokens.take()[1]
                tokens.take('=')
                result[key] = value()
            else:
                result[array_index] = value()
                array_index += 1
            if tokens.peek() in (',', ';'):
                tokens.take()
            elif tokens.peek() != '}':
                raise LuaDataError('expected , or } in table at token %d (%r)' %
                                   (tokens.position, tokens.peek()))
        tokens.take('}')
        return result

    def target_path():
        token = tokens.take()
        if not isinstance(token, tuple) or token[0] != 'name':
            raise LuaDataError('expected assignment target')
        path = [token[1]]
        while tokens.peek() in ('.', '['):
            if tokens.take() == '.':
                name = tokens.take()
                if not isinstance(name, tuple) or name[0] != 'name':
                    raise LuaDataError('expected field name')
                path.append(name[1])
            else:
                tokens.take('[')
                path.append(normalize_key(value()))
                tokens.take(']')
        return path

    while tokens.peek() is not None:
        path = target_path()
        tokens.take('=')
        item = value()
        container = globals_
        for key in path[:-1]:
            existing = container.get(key)
            if not isinstance(existing, dict):
                existing = {}
                container[key] = existing
            container = existing
        if item is None:
            container.pop(path[-1], None)
        else:
            container[path[-1]] = item
        if tokens.peek() == ';':
            tokens.take()
    return globals_


def load_module(data, name=None):
    """Decode bytecode or source; return the requested global or all globals."""
    if data[:4] == b'\x1bLua':
        globals_ = decode_chunk(data)
    else:
        globals_ = parse_source(data)
    if name is None:
        return globals_
    if name not in globals_:
        raise LuaDataError('module does not define %s' % name)
    return globals_[name]
