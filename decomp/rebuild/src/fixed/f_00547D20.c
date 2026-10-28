/* 0x00547D20: CWorldUnit::Render: when the bounds (+0x258) are in the view frustum (0x006CA2C8, 0x00458120, which
 * takes the bounds in EAX too) renders the base (0x004AC890), picks the level of detail by the camera distance
 * (0x00463E20 on the position +0x64, the model's (+0x1F8) vfEC and +0x98) into +0x2D0 and below +0x2D4 sets it on
 * the model (vfC0; 100 when 0x006C88D8's +0x40 is set). The selection marker (+0x2D8), within the range 0x006CAAE4
 * (squared) of the camera (0x00424E70), gets its scale reset (+0x58 from +0x64, then 0x00608A70 / 0 / 0x00608A70;
 * +0x74 rotation 0) and updated (vf18), its world matrix (its +0x168 times the unit's, D3DXMatrixMultiply) set (also
 * left in 0x006CA0A4, a pointer to this frame) and is drawn (vf08) when its 8 transformed corners (vfEC) are in the
 * frustum. Returns what the original leaves in EAX on each path (callers read it) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00458120(void *self, void *eax, void *pos);
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);   /* D3DXMatrixMultiply */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C char d_006CA2C8[], d_006C88D8[], d_006CAAE4[], d_00608A70[], d_006C8C10[], d_006CA0A4[];
typedef void *(__thiscall *vf_547D20)(void *self);
typedef int (__thiscall *vfi_547D20)(void *self);
typedef int (__thiscall *lod_547D20)(void *self, int lod);
typedef long (__stdcall *xf_547D20)(void *dev, unsigned int state, void *m);

#define DEV (*(void ***)d_006C8C10)

DECOMP(00547D20)
int __thiscall f_00547D20(void *this)
{
    char *s = (char *)this;
    int r;
    void **mdl;
    char *cam, *o;
    float dx, dy, dz, d, m[16], c[24], *p;
    unsigned int k, i;
    r = sub_00458120(*(void **)d_006CA2C8, s + 0x258, s + 0x258);
    if ((char)r) {
        sub_004AC890(this);
        mdl = *(void ***)(s + 0x1f8);
        r = sub_00463E20(s + 0x64, ((vf_547D20)(*(void ***)mdl)[0xec / 4])(mdl), s + 0x98);
        *(int *)(s + 0x2d0) = r;
        if (r < *(int *)(s + 0x2d4)) {
            mdl = *(void ***)(s + 0x1f8);
            r = ((lod_547D20)(*(void ***)mdl)[0xc0 / 4])(mdl, (*(char **)d_006C88D8)[0x40] ? 100 : r);
        }
    }
    if (!*(void **)(s + 0x2d8))
        return r;
    cam = sub_00424E70() + 0x44;
    r = (int)(size_t)cam;
    dx = *(float *)(s + 0x64) - *(float *)cam;
    dy = *(float *)(s + 0x68) - *(float *)(cam + 4);
    dz = *(float *)(s + 0x6c) - *(float *)(cam + 8);
    d = dx * dx + dy * dy + dz * dz;
    if (!(*(float *)d_006CAAE4 > d))
        return r;
    o = *(char **)(s + 0x2d8);
    k = *(unsigned int *)d_00608A70;
    *(unsigned int *)(o + 0x58) = *(unsigned int *)(o + 0x64);
    *(unsigned int *)(o + 0x5c) = *(unsigned int *)(o + 0x68);
    *(unsigned int *)(o + 0x60) = *(unsigned int *)(o + 0x6c);
    *(unsigned int *)(o + 0x64) = k;
    *(unsigned int *)(o + 0x68) = 0;
    *(unsigned int *)(o + 0x6c) = k;
    o[0x70] = 1;
    o = *(char **)(s + 0x2d8);
    *(unsigned int *)(o + 0x74) = 0;
    *(unsigned int *)(o + 0x78) = 0;
    *(unsigned int *)(o + 0x7c) = 0;
    o[0x80] = 1;
    o = *(char **)(s + 0x2d8);
    ((vf_547D20)(*(void ***)o)[0x18 / 4])(o);
    sub_005B8020(m, *(char **)(s + 0x2d8) + 0x168, s + 0x168);
    ((xf_547D20)(*(void ***)DEV)[0xb0 / 4])(DEV, 0x100, m);
    *(float **)d_006CA0A4 = m;
    o = *(char **)(s + 0x2d8);
    __builtin_memcpy(c, ((vf_547D20)(*(void ***)o)[0xec / 4])(o), 0x60);
    for (i = 0, p = c; i < 8; i++, p += 3)
        r = (int)(size_t)sub_005B8026(p, p, m);
    r = sub_00458120(*(void **)d_006CA2C8, (void *)(size_t)r, c);
    if ((char)r) {
        o = *(char **)(s + 0x2d8);
        r = ((vfi_547D20)(*(void ***)o)[2])(o);
    }
    return r;
}
