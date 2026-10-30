/* 0x458AC0: a 32-bit bitmap's pixel (x, y from the bottom row +0x1C, row bytes +0x20, data +0xC); returns out (EAX: the generated void version left it there only by chance) */
/* @conv ECX 12 */
#include "auto_pre.h"

DECOMP(00458AC0)
void *__thiscall f_00458AC0(void *self, void *out, int x, int y)
{
    char *this = (char *)self;
    *(unsigned int *)out = *(unsigned int *)(*(char **)(this + 0xc) + (*(int *)(this + 0x1c) - y) *
                                             *(int *)(this + 0x20) + x * 4);
    return out;
}
