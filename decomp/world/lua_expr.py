"""Compile a small JSON expression language into Lua 5.1 function prototypes.

Story modules store ``Condition``/``Action`` as nested functions.  A JSON
expression is compiled into a leaf prototype (no parameters, upvalues or nested
functions) that the patcher appends to the module and references with
``CLOSURE``.  Supported forms::

    true, false, 42, "text", null          literals
    {"global": "Name"}                     global value
    {"global": ["Conditions", "Flag"]}     global table field
    {"op": "and", "args": [...]}           and/or/not
    {"op": "seq", "args": [...]}           evaluate in order, keep the last
    {"op": "eq", "args": [a, b]}           eq ne lt le gt ge
    {"op": "add", "args": [a, b]}          add sub mul div mod pow
    {"op": "neg"|"len", "args": [a]}       unary
    {"op": "concat", "args": [a, b, ...]}  concatenation
    {"call": "Conditions.Check", "args": [...], "method": true}
    {"if": cond, "then": expr, "else": expr}

``method`` mirrors ``obj:method(...)`` and defaults to false, so a plain
``Conditions.Check(...)`` call passes only the listed arguments.
"""
import math
import struct

import lua_data

OPS = lua_data.OPS
OPCODE = {name: index for index, name in enumerate(OPS)}
MAX_STACK = 200                      # Lua 5.1 allows 250; keep a safety margin
MAX_CONSTANTS = 1 << 18
MAX_DEPTH = 64
BINARY = {'add': 'ADD', 'sub': 'SUB', 'mul': 'MUL', 'div': 'DIV', 'mod': 'MOD',
          'pow': 'POW'}
COMPARE = {'eq': 'EQ', 'ne': 'EQ', 'lt': 'LT', 'le': 'LE', 'gt': 'LT', 'ge': 'LE'}


class ExprError(ValueError):
    pass


class Expr:
    """A compiled expression: its JSON source, prototype dict and raw bytes."""

    __slots__ = ('spec', 'proto', 'raw')

    def __init__(self, spec, proto, raw):
        self.spec = spec
        self.proto = proto
        self.raw = raw

    def __repr__(self):
        return '<expr %s>' % (self.spec,)


def _abc(op, a, b, c):
    return OPCODE[op] | (a << 6) | (c << 14) | (b << 23)


def _abx(op, a, bx):
    if not 0 <= bx < MAX_CONSTANTS:
        raise ExprError('expression constant index %d does not fit' % bx)
    return OPCODE[op] | (a << 6) | (bx << 14)


def _float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _number(value, path):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExprError('%s must be a number; got %r' % (path, value))
    if not math.isfinite(float(value)):
        raise ExprError('%s cannot be non-finite' % path)
    rounded = _float32(float(value))
    if isinstance(value, int) and rounded != value:
        raise ExprError('%s: %d is not exactly representable as float32' %
                        (path, value))
    return rounded


def _string(value, path):
    if not isinstance(value, str):
        raise ExprError('%s must be a string; got %r' % (path, value))
    try:
        value.encode('cp1251')
    except UnicodeEncodeError:
        raise ExprError('%s: string %r cannot be encoded as cp1251' %
                        (path, value))
    return value


def _key(value, path):
    if isinstance(value, bool):
        raise ExprError('%s has a boolean table key' % path)
    if isinstance(value, int):
        if not -2 ** 24 < value < 2 ** 24:
            raise ExprError('%s has an integer key outside the float32 range' % path)
        return value
    if isinstance(value, str):
        return _string(value, path)
    raise ExprError('%s has an unsupported table key %r' % (path, value))


def _encode_constant(value):
    if value is None:
        return b'\0'
    if isinstance(value, bool):
        return b'\1' + bytes((1 if value else 0,))
    if isinstance(value, float):
        return b'\3' + struct.pack('<f', value)
    if isinstance(value, str):
        raw = value.encode('cp1251')
        return b'\4' + struct.pack('<I', len(raw) + 1) + raw + b'\0'
    raise ExprError('cannot encode constant %r' % (value,))


