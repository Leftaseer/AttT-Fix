/* 0x0054A7B0: asks the context at +0x14 through the function at +0xC for a 12-byte record, written into a local
 * that the callee also returns, and copies it to the caller's output (which is returned). */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void *(__thiscall *vf_54A7B0)(void *self, void *record, void *owner);

DECOMP(0054A7B0)
void *__thiscall f_0054A7B0(char *this, void *out)
{
    unsigned int record[3];
    void *result;

    result = ((vf_54A7B0)(*(void **)(this + 0xc)))(*(void **)(this + 0x14), record, this);
    ((unsigned int *)out)[0] = ((unsigned int *)result)[0];
    ((unsigned int *)out)[1] = ((unsigned int *)result)[1];
    ((unsigned int *)out)[2] = ((unsigned int *)result)[2];
    return out;
}
