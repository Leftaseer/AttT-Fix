/* 0x00504D70: places an army (a; its owner b): keeps both (+0xE8, the owner's +0x2C8 at +0xEC), 0x00503D20(a, b),
 * the formation (+0xF0: 0x004FB950 with a copy of the container at +0x11C, by value, and 0), then for each group of
 * the map at +0x120 (nil flag +0x1D) each unit of its list (+0x14) goes to the group's target (+0xC) with a delay
 * (0x00512840): the first group 0, the others a random 0..7 (rand() % 8), each unit after the first another random
 * 0..7 on top; finally the state +0x64 = 4 */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int d[3]; } C12_504D70;
DECOMP_C void __thiscall sub_00503D20(void *self, unsigned int a, void *b);
DECOMP_C void __thiscall sub_005019E0(C12_504D70 *self, void *src);
DECOMP_C void __thiscall sub_004FB950(void *self, C12_504D70 c, unsigned int z);
DECOMP_C void __thiscall sub_00512840(void *self, void *target, int delay);
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");

#define NIL(n) (((char *)(n))[0x1d])

DECOMP(00504D70)
void __thiscall f_00504D70(void *this, unsigned int a, char *b)
{
    char *s = (char *)this;
    char **n;
    C12_504D70 c;
    unsigned int g = 0;
    *(unsigned int *)(s + 0xe8) = a;
    *(unsigned int *)(s + 0xec) = *(unsigned int *)(b + 0x2c8);
    sub_00503D20(this, a, b);
    sub_005019E0(&c, s + 0x11c);
    sub_004FB950(*(void **)(s + 0xf0), c, 0);
    for (n = **(char ****)(s + 0x120); n != *(char ***)(s + 0x120); g++) {
        int base = g ? imp_00607400() % 8 : 0;
        char **head = (char **)n[5], **u;
        void *target = n[3];
        int j = 0;
        for (u = (char **)*head; u != (char **)n[5]; u = (char **)*u, j++)
            sub_00512840(u[2], target, j ? imp_00607400() % 8 + base : base);
        if (!NIL(n)) {                                  /* ++it */
            char **r = (char **)n[2];
            if (!NIL(r)) {
                while (!NIL(*r))
                    r = (char **)*r;
                n = r;
            } else {
                char **p = (char **)n[1];
                while (!NIL(p) && n == (char **)p[2]) {
                    n = p;
                    p = (char **)p[1];
                }
                n = p;
            }
        }
    }
    *(int *)(s + 0x64) = 4;
}
