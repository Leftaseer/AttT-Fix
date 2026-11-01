#include "auto_pre.h"
/* @func 0058EF60 */
DECOMP(0058EF60)
void __thiscall f_0058EF60(void *this, float *param_1, float *param_2)
{
  float fVar1;

  fVar1 = *(float *)((int)this + 0x300);
  if (*param_1 < fVar1) {
    fVar1 = *param_1;
  }
  *(float *)((int)this + 0x300) = fVar1;
  fVar1 = *(float *)((int)this + 0x304);
  if (param_1[1] < fVar1) {
    fVar1 = param_1[1];
  }
  *(float *)((int)this + 0x304) = fVar1;
  fVar1 = *(float *)((int)this + 0x308);
  if (param_1[2] < fVar1) {
    fVar1 = param_1[2];
  }
  *(float *)((int)this + 0x308) = fVar1;
  fVar1 = *(float *)((int)this + 0x30c);
  if (fVar1 < *param_2) {
    fVar1 = *param_2;
  }
  *(float *)((int)this + 0x30c) = fVar1;
  fVar1 = *(float *)((int)this + 0x310);
  if (fVar1 < param_2[1]) {
    fVar1 = param_2[1];
  }
  *(float *)((int)this + 0x310) = fVar1;
  /* x87 'jbe' after 'fcomip': the guard is true on unordered, so !(a > b), not a <= b */
  if (!(param_2[2] > *(float *)((int)this + 0x314))) {
    *(float *)((int)this + 0x314) = *(float *)((int)this + 0x314);
    return;
  }
  *(float *)((int)this + 0x314) = param_2[2];
  return;
}
