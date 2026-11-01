/* 0x005B24D0: insertion sort of 8-byte (float key, dword payload) pairs.  The decompiler's
 * `*pfVar3 <= *param_2` is not equivalent to the original: with x87 the unordered (NaN) result makes
 * `fcomi` + `jbe` take the shifting branch, while C's `<=` is false for NaN and the rebuilt comparison
 * took the "insert at head" branch instead, reordering the array differently.  `!(*pfVar3 > *param_2)`
 * is true for NaN and keeps the ordered cases identical. */
/* @conv EAX 0 */
#include "auto_pre.h"
/* @func 005B24D0 custom */
DECOMP_C undefined4 __cdecl sub_005AD780(int p0, undefined4 *p1, undefined4 *p2, undefined4 p3, undefined4 p4);

DECOMP(005B24D0)
void __cdecl f_005B24D0(undefined4 in_eax, float *param_2, float *param_3)
{
  float *pfVar1;
  float *pfVar2;
  float *pfVar3;

  if (param_2 != param_3) {
    for (pfVar3 = param_2 + 2; pfVar3 != param_3; pfVar3 = pfVar3 + 2) {
      pfVar1 = pfVar3;
      if (!(*pfVar3 > *param_2)) {
        do {
          pfVar2 = pfVar1;
          pfVar1 = pfVar2 + -2;
        } while (pfVar2[-2] < *pfVar3);
        if (pfVar2 != pfVar3) goto joined_r0x005b252f;
      }
      else {
        pfVar2 = param_2;
        if (param_2 != pfVar3) {
joined_r0x005b252f:
          if (pfVar3 != pfVar3 + 2) {
            sub_005AD780((int)pfVar2,pfVar3,pfVar3 + 2,0,0);
          }
        }
      }
    }
  }
  return;
}
