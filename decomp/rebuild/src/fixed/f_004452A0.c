/* 0x004452A0: parses a number (string by value, out float): after appending a NUL, a state machine reads an optional
 * sign, digits, a point and fraction digits (each character through operator[], isdigit); a well-formed number ending
 * at the NUL is stored (negated as 0x00608088 - value) and the result is 1, anything else gives 0. Destroys its
 * by-value string */
/* @conv - 32 */
#include "auto_pre.h"
DECOMP_C char d_0060A568[], d_006089A0[], d_0068AE08[], d_00608088[];
DECOMP_C void *(__thiscall *imp_00607204)(void *, char) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@D@Z");
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C int (__cdecl *imp_00607418)(int) __asm__("__imp__isdigit");

#define AT(i) (*imp_00607208(str, i))

DECOMP(004452A0)
unsigned char __stdcall f_004452A0(unsigned int w0, unsigned int w1, unsigned int w2, unsigned int w3,
                                   unsigned int w4, unsigned int w5, unsigned int w6, float *out)
{
    void *str = (char *)__builtin_frame_address(0) + 8;
    float v = 0.0f;
    unsigned int pos = 0, div = 1;
    int st = 0;
    char neg = 0, c;
    imp_00607204(str, 0);
    for (;;) {
        switch (st) {
        case 0:
            if (!AT(pos))
                goto fail;
            if (imp_00607418(AT(pos))) {
                v = (float)(AT(pos) - *(double *)d_0060A568);
                pos++;
                st = 2;
            } else if (AT(pos) == '.') {
                pos++;
                st = 5;
            } else if (AT(pos) == '-' || AT(pos) == '+') {
                if (AT(pos) == '-')
                    neg = 1;
                st = 1;
                pos += 1;
            } else
                goto fail;
            continue;
        case 1:
            if (imp_00607418(AT(pos)))
                st = 2;
            else if (AT(pos) == '.') {
                st = 4;
                pos++;
            } else
                goto fail;
            continue;
        case 2:
            if (imp_00607418(AT(pos))) {
                int d = AT(pos) - '0';
                pos++;
                v = (float)(v * *(double *)d_006089A0 + d);
                continue;
            }
            if (AT(pos) == '.') {
                pos++;
                st = 4;
                continue;
            }
            c = AT(pos);
            goto end;
        case 3:
            if (imp_00607418(AT(pos))) {
                int d;
                float q;
                div *= 10;
                d = AT(pos) - '0';
                q = (float)(int)div;
                if ((int)div < 0)
                    q += *(float *)d_0068AE08;
                pos++;
                v = (float)(d / q + v);
                continue;
            }
            c = AT(pos);
            goto end;
        case 4:
            if (imp_00607418(AT(pos))) {
                st = 3;
                continue;
            }
            c = AT(pos);
            goto end;
        case 5:
            if (!imp_00607418(AT(pos)))
                goto fail;
            st = 3;
            continue;
        }
    }
end:
    if (c)
        goto fail;
    *out = neg ? *(float *)d_00608088 - v : v;
    imp_00607330(str);
    return 1;
fail:
    imp_00607330(str);
    return 0;
}
