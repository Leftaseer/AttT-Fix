/* 0x0048D590: the QuadTree's visibility walk from a node at a depth (level 0 starts a frame: the node counter +0x160,
 * the range counts +0x48 / +0x4C and the index count +0x148 cleared): a node every culler (+0x154, +0x158 of them,
 * vf04 with the counter) passes is visited, else the counter skips its whole subtree ((4^(leaf depth - depth) * 4 - 4)
 * / 3 + 1, _CIpow); a leaf (depth +0x58) takes its number (+0xA0), is listed in its patch row (+0x1A0, 16 bytes per
 * row, by its +0x9C and +0x98) and marks its patch (+0x184 by +0xA4); an inner node recurses into its four children
 * (+0x60..+0x6C). After the walk 0x0048D260 lists the leaves' index ranges (+0x40, {start, end}); with merging
 * (+0x1C0) the touching ones are joined into +0x44 (+0x4C of them) and the ranges' indices (+0x144) copied into the
 * locked index buffer (+0x168) one after another (+0x148 in all) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0048D260(void *self);
DECOMP_C double decomp_CIpow(double x, double y);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */
DECOMP_C char d_00609B68[];
typedef char (__thiscall *cull_48D590)(void *self, void *node, unsigned int n);
typedef long (__stdcall *lock_48D590)(void *self, unsigned int off, unsigned int size, void **data, unsigned int fl);
typedef long (__stdcall *com_48D590)(void *self);

#define CNT (*(unsigned short *)(s + 0x160))
#define R(i) (*(unsigned int (*)[2])(*(char **)(s + 0x40) + (i) * 8))
#define O(i) (*(unsigned int (*)[2])(*(char **)(s + 0x44) + (i) * 8))

DECOMP(0048D590)
void __thiscall f_0048D590(void *this, char *node, unsigned int level)
{
    char *s = (char *)this;
    unsigned short lv = (unsigned short)level;
    unsigned char i;
    unsigned int k, first, n;
    void **ib;
    char *data;
    if (!node)
        return;
    if (lv == 0) {
        CNT = 0;
        *(unsigned int *)(s + 0x48) = 0;
        *(unsigned int *)(s + 0x4c) = 0;
        *(unsigned int *)(s + 0x148) = 0;
    }
    for (i = 0; i < (unsigned char)s[0x158]; i++) {
        void **c = (*(void ****)(s + 0x154))[i];
        if (!((cull_48D590)(*(void ***)c)[1])(c, node, CNT)) {
            unsigned int d = (unsigned short)((unsigned char)s[0x58] - lv);
            int x = (unsigned short)(int)decomp_CIpow(*(double *)d_00609B68, (double)(int)d);
            CNT += (unsigned short)((x * 4 - 4) / 3 + 1);
            return;
        }
    }
    if (lv == (unsigned char)s[0x58]) {
        *(unsigned short *)(node + 0xa0) = CNT;
        CNT++;
        (*(char ***)(*(char **)(s + 0x1a0) + *(int *)(node + 0x9c) * 16 + 4))[*(int *)(node + 0x98)] = node;
        (*(char **)(s + 0x184))[*(int *)(node + 0xa4)] = 1;
        return;
    }
    CNT++;
    f_0048D590(this, *(char **)(node + 0x60), level + 1);
    f_0048D590(this, *(char **)(node + 0x64), level + 1);
    f_0048D590(this, *(char **)(node + 0x68), level + 1);
    f_0048D590(this, *(char **)(node + 0x6c), level + 1);
    if (lv != 0)
        return;
    sub_0048D260(this);
    if (!s[0x1c0])
        return;
    k = 0;
    *(unsigned int *)(s + 0x4c) = 0;
    if (*(unsigned int *)(s + 0x48)) {
        while (k < *(unsigned int *)(s + 0x48) - 1) {
            first = k;
            if (R(k)[1] >= R(k + 1)[0])
                while (k < *(unsigned int *)(s + 0x48) - 1) {
                    k++;
                    if (!(R(k)[1] >= R(k + 1)[0]))
                        break;
                }
            n = *(unsigned int *)(s + 0x4c);
            O(n)[0] = R(first)[0];
            O(*(unsigned int *)(s + 0x4c))[1] = R(k)[1];
            *(unsigned int *)(s + 0x4c) += 1;
            k++;
        }
        if (k == *(unsigned int *)(s + 0x48) - 1) {
            n = *(unsigned int *)(s + 0x4c);
            O(n)[0] = R(k)[0];
            O(n)[1] = R(k)[1];
            *(unsigned int *)(s + 0x4c) += 1;
        }
    }
    ib = *(void ***)(s + 0x168);
    ((lock_48D590)(*(void ***)ib)[0x2c / 4])(ib, 0, 0, (void **)&data, 0);
    for (k = 0; k < *(unsigned int *)(s + 0x48); k++) {
        sub_005E4232(data + *(unsigned int *)(s + 0x148) * 2, *(char **)(s + 0x144) + R(k)[0] * 2,
                     (R(k)[1] - R(k)[0]) * 2);
        *(unsigned int *)(s + 0x148) += R(k)[1] - R(k)[0];
    }
    ib = *(void ***)(s + 0x168);
    ((com_48D590)(*(void ***)ib)[0x30 / 4])(ib);
}
