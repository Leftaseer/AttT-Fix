#include "auto_pre.h"
DECOMP_C undefined4 __fastcall sub_0058F650(int p0);
DECOMP(0058FF10)
void __thiscall f_0058FF10(void *this, float *param_1, float *param_2)
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
  if (*param_2 < fVar1) {
    fVar1 = *param_2;
  }
  *(float *)((int)this + 0x30c) = fVar1;
  fVar1 = *(float *)((int)this + 0x310);
  if (param_2[1] < fVar1) {
    fVar1 = param_2[1];
  }
  *(float *)((int)this + 0x310) = fVar1;
  fVar1 = *(float *)((int)this + 0x314);
  if (param_2[2] < fVar1) {
    fVar1 = param_2[2];
  }
  *(float *)((int)this + 0x314) = fVar1;
  sub_0058F650((int)this);
  return;
}
