/* 0x004F6B30: builds a projectile-like frame from three points (param_1: a 12-float vectors block,
 * local_dc and the corners at fStack_b4.. / fStack_c0..): picks the longest of the three edges (the comparisons
 * with the 0x00607CE0 scale) as the local x axis, crosses it with the next edge for the normal (fStack_94),
 * normalizes both, takes the angle between them (_CIacos) and rotates about the normal
 * (D3DXMatrixRotationAxis), then transforms the edge (sub_004F6950) and returns its scaled x/z (0x00609600,
 * radians->degrees) plus the normal-plane offset. The original rounds the dot product to float (0x4F7158 stores
 * it to [esp+0x60]) before dividing by the product of the two lengths; the generated C kept it extended, so an
 * angle that should be exactly 0 came out as 0.000345 (acos of 0.99999994) and the matrix was not the identity */
#include "auto_pre.h"
DECOMP_C undefined4 __stdcall sub_00433620(void);
DECOMP_C undefined4 __thiscall sub_00434AB0(void *p0, _Demangler_std_basic_string_char_struct_std__char_traits_char__class_std__allocator_char___ *p1);
DECOMP_C float __thiscall sub_00473110(void *p0, float p1, float p2);
DECOMP_C undefined4 __cdecl sub_004F6950(int p0, float *p1, float *p2);
DECOMP_C void *__stdcall sub_005B8026(void *p0, void *p1, void *p2);        /* D3DXVec3TransformCoord */
DECOMP_C void *__stdcall sub_005B8056(void *p0, void *p1, float p2);        /* D3DXMatrixRotationAxis */
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C double decomp_CIacos(double);
DECOMP_C char d_005F36DB[], d_00607CE0[], d_00609600[], d_FFDFF000[];

