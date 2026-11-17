/* 0x00424F20: releases the current control for each empty scene slot, collects visible controls
 * with squared camera distance, sorts them, and updates the hovered control from the mouse ray. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_005084E0(void *self);
DECOMP_C void __thiscall sub_005085E0(void *self, unsigned int lo, unsigned int hi);
DECOMP_C unsigned int __thiscall sub_00424A90(void *self, float *origin, float *dir);
typedef unsigned int (__thiscall *vf_424F20)(void *self);
typedef float *(__thiscall *vf10_424F20)(void *self);
typedef unsigned int (__thiscall *vf18_424F20)(void *self, float *origin, float *dir);

#define VT(o) (*(void ***)(o))

DECOMP(00424F20)
unsigned int __thiscall f_00424F20(void *this, void *unused)
{
    char *s = (char *)this;
    char *scene = *(char **)(s + 0x48);
    void **slots = *(void ***)(scene + 0x66c);
    unsigned int count = *(unsigned int *)(scene + 0x670);
    unsigned int eax = (unsigned int)scene;
    unsigned int i;
    void **head, **n;
    float origin[3], dir[3];

    for (i = 0; i < count; i++) {
        if (!slots[i] && *(void **)(s + 0x38)) {
            void *old = *(void **)(s + 0x38);
            eax = ((vf_424F20)VT(old)[1])(old);
        }
    }

    head = *(void ***)(s + 0x40);
    *(unsigned int *)(s + 0x5c) = 0;
    for (n = (void **)*head; n != head; n = (void **)*n) {
        void **control = (void **)n[2];
        eax = ((vf_424F20)VT(control)[0x14 / 4])(control);
        if ((char)eax) {
            float *camera = (float *)(*(char **)(s + 0x50) + 0x44);
            float *p = ((vf10_424F20)VT(control)[0x10 / 4])(control);
            volatile float dx = p[0] - camera[0];
            volatile float dy = p[1] - camera[1];
            volatile float dz = p[2] - camera[2];
            unsigned int k = *(unsigned int *)(s + 0x5c);
            char *entries = *(char **)(s + 0x58);
            eax = (unsigned int)entries;
            *(void ***)(entries + k * 8) = control;
            *(float *)(entries + k * 8 + 4) = dy * dy + dx * dx + dz * dz;
            *(unsigned int *)(s + 0x5c) += 1;
        }
    }

    if (*(unsigned int *)(s + 0x5c)) {
        if (*(unsigned int *)(s + 0x5c) > 0x26)
            sub_005085E0(s + 0x54, 0, *(unsigned int *)(s + 0x5c) - 1);
        else
            sub_005084E0(s + 0x54);
        eax = sub_00424A90(this, origin, dir);
        for (i = 0; i < *(unsigned int *)(s + 0x5c); i++) {
            void **control = *(void ***)(*(char **)(s + 0x58) + i * 8);
            eax = ((vf18_424F20)VT(control)[0x18 / 4])(control, origin, dir);
            if ((char)eax) {
                void **old = *(void ***)(s + 0x38);
                if (old)
                    ((vf_424F20)VT(old)[0xc / 4])(old);
                control = *(void ***)(*(char **)(s + 0x58) + i * 8);
                *(void ***)(s + 0x38) = control;
                return ((vf_424F20)VT(control)[2])(control);
            }
        }
    }
    if (*(void **)(s + 0x38)) {
        void **old = *(void ***)(s + 0x38);
        eax = ((vf_424F20)VT(old)[0xc / 4])(old);
        *(void ***)(s + 0x38) = 0;
    }
    return eax;
}
