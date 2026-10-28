/* 0x00593D10: CUniBuffer::GetNextItemPos (DXUT): the start of the word after pos (Uniscribe's logical attributes,
 * ScriptString_pLogAttr / ScriptString_pcOutChars through the pointers at 0x6C8298 / 0x6C829C): a word stop (8), or
 * the character after a space (2) that is not one; the last character at the end */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00593770(void *self);
DECOMP_C char d_006C8298[], d_006C829C[];
typedef unsigned char *(__stdcall *pLogAttr_593D10)(void *ssa);
typedef int *(__stdcall *pcOutChars_593D10)(void *ssa);

#define OUTCHARS() (*(pcOutChars_593D10 *)d_006C829C)(*(void **)(s + 0x10))

DECOMP(00593D10)
void __thiscall f_00593D10(void *this, int pos, int *out)
{
    char *s = (char *)this;
    unsigned char *attr;
    int i;
    *out = pos;
    if (s[0xc] && sub_00593770(this) < 0)
        return;
    attr = (*(pLogAttr_593D10 *)d_006C8298)(*(void **)(s + 0x10));
    if (!attr || !OUTCHARS())
        return;
    i = *OUTCHARS();
    if (pos + 1 < i)
        i = pos + 1;
    if (i < *OUTCHARS() - 1)
        do {
            if (attr[i] & 8) {
                *out = i;
                return;
            }
            if ((attr[i] & 2) && !(attr[i + 1] & 2)) {
                *out = i + 1;
                return;
            }
            i++;
        } while (i < *OUTCHARS() - 1);
    *out = *OUTCHARS() - 1;
}
