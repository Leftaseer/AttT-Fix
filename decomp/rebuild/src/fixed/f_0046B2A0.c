/* 0x0046B2A0: nGUI::iDragged::Update(dt): the base update (0x00582870, given the EAX the original leaves: its SEH
 * link); while a press waits (+0x2AC) a mouse move beyond the threshold at 0x60B7B0 from the press (+0x2B0, +0x2B4;
 * the mouse 0x00421680: vf8C, vf90) starts the drag: registered with the drag manager (0x6C901C, 0x0046AA00 with the
 * callback 0x46B200) and its script's "_BeginDrag" (+0x2B8) called with its table (+0x214) when it is a function,
 * then vf11C */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00582870(void *self, unsigned int eax, float dt);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void __cdecl sub_0046AA00(void *self, unsigned int eax, void *o, void *cb);
DECOMP_C int __thiscall sub_0057C660(void *t, const char *key);
DECOMP_C void *__thiscall sub_0057B770(void *t, void *out, const char *key);
DECOMP_C void *__thiscall sub_0057D070(void *self, void *t);
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void __thiscall sub_00422000(void *self);
DECOMP_C char d_0060B7B0[], d_006C901C[], d_0046B200[], d_0060C788[], d_0060826C[], d_00607CB8[];
typedef double (__thiscall *vfpos_46B2A0)(void *self);
typedef void (__thiscall *vf_46B2A0)(void *self);

DECOMP(0046B2A0)
void __thiscall f_0046B2A0(void *this, float dt)
{
    char *s = (char *)this;
    void **m;
    float dx, dy;
    sub_00582870(this, (unsigned int)GH_FS0, dt);
    if (!s[0x2ac])
        return;
    m = (void **)sub_00421680();
    dx = __builtin_fabsf((float)(((vfpos_46B2A0)(*(void ***)m)[0x8c / 4])(m) - *(float *)(s + 0x2b0)));
    m = (void **)sub_00421680();
    dy = __builtin_fabsf((float)(((vfpos_46B2A0)(*(void ***)m)[0x90 / 4])(m) - *(float *)(s + 0x2b4)));
    if (!(dx > *(float *)d_0060B7B0 || dy > *(float *)d_0060B7B0))
        return;
    s[0x2ac] = 0;
    sub_0046AA00(d_006C901C, (unsigned int)d_0046B200, this, d_0046B200);
    if (sub_0057C660(s + 0x2b8, d_0060C788) == 6) {          /* "_BeginDrag" is a function */
        unsigned int guard[3], fn[8], res[8];
        void *f;
        guard[1] = 0;
        guard[0] = (unsigned int)d_0060826C;
        guard[2] = 0;
        f = sub_0057B770(s + 0x2b8, fn, d_0060C788);
        sub_0057A230(f, res, sub_0057D070(guard, s + 0x214), 0);
        sub_00427820(res);
        sub_004378D0(fn);
        guard[0] = (unsigned int)d_00607CB8;
        sub_00422000(guard);
        ((vf_46B2A0)(*(void ***)this)[0x11c / 4])(this);
    }
}
