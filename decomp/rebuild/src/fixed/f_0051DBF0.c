/* 0x0051DBF0: two forms of "the index with its low byte replaced by the byte at index + offset" (the original
 * loads the index into EAX for the address and writes AL).  clang 18 for i686 folds "(x & ~0xFF) | zext(load)"
 * into the zero-extended load alone when the load's address uses x, and the top 24 bits are lost: the byte goes
 * in through asm, which gives the original's mov al */
#include "auto_pre.h"
/* @func 0051DBF0 */
DECOMP(0051DBF0)
undefined4 __thiscall f_0051DBF0(void *this, int gh_arg1, char gh_arg2)
{
#define param_1 (*(int *)(gh_args + 0))
#define param_2 (*(char *)(gh_args + 4))
  unsigned char *gh_args = (unsigned char *)__builtin_frame_address(0) + 8;
  if ((*(char *)((int)this + 0x48) != '\0') && (param_2 != '\0')) {
    unsigned int r = *(int *)((int)this + 0x7c);
    __asm__("movb %1, %b0" : "+q"(r) : "m"(*(unsigned char *)(param_1 + r)));
    return r;
  }
  unsigned int r = (unsigned int)param_1;
  __asm__("movb %1, %b0" : "+q"(r) : "m"(*(unsigned char *)(param_1 + *(int *)((int)this + 0x70))));
  return r;
}