#define sub_005E406A decomp_CIsqrt
#define sub_005E4238 decomp_CIacos
#define G_005F36DB d_005F36DB
#define G_FFDFF000 (*(void * *)d_FFDFF000)
#define GV_00607CE0_8 (*(double *)d_00607CE0)
#define GV_00609600_8 (*(double *)d_00609600)
DECOMP(004F6B30)
undefined4 __cdecl f_004F6B30(float * gh_arg0, float gh_arg1, undefined4 gh_arg2, float gh_arg3, undefined4 gh_arg4, undefined4 gh_arg5, undefined4 gh_arg6, undefined4 gh_arg7, undefined4 gh_arg8, undefined4 gh_arg9, undefined4 gh_arg10, undefined4 gh_arg11, undefined4 gh_arg12, undefined4 gh_arg13, undefined4 gh_arg14, undefined4 gh_arg15, undefined4 gh_arg16, undefined4 gh_arg17, undefined4 gh_arg18, undefined4 gh_arg19, float * gh_arg20, float * gh_arg21, float * gh_arg22)
{
#define param_1 (*(float * *)(gh_args + 0))
#define param_2 (*(float *)(gh_args + 4))
#define param_3 (*(undefined4 *)(gh_args + 8))
#define param_4 (*(float *)(gh_args + 12))
#define param_5 (*(undefined4 *)(gh_args + 16))
#define param_6 (*(undefined4 *)(gh_args + 20))
#define param_7 (*(undefined4 *)(gh_args + 24))
#define param_8 (*(undefined4 *)(gh_args + 28))
#define param_9 (*(undefined4 *)(gh_args + 32))
#define param_10 (*(undefined4 *)(gh_args + 36))
#define param_11 (*(undefined4 *)(gh_args + 40))
#define param_12 (*(undefined4 *)(gh_args + 44))
#define param_13 (*(undefined4 *)(gh_args + 48))
#define param_14 (*(undefined4 *)(gh_args + 52))
#define param_15 (*(undefined4 *)(gh_args + 56))
#define param_16 (*(undefined4 *)(gh_args + 60))
#define param_17 (*(undefined4 *)(gh_args + 64))
#define param_18 (*(undefined4 *)(gh_args + 68))
#define param_19 (*(undefined4 *)(gh_args + 72))
#define param_20 (*(undefined4 *)(gh_args + 76))
#define param_21 (*(float * *)(gh_args + 80))
#define param_22 (*(float * *)(gh_args + 84))
#define param_23 (*(float * *)(gh_args + 88))
  unsigned char *gh_args = (unsigned char *)__builtin_frame_address(0) + 8;
#define fStack_130 (*(float *)(gh_frame + 0))
#define fStack_12c (*(float *)(gh_frame + 4))
#define fStack_128 (*(float *)(gh_frame + 8))
#define local_120 (*(float *)(gh_frame + 16))
#define fStack_11c (*(float *)(gh_frame + 20))
#define fStack_fc (*(float *)(gh_frame + 52))
#define fStack_f8 (*(float *)(gh_frame + 56))
#define fStack_f4 (*(float *)(gh_frame + 60))
#define fStack_ec (*(float *)(gh_frame + 68))
#define local_dc (*(float (*)[6])(gh_frame + 84))
#define fStack_c4 (*(float *)(gh_frame + 108))
#define fStack_c0 (*(float *)(gh_frame + 112))
#define fStack_bc (*(float *)(gh_frame + 116))
#define fStack_b8 (*(float *)(gh_frame + 120))
#define fStack_b4 (*(float *)(gh_frame + 124))
#define fStack_b0 (*(float *)(gh_frame + 128))
#define fStack_ac (*(float *)(gh_frame + 132))
#define local_a8 (*(float *)(gh_frame + 136))
#define local_a4 (*(float *)(gh_frame + 140))
#define local_a0 (*(undefined4 *)(gh_frame + 144))
#define local_9c (*(double *)(gh_frame + 148))
#define fStack_94 (*(float *)(gh_frame + 156))
#define fStack_90 (*(float *)(gh_frame + 160))
#define fStack_8c (*(float *)(gh_frame + 164))
#define fStack_88 (*(float *)(gh_frame + 168))
#define fStack_84 (*(float *)(gh_frame + 172))
#define fStack_80 (*(float *)(gh_frame + 176))
#define local_7c (*(float (*)[7])(gh_frame + 180))
#define fStack_60 (*(float *)(gh_frame + 208))
#define fStack_54 (*(float *)(gh_frame + 220))
#define auStack_4c (*(undefined1 (*)[64])(gh_frame + 228))
#define pvStack_c (*(void **)(gh_frame + 292))
#define puStack_8 (*(undefined1 **)(gh_frame + 296))
#define local_4 (*(undefined4 *)(gh_frame + 300))
  unsigned char gh_frame[304] __attribute__((aligned(16)));
  int iVar1;
  float fVar2;
  float fVar3;
  void *this;
  float fVar5;
  float fVar6;
  float *pfVar7;
  float *pfVar8;
  float10 fVar9;
  float10 fVar10;
  float fVar11;
  volatile float fDot;
  volatile float negNormal;

  local_4 = 0xffffffff;
  puStack_8 = ((void *)G_005F36DB);
  param_1[1] = 0.0;
  param_1[4] = 0.0;
  param_1[7] = 0.0;
  param_1[10] = 0.0;
  this = (void *)sub_00433620();
  local_a8 = 0.0;
  local_a4 = 0.0;
  local_a0 = 0;
  local_4 = 0;
  iVar1 = -(int)param_1;
  (*(unsigned int *)((char *)&local_9c + 0)) = GH_BITS4(4);
  pfVar8 = param_1;
  do {
    pfVar7 = (float *)(((int)local_7c - (int)param_1) + (int)pfVar8);
    sub_005B8026(pfVar7,pfVar8,&param_5);
    fVar5 = pfVar8[1];
    fVar6 = pfVar8[2];
    *(float *)((int)local_dc + iVar1 + (int)pfVar8) = *pfVar8;
    fVar11 = *(float *)((int)local_7c + (8 - (int)param_1) + (int)pfVar8);
    *(float *)((int)local_dc + iVar1 + 4 + (int)pfVar8) = fVar5;
    fVar5 = *pfVar7;
    *(float *)((int)local_dc + iVar1 + 8 + (int)pfVar8) = fVar6;
    fVar11 = sub_00473110(this,fVar5,fVar11);
    *(float *)((int)local_dc + (4 - (int)param_1) + (int)pfVar8) = fVar11;
    pfVar8 = pfVar8 + 3;
    (*(unsigned int *)((char *)&local_9c + 0)) = GH_BITS4((*(unsigned int *)((char *)&local_9c + 0)) + -1);
  } while ((*(unsigned int *)((char *)&local_9c + 0)) != 0);
  if (!((local_dc[1] + fStack_c0) * GV_00607CE0_8 >
        (local_dc[4] + fStack_b4) * GV_00607CE0_8)) {
    if (!(fStack_60 > local_7c[1])) {
      fStack_fc = param_1[3] - param_1[6];
      fStack_ec = fStack_c0;
      fStack_f8 = param_1[4] - param_1[7];
      fStack_f4 = param_1[5] - param_1[8];
      local_120 = local_dc[3] - fStack_c4;
      fStack_11c = local_dc[4] - fStack_c0;
      fVar11 = local_dc[5] - fStack_bc;
      fVar5 = param_1[9] - param_1[6];
      fVar6 = param_1[10] - param_1[7];
      fStack_128 = param_1[0xb] - param_1[8];
      fStack_130 = fStack_b8 - fStack_c4;
      fStack_12c = fStack_b4 - fStack_c0;
      fStack_bc = fStack_b0 - fStack_bc;
    }
    else {
      fStack_fc = param_1[9] - *param_1;
      fStack_ec = local_dc[1];
      fStack_f8 = param_1[10] - param_1[1];
      fStack_f4 = param_1[0xb] - param_1[2];
      local_120 = fStack_b8 - local_dc[0];
      fStack_11c = fStack_b4 - local_dc[1];
      fVar11 = fStack_b0 - local_dc[2];
      fVar5 = param_1[3] - *param_1;
      fVar6 = param_1[4] - param_1[1];
      fStack_128 = param_1[5] - param_1[2];
      fStack_130 = local_dc[3] - local_dc[0];
      fStack_12c = local_dc[4] - local_dc[1];
      fStack_bc = local_dc[5] - local_dc[2];
    }
  }
  else if (!(fStack_54 > local_7c[4])) {
    fStack_fc = param_1[6] - param_1[9];
    fStack_ec = fStack_b4;
    fStack_f8 = param_1[7] - param_1[10];
    fStack_f4 = param_1[8] - param_1[0xb];
    local_120 = fStack_c4 - fStack_b8;
    fStack_11c = fStack_c0 - fStack_b4;
    fVar11 = fStack_bc - fStack_b0;
    fVar5 = *param_1 - param_1[9];
    fVar6 = param_1[1] - param_1[10];
    fStack_128 = param_1[2] - param_1[0xb];
    fStack_130 = local_dc[0] - fStack_b8;
    fStack_12c = local_dc[1] - fStack_b4;
    fStack_bc = local_dc[2] - fStack_b0;
  }
  else {
    fStack_fc = *param_1 - param_1[3];
    fStack_ec = local_dc[4];
    fStack_f8 = param_1[1] - param_1[4];
    fStack_f4 = param_1[2] - param_1[5];
    local_120 = local_dc[0] - local_dc[3];
    fStack_11c = local_dc[1] - local_dc[4];
    fVar11 = local_dc[2] - local_dc[5];
    fVar5 = param_1[6] - param_1[3];
    fVar6 = param_1[7] - param_1[4];
    fStack_128 = param_1[8] - param_1[5];
    fStack_130 = fStack_c4 - local_dc[3];
    fStack_12c = fStack_c0 - local_dc[4];
    fStack_bc = fStack_bc - local_dc[5];
  }
  fVar2 = fStack_f8 * fStack_128 - fStack_f4 * fVar6;
  fStack_84 = fVar5 * fStack_f4 - fStack_fc * fStack_128;
  fVar5 = fStack_fc * fVar6 - fVar5 * fStack_f8;
  fVar6 = fStack_11c * fStack_bc - fVar11 * fStack_12c;
  fVar11 = fStack_130 * fVar11 - local_120 * fStack_bc;
  fVar3 = local_120 * fStack_12c - fStack_130 * fStack_11c;
  local_9c = (double)fStack_84;
  fStack_ac = fVar3 * fStack_84 - fVar11 * fVar5;
  local_a8 = fVar6 * fVar5 - fVar2 * fVar3;
  local_a4 = fVar2 * fVar11 - fVar6 * fStack_84;
  fStack_94 = fStack_ac;
  fStack_90 = local_a8;
  fStack_8c = local_a4;
  fStack_88 = fVar2;
  fStack_80 = fVar5;
  fVar9 = (float10)GH_FROUND(sub_005E406A((float10)GH_FROUND(
      (fVar3 * fVar3 + fVar6 * fVar6 + fVar11 * fVar11))));
  fVar10 = (float10)GH_FROUND(sub_005E406A((float10)GH_FROUND(
      (fVar5 * fVar5 + fStack_84 * fStack_84 + fVar2 * fVar2))));
  fDot = fVar5 * fVar3 + fVar2 * fVar6 + fVar11 * fStack_84;
  fVar9 = sub_005E4238((float10)GH_FROUND(
      (fDot / ((float)fVar10 * (float)fVar9))));
  sub_005B8056(auStack_4c,&fStack_94,(float)fVar9);
  sub_004F6950((int)auStack_4c,&fStack_94,&fStack_ac);
  fVar5 = GV_00609600_8;
  *param_21 = fStack_94 * fVar5;
  *param_22 = fVar5 * fStack_8c;
  /* Preserve the original fchs / fdiv / fadd order. Clang otherwise turns
   * numerator / -normal + offset into offset - numerator / normal, flipping
   * the NaN sign bit (seed 11, n=64, case 55). The normal is already float. */
  negNormal = -fVar11;
  *param_23 = (fVar3 * (param_4 - fVar3) + fVar6 * (param_2 - fVar6)) / negNormal + fStack_ec;
  return param_22;
}
#undef sub_005E406A
#undef sub_005E4238
#undef G_005F36DB
#undef G_FFDFF000
#undef GV_00607CE0_8
#undef GV_00609600_8
#undef fStack_130
#undef fStack_12c
#undef fStack_128
#undef local_120
#undef fStack_11c
#undef fStack_fc
#undef fStack_f8
#undef fStack_f4
#undef fStack_ec
#undef local_dc
#undef fStack_c4
#undef fStack_c0
#undef fStack_bc
#undef fStack_b8
#undef fStack_b4
#undef fStack_b0
#undef fStack_ac
#undef local_a8
#undef local_a4
#undef local_a0
#undef local_9c
#undef fStack_94
#undef fStack_90
#undef fStack_8c
#undef fStack_88
#undef fStack_84
#undef fStack_80
#undef local_7c
#undef fStack_60
#undef fStack_54
#undef auStack_4c
#undef pvStack_c
#undef puStack_8
#undef local_4
#undef param_1
#undef param_2
#undef param_3
#undef param_4
#undef param_5
#undef param_6
#undef param_7
#undef param_8
#undef param_9
#undef param_10
#undef param_11
#undef param_12
#undef param_13
#undef param_14
#undef param_15
#undef param_16
#undef param_17
#undef param_18
#undef param_19
#undef param_20
#undef param_21
#undef param_22
#undef param_23
