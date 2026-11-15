/* 0x00426D50: the alpha control manager's destructor: the 0x0060819C vtable, the +0x5C list cleared and its nodes
 * freed, the +0x58 part destroyed, then the control base. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060819C[];
DECOMP_C void __cdecl sub_005E3E9C(void *block);
DECOMP_C void __thiscall sub_0044CFE0(void *self);
DECOMP_C void __thiscall sub_004AB940(void *self);

DECOMP(00426D50)
void __thiscall f_00426D50(void *this)
{
    char *s = (char *)this;
    unsigned int *head = *(unsigned int **)(s + 0x5c);
    unsigned int *node = (unsigned int *)*head;

    *(const void **)s = d_0060819C;
    *head = (unsigned int)head;
    head = *(unsigned int **)(s + 0x5c);
    head[1] = (unsigned int)head;
    *(unsigned int *)(s + 0x60) = 0;
    while (node != *(unsigned int **)(s + 0x5c)) {
        unsigned int *next = (unsigned int *)*node;
        sub_005E3E9C(node);
        node = next;
    }
    sub_0044CFE0(s + 0x58);
    sub_004AB940(s);
}
