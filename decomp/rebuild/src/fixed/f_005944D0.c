/* 0x005944D0: CDXUTDialog::GetControlAtPoint: the first control (array +0x1B4, count +0x1B8) that contains the point
 * (vf34, the POINT by value) and is enabled (vf3C) and visible (vf44); NULL if none */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef int (__thiscall *vf34_5944D0)(void *self, int x, int y);
typedef char (__thiscall *vfb_5944D0)(void *self);

DECOMP(005944D0)
void *__thiscall f_005944D0(void *this, int x, int y)
{
    char *s = (char *)this;
    int i;
    for (i = 0; i < *(int *)(s + 0x1b8); i++) {
        void **c = (*(void ****)(s + 0x1b4))[i];
        if (c && ((vf34_5944D0)(*(void ***)c)[0x34 / 4])(c, x, y) &&
            ((vfb_5944D0)(*(void ***)c)[0x3c / 4])(c) && ((vfb_5944D0)(*(void ***)c)[0x44 / 4])(c))
            return c;
    }
    return 0;
}
