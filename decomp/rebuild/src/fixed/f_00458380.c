/* Frustum plane test: the original sums y, x, z, then w without a float
 * store, and fcomip; ja accepts only an ordered strictly positive result.
 * NaNs must remain in the vertex scan, not count as a positive plane hit. */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005B8026(void *p0, void *p1, void *p2);
/* @func 00458380 custom */

DECOMP(00458380)
uint __cdecl f_00458380(int this, void *in_eax, int param_3, uint param_4, void *param_5)
{
#define local_10 (*(void **)(gh_frame + 0))
#define local_c (*(float *)(gh_frame + 4))
#define fStack_8 (*(float *)(gh_frame + 8))
#define fStack_4 (*(float *)(gh_frame + 12))
  unsigned char gh_frame[16] __attribute__((aligned(16)));
  void *pvVar1;
  float *pfVar2;
  uint uVar3;

  local_10 = (void *)0x0;
  pfVar2 = (float *)(this + 4);
  while (uVar3 = 0, pvVar1 = (void *)param_3, param_4 != 0) {
    while (in_eax = sub_005B8026(&local_c,pvVar1,param_5),
          !(pfVar2[1] * fStack_8 + *pfVar2 * local_c + pfVar2[2] * fStack_4 + pfVar2[3] > 0.0)) {
      uVar3 = uVar3 + 1;
      pvVar1 = (void *)((int)pvVar1 + 0x20);
      if (param_4 <= uVar3) goto LLAB_004583df;
    }
    in_eax = (void *)((int)local_10 + 1);
    pfVar2 = pfVar2 + 4;
    local_10 = in_eax;
    if (5 < (int)in_eax) {
      return CONCAT31((undefined4)((uint)in_eax >> 8),1);
    }
  }
LLAB_004583df:
  return (uint)in_eax & 0xffffff00;
}
#undef local_10
#undef local_c
#undef fStack_8
#undef fStack_4
