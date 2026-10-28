/* 0x00464220: Lua binding that places the camera target (this) at the x, z of args 2 and 3 on the ground
 * (0x00473110 on the terrain 0x006CA2D0) with the angle of arg 4 (+0x78), after vf4C, and applies the script table
 * Camera.Presets.p1 to the camera (0x006CA2C4): "dist" (+0x68), "targetY" (+0x54), "angleX" (+0x5C) and the yaw
 * 0x006099D8 - angle - "angleY" (+0x60), each marking it changed (+0x70), then its +0x04 part's vf18; returns 0
 * (the original destroys the tables if one throws; this C does not) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_00464220;
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);     /* lua_tonumber */
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Tbl_00464220 *__thiscall sub_0057B4E0(void *self, Tbl_00464220 *out, void *key);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C char d_006CA2D0[], d_006CA2C4[], d_00609850[], d_00609B4C[], d_0060C07C[], d_006099F8[], d_006099E0[],
    d_006099E8[], d_006099F0[], d_006099D8[];
typedef void (__thiscall *vf_464220)(void *self);

#define CAM (*(char **)d_006CA2C4)

DECOMP(00464220)
int __thiscall f_00464220(void *this, void *L)
{
    char *s = (char *)this;
    float x, z, a, ay;
    unsigned int o64, o68, o6c;
    Tbl_00464220 t1, t2, t3;
    void *p;
    ((vf_464220)(*(void ***)this)[0x4c / 4])(this);
    x = (float)sub_00402DE0(L, 2);
    z = (float)sub_00402DE0(L, 3);
    o68 = *(unsigned int *)(s + 0x68);
    o64 = *(unsigned int *)(s + 0x64);
    o6c = *(unsigned int *)(s + 0x6c);
    *(float *)(s + 0x64) = x;
    *(float *)(s + 0x6c) = z;
    *(unsigned int *)(s + 0x58) = o64;
    *(unsigned int *)(s + 0x5c) = o68;
    *(unsigned int *)(s + 0x60) = o6c;
    *(unsigned int *)(s + 0x68) = 0;
    s[0x70] = 1;
    a = sub_00473110(*(void **)d_006CA2D0, x, z);
    *(float *)(s + 0x5c) = *(float *)(s + 0x68);
    s[0x70] = 1;
    *(float *)(s + 0x68) = a;
    *(float *)(s + 0x78) = (float)sub_00402DE0(L, 4);
    s[0x80] = 1;
    ((vf_464220)(*(void ***)this)[0x18 / 4])(this);
    p = sub_004323E0(&t1, d_00609850);
    p = sub_0057B4E0(p, &t2, d_00609B4C);
    sub_0057B4E0(p, &t3, d_0060C07C);
    sub_004220A0(&t2);
    sub_004220A0(&t1);
    a = sub_0057AD40(&t3, d_006099F8);
    *(float *)(CAM + 0x68) = a;
    CAM[0x70] = 1;
    a = sub_0057AD40(&t3, d_006099E0);
    *(float *)(CAM + 0x54) = a;
    CAM[0x70] = 1;
    a = sub_0057AD40(&t3, d_006099E8);
    *(float *)(CAM + 0x5c) = a;
    CAM[0x70] = 1;
    a = *(float *)(s + 0x78);
    ay = sub_0057AD40(&t3, d_006099F0);
    CAM[0x70] = 1;
    *(float *)(CAM + 0x60) = (float)(*(double *)d_006099D8 - a - ay);
    ((vf_464220)(*(void ***)(CAM + 4))[0x18 / 4])(CAM + 4);
    sub_004220A0(&t3);
    return 0;
}
