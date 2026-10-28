/* 0x0047B8C0: a GUI element constructor (f1, the item s2, s3..s5, s6 unused, d7): the base (0x00588480 at (0, 0)
 * with two empty strings), the vtables, the delay +0x2D4 = twice the item's +0x14 (as unsigned) times the double at
 * 0x60A700, truncated, at least 35, +0x2D8 = d7, and its slot from the registry (0x6CA0E0: 0x0047C070) at +0x2E0
 * (the original destroys the strings if the base throws; this C does not) */
/* @conv ECX 28 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00588480(void *self, float x, float y, float f1, void *s2, void *s3, void *s4, void *s5,
                                      float scale, unsigned int z9, void *sb, void *sa, unsigned int z12,
                                      unsigned int z13, float z14, float z15);
DECOMP_C unsigned int *__thiscall sub_0047C070(void *self, void *out, void *o);
DECOMP_C char d_0060FA8B[], d_0060EF7C[], d_0060EF70[], d_0060A700[], d_006CA0E0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0047B8C0)
void *__thiscall f_0047B8C0(void *this, float f1, char *s2, void *s3, void *s4, void *s5, unsigned int s6,
                            unsigned int d7)
{
    char *s = (char *)this;
    unsigned int sa[7], sb[7], out, n;
    imp_00607324(sa, d_0060FA8B);
    imp_00607324(sb, d_0060FA8B);
    sub_00588480(this, 0.0f, 0.0f, f1, s2, s3, s4, s5, 1.0f, 0, sb, sa, 0, 0, 0.0f, 0.0f);
    imp_00607330(sb);
    imp_00607330(sa);
    *(void **)s = d_0060EF7C;
    *(void **)(s + 0x214) = d_0060EF70;
    *(unsigned int *)(s + 0x2e0) = 0;
    n = (unsigned int)(long long)((double)(unsigned int)(*(int *)(s2 + 0x14) * 2) * *(double *)d_0060A700);
    *(unsigned int *)(s + 0x2d4) = n;
    if (n < 0x23)
        *(unsigned int *)(s + 0x2d4) = 0x23;
    *(unsigned int *)(s + 0x2d8) = d7;
    *(unsigned int *)(s + 0x2dc) = 0;
    *(unsigned int *)(s + 0x2e0) = *sub_0047C070(*(void **)d_006CA0E0, &out, this);
    s[0x2e4] = 0;
    s[0x2e5] = 0;
    return this;
}
