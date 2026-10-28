/* 0x00467CD0: loads the hero from a saved script table (arg; this is the hero's interface at +0x1C8): from
 * HeroPos.pos the position (x, z: 0x004AC940) and the heading "roty" (+0x78) unless 0x006C8EFC asks to keep them
 * (then just cleared), the class "type" (+0x2E0 of the interface, truncated) and its name of
 * {"Warrior", "Mage", "Valkyr"} (a vector of 3 strings, 0x00466220 / 0x00434A60, whose EAX input only passes through)
 * into +0x08; updates (vf18), puts the camera (0x006CA2C4) on the hero when it follows (+0x4B4) and updates it (its
 * +0x04 vf18), and 0x005296B0 on the interface's +0x33C (the original destroys the tables if one throws; this C
 * does not); returns what the original leaves in EAX */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_004AC940(void *self, float x, float z);
DECOMP_C void __thiscall sub_00466220(void *self, unsigned int n);
DECOMP_C void __cdecl sub_00434A60(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_005296B0(void *self);
DECOMP_C char d_0060C090[], d_006098E8[], d_006C8EFC[], d_006098C8[], d_006098D0[], d_0060C098[], d_0068A2C4[],
    d_0060C384[], d_0060C37C[], d_0060C374[], d_006CA2C4[];
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef void (__thiscall *vf_467CD0)(void *self);

#define CAM (*(char **)d_006CA2C4)

DECOMP(00467CD0)
int __thiscall f_00467CD0(void *this, void *save)
{
    char *s = (char *)this, *hero = s - 0x1c8, *names;
    struct { void *tbl; const char *key; } p;
    unsigned int t0[3], h[3], pos[3], vec[4];
    float x, z;
    p.tbl = save;
    p.key = d_0060C090;
    sub_004369F0(&p, t0);
    sub_00435D90(h, t0);
    sub_004220A0(t0);
    p.tbl = h;
    p.key = d_006098E8;
    sub_004369F0(&p, t0);
    sub_00435D90(pos, t0);
    sub_004220A0(t0);
    if (!*d_006C8EFC) {
        z = sub_0057AD40(pos, d_006098C8);
        x = sub_0057AD40(pos, d_006098D0);
        sub_004AC940(hero, x, z);
        x = sub_0057AD40(pos, d_0060C098);
        hero[0x80] = 1;
        *(float *)(hero + 0x78) = x;
    } else
        *d_006C8EFC = 0;
    *(int *)(s + 0x2e0) = (int)(long long)sub_0057AD40(h, d_0068A2C4);
    sub_00466220(vec, 3);
    names = (char *)vec[1];
    imp_006072F8(names, d_0060C384);
    imp_006072F8(names + 0x1c, d_0060C37C);
    imp_006072F8(names + 0x38, d_0060C374);
    imp_0060731C(s - 0x1c0, names + *(int *)(s + 0x2e0) * 0x1c);
    ((vf_467CD0)(*(void ***)hero)[0x18 / 4])(hero);
    if (hero[0x4b4]) {
        *(unsigned int *)(CAM + 0x50) = *(unsigned int *)(hero + 0x64);
        CAM[0x70] = 1;
        *(unsigned int *)(CAM + 0x58) = *(unsigned int *)(hero + 0x6c);
        CAM[0x70] = 1;
    }
    ((vf_467CD0)(*(void ***)(CAM + 4))[0x18 / 4])(CAM + 4);
    sub_005296B0(*(void **)(s + 0x33c));
    sub_00434A60(vec, 0);
    sub_004220A0(pos);
    return sub_004220A0(h);
}
