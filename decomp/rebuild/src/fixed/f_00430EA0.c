/* 0x00430EA0: releases the previous Bink movie, reads a file into memory and opens it with BinkOpen. */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef void (__stdcall *release_430EA0)(void *self);
DECOMP_C void __thiscall sub_00458F80(void *file, void *buffer, unsigned int size);
DECOMP_C void __stdcall sub_00430C70(void *message);
DECOMP_C void __thiscall sub_00430E10(void *self);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void __cdecl sub_005E3EBA(void *memory);
DECOMP_C void (__stdcall *imp_00607714)(void *) __asm__("__imp__BinkClose@4");
DECOMP_C int (__stdcall *imp_00607718)(void *, void *) __asm__("__imp__BinkSetSoundSystem@8");
DECOMP_C void (__stdcall *imp_0060771C)(void *) __asm__("__imp__BinkOpenDirectSound@4");
DECOMP_C void *(__stdcall *imp_00607734)(void *, unsigned int) __asm__("__imp__BinkOpen@8");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_006C88CC[], d_006091D0[];

DECOMP(00430EA0)
void __thiscall f_00430EA0(char *this, void *file, unsigned int size, unsigned int flags)
{
    unsigned int message[7];
    void *object;
    if (this[8]) {
        imp_00607714(*(void **)(this + 0x0c));
        *(void **)(this + 0x0c) = 0;
        object = *(void **)(this + 4);
        if (object) {
            ((release_430EA0)(*(void ***)object)[0x8 / 4])(object);
            *(void **)(this + 4) = 0;
        }
        sub_005E3EBA(*(void **)(this + 0x10));
        *(void **)(this + 0x10) = 0;
        this[8] = 0;
    }
    if (!d_006C88CC[0])
        d_006C88CC[0] = imp_00607718(imp_0060771C, 0) != 0;
    *(unsigned int *)(this + 0x14) = flags;
    object = sub_005E3B10(size);
    *(void **)(this + 0x10) = object;
    sub_00458F80(file, object, size);
    object = imp_00607734(object, flags | 0x04100000);
    *(void **)(this + 0x0c) = object;
    if (!object) {
        imp_00607324(message, d_006091D0);
        sub_00430C70(message);
    }
    sub_00430E10(this);
    this[8] = 1;
}
