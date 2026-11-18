/* 0x0048A350: constructs a 0xEC-byte child from the by-value string, stores it at +0x50,
 * and caches the child's +0x34/+0x2C render value at +0x54. */
/* @conv ECX 28 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[7];
} String_0048A350;

DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_004792A0(void *self, const void *name, unsigned int mode);
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0048A350)
void __thiscall f_0048A350(char *this, String_0048A350 name)
{
    char *child = sub_005E3EAE(0xec);

    if (child)
        child = sub_004792A0(child, &name, 2);
    *(char **)(this + 0x50) = child;
    *(unsigned int *)(this + 0x54) = *(unsigned int *)(*(char **)(child + 0x34) + 0x2c);
    imp_00607330(&name);
}
