/* 0x005191A0: runs the battle screen's current step (+0x110) and returns what follows it: 0 clears the script's
 * TacticLevel.Scene (0x0057C220) and returns +0x3C; 1-4 update the screen (vf18) inside a timing scope (a 0x224-byte
 * object, 0x0043A280 / 0x0043A320 / 0x0043A310) with the renderer (0x00421730) begun and ended (0x00430350 /
 * 0x00430430), after (but for 4) giving the view (+0x11C vfE8) the camera +0x12C; 1 returns +0x114, the others +0x21C;
 * any other step returns 0 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_0057C220(void *self, const char *key);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0043A280(void *self);
DECOMP_C void __thiscall sub_0043A320(void *self);
DECOMP_C void __thiscall sub_0043A310(void *self);
DECOMP_C void *__cdecl sub_00421730(void);
DECOMP_C void __thiscall sub_00430350(void *self);
DECOMP_C void __thiscall sub_00430430(void *self);
DECOMP_C char d_0060AB58[], d_00613FD8[];
typedef void (__thiscall *vf_5191A0)(void *self);
typedef void (__thiscall *cam_5191A0)(void *self, void *cam);

DECOMP(005191A0)
void *__thiscall f_005191A0(void *this)
{
    char *s = (char *)this;
    unsigned int t[3];
    unsigned int scope[0x224 / 4];
    void **v, *g, *r;
    int step = *(int *)(s + 0x110);
    if ((unsigned int)step > 4)
        return 0;
    if (step == 0) {
        sub_0057C220(sub_004323E0(t, d_0060AB58), d_00613FD8);
        sub_004220A0(t);
        return *(void **)(s + 0x3c);
    }
    sub_0043A280(scope);
    if (step != 4) {
        v = *(void ***)(s + 0x11c);
        ((cam_5191A0)(*(void ***)v)[0xe8 / 4])(v, *(void **)(s + 0x12c));
    }
    g = sub_00421730();
    sub_00430350(g);
    ((vf_5191A0)(*(void ***)this)[0x18 / 4])(this);
    sub_0043A320(scope);
    sub_00430430(g);
    r = *(void **)(s + (step == 1 ? 0x114 : 0x21c));
    sub_0043A310(scope);
    return r;
}
