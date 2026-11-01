/* 0x0054B2D0: fills a scene object's transform fields.  The reciprocals are x87 divisions of 1 by a float
 * that MSVC rounds once, when the field is stored; `1.0 / x` in the generated code divides in double instead
 * and the second rounding moves the stored float by 1 ulp (this+0x94 in the failing case). */
#include "auto_pre.h"
/* @func 0054B2D0 */
#define sub_00607400 (*imp_00607400)
#define GV_0061B560_8 (*(double *)d_0061B560)
#define GV_0068AE10_8 (*(double *)d_0068AE10)
#define GV_0068AE28_8 (*(double *)d_0068AE28)
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
DECOMP_C char d_0061B560[];
DECOMP_C char d_0068AE10[];
DECOMP_C char d_0068AE28[];
DECOMP_C undefined4 __thiscall sub_0054B210(void *p0, float p1);

DECOMP(0054B2D0)
void __thiscall f_0054B2D0(void *this, undefined4 *param_1, undefined4 *param_2, undefined4 *param_3, undefined4 *param_4, float param_5, float param_6, float param_7, float param_8, float param_9, float param_10, ushort param_11, float param_12, float param_13)
{
  undefined4 uVar1;
  int iVar2;

  *(undefined4 *)((int)this + 0x98) = *param_1;
  *(undefined4 *)((int)this + 0x9c) = param_1[1];
  *(undefined4 *)((int)this + 0xa0) = param_1[2];
  *(undefined4 *)((int)this + 0xa4) = *param_2;
  *(undefined4 *)((int)this + 0xa8) = param_2[1];
  *(undefined4 *)((int)this + 0xac) = param_2[2];
  *(undefined4 *)((int)this + 0xb0) = *param_3;
  *(undefined4 *)((int)this + 0xb4) = param_3[1];
  *(undefined4 *)((int)this + 0xb8) = param_3[2];
  *(undefined4 *)((int)this + 0xc0) = *param_4;
  *(undefined4 *)((int)this + 0xc4) = param_4[1];
  *(undefined4 *)((int)this + 200) = param_4[2];
  uVar1 = param_4[3];
  *(float *)((int)this + 0x48) = param_6;
  *(float *)((int)this + 0x4c) = param_7;
  *(float *)((int)this + 0x50) = param_8;
  *(float *)((int)this + 0x54) = param_9;
  *(float *)((int)this + 0x58) = 1.0f / param_6;
  *(float *)((int)this + 0x6c) = param_12;
  *(float *)((int)this + 0x74) = param_12;
  *(undefined4 *)((int)this + 0xcc) = uVar1;
  *(float *)((int)this + 0x70) = param_13;
  *(float *)((int)this + 0x3c) = param_5;
  *(float *)((int)this + 0x5c) = 1.0f / param_7;
  *(float *)((int)this + 0x60) = 1.0f / param_8;
  *(float *)((int)this + 100) = 1.0f / param_9;
  *(float *)((int)this + 0x40) = 1.0f / param_5;
  { volatile float ratio = param_5 / (float)param_11;
    *(float *)((int)this + 0x90) = ratio;
    *(float *)((int)this + 0x94) = 1.0f / ratio; }
  iVar2 = sub_00607400();
  *(float *)((int)this + 0x78) =
       (((float)iVar2 * (GV_0061B560_8 - 0.0)) / GV_0068AE28_8 + 0.0) /
       GV_0068AE10_8;
  sub_0054B210(this,param_10);
  return;
}
#undef sub_00607400
#undef GV_0061B560_8
#undef GV_0068AE10_8
#undef GV_0068AE28_8
