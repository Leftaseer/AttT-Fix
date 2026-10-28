/* 0x00593C80: CUniBuffer::GetPriorItemPos (DXUT): the start of the word before pos (Uniscribe's logical attributes,
 * ScriptString_pLogAttr / ScriptString_pcOutChars through the pointers at 0x6C8298 / 0x6C829C): a word stop (8), or
 * a non-space after a space (2); 0 at the start */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00593770(void *self);
DECOMP_C char d_006C8298[], d_006C829C[];
typedef unsigned char *(__stdcall *pLogAttr_593C80)(void *ssa);
typedef int *(__stdcall *pcOutChars_593C80)(void *ssa);

DECOMP(00593C80)
void __thiscall f_00593C80(void *this, int pos, int *out)
{
    char *s = (char *)this;
    unsigned char *attr;
    int i;
    *out = pos;
    if (s[0xc] && sub_00593770(this) < 0)
        return;
    attr = (*(pLogAttr_593C80 *)d_006C8298)(*(void **)(s + 0x10));
    if (!attr || !(*(pcOutChars_593C80 *)d_006C829C)(*(void **)(s + 0x10)))
        return;
    i = *(*(pcOutChars_593C80 *)d_006C829C)(*(void **)(s + 0x10));
    if (pos - 1 < i)
        i = pos - 1;
    for (; i > 0; i--)
        if ((attr[i] & 8) || (!(attr[i] & 2) && (attr[i - 1] & 2))) {
            *out = i;
            return;
        }
    *out = 0;
}
