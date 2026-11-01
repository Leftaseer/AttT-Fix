/* 0x00473B40: returns the byte at this->0xc + this->0x14 * param_2 + param_1, with EAX's upper three bytes
 * still holding the index (the original is `mov (%eax,%ecx,1),%al`).  Written as CONCAT31 the rebuilt code
 * is wrong: clang's 32-bit backend folds `(i & 0xffffff00) | *(unsigned char *)(addr(i))` into a bare
 * movzbl, so EAX came back as just the byte (0 instead of the index's high part).  The AL store is spelled
 * out instead. */
#include "auto_pre.h"
/* @func 00473B40 */

DECOMP(00473B40)
unsigned int __thiscall f_00473B40(void *this, int param_1, int param_2)
{
    unsigned int a = *(unsigned int *)((char *)this + 0x14) * param_2 + *(unsigned int *)((char *)this + 0xc);
    unsigned char b = *(unsigned char *)(a + param_1);
    __asm__ ("movb %b1, %b0" : "+r" (a) : "r" ((unsigned int)b));
    return a;
}
