/* 0x00519CE0: creates a child render object, configures it with two generated strings,
 * and updates the parent and shared render state. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_00582FA0(void *self, int one);
DECOMP_C void __thiscall sub_00435E00(void *self, int zero);
DECOMP_C void __thiscall sub_0057BB20(void *self, const char *text, int one);
DECOMP_C void __thiscall sub_0046CF30(void *self);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_00614068[], d_0061405C[];
typedef void (__thiscall *configure_519CE0)(void *self, void *name, void *value, int one);

DECOMP(00519CE0)
void __thiscall f_00519CE0(char *this)
{
    unsigned int value[7], name[7];
    void *memory, *child, *state;

    memory = sub_005E3EAE(0x194);
    child = memory ? sub_00582FA0(memory, 1) : 0;
    *(void **)(this + 0x21c) = child;
    sub_00435E00(value, 0);
    sub_0057BB20(value, d_00614068, 1);
    imp_00607324(name, d_0061405C);
    ((configure_519CE0)(*(void ***)child)[0x3c / 4])(child, name, value, 1);
    imp_00607330(name);
    *(unsigned int *)(this + 0x110) = 4;
    state = *(void **)(this + 0x38);
    sub_0046CF30((char *)state + 0x80);
    *(unsigned int *)((char *)state + 0xac) = 5;
    sub_004220A0(value);
}
