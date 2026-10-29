/* 0x0058DDD0: ChooseHeroScene::vf15 (scene name, two unused args): becomes the current scene (0x006CA990 = this + 4,
 * or 0x0044E5A0 without this), the base loads it (0x00584190 with a nil table); its GUIScene entry (0x00437870) gives
 * the clear colour (clearColor[1..3] truncated into the bytes of 0xFFRRGGBB, the world's +0xA0) and the camera
 * (0x00424E70, kept at +0x194): its "cameraInfo" target (cx, cy, cz: +0x50), angles (ax, ay, az: +0x5C) and distance
 * ("dist", +0x68), fixed +0x70, limits 0x0060B878 / 0x0068AE40 / 0x0060B080 / 0x0061F5AC (+0x74..+0x80) and +0x84,
 * no motion (+0x211, +0x214); it updates (its +4's vf18) and its matrices (0x00435550, 0x44 bytes) are copied to +0x1B8
 * and +0xA8. Returns what the original leaves in EAX */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_58DDD0;                 /* nScript::Table */
DECOMP_C void *__cdecl sub_0044E5A0(void);
DECOMP_C void __thiscall sub_00584190(void *self, void *name, Tbl_58DDD0 *t, int a);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00437870(void *self, Tbl_58DDD0 *out, void *name);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, Tbl_58DDD0 *out, const char *key);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C char d_006CA990[], d_00607CC4[], d_0060AD08[], d_0061F5B0[], d_0060E72C[], d_0061F0EC[], d_0061F0E8[],
    d_0061F0E4[], d_0061F0E0[], d_0061F0DC[], d_0061F0D8[], d_006099F8[], d_0060B878[], d_0068AE40[], d_0060B080[],
    d_0061F5AC[];
typedef int (__thiscall *vf_58DDD0)(void *self);

DECOMP(0058DDD0)
int __thiscall f_0058DDD0(void *this, void *name, unsigned int a2, unsigned int a3)
{
    char *s = (char *)this, *cam, *o;
    Tbl_58DDD0 nil, t, sc, cc, ci;
    unsigned int col, m[0x44 / 4];
    float ax, ay, az, cx, cy, cz, dist;
    *(void **)d_006CA990 = s ? s + 4 : sub_0044E5A0();
    nil.w[1] = 0;
    nil.w[0] = (unsigned int)d_00607CC4;
    nil.w[2] = 0xffffffff;
    sub_00584190(this, name, &nil, 0);
    sub_004220A0(&nil);
    sub_00437870(sub_004323E0(&t, d_0060AD08), &sc, name);
    sub_004220A0(&t);
    sub_0057B4E0(&sc, &cc, d_0061F5B0);
    col = ((unsigned char)(int)sub_0057AC90(&cc, 1) | 0xffffff00) << 8;
    col = ((unsigned char)(int)sub_0057AC90(&cc, 2) | col) << 8;
    col = (unsigned char)(int)sub_0057AC90(&cc, 3) | col;
    *(unsigned int *)(sub_0042F160() + 0xa0) = col;
    sub_0057B4E0(&sc, &ci, d_0060E72C);
    *(char **)(s + 0x194) = sub_00424E70();
    ax = sub_0057AD40(&ci, d_0061F0EC);
    ay = sub_0057AD40(&ci, d_0061F0E8);
    az = sub_0057AD40(&ci, d_0061F0E4);
    cx = sub_0057AD40(&ci, d_0061F0E0);
    cy = sub_0057AD40(&ci, d_0061F0DC);
    cz = sub_0057AD40(&ci, d_0061F0D8);
    dist = sub_0057AD40(&ci, d_006099F8);
    cam = *(char **)(s + 0x194);
    *(float *)(cam + 0x68) = dist;
    *(float *)(cam + 0x50) = cx;
    *(float *)(cam + 0x54) = cy;
    *(float *)(cam + 0x5c) = ax;
    *(float *)(cam + 0x58) = cz;
    *(float *)(cam + 0x60) = ay;
    *(float *)(cam + 0x64) = az;
    cam[0x70] = 1;
    cam = *(char **)(s + 0x194);
    *(unsigned int *)(cam + 0x74) = *(unsigned int *)d_0060B878;
    *(unsigned int *)(cam + 0x78) = *(unsigned int *)d_0068AE40;
    *(unsigned int *)(cam + 0x7c) = *(unsigned int *)d_0060B080;
    *(unsigned int *)(cam + 0x80) = *(unsigned int *)d_0061F5AC;
    cam[0x84] = 1;
    cam = *(char **)(s + 0x194);
    cam[0x211] = 0;
    *(float *)(cam + 0x214) = 0;
    o = *(char **)(s + 0x194) + 4;
    ((vf_58DDD0)(*(void ***)o)[0x18 / 4])(o);
    cam = *(char **)(s + 0x194);
    __builtin_memcpy(s + 0x1b8, sub_00435550(cam, m), 0x44);
    __builtin_memcpy(s + 0xa8, sub_00435550(cam, m), 0x44);
    sub_004220A0(&ci);
    sub_004220A0(&cc);
    return sub_004220A0(&sc);
}
