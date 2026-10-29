/* 0x00551A70: a particle emitter's emission, while enabled (provider +0x24C): each period (+0x28C since +0x5EC) picks
 * a new rate between +0x26C and +0x27C (unsigned, rand) into +0x5E8; the particles due since the start (+0x5E0) at that
 * rate plus the carried fraction (+0x5FC; floor, _ftol) are made (a list +0x5D0 grown to at least that many with
 * default particles, 0x0054AD50 / 0x00550360 taking one by value), every n / (n * provider +0x29C)-th of them (none
 * when that is 0) given a random time between its +0x44 plus now (+0x5E4) and now in +0x4C; each is spawned
 * (0x0054B8D0) with the emitter's position (+0x2E4.. into +0x584..) and the batch is spliced into the live list
 * (0x005519F0 on +0x5C4, which takes the batch's first node in EAX too). Providers call +0x04 on +0x0C */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[0xd0 / 4]; } Particle_551A70;
DECOMP_C double __cdecl sub_005E420E(double x);                     /* floor */
DECOMP_C void __thiscall sub_0054AD50(void *self);
DECOMP_C void __thiscall sub_00550360(void *self, int n, Particle_551A70 proto);
DECOMP_C void __thiscall sub_0054B8D0(void *self, void *p);
DECOMP_C void __cdecl sub_005519F0(void *self, void *eax, void *where, void *list, void *first, void *last);
DECOMP_C char d_0068AE28[];
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef char (__thiscall *flag_551A70)(void *obj, void *self);
typedef float (__thiscall *num_551A70)(void *obj, void *self);

#define F(o) (*(float *)(s + (o)))
#define RM (*(double *)d_0068AE28)
#define NUM(p) ((num_551A70)((void **)(p))[1])(((void **)(p))[3], p)

DECOMP(00551A70)
void __thiscall f_00551A70(void *this)
{
    char *s = (char *)this, *p = s + 0x24c, **first, **node;
    float now, lo, hi, acc, nf, t, tnow;
    int n, idx, k, r;
    if (!((flag_551A70)((void **)p)[1])(((void **)p)[3], p))
        return;
    now = F(0x5e4);
    if (!(now - F(0x5ec) < F(0x28c))) {
        lo = (float)(double)*(unsigned int *)(s + 0x26c);
        hi = (float)(double)*(unsigned int *)(s + 0x27c);
        r = imp_00607400();
        now = F(0x5e4);
        *(unsigned int *)(s + 0x5ec) = *(unsigned int *)(s + 0x5e4);
        F(0x5e8) = (float)(lo + (double)r * (hi - lo) / RM);
    }
    acc = (now - F(0x5e0)) * F(0x5e8) + F(0x5fc);
    n = (int)(long long)(float)sub_005E420E(acc);
    nf = (float)n;
    idx = 0;
    F(0x5fc) = acc - nf;
    if (n != 0) {
        double d = nf;
        float c = NUM(s + 0x29c);
        idx = (int)(long long)(d / (c * d));
    }
    if (NUM(s + 0x29c) == 0.0f)
        idx = 0;
    if (*(int *)(s + 0x5d8) < n) {
        Particle_551A70 proto;
        sub_0054AD50(&proto);
        sub_00550360(s + 0x5d0, n, proto);
    }
    first = (char **)**(char ***)(s + 0x5d4);
    *(unsigned int *)(s + 0x584) = *(unsigned int *)(s + 0x2e4);
    *(unsigned int *)(s + 0x588) = *(unsigned int *)(s + 0x2e8);
    *(unsigned int *)(s + 0x58c) = *(unsigned int *)(s + 0x2ec);
    node = first;
    for (k = 1; n > 0; n--, k++) {
        sub_0054B8D0(this, node + 2);
        if (k == idx) {
            tnow = F(0x5e4);
            t = *(float *)((char *)node + 0x44) + tnow;
            r = imp_00607400();
            k = 0;
            *(float *)((char *)node + 0x4c) = (float)(tnow + (double)r * (t - tnow) / RM);
        }
        node = (char **)node[0];
    }
    sub_005519F0(s + 0x5c4, first, *(void **)(s + 0x5c8), s + 0x5d0, first, node);
}
