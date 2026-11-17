/* 0x0047A400: installs the object's transform with its second translation component zeroed,
 * draws through +0x210 and recursively renders each 0x21c-byte child. */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef void (__stdcall *set_transform_47A400)(void *device, unsigned int state, const void *matrix);
DECOMP_C void __thiscall sub_004773F0(void *self, void *first, void *second);
DECOMP_C char d_006C8C10[], d_006CA0A4[];

DECOMP(0047A400)
void __thiscall f_0047A400(char *this, void *first, void *second)
{
    unsigned int matrix[16];
    unsigned int i, count;
    void *device = *(void **)d_006C8C10;
    for (i = 0; i < 16; i++)
        matrix[i] = *(unsigned int *)(this + 0x1d0 + 4 * i);
    matrix[13] = 0;
    (*(set_transform_47A400 **)device)[0xb0 / 4](device, 0x100, matrix);
    *(unsigned int **)d_006CA0A4 = matrix;
    sub_004773F0(*(void **)(this + 0x210), first, second);
    count = *(unsigned int *)(this + 0x214);
    for (i = 0; i < count; i++)
        f_0047A400(*(char **)(this + 0x218) + i * 0x21c, first, second);
}
