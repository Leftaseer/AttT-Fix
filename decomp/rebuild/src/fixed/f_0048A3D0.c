#include "auto_pre.h"
/* @func 0048A3D0 */
DECOMP(0048A3D0)
void __stdcall f_0048A3D0(float *param_1, float *param_2, uint param_3)
{
  float fVar1;
  float *pfVar2;
  uint uVar3;
  int iVar4;
  
  *param_1 = *param_2;
  param_1[1] = *param_2;
  param_1[3] = param_2[2];
  uVar3 = 1;
  param_1[2] = param_2[2];
  if (3 < (int)(param_3 - 1)) {
    iVar4 = (param_3 - 5 >> 2) + 1;
    pfVar2 = param_2 + 0x10;
    uVar3 = iVar4 * 4 + 1;
    do {
      fVar1 = pfVar2[-8];
      if (!(*param_1 > fVar1)) {
        if (param_1[1] < fVar1) {
          param_1[1] = fVar1;
        }
      }
      else {
        *param_1 = fVar1;
      }
      fVar1 = pfVar2[-6];
      if (!(param_1[3] > fVar1)) {
        if (param_1[2] < fVar1) {
          param_1[2] = fVar1;
        }
      }
      else {
        param_1[3] = fVar1;
      }
      fVar1 = *pfVar2;
      if (!(*param_1 > fVar1)) {
        if (param_1[1] < fVar1) {
          param_1[1] = fVar1;
        }
      }
      else {
        *param_1 = fVar1;
      }
      fVar1 = pfVar2[2];
      if (!(param_1[3] > fVar1)) {
        if (param_1[2] < fVar1) {
          param_1[2] = fVar1;
        }
      }
      else {
        param_1[3] = fVar1;
      }
      fVar1 = pfVar2[8];
      if (!(*param_1 > fVar1)) {
        if (param_1[1] < fVar1) {
          param_1[1] = fVar1;
        }
      }
      else {
        *param_1 = fVar1;
      }
      fVar1 = pfVar2[10];
      if (!(param_1[3] > fVar1)) {
        if (param_1[2] < fVar1) {
          param_1[2] = fVar1;
        }
      }
      else {
        param_1[3] = fVar1;
      }
      fVar1 = pfVar2[0x10];
      if (!(*param_1 > fVar1)) {
        if (param_1[1] < fVar1) {
          param_1[1] = fVar1;
        }
      }
      else {
        *param_1 = fVar1;
      }
      fVar1 = pfVar2[0x12];
      if (!(param_1[3] > fVar1)) {
        if (param_1[2] < fVar1) {
          param_1[2] = fVar1;
        }
      }
      else {
        param_1[3] = fVar1;
      }
      pfVar2 = pfVar2 + 0x20;
      iVar4 = iVar4 + -1;
    } while (iVar4 != 0);
  }
  if (uVar3 < param_3) {
    pfVar2 = param_2 + uVar3 * 8;
    iVar4 = param_3 - uVar3;
    do {
      fVar1 = *pfVar2;
      if (!(*param_1 > fVar1)) {
        if (param_1[1] < fVar1) {
          param_1[1] = fVar1;
        }
      }
      else {
        *param_1 = fVar1;
      }
      fVar1 = pfVar2[2];
      if (!(param_1[3] > fVar1)) {
        if (param_1[2] < fVar1) {
          param_1[2] = fVar1;
        }
      }
      else {
        param_1[3] = fVar1;
      }
      pfVar2 = pfVar2 + 8;
      iVar4 = iVar4 + -1;
    } while (iVar4 != 0);
  }
  return;
}
