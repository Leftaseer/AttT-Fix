/* 0x0050E550: the battle's hover update for the unit under the cursor (+0xB4's +0x1D4 into +0xB0): casting (+0x158)
 * a spell (+0x1C0 vf68) that can target it shows the spell cursor (+0x1FC on +0x70 vfE8, state +0x9C = 4) and marks it
 * (its board +0x2C8, 0x0051F5F0; +0x1C0 vf8C), else the no cursor (+0x200, state 0); otherwise a unit that is not an
 * enemy (0x00511A80 not 1) gets +0x1E4 (state 3); an enemy the selected unit (+0x64) can reach (0x0051DBF0 on the
 * board's +0x98, Shift not held (+0x6C key states +0x72 / +0x7E) when +0x1C8) gets state 5 with its reach shown
 * (0x00503D20 / 0x00504400 on +0xD8, 0x0050E2D0) and the "Arrow" cursor (named, 0x00443460) or +0x1F4; out of reach,
 * state 0 with "ArrowInactive" for a shooter (+0x48) or +0x1F8. The board is kept (+0x210) and refreshed (0x0051DA30,
 * its EAX input only passed through) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0051F5F0(void *self, void *unit);
DECOMP_C int __thiscall sub_00511A80(void *self);
DECOMP_C char __thiscall sub_0051DBF0(void *self, void *map, int a);
DECOMP_C void __thiscall sub_00503D20(void *self, void *unit, void *target);
DECOMP_C void __thiscall sub_00504400(void *self, void *unit, void *target);
DECOMP_C void __thiscall sub_0050E2D0(void *self, void *a1, void *unit, int a3, unsigned char board);
DECOMP_C void __thiscall sub_00443460(void *self, void *name);
DECOMP_C void __cdecl sub_0051DA30(void *self, unsigned int eax);
DECOMP_C char d_00608C28[], d_0060A474[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef char (__thiscall *can_50E550)(void *self, void *unit);
typedef void (__thiscall *vf_50E550)(void *self);
typedef void (__thiscall *cur_50E550)(void *self, void *c);

#define U (*(char **)(s + 0xb0))
#define SEL (*(char **)(s + 0x64))

static void cursor_50E550(char *s, unsigned int o)
{
    void **c = *(void ***)(s + 0x70);
    ((cur_50E550)(*(void ***)c)[0xe8 / 4])(c, *(void **)(s + o));
}

static void named_50E550(char *s, const char *n)
{
    unsigned int name[7];
    imp_00607324(name, n);
    sub_00443460(*(void **)(s + 0x70), name);
    imp_00607330(name);
}

static int noshift_50E550(char *s)
{
    char *kb = *(char **)(s + 0x6c);
    return s[0x1c8] && !(kb[0x72] & 0x80) && !(kb[0x7e] & 0x80);
}

DECOMP(0050E550)
void __thiscall f_0050E550(void *this)
{
    char *s = (char *)this;
    void **sp;
    U = *(char **)(*(char **)(s + 0xb4) + 0x1d4);
    if (s[0x158]) {
        sp = *(void ***)(s + 0x1c0);
        if (((can_50E550)(*(void ***)sp)[0x68 / 4])(sp, U)) {
            *(int *)(s + 0x9c) = 4;
            cursor_50E550(s, 0x1fc);
            sub_0051F5F0(*(void **)(U + 0x2c8), U);
            sp = *(void ***)(s + 0x1c0);
            ((vf_50E550)(*(void ***)sp)[0x8c / 4])(sp);
        } else {
            *(int *)(s + 0x9c) = 0;
            cursor_50E550(s, 0x200);
        }
    } else if (sub_00511A80(U) != 1) {
        *(int *)(s + 0x9c) = 3;
        cursor_50E550(s, 0x1e4);
    } else if (sub_0051DBF0(SEL, *(void **)(*(char **)(U + 0x2c8) + 0x98), noshift_50E550(s))) {
        *(int *)(s + 0x9c) = 5;
        if (SEL[0x48] && noshift_50E550(s)) {
            sub_00503D20(*(void **)(s + 0xd8), SEL, U);
            sub_0050E2D0(this, SEL, U, 0, 0);
            named_50E550(s, d_00608C28);
        } else {
            sub_00504400(*(void **)(s + 0xd8), SEL, U);
            sub_0050E2D0(this, SEL, U, 1, 0);
            cursor_50E550(s, 0x1f4);
        }
    } else {
        *(int *)(s + 0x9c) = 0;
        if (SEL[0x48])
            named_50E550(s, d_0060A474);
        else
            cursor_50E550(s, 0x1f8);
    }
    *(void **)(s + 0x210) = *(void **)(U + 0x2c8);
    sub_0051DA30(*(void **)(U + 0x2c8), 0);
}
