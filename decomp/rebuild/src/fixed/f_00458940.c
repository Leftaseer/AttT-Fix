/* 0x00458940: the check of a D3D result (with the file and line, unused): a failure gets its name
 * (DXGetErrorString, 0x005B8210); out of memory (E_OUTOFMEMORY, D3DERR_OUTOFVIDEOMEMORY) raises 0xE0000003 with a new
 * std::string of the name as the first argument (and 0x3C as the count, as the original has it), and 0xE0000004
 * raises itself (the original deletes the string again if its constructor throws; this C does not) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C const char *__stdcall sub_005B8210(long hr);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__stdcall *imp_006070F8)(unsigned int, unsigned int, unsigned int, const void *) __asm__("__imp__RaiseException@16");

DECOMP(00458940)
void __cdecl f_00458940(long hr, const char *file, int line)
{
    if (hr < 0) {
        const char *name = sub_005B8210(hr);
        if (hr == (long)0x8007000e || hr == (long)0x8876017c) {
            unsigned int args[15];
            void *str = sub_005E3EAE(0x1c);
            if (str)
                imp_00607324(str, name);
            args[0] = (unsigned int)str;
            imp_006070F8(0xe0000003, 0, 0x3c, args);
        }
        if (hr == (long)0xe0000004)
            imp_006070F8(0xe0000004, 0, 0, 0);
    }
}
