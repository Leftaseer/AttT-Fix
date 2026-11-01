#include "auto_pre.h"
DECOMP_C undefined4 __cdecl sub_004ABFC0(_CRenderObject2D * p0, undefined4 p1);
DECOMP_C float __fastcall sub_00587470(undefined4 p0);
DECOMP_C float __fastcall sub_00587490(undefined4 p0);
DECOMP_C char d_0060B360[];
DECOMP_C char d_006C8958[];
DECOMP_C char d_006C895C[];
/* @func 005882C0 */
/* sub_004ABFC0 does not read EAX: it hands whatever the caller has there back in EAX (EAX pass-through),
   so the original passes the leftover of the preceding float-returning calls, not a constant. */
#define GV_0060B360_8 (*(double *)d_0060B360)
#define GV_006C8958_4 (*(float *)d_006C8958)
#define GV_006C895C_4 (*(float *)d_006C895C)
DECOMP(005882C0)
undefined4 __thiscall f_005882C0(_nGUI_ToolTip *this)
{
#define local_8 (*(float *)(gh_frame + 0))
#define local_4 (*(float *)(gh_frame + 4))
  unsigned char gh_frame[8] __attribute__((aligned(16)));
  int *piVar1;
  int iVar2;
  undefined4 in_eax = 0;
  undefined4 uVar3;
  float fVar4;
  float fVar5;
  
  if ((this->base_Text).base_iGUIElement.field_0x2d0 != '\0') {
    fVar4 = sub_00587490(this);
    fVar5 = GV_006C8958_4;
    if (GV_006C8958_4 <
        fVar4 + fVar4 +
        *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.base_CRenderObject2D.
                   base_CRenderObject.field_0x5c +
        *(float *)&(this->base_Text).base_iGUIElement.field_0x2cc) {
      fVar4 = sub_00587490(this);
      *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.base_CRenderObject2D.
                 base_CRenderObject.field_0x5c =
           (fVar5 - (fVar4 + fVar4)) - *(float *)&(this->base_Text).base_iGUIElement.field_0x2cc;
    }
    fVar4 = sub_00587470(this);
    fVar5 = GV_006C895C_4;
    if (GV_006C895C_4 <
        fVar4 + *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.
                           base_CRenderObject2D.base_CRenderObject.field_0x58 +
        *(float *)&(this->base_Text).base_iGUIElement.field_0x2c8 + GV_0060B360_8) {
      fVar4 = sub_00587470(this);
      *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.base_CRenderObject2D.
                 base_CRenderObject.field_0x58 =
           ((fVar5 - fVar4) - *(float *)&(this->base_Text).base_iGUIElement.field_0x2c8) -
           GV_0060B360_8;
    }
  }
  piVar1 = *(int **)&(this->base_Text).base_iGUIElement.field_0x2c4;
  local_8 = *(float *)&(this->base_Text).base_iGUIElement.field_0x2c8 +
            *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.
                       base_CRenderObject2D.base_CRenderObject.field_0x58;
  local_4 = *(float *)&(this->base_Text).base_iGUIElement.field_0x2cc +
            *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.
                       base_CRenderObject2D.base_CRenderObject.field_0x5c;
  if (piVar1 != (int *)0x0) {
    ((void (__thiscall *)(void *, undefined4))(*(undefined1 **)(*piVar1 + 0x6c)))(piVar1, &local_8);
    piVar1 = *(int **)&(this->base_Text).base_iGUIElement.field_0x2c4;
    ((void (__thiscall *)(void *))(*(undefined1 **)(*piVar1 + 0x18)))(piVar1);
  }
  iVar2 = *(int *)(*(int *)&(this->base_Text).base_iGUIElement.field_0x2a0 + 0x24c);
  fVar5 = sub_00587490(this);
  *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.base_CRenderObject2D.
             base_CRenderObject.field_0x5c =
       fVar5 / (float)iVar2 +
       *(float *)&(this->base_Text).base_iGUIElement.base_CRenderObject2DRes.base_CRenderObject2D.
                  base_CRenderObject.field_0x5c;
  __asm__("" : "=a"(in_eax));
  uVar3 = sub_004ABFC0((_CRenderObject2D *)this,in_eax);
  return uVar3;
}
