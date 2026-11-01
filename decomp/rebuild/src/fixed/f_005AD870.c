#include "auto_pre.h"
DECOMP(005AD870)
void __cdecl f_005AD870(int param_1, int param_2, int param_3, float param_4, undefined4 param_5)
{
  int iVar1;

  if (param_3 < param_2) {
    do {
      iVar1 = (param_2 + -1) / 2;
      /* x87 'jbe' after 'fcomip': the guard is true on unordered, so !(a > b), not a <= b */
      if (!(param_4 > *(float *)(param_1 + iVar1 * 8))) break;
      *(undefined4 *)(param_1 + param_2 * 8) = *(undefined4 *)(param_1 + iVar1 * 8);
      *(undefined4 *)(param_1 + 4 + param_2 * 8) = *(undefined4 *)(param_1 + 4 + iVar1 * 8);
      param_2 = iVar1;
    } while (param_3 < iVar1);
  }
  *(float *)(param_1 + param_2 * 8) = param_4;
  *(undefined4 *)(param_1 + 4 + param_2 * 8) = param_5;
  return;
}
