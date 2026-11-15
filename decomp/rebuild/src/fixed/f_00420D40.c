/* 0x00420D40: allocates room for arg 1 records of 0xE4 bytes (operator new 0x005E3EAE); a count too large for the
 * size (0xFFFFFFFF / count < 0xE4) throws the message-less std::bad_alloc: the exception is built through MSVCR80's
 * exception constructor (IAT 0x6073B4), its vtable 0x00607B0C is stored and it is thrown with 0x006990C4. */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);       /* _CxxThrowException */
DECOMP_C char d_00607B0C[], d_006990C4[];
DECOMP_C void (__thiscall *imp_006073B4)(void *, const char *const *)
    __asm__("__imp_??0exception@std@@QAE@ABQBD@Z");

DECOMP(00420D40)
void *__cdecl f_00420D40(unsigned int count)
{
    typedef struct { void *vftable; const char *what; int doFree; } BadAlloc_420D40;
    BadAlloc_420D40 error;
    const char *message = 0;
    if (count != 0 && 0xFFFFFFFFu / count < 0xE4) {
        imp_006073B4(&error, &message);
        error.vftable = d_00607B0C;
        sub_005E3EC0(&error, d_006990C4);
        __builtin_unreachable();
    }
    return sub_005E3EAE(count * 0xE4);
}
