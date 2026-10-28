/* 0x00473B60: CMaskControlsManager::Update: when active (+0x454): a left press (button events of the input +0x448:
 * +0x66C, count +0x670) clicks the hovered control (vf04); then the control under the mouse (+0x444: vf8C / vf90,
 * minus the origin +0x44C / +0x450 as unsigned) is the byte of the mask image (+0x43C: width +0x14, height +0x18, bytes
 * +0xC) there (0 outside); a change leaves the old one (vf0C) and enters the new one (vf08), kept at +0x438; EAX as
 * it came when inactive */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 00473B60 custom */
typedef unsigned int (__thiscall *vf_473B60)(void *self);
typedef double (__thiscall *vfpos_473B60)(void *self);

#define CTRL(i) (*(void ***)(s + 0x38 + (i) * 4))
#define VCALL(o, off) ((vf_473B60)(*(void ***)(o))[(off) / 4])(o)

DECOMP(00473B60)
unsigned int __cdecl f_00473B60(void *this, unsigned int eax, float dt)
{
    char *s = (char *)this;
    char *in, *mask;
    unsigned int *ev, n, i, cur, c = 0, r = eax;
    void **m;
    float x, y;
    if (!s[0x454])
        return eax;
    in = *(char **)(s + 0x448);
    n = *(unsigned int *)(in + 0x670);
    ev = *(unsigned int **)(in + 0x66c);
    for (i = 0; i < n; i++)
        if (!ev[i] && (int)*(unsigned int *)(s + 0x438) >= 0 && CTRL(*(int *)(s + 0x438)))
            r = VCALL(CTRL(*(int *)(s + 0x438)), 4);
    if (!s[0x454])
        return r;
    m = *(void ***)(s + 0x444);
    x = (float)(((vfpos_473B60)(*(void ***)m)[0x8c / 4])(m) - (double)*(unsigned int *)(s + 0x44c));
    m = *(void ***)(s + 0x444);
    y = (float)(((vfpos_473B60)(*(void ***)m)[0x90 / 4])(m) - (double)*(unsigned int *)(s + 0x450));
    mask = *(char **)(s + 0x43c);
    if (mask && !(0.0f > x) && !(x >= (double)*(unsigned int *)(mask + 0x14)) &&
        !(0.0f > y) && !(y >= (double)*(unsigned int *)(mask + 0x18)))
        c = (unsigned char)(*(char **)(mask + 0xc))[(int)(long long)y * *(int *)(mask + 0x14) + (int)(long long)x];
    cur = *(unsigned int *)(s + 0x438);
    if (cur == c)
        return cur;
    if ((int)cur >= 0 && CTRL(cur))
        r = VCALL(CTRL(cur), 0xc);
    *(unsigned int *)(s + 0x438) = c;
    if (CTRL(c))
        r = VCALL(CTRL(c), 8);
    return r;
}
