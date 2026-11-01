#include "auto_pre.h"
/* @func 0043C340 custom */
DECOMP_C char d_0060A0D8[];
DECOMP_C undefined4 __thiscall sub_0043F770(void * p0, float * p1);
DECOMP_C undefined4 __cdecl sub_004402A0(undefined4 p0, undefined4 p1, int p2);
DECOMP_C float * __thiscall sub_00440A30(void * p0, float * p1, void * p2);
/* the two x87 'jbe' guards are true on unordered: !(a > b), not a <= b */
DECOMP(0043C340)
undefined4 __cdecl f_0043C340(undefined4 in_eax, void *param_2, void *param_3)
{
#define local_c (*(float (*)[2])(gh_frame + 0))
#define local_4 (*(float *)(gh_frame + 8))
#define GV_0060A0D8_8 (*(double *)d_0060A0D8)
  unsigned char gh_frame[12] __attribute__((aligned(16)));
  float *pfVar1;
  undefined4 uVar2;

  pfVar1 = (float *)sub_004402A0(param_3,in_eax,(int)param_2);
  if ((char)pfVar1 != '\0') {
    pfVar1 = sub_00440A30(param_3,local_c,param_2);
    if ((!(GV_0060A0D8_8 > ABS(local_c[0]))) || (!(GV_0060A0D8_8 > ABS(local_4)))) {
      uVar2 = sub_0043F770(param_2,local_c);
      return CONCAT31((undefined4)((uint)uVar2 >> 8),1);
    }
  }
  return (uint)pfVar1 & 0xffffff00;
#undef GV_0060A0D8_8
#undef local_4
#undef local_c
}
