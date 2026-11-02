#!/usr/bin/env python3
"""Decode the game's data-only Lua save constructors without executing Lua or loading game code.

Unsupported instructions, globals, closures or malformed headers fail closed. Canonical output
retains key types, ignoring bytecode instruction/table insertion order and source/debug metadata.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

spec = importlib.util.spec_from_file_location('luadis', Path(__file__).with_name('luadis.py'))
lua = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lua)


def decode(data):
    if data[:12] != b'\x1bLua\x51\x00\x01\x04\x04\x04\x04\x00':
        raise ValueError('expected little-endian float32 / size_t32 Lua 5.1 save')
    reader = lua.R(data)
    reader.p = 12
    function = lua.function(reader)
    if reader.p != len(data) or function['protos'] or function['nups']:
        raise ValueError('save is not a single data-only constructor')
    return evaluate(function)


def evaluate(function):
    registers, globals_ = {}, {}
    constants, code = function['k'], function['code']

    def rk(index):
        return constants[index - 256] if index >= 256 else registers[index]

    def put(table, key, value):
        if isinstance(key, bool) or not isinstance(key, (str, int, float)):
            raise ValueError('unsupported save key')
        if value is None:
            table.pop(key, None)
        else:
            table[key] = value

    pc = 0
    while pc < len(code):
        instruction = code[pc]
        pc += 1
        op, a, c, b = instruction & 63, (instruction >> 6) & 255, (instruction >> 14) & 511, (instruction >> 23) & 511
        bx = instruction >> 14
        name = lua.OPS[op] if op < len(lua.OPS) else 'INVALID'
        if name == 'NEWTABLE':
            registers[a] = {}
        elif name == 'LOADK':
            registers[a] = constants[bx]
        elif name == 'MOVE':
            registers[a] = registers[b]
        elif name == 'LOADBOOL' and c == 0:
            registers[a] = bool(b)
        elif name == 'LOADNIL':
            for register in range(a, b + 1):
                registers[register] = None
        elif name == 'SETTABLE':
            put(registers[a], rk(b), rk(c))
        elif name == 'SETLIST' and b:
            if c == 0:
                c = code[pc]
                pc += 1
            for index in range(1, b + 1):
                put(registers[a], (c - 1) * 50 + index, registers[a + index])
        elif name == 'SETGLOBAL' and constants[bx] == 'Serialize':
            globals_['Serialize'] = registers[a]
        elif name == 'RETURN' and b == 1 and pc == len(code):
            break
        else:
            raise ValueError('unsupported save instruction at %d: %s' % (pc - 1, name))
    if not isinstance(globals_.get('Serialize'), dict):
        raise ValueError('save did not construct Serialize')
    return globals_['Serialize']


def canonical(value):
    if isinstance(value, dict):
        return {(('s:' + key) if isinstance(key, str) else ('n:' + format(key, '.17g'))): canonical(item)
                for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError('unsupported save value')


def differences(left, right, path='Serialize'):
    result = []
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(left.keys() | right.keys()):
            if key not in left or key not in right:
                result.append({'path': path + '/' + key, 'left_present': key in left, 'right_present': key in right})
            else:
                result.extend(differences(left[key], right[key], path + '/' + key))
    elif (type(left) != type(right) or left != right or
          isinstance(left, float) and struct.pack('<f', left) != struct.pack('<f', right)):
        result.append({'path': path, 'left': left, 'right': right})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    data = args.save.read_bytes()
    result = {'save_sha256': hashlib.sha256(data).hexdigest(), 'state': canonical(decode(data))}
    if args.compare:
        other = args.compare.read_bytes()
        result['comparison_sha256'] = hashlib.sha256(other).hexdigest()
        result['differences'] = differences(result['state'], canonical(decode(other)))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + '\n')
    print('Decoded', args.save, 'to', args.output)
    return int(bool(result.get('differences')))


if __name__ == '__main__':
    raise SystemExit(main())
