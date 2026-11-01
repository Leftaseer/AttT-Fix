/* 0x0048A270: maps a position to a chunk: row = ftol((this[0x78] - p[2]) / this[0x60]), col =
 * ftol((p[0] - this[0x70]) / this[0x5c]), result = table[row] + col * 0x38. The original converts through
 * __ftol2 (64-bit) and keeps EAX, so a quotient outside the int range gives the low 32 bits of the 64-bit
 * result instead of the INT_MIN a 32-bit fistp would produce. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0048A270)
int __thiscall f_0048A270(void *this, float *param_1)
{
    int row = (int)(long long)((*(float *)((int)this + 0x78) - param_1[2]) / *(float *)((int)this + 0x60));
    int col = (int)(long long)((param_1[0] - *(float *)((int)this + 0x70)) / *(float *)((int)this + 0x5c));
    int *tab = *(int **)((int)this + 0x6c);

    return tab[row] + col * 0x38;
}
