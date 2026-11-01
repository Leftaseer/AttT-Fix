#include "auto_pre.h"
/* @func 0047F4A0 */
/* MSVC compares here with 'ja' plus a 'lahf/test ah,0x44/jp' pair: only an ordered 'less' is recognised
 * (it jumps to the return-0 path), and so is unordered.  The decompiler's 'a < b' is false on NaN and would
 * fall through to the second component instead of returning 0. */
DECOMP(0047F4A0)
undefined4 __thiscall f_0047F4A0(void *this, float *param_1)
{
  if (*(float *)this > *param_1) {
    return 1;
  }
  if (!(*(float *)this >= *param_1)) {
    return 0;
  }
  if (*(float *)((int)this + 4) > param_1[1]) {
    return 1;
  }
  return 0;
}
