/* 0x00459050: opens the file named by the string: drops the old data (+0x28, delete[]) and file (+0x24), keeps the
 * name at +8, opens it in the file system (0x004514B0 of 0x6C8DE4); a missing file raises 0xE0000002 with a new
 * std::string of the name (and 0x3C as the count, as the original has it) and returns false; otherwise it is open
 * (+0x2C) and, unless asked not to, read whole (vf04) into a new buffer of its size (+8) and a terminating 0 */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3EBA(void *p);                /* operator delete[] */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);     /* operator new[] */
DECOMP_C void *__thiscall sub_004514B0(void *fs, void *name);
DECOMP_C char d_006C8DE4[];
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__stdcall *imp_006070F8)(unsigned int, unsigned int, unsigned int, const void *) __asm__("__imp__RaiseException@16");
typedef void (__thiscall *dtor_459050)(void *self, int flags);
typedef void (__thiscall *read_459050)(void *self, void *buf, unsigned int n);

DECOMP(00459050)
unsigned char __thiscall f_00459050(void *this, void *name, int noload)
{
    char *s = (char *)this;
    char *f;
    if (*(void **)(s + 0x28)) {
        sub_005E3EBA(*(void **)(s + 0x28));
        *(void **)(s + 0x28) = 0;
    }
    if (*(void **)(s + 0x24)) {
        void **o = *(void ***)(s + 0x24);
        ((dtor_459050)(*(void ***)o)[0])(o, 1);
        *(void **)(s + 0x24) = 0;
    }
    s[0x2c] = 0;
    imp_0060731C(s + 8, name);
    f = sub_004514B0(*(void **)d_006C8DE4, name);
    *(char **)(s + 0x24) = f;
    if (!f) {
        unsigned int args[15];
        void *str = sub_005E3EAE(0x1c);
        if (str)
            imp_00607324(str, imp_0060732C(name));
        args[0] = (unsigned int)str;
        s[0x2c] = 0;
        imp_006070F8(0xe0000002, 0, 0x3c, args);
        return 0;
    }
    s[0x2c] = 1;
    if (!noload) {
        unsigned int n = 0;
        void **o;
        if (!*(void **)(s + 0x28)) {
            n = *(unsigned int *)(f + 8);
            *(char **)(s + 0x28) = sub_005E3B10(n + 1);
            (*(char **)(s + 0x28))[n] = 0;
        }
        o = *(void ***)(s + 0x24);
        ((read_459050)(*(void ***)o)[1])(o, *(void **)(s + 0x28), n);
    }
    return 1;
}
