/* 0x458A90: a 24-bit bitmap's pixel (x, y from the bottom row +0x1C, row bytes +0x20, data +0xC) as 3 bytes and an opaque alpha; returns out (EAX: the generated void version left it there only by chance) */
/* @conv ECX 12 */
#include "auto_pre.h"

DECOMP(00458A90)
void *__thiscall f_00458A90(void *self, void *out, int x, int y)
{
    char *this = (char *)self;
    char *p = *(char **)(this + 0xc) + (*(int *)(this + 0x1c) - y) * *(int *)(this + 0x20) + x * 3;
    *(unsigned short *)out = *(unsigned short *)p;
    ((unsigned char *)out)[2] = (unsigned char)p[2];
    ((unsigned char *)out)[3] = 0xff;
    return out;
}
