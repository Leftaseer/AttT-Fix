# MSVC runtime helpers the tools recognise by their machine code (the exe has no names for them).
import re

# float to integer conversion of the value in ST0, towards zero:
#   _ftol2_sse: 'cmp [__sse2_available], 0; je _ftol2; ... fstp qword [esp]; cvttsd2si eax, [esp]' -> EAX
#   _ftol2:     'push ebp; mov ebp, esp; sub esp, 0x20; and esp, -16; fld st0; fst [esp+0x18]; fistp qword [esp+0x10]'
#               -> EDX:EAX
FTOL = [(re.compile(rb'\x83\x3d....\x00\x74.\x55\x8b\xec\x83\xec\x08\x83\xe4\xf8\xdd\x1c\x24\xf2\x0f\x2c\x04\x24', re.S), 'int'),
        (re.compile(rb'\x55\x8b\xec\x83\xec\x20\x83\xe4\xf0\xd9\xc0\xd9\x54\x24\x18\xdf\x7c\x24\x10\xdf\x6c\x24\x10', re.S),
         'long long')]


def ftol_kind(code):
    """'int' (_ftol2_sse), 'long long' (_ftol2) or None, from the first bytes of a function"""
    for rx, kind in FTOL:
        if rx.match(code or b''):
            return kind
    return None
