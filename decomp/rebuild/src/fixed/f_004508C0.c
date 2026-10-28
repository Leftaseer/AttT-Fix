/* 0x004508C0: NSFileSystem::CArchFile::vf1 (read n bytes into buf): seeks the archive stream (+0xC) to the file's
 * start (+0x14) plus the position (+0x10), reads, and for an encrypted file (+0x18) XORs the part within its first
 * 16 bytes with the key at 0x6C04B4; the position advances; the range read is noted at 0x6C8D6C/0x6C8D68; returns
 * where the decryption stopped */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int off, pad, fpos_lo, fpos_hi, state, pad2; } Fpos_4508C0;   /* std::fpos<_Mbstatet> */
DECOMP_C char d_006C04B4[], d_006C8D6C[], d_006C8D68[];
DECOMP_C void *(__thiscall *imp_006072D0)(void *, Fpos_4508C0) __asm__("__imp_?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@V?$fpos@H@2@@Z");
DECOMP_C void *(__thiscall *imp_006071A0)(void *, char *, int) __asm__("__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");

DECOMP(004508C0)
unsigned int __thiscall f_004508C0(void *this, char *buf, unsigned int n)
{
    char *s = (char *)this;
    Fpos_4508C0 pos = { *(unsigned int *)(s + 0x14) + *(unsigned int *)(s + 0x10), 0, 0, 0, 0, 0 };
    unsigned int i, end;
    imp_006072D0(*(void **)(s + 0xc), pos);
    imp_006071A0(*(void **)(s + 0xc), buf, n);
    i = *(unsigned int *)(s + 0x10);
    end = i + n;
    *(unsigned int *)d_006C8D6C = i;
    *(unsigned int *)d_006C8D68 = end;
    if (s[0x18] && i < 0x10) {
        char *b = buf - i;
        for (; i < end; ) {
            b[i] ^= d_006C04B4[i];
            if (++i >= 0x10)
                break;
        }
    }
    *(unsigned int *)(s + 0x10) += n;
    return i;
}
