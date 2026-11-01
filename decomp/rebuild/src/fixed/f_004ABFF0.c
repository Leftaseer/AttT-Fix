#include "auto_pre.h"
DECOMP_C void * __stdcall sub_005B8020(void * p0, void * p1, void * p2);
/* @func 004ABFF0 */
/* The original returns the last D3DXMatrixMultiply's pOut, which is its own stack local at
   entry_esp - 0x40 (EBP - 0x3C).  clang places the buffer elsewhere, but the value is only that
   address (the caller ignores it), so it is rebuilt from the frame pointer. */
DECOMP(004ABFF0)
undefined4 __thiscall f_004ABFF0(_CRenderObject2D *this)
{
#define auStack_100 (*(undefined1 (*)[64])(gh_frame + 0))
#define auStack_c0 (*(undefined1 (*)[64])(gh_frame + 64))
#define local_80 (*(undefined1 (*)[64])(gh_frame + 128))
#define auStack_40 (*(undefined4 (*)[16])(gh_frame + 192))
  unsigned char gh_frame[256] __attribute__((aligned(16)));
  void *pvVar1;
  int iVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  
  sub_005B8020(local_80,&(this->base_CRenderObject).field_0x100,
                     &(this->base_CRenderObject).field_0x184);
  sub_005B8020(auStack_100,local_80,&(this->base_CRenderObject).field_0xc0);
  sub_005B8020(auStack_c0,auStack_100,&this->field17_0x1c4);
  pvVar1 = sub_005B8020(auStack_40,auStack_c0,&(this->base_CRenderObject).field_0x80);
  puVar3 = auStack_40;
  puVar4 = (undefined4 *)&(this->base_CRenderObject).field_0x140;
  for (iVar2 = 0x10; iVar2 != 0; iVar2 = iVar2 + -1) {
    *puVar4 = *puVar3;
    puVar3 = puVar3 + 1;
    puVar4 = puVar4 + 1;
  }
  (this->base_CRenderObject).field_0x180 = 0;
  (void)pvVar1;
  return (char *)__builtin_frame_address(0) - 0x3C;
}
