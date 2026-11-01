/* 0x00507E40: the offset field with its low byte replaced by the byte at param_1 + offset (the original loads the
 * offset into EAX for the address and writes AL).  clang 18 for i686 folds "(x & ~0xFF) | zext(load)" into the
 * zero-extended load alone when the load's address uses x, and the top 24 bits are lost: the byte goes in through
 * asm, which gives the original's mov al */
#include "auto_pre.h"
/* @func 00507E40 */
DECOMP(00507E40)
undefined4 __thiscall f_00507E40(void *this, int param_1)
{
  unsigned int off = *(int *)((int)this + 0x7c);
  __asm__("movb %1, %b0" : "+q"(off) : "m"(*(unsigned char *)(param_1 + off)));
  return off;
}
