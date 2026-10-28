/* 0x00425090: C3DControlsManager::vf6 (mouse picking): the visible controls (list +0x40, vf14) with their squared
 * distance to the camera (0x6CA2C4-like object +0x50, +0x44) go into the array at +0x58 (count +0x5C), sorted by it
 * (+0x54: insertion sort 0x005084E0 up to 38, else quicksort 0x005085E0); the first one hit by the mouse ray
 * (0x00424A90; vf18) becomes the hovered control (+0x38: the old one vf0C, the new one vf08, whose result is
 * returned); none hit: the old one is left (vf0C) and cleared; EAX as the last call left it otherwise */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 00425090 custom */
DECOMP_C void __thiscall sub_005084E0(void *self);
DECOMP_C void __thiscall sub_005085E0(void *self, unsigned int lo, unsigned int hi);
DECOMP_C unsigned int __thiscall sub_00424A90(void *self, float *origin, float *dir);
typedef unsigned int (__thiscall *vf_425090)(void *self);
typedef float *(__thiscall *vf10_425090)(void *self);
typedef unsigned int (__thiscall *vf18_425090)(void *self, float *origin, float *dir);

#define VT(o) (*(void ***)(o))

DECOMP(00425090)
unsigned int __cdecl f_00425090(void *this, unsigned int eax)
{
    char *s = (char *)this;
    void **head = *(void ***)(s + 0x40), **n;
    float origin[3], dir[3];
    unsigned int i;
    *(unsigned int *)(s + 0x5c) = 0;
    for (n = (void **)*head; n != head; n = (void **)*n) {
        void **c = (void **)n[2];
        eax = ((vf_425090)VT(c)[0x14 / 4])(c);
        if ((char)eax) {
            float *cam = (float *)(*(char **)(s + 0x50) + 0x44);
            float *p = ((vf10_425090)VT(c)[0x10 / 4])(c);
            float dx = p[0] - cam[0], dy = p[1] - cam[1], dz = p[2] - cam[2];
            unsigned int k = *(unsigned int *)(s + 0x5c);
            char *arr = *(char **)(s + 0x58);
            eax = (unsigned int)arr;
            *(void ***)(arr + k * 8) = c;
            *(float *)(arr + k * 8 + 4) = dy * dy + dx * dx + dz * dz;
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
            void **c = *(void ***)(*(char **)(s + 0x58) + i * 8);
            eax = ((vf18_425090)VT(c)[0x18 / 4])(c, origin, dir);
            if ((char)eax) {
                void **old = *(void ***)(s + 0x38);
                if (old)
                    ((vf_425090)VT(old)[0xc / 4])(old);
                c = *(void ***)(*(char **)(s + 0x58) + i * 8);
                *(void ***)(s + 0x38) = c;
                return ((vf_425090)VT(c)[2])(c);
            }
        }
    }
    if (*(void **)(s + 0x38)) {
        void **old = *(void ***)(s + 0x38);
        eax = ((vf_425090)VT(old)[0xc / 4])(old);
        *(void **)(s + 0x38) = 0;
    }
    return eax;
}
