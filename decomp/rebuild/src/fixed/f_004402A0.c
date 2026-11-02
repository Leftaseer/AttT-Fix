/* Circle broad-phase guard: original fstps/flds round deltas, radius sum,
 * squared radius and squared distance to float before comparison. Omitting
 * the square stores distinguishes finite wide values where both originals
 * overflow to +inf; the original then continues to the polygon test.
 * The ordered comparison already has the correct unordered (NaN) behavior. */
#include "auto_pre.h"
DECOMP_C bool __cdecl sub_0047FEF0(int *p0, float p1, float p2, float p3);
/* @func 004402A0 custom */

DECOMP(004402A0)
undefined4 __cdecl f_004402A0(int this, undefined4 in_eax, int param_3)
{
  volatile float fVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  volatile float x;
  volatile float y;
  bool bVar4;
  undefined4 uVar6;
  uint uVar5;

  x = *(float *)(param_3 + 0x3fc) - *(float *)(this + 0x3fc);
  y = *(float *)(param_3 + 0x404) - *(float *)(this + 0x404);
  fVar1 = *(float *)(param_3 + 0x410) + *(float *)(this + 0x410);
  uVar6 = (undefined4)((uint)in_eax >> 8);
  if ((*(char *)(this + 0x21) != '\0') && (GH_FROUND(fVar1 * fVar1) < GH_FROUND(x * x + y * y))) {
    return (uint)uVar6 << 8;
  }
  if (*(char *)(this + 0x20) == '\0') {
    return CONCAT31(uVar6,1);
  }
  uVar5 = *(uint *)(this + 8);
  fVar1 = *(float *)(param_3 + 0x414);
  puVar2 = *(undefined4 **)(uVar5 + 4);
  puVar3 = (undefined4 *)*puVar2;
  while( true ) {
    if (puVar3 == puVar2) {
      return uVar5 & 0xffffff00;
    }
    bVar4 = sub_0047FEF0((int *)puVar3[2],x,y,fVar1);
    uVar5 = CONCAT31(0,bVar4);
    if (bVar4) break;
    puVar3 = (undefined4 *)*puVar3;
  }
  return CONCAT31(0,1);
}
