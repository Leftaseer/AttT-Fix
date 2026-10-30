/* 0x4589E0: a palette bitmap's pixel (x, y counted from the bottom row +0x1C, row bytes +0x20, bits per pixel +0x16 from bit +0x28 of the data +0xC, masked by +0x2C) as its colour from the palette +0x10; returns out (EAX: the generated void version left it there only by chance) */
/* @conv ECX 12 */
#include "auto_pre.h"

DECOMP(004589E0)
void *__thiscall f_004589E0(void *self, void *out, int x, int y)
{
    char *this = (char *)self;
    unsigned int bit = (unsigned int)(((*(int *)(this + 0x1c) - y) - 1) * *(int *)(this + 0x20) +
                                      *(unsigned char *)(this + 0x16) * x - *(int *)(this + 0x28));
    unsigned char b = (unsigned char)(*(unsigned char *)(*(char **)(this + 0xc) + (bit >> 3)) << (bit & 7));
    *(unsigned int *)out = *(unsigned int *)(*(char **)(this + 0x10) + (b & *(unsigned char *)(this + 0x2c)) * 4);
    return out;
}
