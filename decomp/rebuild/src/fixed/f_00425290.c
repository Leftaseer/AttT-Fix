/* 0x00425290: C3DControlsManager::C3DControlsManager: the CUpdateObject base with an empty name and no parent
 * (0x00424D00), then the vtable 0x00607D88; the ring at +0x3C (0x004C2F40, count +0x44 = 0); the vtable
 * 0x00607D0C at +0x54 and the picker array at +0x58 (null for now, count +0x5C = 0); the input, cursor and camera
 * singletons at +0x48/+0x4C/+0x50; the hovered control +0x38 = 0; finally a fresh 4000-byte array at +0x58.
 * Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607D88[], d_00607D0C[], d_0060FA8B[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __thiscall sub_00424D00(void *self, void *name, void *parent);
DECOMP_C void *__thiscall sub_004C2F40(void *self);
DECOMP_C void *__cdecl sub_004215D0(void);      /* CInput */
DECOMP_C void *__cdecl sub_00421680(void);      /* CCursor */
DECOMP_C void *__cdecl sub_00424E70(void);      /* CCamera */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size); /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *block);       /* operator delete[] */

DECOMP(00425290)
void *__thiscall f_00425290(void *this)
{
    char *s = (char *)this;
    unsigned int name[7];
    imp_00607324(name, d_0060FA8B);
    sub_00424D00(s, name, 0);
    imp_00607330(name);
    *(const void **)s = d_00607D88;
    *(void **)(s + 0x40) = sub_004C2F40(s + 0x3c);
    *(unsigned int *)(s + 0x44) = 0;
    *(const void **)(s + 0x54) = d_00607D0C;
    *(void **)(s + 0x58) = 0;
    *(unsigned int *)(s + 0x5c) = 0;
    *(void **)(s + 0x48) = sub_004215D0();
    *(void **)(s + 0x4c) = sub_00421680();
    *(void **)(s + 0x50) = sub_00424E70();
    *(void **)(s + 0x38) = 0;
    if (*(void **)(s + 0x58)) {
        sub_005E3EBA(*(void **)(s + 0x58));
        *(void **)(s + 0x58) = 0;
    }
    *(void **)(s + 0x58) = sub_005E3B10(0x1f4 * 8);
    *(unsigned int *)(s + 0x5c) = 0;
    return s;
}
