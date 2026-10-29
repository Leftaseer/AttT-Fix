/* 0x0059A660: CDXUTDialog::DrawText for a narrow string (text, element, rect, shadow, count): nothing for a fully
 * transparent font colour (element +0x68 alpha); the rect moves by the dialog's position (+0x174 / +0x178) and, with a
 * caption (+0x71), its height (+0x184); the manager's (0x00599A20) sprite (+4) gets the identity transform (vf14) and
 * the element's font (+4, through the dialog's font list +0x1A8 and the manager's cache +0x14; none without a manager)
 * draws (its ID3DXFont +0x104, DrawTextA vf38) with the element's format (+8): first a black shadow one pixel off in
 * the colour's alpha, then the text in the colour (+0x5C..+0x68 r, g, b, a as D3DXCOLOR's DWORD). Returns the failing
 * HRESULT or S_OK */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00599A20(void);
DECOMP_C char d_0060FAC0[], d_0068AE40[], d_00609620[], d_00607CE0[];
DECOMP_C int (__stdcall *imp_00607638)(void *, int, int) __asm__("__imp__OffsetRect@12");
typedef int (__stdcall *settf_59A660)(void *sprite, const float *m);
typedef int (__stdcall *draw_59A660)(void *font, void *sprite, const void *text, int count, void *rect,
                                     unsigned int format, unsigned int color);

#define K255 (*(double *)d_00609620)

static unsigned int byte_59A660(float v)
{
    if (v >= *(float *)d_0068AE40)
        return 0xff;
    if (0.0f >= v)
        return 0;
    return (unsigned int)(long long)(v * K255 + *(double *)d_00607CE0);
}

DECOMP(0059A660)
int __thiscall f_0059A660(void *this, const void *text, char *el, const int *rect, unsigned char shadow, int count)
{
    char *s = (char *)this, *mgr, *node;
    int rc[4], i;
    float m[16];
    unsigned int c;
    void *font;
    int hr;
    if (*(float *)(el + 0x68) == *(float *)d_0060FAC0)
        return 0;
    rc[0] = rect[0];
    rc[1] = rect[1];
    rc[2] = rect[2];
    rc[3] = rect[3];
    imp_00607638(rc, *(int *)(s + 0x174), *(int *)(s + 0x178));
    if (s[0x71])
        imp_00607638(rc, 0, *(int *)(s + 0x184));
    for (i = 0; i < 16; i++)
        m[i] = 0.0f;
    m[0] = m[5] = m[10] = m[15] = *(float *)d_0068AE40;
    mgr = sub_00599A20();
    ((settf_59A660)(*(void ***)*(void **)(mgr + 4))[0x14 / 4])(*(void **)(mgr + 4), m);
    i = *(int *)(el + 4);
    if (!sub_00599A20())
        node = 0;
    else {
        int k = (*(int **)(s + 0x1a8))[i];
        node = (*(char ***)(sub_00599A20() + 0x14))[k];
    }
    if (shadow) {
        int sh[4];
        sh[0] = rc[0];
        sh[1] = rc[1];
        sh[2] = rc[2];
        sh[3] = rc[3];
        imp_00607638(sh, 1, 1);
        c = (unsigned int)(long long)(*(float *)(el + 0x68) * K255) << 24;
        font = *(void **)(node + 0x104);
        hr = ((draw_59A660)(*(void ***)font)[0x38 / 4])(font, *(void **)(sub_00599A20() + 4), text, count, sh,
                                                         *(unsigned int *)(el + 8), c);
        if (hr < 0)
            return hr;
    }
    {
        unsigned int r = byte_59A660(*(float *)(el + 0x5c)), g = byte_59A660(*(float *)(el + 0x60));
        unsigned int b = byte_59A660(*(float *)(el + 0x64)), a = byte_59A660(*(float *)(el + 0x68));
        c = ((((a << 8) | r) << 8 | g) << 8) | b;
    }
    font = *(void **)(node + 0x104);
    hr = ((draw_59A660)(*(void ***)font)[0x38 / 4])(font, *(void **)(sub_00599A20() + 4), text, count, rc,
                                                     *(unsigned int *)(el + 8), c);
    return hr < 0 ? hr : 0;
}
