#include "auto_pre.h"
/* @func 0047F450 */
/* naive: a 3-way compare like f_0047F4A0; unordered returns 0, only equal reaches the second component */
DECOMP(0047F450)
undefined4 __thiscall f_0047F450(void *this, float *param_1)
{
  if (*param_1 > *(float *)this) {
    return 1;
  }
  if (!(*param_1 >= *(float *)this)) {
    return 0;
  }
  if (param_1[1] > *(float *)((int)this + 4)) {
    return 1;
  }
  return 0;
}
