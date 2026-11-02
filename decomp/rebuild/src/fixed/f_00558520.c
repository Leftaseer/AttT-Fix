/* 0x00558520: particle/instance distance keys. The original rounds each coordinate
 * difference to float and sums (dx*dx + dy*dy) + dz*dz, then stores float.
 * Reordering to (dz*dz + dx*dx) + dy*dy loses two unit terms beside 4096^2
 * under the game's x87 single precision (0x7f). Preserve the actor-radius
 * comparison's float store and x/y/z order as well. */
#include "auto_pre.h"
DECOMP_C undefined4 __stdcall sub_0042F160(void);
DECOMP_C undefined4 __stdcall sub_00432260(void);
DECOMP_C undefined4 __stdcall sub_004F9ED0(void);
DECOMP_C undefined4 __thiscall sub_00556020(void *p0, int p1, int p2);
DECOMP_C undefined4 __fastcall sub_00556100(int p0);
DECOMP_C undefined4 __thiscall sub_00558440(void *p0, undefined4 *p1);
/* @func 00558520 */

DECOMP(00558520)
void __thiscall f_00558520(void *this, float *param_1, void *param_2)
{
#define local_34 (*(float *)(gh_frame + 0))
#define local_30 (*(float *)(gh_frame + 4))
#define local_28 (*(float *)(gh_frame + 12))
  unsigned char gh_frame[52] __attribute__((aligned(16)));
  undefined4 *puVar1;
  volatile float fVar2;
  volatile float fVar3;
  volatile float fVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  bool bVar8;

  if (*(int *)((int)this + 0x10) != 0) {
    iVar5 = sub_0042F160();
    iVar5 = *(int *)(iVar5 + 0x5c);
    iVar6 = sub_00432260();
    bVar8 = iVar5 == iVar6;
    local_34 = 0.0;
    local_30 = 0.0;
    local_28 = 0.0;
    if (bVar8) {
      iVar5 = sub_004F9ED0();
      local_30 = *(float *)(iVar5 + 0x84);
      local_28 = *(float *)(iVar5 + 0x8c);
      iVar5 = sub_004F9ED0();
      local_34 = GH_FROUND(*(float *)(iVar5 + 0x5c) * *(float *)(iVar5 + 0x5c));
    }
    uVar7 = 0;
    if (*(int *)((int)this + 0x10) != 0) {
      iVar5 = 0;
      do {
        fVar2 = *param_1 - *(float *)(*(int *)((int)this + 0x2c) + iVar5);
        iVar6 = *(int *)((int)this + 0x2c) + iVar5;
        fVar3 = param_1[1] - *(float *)(iVar6 + 4);
        fVar4 = param_1[2] - *(float *)(iVar6 + 8);
        *(uint *)(*(int *)((int)this + 0x38) + uVar7 * 8) = uVar7;
        *(float *)(*(int *)((int)this + 0x38) + 4 + uVar7 * 8) =
             GH_FROUND(fVar2 * fVar2 + fVar3 * fVar3 + fVar4 * fVar4);
        if ((bVar8) &&
           (iVar6 = *(int *)(*(int *)((int)this + 0x38) + uVar7 * 8),
           puVar1 = (undefined4 *)(*(int *)((int)this + 0x18) + iVar6 * 0x48),
           fVar2 = *(float *)(*(int *)((int)this + 0x18) + 0x38 + iVar6 * 0x48) - local_30,
           fVar3 = BITCAST(float, (puVar1[0x10])) - local_28, GH_FROUND(fVar2 * fVar2 + 0.0 + fVar3 * fVar3) < local_34))
        {
          sub_00558440(param_2,puVar1);
          *(undefined4 *)(*(int *)((int)this + 0x38) + uVar7 * 8) =
               *(undefined4 *)((int)this + 0x10);
          *(int *)((int)this + 0x24) = *(int *)((int)this + 0x24) + -1;
        }
        uVar7 = uVar7 + 1;
        iVar5 = iVar5 + 0x18;
      } while (uVar7 < *(uint *)((int)this + 0x10));
    }
    if (0x10 < *(uint *)((int)this + 0x10)) {
      sub_00556020(this,0,*(uint *)((int)this + 0x10) - 1);
      return;
    }
    sub_00556100((int)this);
  }
  return;
}
#undef local_34
#undef local_30
#undef local_28
