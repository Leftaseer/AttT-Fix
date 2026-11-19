/* 0x005E218A: a four-argument wrapper (the CRT's checked count path): a count above 0x7FFFFFFF is rejected
 * with E_INVALIDARG (0x80070057) before anything else happens, otherwise the three arguments are forwarded
 * to 0x005B818A together with the address of the fourth caller slot (the start of the caller's argument
 * continuation, used there as the variable part).  The callee pops its own four dwords, so the wrapper
 * returns without touching the stack; its EAX is the callee's result. */
#include "auto_pre.h"
DECOMP_C long __stdcall sub_005B818A(void *arg0, unsigned int count, void *arg2, void *arg3);

DECOMP(005E218A)
long __cdecl f_005E218A(void *arg0, unsigned int count, void *arg2, void *arg3)
{
    if (count > 0x7FFFFFFF)
        return 0x80070057;
    return sub_005B818A(arg0, count, arg2, &arg3);
}
