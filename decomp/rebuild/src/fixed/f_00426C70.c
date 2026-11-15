/* 0x00426C70: the alpha manager's per-frame pick.  While a pick table entry (+0x66C, count +0x670) is zero the
 * current highlight (+0x6C) gets its +4 virtual, then every control in the +0x5C list is hit-tested at the
 * position of +0x64 (+0x204/+0x208).  The first control reported hit becomes the highlight: the old one gets its
 * +0xC virtual, the new one its +8 virtual.  With no hit the old highlight is released and +0x6C cleared. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00426B20(void *self, unsigned int eax, float x, float y);

DECOMP(00426C70)
unsigned int __thiscall f_00426C70(void *this, unsigned int param)
{
    char *s = (char *)this;
    char *pos = *(char **)(s + 0x64);
    volatile float x = *(float *)(pos + 0x204);
    volatile float y = *(float *)(pos + 0x208);
    char *table = *(char **)(s + 0x68);
    unsigned int count = *(unsigned int *)(table + 0x670);
    unsigned int *skip = *(unsigned int **)(table + 0x66c);
    char *head = *(char **)(s + 0x5c);
    char *node = *(char **)head;
    unsigned int result = 0;
    unsigned int i;
    int hit = 0;

    for (i = 0; i < count; i++) {
        char *cur = *(char **)(s + 0x6c);
        if (skip[i] == 0 && cur != 0)
            result = (*(unsigned int (__thiscall **)(void *))(*(char **)cur + 4))(cur);
    }
    while (node != head) {
        char *control = *(char **)(node + 8);
        result = sub_00426B20(control, result, x, y);
        if ((result & 0xff) != 0) {
            char *cur = *(char **)(s + 0x6c);
            if (control != cur) {
                if (cur != 0)
                    result = (*(unsigned int (__thiscall **)(void *))(*(char **)cur + 0xc))(cur);
                *(char **)(s + 0x6c) = control;
                result = (*(unsigned int (__thiscall **)(void *))(*(char **)control + 8))(control);
            }
            hit = 1;
        }
        node = *(char **)node;
    }
    if (!hit) {
        char *cur = *(char **)(s + 0x6c);
        if (cur != 0)
            result = (*(unsigned int (__thiscall **)(void *))(*(char **)cur + 0xc))(cur);
        *(char **)(s + 0x6c) = 0;
    }
    return result;
}
