/* std::basic_ifstream<char> / std::basic_ofstream<char> of Visual C++ 2005 (MSVCP80.dll), the ones the game's
 * objects contain.  The layout is MSVC's; the state is opaque here, and only the members the decompiled code uses
 * are declared.  The MSVC 2005 stream constructors pop one more stack argument than their decorated names say
 * (every original caller pushes a bool `1`, and MSVCP80's `ret 4`/`ret 0x10` confirms it), hence the explicit
 * asm labels and the extra parameter.
 *
 *   0x441DF0 (CConfig::LoadGraphicCfg) reserves 0xA0 bytes for each stream object on the stack.
 */
#pragma once
#include "string.h"

/* MSVCP80: ??7ios_base@std@@QBE_NXZ, takes the ios_base subobject of the stream */
extern "C" __declspec(dllimport) bool __thiscall ios_base_operator_not(const void *)
    __asm__("??7ios_base@std@@QBE_NXZ");

namespace std {

class ios_base {
public:
    /* the VC8 _Openmode bits and the CRT open protection (_SH_DENYNO) */
    enum openmode { _In = 0x01, _Out = 0x02, _Ate = 0x04, _App = 0x08, _Trunc = 0x10, _Binary = 0x20 };
    enum { _Openprot = 0x40 };
};

/* the ios_base subobject sits at vftable[1] bytes into the stream */
template <class S>
inline const void *stream_ios_base(const S *s)
{
    const char *obj = (const char *)s;
    return obj + *(const int *)(*(const char *const *)obj + 4);
}

template <class E, class Tr = char_traits<E>>
class basic_ifstream {
public:
    MSVCP80_IMPORT basic_ifstream(bool init = true)
        __asm__("??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@XZ");
    MSVCP80_IMPORT basic_ifstream(const E *name, int mode, int prot, bool init = true)
        __asm__("??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z");
    MSVCP80_IMPORT ~basic_ifstream() __asm__("??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");

    MSVCP80_IMPORT void open(const E *name, int mode, int prot)
        __asm__("?open@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXPBDHH@Z");
    MSVCP80_IMPORT void close() __asm__("?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
    MSVCP80_IMPORT void read(E *buf, int n)
        __asm__("?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");

    bool fail() const { return ios_base_operator_not(stream_ios_base(this)); }
    bool operator!() const { return fail(); }
    explicit operator bool() const { return !fail(); }

private:
    alignas(4) unsigned char opaque[0xa0];
};

template <class E, class Tr = char_traits<E>>
class basic_ofstream {
public:
    MSVCP80_IMPORT basic_ofstream(const E *name, int mode, int prot, bool init = true)
        __asm__("??0?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z");
    MSVCP80_IMPORT ~basic_ofstream() __asm__("??_D?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXXZ");

    MSVCP80_IMPORT void close() __asm__("?close@?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
    MSVCP80_IMPORT void write(const E *buf, int n)
        __asm__("?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z");

    bool fail() const { return ios_base_operator_not(stream_ios_base(this)); }
    bool operator!() const { return fail(); }
    explicit operator bool() const { return !fail(); }

private:
    alignas(4) unsigned char opaque[0xa0];
};

typedef basic_ifstream<char> ifstream;
typedef basic_ofstream<char> ofstream;

} // namespace std