def encode_proto(code, constants, stack, line=0):
    """Serialize one leaf function prototype in the game's Lua 5.1 format."""
    if not 1 <= stack <= 255:
        raise ExprError('expression needs %d registers, Lua allows 255' % stack)
    out = bytearray()
    out += struct.pack('<I', 0)                       # source name (none)
    out += struct.pack('<ii', line, line)
    out += struct.pack('<4B', 0, 0, 0, stack)         # nups, params, vararg, stack
    out += struct.pack('<I', len(code))
    out += struct.pack('<%dI' % len(code), *code)
    out += struct.pack('<I', len(constants))
    for value in constants:
        out += _encode_constant(value)
    out += struct.pack('<I', 0)                       # nested prototypes
    out += struct.pack('<I', 0)                       # line info
    out += struct.pack('<I', 0)                       # local names
    out += struct.pack('<I', 0)                       # upvalue names
    return bytes(out)


class _Builder:
    def __init__(self, root, line=0):
        self.root = root
        self.line = line
        self.code = []
        self.constants = []
        self.next_register = 1
        self.stack = 1
        self.key_register = None

    # --- registers and constants -----------------------------------------
    def _alloc(self):
        register = self.next_register
        self.next_register += 1
        if self.next_register > MAX_STACK:
            raise ExprError('expression needs more than %d registers' % MAX_STACK)
        self.stack = max(self.stack, self.next_register)
        return register

    def _key(self):
        if self.key_register is None:
            self.key_register = self._alloc()
        return self.key_register

    def _constant(self, value, path):
        if isinstance(value, bool):
            value = bool(value)
        elif isinstance(value, (int, float)):
            value = _number(value, path)
        elif isinstance(value, str):
            value = _string(value, path)
        else:
            raise ExprError('cannot use %r as a constant' % (value,))
        for index, existing in enumerate(self.constants):
            if isinstance(existing, float) and isinstance(value, float):
                if struct.pack('<f', existing) == struct.pack('<f', value):
                    return index
            elif type(existing) is type(value) and existing == value:
                return index
        if len(self.constants) >= MAX_CONSTANTS:
            raise ExprError('expression constant table is full')
        self.constants.append(value)
        return len(self.constants) - 1

    # --- jumps ------------------------------------------------------------
    def _emit_jump(self):
        self.code.append(_abx('JMP', 0, 131071))
        return len(self.code) - 1

    def _patch_jump(self, index, target):
        sbx = target - (index + 1)
        bx = sbx + 131071
        if not 0 <= bx < MAX_CONSTANTS:
            raise ExprError('expression jump is out of range')
        self.code[index] = _abx('JMP', 0, bx)

    # --- expressions ------------------------------------------------------
    def compile(self, spec, dest, path=None, depth=0):
        path = path or self.root
        if depth > MAX_DEPTH:
            raise ExprError('%s is nested too deeply' % path)
        if spec is None:
            self.code.append(_abc('LOADNIL', dest, 0, 0))
        elif isinstance(spec, bool):
            self.code.append(_abc('LOADBOOL', dest, 1 if spec else 0, 0))
        elif isinstance(spec, (int, float)):
            index = self._constant(spec, path)
            self.code.append(_abx('LOADK', dest, index))
        elif isinstance(spec, str):
            index = self._constant(spec, path)
            self.code.append(_abx('LOADK', dest, index))
        elif isinstance(spec, dict):
            self._compound(spec, dest, path, depth)
        else:
            raise ExprError('%s cannot be an expression: %r' % (path, spec))

    def _compound(self, spec, dest, path, depth):
        forms = [key for key in ('global', 'op', 'call', 'if') if key in spec]
        if len(forms) != 1:
            raise ExprError('%s must have exactly one of global, op, call or if' % path)
        form = forms[0]
        allowed = {'global': {'global'}, 'op': {'op', 'args'},
                   'call': {'call', 'args', 'method'}, 'if': {'if', 'then', 'else'}}
        extra = set(spec) - allowed[form]
        if extra:
            raise ExprError('%s has unknown keys: %s' % (path, ', '.join(sorted(extra))))
        if form == 'global':
            self._global(spec['global'], dest, path)
        elif form == 'op':
            self._operator(spec, dest, path, depth)
        elif form == 'call':
            self._call(spec, dest, path, depth)
        else:
            self._if(spec, dest, path, depth)

    def _global(self, target, dest, path):
        if isinstance(target, str):
            keys = [target]
        elif isinstance(target, list) and target:
            keys = target
        else:
            raise ExprError('%s.global must be a global name or a non-empty array' % path)
        if not isinstance(keys[0], str) or not keys[0]:
            raise ExprError('%s.global must start with a global name' % path)
        keys = [keys[0]] + [_key(key, path + '.global') for key in keys[1:]]
        self.code.append(_abx('GETGLOBAL', dest, self._constant(keys[0], path)))
        for key in keys[1:]:
            index = self._constant(key, path)
            self.code.append(_abx('LOADK', self._key(), index))
            self.code.append(_abc('GETTABLE', dest, dest, self._key()))

    def _operator(self, spec, dest, path, depth):
        name = spec['op']
        args = spec.get('args')
        if not isinstance(args, list):
            raise ExprError('%s.args must be an array' % path)
        if name in ('and', 'or'):
            if len(args) < 2:
                raise ExprError('%s: %s needs at least two arguments' % (path, name))
            jumps = []
            self.compile(args[0], dest, '%s.args[1]' % path, depth + 1)
            for index, item in enumerate(args[1:], 2):
                self.code.append(_abc('TEST', dest, 0, 0 if name == 'and' else 1))
                jumps.append(self._emit_jump())
                self.compile(item, dest, '%s.args[%d]' % (path, index), depth + 1)
            end = len(self.code)
            for jump in jumps:
                self._patch_jump(jump, end)
            return
        if name == 'seq':
            if not args:
                raise ExprError('%s: seq needs at least one argument' % path)
            for index, item in enumerate(args, 1):
                self.compile(item, dest, '%s.args[%d]' % (path, index), depth + 1)
            return
        if name == 'not':
            if len(args) != 1:
                raise ExprError('%s: not takes exactly one argument' % path)
            self.compile(args[0], dest, '%s.args[1]' % path, depth + 1)
            self.code.append(_abc('NOT', dest, dest, 0))
            return
        if name in ('neg', 'len'):
            if len(args) != 1:
                raise ExprError('%s: %s takes exactly one argument' % (path, name))
            source = self._alloc()
            self.compile(args[0], source, '%s.args[1]' % path, depth + 1)
            self.code.append(_abc('UNM' if name == 'neg' else 'LEN', dest, source, 0))
            return
        if name == 'concat':
            if len(args) < 2:
                raise ExprError('%s: concat needs at least two arguments' % path)
            registers = [self._alloc() for _ in args]
            for register, item, index in zip(registers, args, range(1, len(args) + 1)):
                self.compile(item, register, '%s.args[%d]' % (path, index), depth + 1)
            if registers[-1] > 511:
                raise ExprError('%s: too many concatenation operands' % path)
            self.code.append(_abc('CONCAT', dest, registers[0], registers[-1]))
            return
        if name in BINARY:
            if len(args) != 2:
                raise ExprError('%s: %s takes exactly two arguments' % (path, name))
            left = self._alloc()
            self.compile(args[0], left, '%s.args[1]' % path, depth + 1)
            right = self._alloc()
            self.compile(args[1], right, '%s.args[2]' % path, depth + 1)
            self.code.append(_abc(BINARY[name], dest, left, right))
            return
        if name in COMPARE:
            if len(args) != 2:
                raise ExprError('%s: %s takes exactly two arguments' % (path, name))
            left = self._alloc()
            self.compile(args[0], left, '%s.args[1]' % path, depth + 1)
            right = self._alloc()
            self.compile(args[1], right, '%s.args[2]' % path, depth + 1)
            opcode = COMPARE[name]
            if name in ('gt', 'ge'):
                self.code.append(_abc(opcode, 1, right, left))
            else:
                self.code.append(_abc(opcode, 1, left, right))
            jump = self._emit_jump()
            if name == 'ne':
                self.code.append(_abc('LOADBOOL', dest, 1, 1))
                self.code.append(_abc('LOADBOOL', dest, 0, 0))
            else:
                self.code.append(_abc('LOADBOOL', dest, 0, 1))
                self.code.append(_abc('LOADBOOL', dest, 1, 0))
            self._patch_jump(jump, jump + 2)
            return
        raise ExprError('%s: unknown operation %r' % (path, name))

    def _call(self, spec, dest, path, depth):
        target = spec['call']
        if isinstance(target, str):
            keys = target.split('.')
        elif isinstance(target, list) and target:
            keys = target
        else:
            raise ExprError('%s.call must be a name or a non-empty array' % path)
        if any(not isinstance(key, str) or not key for key in keys):
            raise ExprError('%s.call parts must be non-empty strings' % path)
        args = spec.get('args', [])
        if not isinstance(args, list):
            raise ExprError('%s.args must be an array' % path)
        if len(args) > 250:
            raise ExprError('%s has too many arguments' % path)
        method = spec.get('method', False)
        if not isinstance(method, bool):
            raise ExprError('%s.method must be true or false' % path)
        if method and len(keys) < 2:
            raise ExprError('%s.method needs table.method syntax' % path)
        base = self._alloc()
        receiver = self._alloc() if method else None
        slots = [self._alloc() for _ in args]
        self.code.append(_abx('GETGLOBAL', base, self._constant(keys[0], path)))
        if len(keys) > 1:
            for part in keys[1:-1]:
                index = self._constant(part, path)
                self.code.append(_abx('LOADK', self._key(), index))
                self.code.append(_abc('GETTABLE', base, base, self._key()))
            if method:
                self.code.append(_abc('MOVE', receiver, base, 0))
            index = self._constant(keys[-1], path)
            self.code.append(_abx('LOADK', self._key(), index))
            self.code.append(_abc('GETTABLE', base, base, self._key()))
        for slot, item, number in zip(slots, args, range(1, len(args) + 1)):
            self.compile(item, slot, '%s.args[%d]' % (path, number), depth + 1)
        results = 1
        arguments = len(args) + (1 if method else 0)
        self.code.append(_abc('CALL', base, arguments + 1, results + 1))
        if dest != base:
            self.code.append(_abc('MOVE', dest, base, 0))

    def _if(self, spec, dest, path, depth):
        if set(spec) != {'if', 'then', 'else'}:
            raise ExprError('%s needs exactly if, then and else' % path)
        self.compile(spec['if'], dest, path + '.if', depth + 1)
        self.code.append(_abc('TEST', dest, 0, 0))
        alternate = self._emit_jump()
        self.compile(spec['then'], dest, path + '.then', depth + 1)
        done = self._emit_jump()
        self._patch_jump(alternate, len(self.code))
        self.compile(spec['else'], dest, path + '.else', depth + 1)
        self._patch_jump(done, len(self.code))

    def finish(self):
        self.code.append(_abc('RETURN', 0, 2, 0))
        stack = max(self.stack, 2)
        proto = {'source': None, 'line': self.line, 'lastline': self.line,
                 'nups': 0, 'nparams': 0, 'vararg': 0, 'stack': stack,
                 'code': list(self.code), 'k': list(self.constants), 'protos': [],
                 'locals': [], 'upnames': []}
        raw = encode_proto(self.code, self.constants, stack, self.line)
        return proto, raw


def compile_expression(spec, path='$expr', line=0):
    """Validate and compile a JSON expression into an ``Expr``."""
    builder = _Builder(path, line)
    builder.compile(spec, 0, path)
    proto, raw = builder.finish()
    return Expr(spec, proto, raw)


def evaluate(expr, globals_=None):
    """Run a compiled expression; used by tests and validation tooling."""
    if not isinstance(expr, Expr):
        expr = compile_expression(expr)
    closure = lua_data.Closure(expr.proto)
    budget = {'left': 100000}
    values = lua_data._call(closure, [], globals_ or {}, True, 0, budget)
    return values[0] if values else None
