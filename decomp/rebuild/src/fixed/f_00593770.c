/* 0x00593770: CUniBuffer::Analyse (DXUT): frees the old analysis (+0x10, ScriptStringFree), digit substitution
 * defaults (ScriptApplyDigitSubstitution), then ScriptStringAnalyse of the text (+0) with the font's DC (+8, its
 * ID3DXFont at +0x104: GetDC) into +0x10; success clears the dirty flag (+0xC); E_FAIL without a font (usp10
 * through the pointers at 0x6C8284..0x6C8294) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006C8284[], d_006C8288[], d_006C8294[];
DECOMP_C int (__stdcall *imp_00607070)(const unsigned short *) __asm__("__imp__lstrlenW@4");
typedef long (__stdcall *Free_593770)(void *pssa);
typedef long (__stdcall *Digit_593770)(const void *sds, void *control, void *state);
typedef long (__stdcall *Analyse_593770)(void *hdc, const void *str, int n, int glyphs, int charset,
                                          unsigned int flags, int width, void *control, void *state,
                                          const int *dx, void *tabdef, const unsigned char *inclass, void *pssa);
typedef void *(__stdcall *GetDC_593770)(void *font);

DECOMP(00593770)
long __thiscall f_00593770(void *this)
{
    char *s = (char *)this;
    unsigned short state;           /* SCRIPT_STATE */
    unsigned int control;           /* SCRIPT_CONTROL */
    char *font;
    void *hdc;
    int glyphs, n;
    long hr;
    if (*(void **)(s + 0x10))
        (*(Free_593770 *)d_006C8294)(s + 0x10);
    control = 0;
    state = 0;
    (*(Digit_593770 *)d_006C8284)(0, &control, &state);
    font = *(char **)(s + 8);
    if (!font)
        return (long)0x80004005;
    if (*(void **)(font + 0x104)) {
        void **f = *(void ***)(font + 0x104);
        hdc = ((GetDC_593770)(*(void ***)f)[0x20 / 4])(f);
    } else
        hdc = 0;
    glyphs = imp_00607070(*(unsigned short **)s) * 3 / 2 + 0x10;
    n = imp_00607070(*(unsigned short **)s) + 1;
    hr = (*(Analyse_593770 *)d_006C8288)(hdc, *(void **)s, n, glyphs, -1, 0x10e0, 0, &control, &state, 0, 0, 0,
                                         s + 0x10);
    if (hr >= 0)
        s[0xc] = 0;
    return hr;
}
