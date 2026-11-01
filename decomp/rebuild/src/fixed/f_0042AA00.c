#include "auto_pre.h"
/* @func 0042AA00 */
DECOMP(0042AA00)
double __fastcall f_0042AA00(int param_1)
{
  int iVar1;
  
  iVar1 = *(int *)(param_1 + 0x1cc);
  if (iVar1 != *(int *)(param_1 + 0x1d0)) {
    { volatile float gh_f = (float)(*(float *)(*(int *)(param_1 + 0x1d8) + 8 + iVar1 * 0xc) -
                   *(float *)(*(int *)(param_1 + 0x1d8) + iVar1 * 0xc + -4)); volatile double gh_ret = gh_f; return gh_ret; }
  }
  { volatile double gh_ret = 0.0; return gh_ret; }
}
