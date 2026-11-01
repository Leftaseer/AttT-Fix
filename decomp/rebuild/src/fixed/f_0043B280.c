#include "auto_pre.h"
DECOMP_C undefined4 __thiscall sub_0043AFF0(void * p0, int p1);
/* @func 0043B280 */
/* 0043B2E0 tail-calls this function (jmp), so its own return value is whatever EAX is left behind:
   param_1 on the early path, minutes*1000 on the middle path.  clang does not reload EAX on those
   paths, so the leftovers are pinned with empty asm. */
DECOMP(0043B280)
void __thiscall f_0043B280(void *this, int param_1)
{
  uint uVar1, minutes;
  
  *(int *)((int)this + 0x5c) = *(int *)((int)this + 0x5c) + param_1;
  uVar1 = *(uint *)((int)this + 0x5c);
  if (999 < uVar1) {
    minutes = uVar1 / 1000;
    *(int *)((int)this + 0x58) = *(int *)((int)this + 0x58) + minutes;
    *(uint *)((int)this + 0x5c) = uVar1 % 1000;
    uVar1 = *(uint *)((int)this + 0x58);
    if (0x3b < uVar1) {
      *(uint *)((int)this + 0x58) = uVar1 % 0x3c;
      sub_0043AFF0(this,uVar1 / 0x3c);
      return;
    }
    __asm__ volatile("" : : "a"(minutes * 1000));
  }
  __asm__ volatile("" : : "a"(param_1));
}
