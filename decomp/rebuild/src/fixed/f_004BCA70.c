/* 0x004BCA70: reads a vector of 100-byte records from the stream: the count (4 bytes, 0x00458F80), resize
 * (0x004BC3E0, with a default record by value: only its string at +0x44 constructed, the rest as the stack has it),
 * then each record (0x004BC010) */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { unsigned int d[25]; } Rec_4BCA70;
DECOMP_C void __thiscall sub_00458F80(void *stream, void *dst, int size);
DECOMP_C void __thiscall sub_004BC3E0(void *vec, unsigned int n, Rec_4BCA70 val);
DECOMP_C void __thiscall sub_004BC010(void *rec, void *stream);
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(004BCA70)
void __cdecl f_004BCA70(void *stream, void *vec)
{
    unsigned int n, i;
    Rec_4BCA70 val;
    sub_00458F80(stream, &n, 4);
    imp_006071E0(&val.d[0x44 / 4]);
    sub_004BC3E0(vec, n, val);
    for (i = 0; i < n; i++)
        sub_004BC010(*(char **)((char *)vec + 4) + i * 100, stream);
}
