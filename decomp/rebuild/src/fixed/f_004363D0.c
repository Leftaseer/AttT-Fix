/* 0x004363D0: camera placement update; every rotation angle is scaled by the double pi/180 and rounded to
 * float before sin/cos, and both CRT results are rounded to float before the products. The decompiler used the
 * float rounding of pi/180 and kept the products in extended precision. */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 004363D0 custom */

DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_00608528[], d_00609848[], d_0060984C[], d_0068AE18[], d_006BFA58[], d_006C8910[], d_006C8914[], d_006C8918[], d_006C891C[];
DECOMP_C undefined4 __stdcall sub_00433620(void);
DECOMP_C undefined4 __stdcall sub_00435C50(void);
DECOMP_C undefined4 __stdcall sub_00435CF0(void);
DECOMP_C void __thiscall sub_00452A70(void *p0, float *p1);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C undefined4 __thiscall sub_00457B00(void *p0, float *p1);
DECOMP_C void *__stdcall sub_005B8020(void *out, void *a, void *b);
DECOMP_C void *__stdcall sub_005B805C(void *p0, void *p1, void *p2, void *p3);
DECOMP_C void *__stdcall sub_005B806E(void *p0, float p1, float p2, float p3, float p4);

DECOMP(004363D0)
undefined4 __cdecl f_004363D0(_CCamera *this, void *in_eax, char param_3)
{
#define local_70 (*(float *)(gh_frame + 0))
#define local_64 (*(float *)(gh_frame + 12))
#define local_60 (*(float *)(gh_frame + 16))
#define local_5c (*(float *)(gh_frame + 20))
#define fStack_58 (*(float *)(gh_frame + 24))
#define fStack_54 (*(float *)(gh_frame + 28))
#define fStack_50 (*(float *)(gh_frame + 32))
#define fStack_4c (*(float *)(gh_frame + 36))
#define fStack_48 (*(float *)(gh_frame + 40))
#define fStack_44 (*(float *)(gh_frame + 44))
#define afStack_40 (*(float (*)[16])(gh_frame + 48))
#define GV_00608528_8 (*(double *)d_00608528)
#define GV_00609848_4 (*(float *)d_00609848)
#define GV_0060984C_4 (*(float *)d_0060984C)
#define GV_0068AE18_8 (*(double *)d_0068AE18)
#define GV_006C8910_4 (*(float *)d_006C8910)
#define GV_006C8914_4 (*(float *)d_006C8914)
#define GV_006C8918_4 (*(float *)d_006C8918)
#define GV_006C891C_4 (*(unsigned int *)d_006C891C)
  unsigned char gh_frame[112] __attribute__((aligned(16)));
  float *pfVar1;
  void *pvVar2;
  int iVar3;
  float fVar6;
  float *pfVar7;

  if (this->field64_0x70 != '\0') {
    if ((GV_006C891C_4 & 1) == 0) {
      GV_006C891C_4 = GV_006C891C_4 | 1;
    }
    local_70 = this->field59_0x5c;
    if ((local_70 < GV_0060984C_4) && (GV_00609848_4 < local_70)) {
      local_70 = GV_0060984C_4;
    }
    {
      volatile float ang_y = local_70 * GV_00608528_8;
      volatile float cos_y = (float)decomp_CIcos(ang_y);
      volatile float ang_x = this->field60_0x60 * GV_00608528_8;
      volatile float sin_x = (float)decomp_CIsin(ang_x);
      volatile float t;

      GV_006C8910_4 = -((float)sin_x * (float)cos_y);
      t = (float)decomp_CIsin(ang_y);
      GV_006C8914_4 = t;
      t = (float)decomp_CIcos(ang_x);
      GV_006C8918_4 = t * (float)cos_y;
    }
    local_64 = this->field56_0x50;
    local_60 = this->field57_0x54;
    local_5c = this->field58_0x58;
    if (this->field236_0x218 != '\0') {
      pvVar2 = (void *)sub_00433620();
      fVar6 = sub_00473110(pvVar2, local_64, local_5c);
      local_60 = fVar6 + local_60;
    }
    pfVar1 = &this->field53_0x44;
    fStack_44 = this->field62_0x68;
    fStack_4c = fStack_44 * -GV_006C8910_4;
    fStack_48 = -GV_006C8914_4 * fStack_44;
    fStack_44 = fStack_44 * -GV_006C8918_4;
    fStack_58 = fStack_4c + local_64;
    *pfVar1 = fStack_58;
    fStack_54 = fStack_48 + local_60;
    this->field54_0x48 = fStack_54;
    fStack_50 = fStack_44 + local_5c;
    this->field55_0x4c = fStack_50;
    if (this->field232_0x211 != '\0') {
      pvVar2 = (void *)sub_00433620();
      fVar6 = sub_00473110(pvVar2, *pfVar1, this->field55_0x4c);
      fVar6 = BITCAST(float, (this->field235_0x214)) + fVar6;
      if (this->field54_0x48 < fVar6) {
        this->field54_0x48 = fVar6;
      }
      fVar6 = BITCAST(float, (this->field235_0x214)) + (float)GV_0068AE18_8;
      if (this->field54_0x48 < fVar6) {
        this->field54_0x48 = fVar6;
      }
    }
    if (this->field243_0x228 != '\0') {
      pfVar7 = pfVar1;
      pvVar2 = (void *)sub_00435CF0();
      sub_00452A70(pvVar2, pfVar7);
    }
    fStack_4c = *pfVar1 + GV_006C8910_4;
    fStack_48 = this->field54_0x48 + GV_006C8914_4;
    fStack_44 = this->field55_0x4c + GV_006C8918_4;
    this->field240_0x21c = fStack_4c;
    this->field241_0x220 = fStack_48;
    this->field242_0x224 = fStack_44;
    in_eax = sub_005B805C(&this->field76_0x88, pfVar1, &this->field240_0x21c, ((void *)d_006BFA58));
    this->field64_0x70 = 0;
    this->field231_0x210 = 1;
    this->field229_0x208 = 0;
  }
  if (this->field65_0x71 != '\0') {
    local_64 = this->field56_0x50;
    local_60 = this->field57_0x54;
    local_5c = this->field58_0x58;
    if (this->field236_0x218 != '\0') {
      pvVar2 = (void *)sub_00433620();
      fVar6 = sub_00473110(pvVar2, local_64, local_5c);
      local_60 = fVar6 + local_60;
    }
    in_eax = sub_005B805C(&this->field76_0x88, &this->field53_0x44, &local_64, ((void *)d_006BFA58));
    this->field65_0x71 = 0;
    this->field231_0x210 = 1;
    this->field229_0x208 = 0;
  }
  if (this->field72_0x84 != '\0') {
    in_eax = sub_005B806E
                       (&this->field95_0xc8, this->field68_0x74 * GV_00608528_8,
                        this->field71_0x80, this->field69_0x78, this->field70_0x7c);
    this->field72_0x84 = 0;
    this->field231_0x210 = 1;
    this->field229_0x208 = 0;
  }
  if (this->field231_0x210 != '\0') {
    if (param_3 != '\0') {
      iVar3 = sub_00435C50();
      in_eax = (void *)(iVar3 + 8);
      if (*(char *)(iVar3 + 0x18) != '\0') {
        sub_005B8020(afStack_40, &this->field76_0x88, &this->field95_0xc8);
        in_eax = (void *)sub_00457B00(this->field230_0x20c, afStack_40);
      }
    }
    this->field231_0x210 = 0;
  }
  return (undefined4)in_eax;
#undef GV_006C891C_4
#undef GV_006C8918_4
#undef GV_006C8914_4
#undef GV_006C8910_4
#undef GV_0068AE18_8
#undef GV_0060984C_4
#undef GV_00609848_4
#undef GV_00608528_8
}
