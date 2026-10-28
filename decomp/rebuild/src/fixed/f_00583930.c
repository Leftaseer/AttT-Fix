/* 0x00583930: a modal window's update (dt): the cursor (0x00421680, 0x00443460) is "Default", or this window's own
 * (+0x130) when the mouse (vf88) is outside the child +0x78 (left vf8C, top vf90, width +0x74, height +0x78); the
 * base update (0x004B1D10); when cancellable (+0xA5) a mouse button released (0x004215D0: +0x66C buttons, +0x670
 * their count) outside calls the script's "_OnCancel" (+0x98, 0x0057B770 / 0x0057A230 with an empty Object
 * argument). Returns what the original leaves in EAX */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void __thiscall sub_00443460(void *self, void *name);
DECOMP_C int __thiscall sub_004B1D10(void *self, float dt);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C char d_00607C00[], d_0060826C[], d_00607CB8[], d_0061E2CC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef unsigned int *(__thiscall *vfp_583930)(void *self);
typedef double (__thiscall *vfd_583930)(void *self);

DECOMP(00583930)
int __thiscall f_00583930(void *this, float dt)
{
    char *s = (char *)this, *inp;
    unsigned int name[7], *m, i, n, *keys;
    float mx, my, ext;
    char outside = 0;
    void **w, *c;
    int r;
    imp_00607324(name, d_00607C00);
    sub_00443460(sub_00421680(), name);
    imp_00607330(name);
    w = *(void ***)(s + 0x78);
    if (w) {
        c = sub_00421680();
        m = ((vfp_583930)(*(void ***)c)[0x88 / 4])(c);
        ((unsigned int *)&mx)[0] = m[0];
        ((unsigned int *)&my)[0] = m[1];
        if (((vfd_583930)(*(void ***)w)[0x8c / 4])(w) > mx)
            outside = 1;
        else if (w = *(void ***)(s + 0x78), ((vfd_583930)(*(void ***)w)[0x90 / 4])(w) > my)
            outside = 1;
        else if (w = *(void ***)(s + 0x78), ext = *(float *)((char *)w + 0x74),
                 mx > ((vfd_583930)(*(void ***)w)[0x8c / 4])(w) + ext)
            outside = 1;
        else if (w = *(void ***)(s + 0x78), ext = *(float *)((char *)w + 0x78),
                 my > ((vfd_583930)(*(void ***)w)[0x90 / 4])(w) + ext)
            outside = 1;
        if (outside)
            sub_00443460(sub_00421680(), s + 0x130);
    }
    r = sub_004B1D10(this, dt);
    if (!s[0xa5])
        return r;
    inp = sub_004215D0();
    n = *(unsigned int *)(inp + 0x670);
    keys = *(unsigned int **)(inp + 0x66c);
    r = (int)(size_t)inp;
    for (i = 0; i < n; i++) {
        r = (int)(size_t)keys;
        if (!keys[i] && outside) {
            struct { void *vt; void *child; int a; } o;
            unsigned int x[6], y[6];
            o.child = 0;
            o.vt = d_0060826C;
            o.a = 0;
            sub_0057A230(sub_0057B770(s + 0x98, x, d_0061E2CC), y, &o, 0);
            sub_00427820(y);
            sub_004378D0(x);
            o.vt = d_00607CB8;
            r = sub_00422000(&o);
        }
    }
    return r;
}
