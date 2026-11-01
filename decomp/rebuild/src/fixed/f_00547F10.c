/* 0x00547F10: recomputes this->field_0x68, then stores the transform through 004AC7F0, which the original
 * enters with a tail jump.  004AC7F0 returns its EAX argument, so the visible result of 00547F10 is the EAX
 * left behind by 00473110 - the generated `in_eax = 0` returned 0 instead.  The call is spelled in asm to
 * read the register after it. */
#include "auto_pre.h"
/* @func 00547F10 */
DECOMP_C undefined4 __stdcall sub_00433620(void);
DECOMP_C float __thiscall sub_00473110(void *p0, float p1, float p2);
DECOMP_C undefined4 __cdecl sub_004AC7F0(_CRenderObject3D *p0, undefined4 p1);

DECOMP(00547F10)
undefined4 __thiscall f_00547F10(_CWorldUnit *this)
{
  void *obj;
  float fv;
  unsigned leftover;
  union { float f; unsigned u; } ua, ub;

  obj = (void *)sub_00433620();
  ua.f = *(float *)&(this->base_CRenderObject3D).base_CRenderObject.field_0x64;
  ub.f = *(float *)&(this->base_CRenderObject3D).base_CRenderObject.field_0x6c;
  __asm__ volatile(
      "subl $8, %%esp\n\t"
      "movl %[b], 4(%%esp)\n\t"
      "movl %[a], (%%esp)\n\t"
      "movl %[obj], %%ecx\n\t"
      /* 00473110 is __thiscall: its `ret 8` already removes the two arguments */
      "call *%[fn]\n\t"
      "fstps %[fv]\n\t"
      : "=a"(leftover), [fv] "=m"(fv)
      : [a] "r"(ua.u), [b] "r"(ub.u), [obj] "r"(obj), [fn] "r"(sub_00473110)
      : "ecx", "edx", "memory", "st");
  *(float *)&(this->base_CRenderObject3D).base_CRenderObject.field_0x68 = fv;
  return sub_004AC7F0(&this->base_CRenderObject3D, leftover);
}
