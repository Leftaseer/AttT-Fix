/* Circle broad-phase guard: original fstps/flds round deltas, radius sum,
 * squared radius and squared distance to float before comparison. Omitting
 * the square stores distinguishes finite wide values where both originals
 * overflow to +inf; the original then continues to the polygon test.
 * The ordered comparison already has the correct unordered (NaN) behavior. */
#include "auto_pre.h"
DECOMP_C undefined4 __stdcall sub_0043FB20(int *p0, float p1, float p2, float p3);
/* @func 00440390 custom */

DECOMP(00440390)
undefined4 __cdecl f_00440390(int this, undefined4 in_eax, int param_3)
{
  volatile float fVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  volatile float fVar4;
  volatile float fVar5;
  undefined4 uVar7;
  uint uVar6;

  fVar4 = *(float *)(param_3 + 0x3fc) - *(float *)(this + 0x3fc);
  fVar5 = *(float *)(param_3 + 0x404) - *(float *)(this + 0x404);
  fVar1 = *(float *)(param_3 + 0x410) + *(float *)(this + 0x410);
  uVar7 = (undefined4)((uint)in_eax >> 8);
  if ((*(char *)(this + 0x21) != '\0') && (GH_FROUND(fVar1 * fVar1) < GH_FROUND(fVar4 * fVar4 + fVar5 * fVar5))) {
    return (uint)uVar7 << 8;
  }
  if (*(char *)(this + 0x20) == '\0') {
    return CONCAT31(uVar7,1);
  }
  uVar6 = *(uint *)(this + 8);
  fVar1 = *(float *)(param_3 + 0x414);
  puVar2 = *(undefined4 **)(uVar6 + 4);
  puVar3 = (undefined4 *)*puVar2;
  while( true ) {
    if (puVar3 == puVar2) {
      return uVar6 & 0xffffff00;
    }
    uVar6 = sub_0043FB20((int *)puVar3[2],fVar4,fVar5,fVar1);
    if ((char)uVar6 != '\0') break;
    puVar3 = (undefined4 *)*puVar3;
  }
  return CONCAT31((undefined4)(uVar6 >> 8),1);
}
