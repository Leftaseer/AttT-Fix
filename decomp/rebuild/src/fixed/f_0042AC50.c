#include "auto_pre.h"
/* @func 0042AC50 */
DECOMP(0042AC50)
double __thiscall f_0042AC50(void *this, int param_1)
{
  if (param_1 != *(int *)((int)this + 0x1d0)) {
    { volatile float gh_f = (float)(*(float *)(*(int *)((int)this + 0x1d8) + param_1 * 0xc) -
                   *(float *)(*(int *)((int)this + 0x1d8) + param_1 * 0xc + -0xc)); volatile double gh_ret = gh_f; return gh_ret; }
  }
  { volatile double gh_ret = 0.0; return gh_ret; }
}
