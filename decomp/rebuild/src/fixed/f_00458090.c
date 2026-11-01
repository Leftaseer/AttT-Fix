#include "auto_pre.h"
/* @func 00458090 custom */
DECOMP(00458090)
undefined4 __cdecl f_00458090(int this, undefined4 in_eax, float param_3, float param_4, float param_5)
{
  float fVar1;
  undefined4 uVar2;
  
  fVar1 = -param_5;
  uVar2 = (undefined4)((uint)in_eax >> 8);
  if (((!(fVar1 >= param_3 * *(float *)(this + 4) + param_4 * *(float *)(this + 0xc) +
                 *(float *)(this + 0x10)) &&
       !(fVar1 >= *(float *)(this + 0x1c) * param_4 + *(float *)(this + 0x14) * param_3 +
                *(float *)(this + 0x20))) &&
      !(fVar1 >= *(float *)(this + 0x4c) * param_4 + *(float *)(this + 0x44) * param_3 +
               *(float *)(this + 0x50))) &&
     !(fVar1 >= *(float *)(this + 0x60) +
              *(float *)(this + 0x54) * param_3 + *(float *)(this + 0x5c) * param_4)) {
    return CONCAT31(uVar2,1);
  }
  return (uint)uVar2 << 8;
}
