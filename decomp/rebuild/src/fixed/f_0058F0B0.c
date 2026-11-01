#include "auto_pre.h"
/* @func 0058F0B0 */
DECOMP(0058F0B0)
void __thiscall f_0058F0B0(void *this, float *param_1)
{
  int iVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float fVar6;

  iVar1 = 8;
  do {
    fVar6 = *param_1;
    fVar2 = *(float *)((int)this + 0x300);
    fVar5 = param_1[1];
    fVar4 = param_1[2];
    if (fVar6 < fVar2) {
      fVar2 = fVar6;
    }
    fVar3 = *(float *)((int)this + 0x304);
    *(float *)((int)this + 0x300) = fVar2;
    if (fVar5 < fVar3) {
      fVar3 = fVar5;
    }
    fVar2 = *(float *)((int)this + 0x308);
    *(float *)((int)this + 0x304) = fVar3;
    if (fVar4 < fVar2) {
      fVar2 = fVar4;
    }
    *(float *)((int)this + 0x308) = fVar2;
    /* x87 'ja' guards: the else branch (keep the old value) is taken on unordered, not a <= b */
    if (!(fVar6 > *(float *)((int)this + 0x30c))) {
      fVar6 = *(float *)((int)this + 0x30c);
    }
    *(float *)((int)this + 0x30c) = fVar6;
    if (!(fVar5 > *(float *)((int)this + 0x310))) {
      fVar5 = *(float *)((int)this + 0x310);
    }
    *(float *)((int)this + 0x310) = fVar5;
    if (!(fVar4 > *(float *)((int)this + 0x314))) {
      fVar4 = *(float *)((int)this + 0x314);
    }
    param_1 = param_1 + 3;
    iVar1 = iVar1 + -1;
    *(float *)((int)this + 0x314) = fVar4;
  } while (iVar1 != 0);
  return;
}
