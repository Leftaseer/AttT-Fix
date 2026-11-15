/* 0x00426B20: with the +0x9D flag set, a point (x, y) inside the +0xAC/+0xB0 rect (0..+0xC8, 0..+0xCC) makes the
 * current slot of the +0x98 texture play (slots 4 and 5 of the current slot's virtual), and AL comes back 1; anything
 * outside leaves EAX's low byte cleared. */
/* @func 00426B20 custom */
/* @conv ECX,EAX 8 */
#include "auto_pre.h"

DECOMP(00426B20)
unsigned int __cdecl f_00426B20(void *this, unsigned int eax, float x, float y)
{
    char *s = (char *)this;
    volatile float dx, dy;
    char *texture, *slot;
    unsigned int r;

    if (!s[0x9d])
        goto fail;
    dx = x - *(float *)(s + 0xac);
    dy = y - *(float *)(s + 0xb0);
    if (!(dx >= 0.0f) || !(*(float *)(s + 0xc8) >= dx))
        goto fail;
    if (!(dy >= 0.0f) || !(*(float *)(s + 0xcc) >= dy))
        goto fail;
    texture = *(char **)(s + 0x98);
    slot = *(char **)(*(char **)(texture + 0x38) + *(unsigned int *)(texture + 0x40) * 4);
    (*(void (__thiscall **)(void *))(*(char **)slot + 0x10))(slot);
    texture = *(char **)(s + 0x98);
    slot = *(char **)(*(char **)(texture + 0x38) + *(unsigned int *)(texture + 0x40) * 4);
    r = (*(unsigned int (__thiscall **)(void *))(*(char **)slot + 0x14))(slot);
    return (r & 0xffffff00) | 1;
fail:
    return eax & 0xffffff00;
}
