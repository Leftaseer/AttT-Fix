#include "auto_pre.h"
DECOMP_C void * __stdcall sub_005B805C(void * p0, void * p1, void * p2, void * p3);
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_006BFA58[], d_00608528[], d_006C88F0[], d_006C88F4[], d_006C88F8[], d_006C88FC[];
/* @func 00435840 */
#define sub_005E4058 decomp_CIcos
#define sub_005E405E decomp_CIsin
#define G_006BFA58 d_006BFA58
#define GV_00608528_8 (*(double *)d_00608528)
#define GV_006C88F0_4 (*(float *)d_006C88F0)
#define GV_006C88F4_4 (*(float *)d_006C88F4)
#define GV_006C88F8_4 (*(float *)d_006C88F8)
#define GV_006C88FC_4 (*(unsigned int *)d_006C88FC)
DECOMP(00435840)
undefined4 __stdcall f_00435840(void *param_1, float *param_2, float *param_3, float param_4)
{
#define fStack_18 (*(float *)(gh_frame + 0))
#define fStack_14 (*(float *)(gh_frame + 4))
#define fStack_10 (*(float *)(gh_frame + 8))
#define fStack_c (*(float *)(gh_frame + 12))
#define fStack_8 (*(float *)(gh_frame + 16))
#define fStack_4 (*(float *)(gh_frame + 20))
  unsigned char gh_frame[24] __attribute__((aligned(16)));
  float10 fVar1;
  float10 fVar2;
  
  if ((GV_006C88FC_4 & 1) == 0) {
    GV_006C88FC_4 = GV_006C88FC_4 | 1;
  }
  fVar1 = sub_005E4058((float10)GH_FROUND((*param_3 * GV_00608528_8)));
  fVar2 = sub_005E405E((float10)GH_FROUND((param_3[1] * GV_00608528_8)));
  GV_006C88F0_4 = -(GH_FROUND((float)fVar2) * GH_FROUND((float)fVar1));
  fVar1 = sub_005E405E((float10)GH_FROUND((*param_3 * GV_00608528_8)));
  GV_006C88F4_4 = (float)fVar1;
  fVar1 = sub_005E4058((float10)GH_FROUND((*param_3 * GV_00608528_8)));
  fVar2 = sub_005E4058((float10)GH_FROUND((param_3[1] * GV_00608528_8)));
  GV_006C88F8_4 = GH_FROUND((float)fVar2) * GH_FROUND((float)fVar1);
  fStack_18 = *param_2 + GH_FROUND(param_4 * -GV_006C88F0_4);
  fStack_14 = param_2[1] + GH_FROUND(-GV_006C88F4_4 * param_4);
  fStack_10 = param_2[2] + GH_FROUND(param_4 * -GV_006C88F8_4);
  fStack_c = GH_FROUND(fStack_18) + GV_006C88F0_4;
  fStack_8 = GV_006C88F4_4 + GH_FROUND(fStack_14);
  fStack_4 = GV_006C88F8_4 + GH_FROUND(fStack_10);
  sub_005B805C(param_1,&fStack_18,&fStack_c,((void *)G_006BFA58));
  return param_1;
}
