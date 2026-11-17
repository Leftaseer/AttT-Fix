/* 0x004E56A0: rebuilds the configured object array, initializes both object sets, and applies
 * the two float parameters at this+8C/+90 through virtual slot 0x78. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00421510(void);
DECOMP_C char *__thiscall sub_00424270(void *self, void *name);
DECOMP_C void __thiscall sub_004E48B0(void *self, void *config);
DECOMP_C void __thiscall sub_004E48F0(void *self, void *config);
DECOMP_C void __thiscall sub_004E4B80(void *self, void *config);
DECOMP_C void __thiscall sub_004E4540(void *self, void *config);
DECOMP_C void __cdecl sub_005E3EBA(void *memory);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_00612810[];
typedef void (__thiscall *set_parameters_4E56A0)(void *self, float first, float second);

DECOMP(004E56A0)
void __thiscall f_004E56A0(char *this)
{
    unsigned int name[7];
    char *config;
    unsigned int i;

    imp_00607324(name, d_00612810);
    config = sub_00424270(sub_00421510() + 4, name);
    imp_00607330(name);
    if (*(void **)(this + 0x84)) {
        sub_005E3EBA(*(void **)(this + 0x84));
        *(void **)(this + 0x84) = 0;
    }
    *(void **)(this + 0x84) = sub_005E3B10(1000 * 4);
    *(unsigned int *)(this + 0x88) = 0;
    sub_004E48B0(this, config + 0xd8);
    sub_004E48F0(this, config + 0x118);
    sub_004E4B80(this, config + 0x128);
    sub_004E4540(this, config + 0xac);
    for (i = 0; i < *(unsigned int *)(this + 0x88); i++) {
        void *object = *(void **)(*(char **)(this + 0x84) + i * 4);
        ((set_parameters_4E56A0)(*(void ***)object)[0x78 / 4])(
            object, *(float *)(this + 0x8c), *(float *)(this + 0x90));
    }
    for (i = 0; i < *(unsigned int *)(this + 0x9c); i++) {
        void *object = *(void **)(*(char **)(this + 0x98) + i * 4);
        ((set_parameters_4E56A0)(*(void ***)object)[0x78 / 4])(
            object, *(float *)(this + 0x8c), *(float *)(this + 0x90));
    }
}
