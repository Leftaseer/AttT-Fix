/* 0x005886A0: a GUI element's setup with an optional icon: the base (0x00587690, the first nine arguments); with an
 * icon name (s10 not "") a new icon element (0x294 bytes, 0x00585680 at (x12, y13) inside, offset by the element's
 * x (0x00587470) + x14 and y (0x00587490) + y15, with s10 and f11) replaces the reference-counted one at +0x2C4 (its
 * place kept at +0x2C8) and is registered with the GUI (0x8D1230 +4 vf10); the element itself is registered too (+4
 * vf10, +0x54 vf04) (the original frees the icon if its constructor throws; this C does not) */
/* @conv ECX 60 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00587690(void *self, float a, float b, float c, void *s4, void *s5, unsigned int d6,
                                      void *s7, float f8, unsigned int d9);
DECOMP_C float __thiscall sub_00587490(void *self);
DECOMP_C float __thiscall sub_00587470(void *self);
DECOMP_C void *__thiscall sub_00585680(void *self, float x, float y, float ox, float oy, void *name, float f);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_0060FA8B[], d_008D1230[];
DECOMP_C int (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *dtor_5886A0)(void *self, int flags);
typedef void (__thiscall *reg_5886A0)(void *self, void *o);

#define GUI (*(char **)d_008D1230)

DECOMP(005886A0)
void __thiscall f_005886A0(void *this, float a, float b, float c, void *s4, void *s5, unsigned int d6, void *s7,
                           float f8, unsigned int d9, void *s10, float f11, float x12, float y13, float x14, float y15)
{
    char *s = (char *)this;
    sub_00587690(this, a, b, c, s4, s5, d6, s7, f8, d9);
    if ((char)imp_00607214(s10, d_0060FA8B)) {
        char *icon = sub_005E3EAE(0x294), *old;
        if (icon) {
            float oy = sub_00587490(this) + y15;
            float ox = sub_00587470(this) + x14;
            icon = sub_00585680(icon, x12, y13, ox, oy, s10, f11);
        }
        if (icon)
            ++*(int *)(icon + 4);
        old = *(char **)(s + 0x2c4);
        if (old && --*(int *)(old + 4) == 0)
            ((dtor_5886A0)(*(void ***)old)[0])(old, 1);
        *(char **)(s + 0x2c4) = icon;
        *(float *)(s + 0x2c8) = x12;
        *(float *)(s + 0x2cc) = y13;
        if (!GUI)
            return;
        ((reg_5886A0)(*(void ***)(GUI + 4))[0x10 / 4])(GUI + 4, *(void **)(s + 0x2c4));
    }
    if (GUI) {
        ((reg_5886A0)(*(void ***)(GUI + 4))[0x10 / 4])(GUI + 4, this);
        ((reg_5886A0)(*(void ***)(GUI + 0x54))[1])(GUI + 0x54, this);
    }
}
