/* 0x00593340: linear interpolation parameter converted to a 64-bit integer.  The original rounds the ratio to
 * float (fstp dword + fld) before the fimul, keeps the product in extended precision, and ends by calling the
 * CRT's _ftol2 (0x5E3FA0) instead of an inline conversion.  That matters: _ftol2 clobbers ECX on its slow path
 * (taken while the SSE2 guard 0x8D18C0 is still zero in the verifier) and leaves EDX = its argument on the fast
 * path, so only the same call reproduces the original register state in both environments. */
#include "auto_pre.h"
/* @func 00593340 */
DECOMP_C char d_00607CE0[];

DECOMP(00593340)
ulonglong __thiscall f_00593340(void *this, int param_1)
{
  int a = *(int *)((int)this + 0x5c) - *(int *)((int)this + 0x58);   /* numerator */
  int b = *(int *)((int)this + 0x48) - *(int *)((int)this + 0x40);   /* denominator */
  int c = *(int *)((int)this + 0x58);
  int d = param_1 - *(int *)((int)this + 0x40);
  int tmp;
  void *fn = (void *)0x5e3fa0;                                       /* _ftol2 */
  unsigned lo, hi;
  __asm__ volatile(
      "movl %[d], %%edx\n\t"          /* _ftol2's fast path passes EDX through */
      "fildl %[a]\n\t"
      "fidivl %[b]\n\t"
      "fstps %[tmp]\n\t"              /* round the ratio to float */
      "flds %[tmp]\n\t"
      "fimull %[d]\n\t"               /* ratio * (param_1 - this[0x40]) in extended precision */
      "fildl %[c]\n\t"
      "faddl %[k]\n\t"
      "faddp %%st, %%st(1)\n\t"
      "movl %[th], %%ecx\n\t"         /* _ftol2's fast path preserves ECX */
      "call *%[fn]\n\t"
      : "=a"(lo), "=d"(hi), [tmp] "=m"(tmp)
      : [a] "m"(a), [b] "m"(b), [c] "m"(c), [d] "m"(d),
        [k] "m"(*(double *)d_00607CE0), [th] "m"(this), [fn] "m"(fn)
      : "ecx", "memory", "st", "ebp");
  return ((ulonglong)hi << 32) | lo;
}
