/* 0x00431440: loads an object from a binary std::fstream; returns false when opening fails. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__thiscall *imp_00607194)(void *, const char *, int, int, int) __asm__("__imp_??0?$basic_fstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z");
DECOMP_C unsigned char (__thiscall *imp_00607198)(void *) __asm__("__imp_?fail@ios_base@std@@QBE_NXZ");
DECOMP_C void (__thiscall *imp_0060719C)(void *) __asm__("__imp_??_D?$basic_fstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C unsigned char __thiscall sub_004313A0(void *self, void *stream);

DECOMP(00431440)
unsigned char __thiscall f_00431440(void *this, void *path)
{
    unsigned int stream[40];
    unsigned char result;

    imp_00607194(stream, imp_0060732C(path), 0x22, 0x40, 1);
    if (imp_00607198((char *)stream + (*(int **)stream)[1])) {
        imp_0060719C(stream);
        return 0;
    }
    result = sub_004313A0(this, (char *)stream + 8);
    imp_0060719C(stream);
    return result;
}
