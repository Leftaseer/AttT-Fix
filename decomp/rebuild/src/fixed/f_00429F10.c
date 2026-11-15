/* 0x00429F10: a constructor of the ambient sound manager family: the CUpdateObject/CGameObject base named d_0060FA8B
 * (0x00424D00), the vtables 0x006083E0/+0x38 0x006083D8/+0x3C 0x006083D0, the reader at +0x44 (0x00458AF0), the map at
 * +0x88 (self-linked head node, count +0x90 = 0) and the cell containers at +0x98 (0x00427FF0). The EDX register and
 * the stack argument are not used (this compiler kept the ECX/EDX register convention and pops 4 bytes). */
/* @conv ECX,EDX 4 */
#include "auto_pre.h"
DECOMP_C char d_006083E0[], d_006083D8[], d_006083D0[], d_00608250[], d_00608214[], d_0060FA8B[];
DECOMP_C void __thiscall sub_00424D00(void *self, void *name, void *parent);
DECOMP_C void *__thiscall sub_00458AF0(void *self);
DECOMP_C char *__cdecl sub_00427C00(void);
DECOMP_C void *__thiscall sub_00427FF0(void *self);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00429F10)
void *__fastcall f_00429F10(void *this, unsigned int edx, unsigned int stack_arg)
{
    char *s = (char *)this;
    unsigned int name[7];
    char *head;

    imp_00607324(name, d_0060FA8B);
    sub_00424D00(s, name, 0);
    imp_00607330(name);
    *(void **)(s + 0x38) = d_00608250;
    *(void **)(s + 0x3c) = d_00608214;
    *(void **)s = d_006083E0;
    *(void **)(s + 0x38) = d_006083D8;
    *(void **)(s + 0x3c) = d_006083D0;
    sub_00458AF0(s + 0x44);
    head = sub_00427C00();
    *(char **)(s + 0x8c) = head;
    head[0x31] = 1;
    *(char **)(head + 4) = head;
    *(char **)head = head;
    *(char **)(head + 8) = head;
    *(unsigned int *)(s + 0x90) = 0;
    sub_00427FF0(s + 0x98);
    (void)edx;
    (void)stack_arg;
    return s;
}
