/* 0x00582870: nGUI::iGUIElement::Update (dt; EAX passed through to the base): its time (+0x260) grows; when enabled
 * (+0x49) the base updates (0x004ABE70); the cursor (0x00421680 vf88) over it (vf FC(pos, 1)) sets hover (+0x254, vf108
 * on entering, vf10C and +0x255 cleared on leaving). Its tooltip (+0x26C, while +0x264): with the mouse still (0x004215D0
 * +0x7C9 clear) the hover time (+0x268) grows and after K (0x00609648) a ready tooltip (vf60) replaces the shown one
 * (0x008D1234, vf50 hides it), goes to the cursor plus 0x0061E230 (vf6C) and shows (vf4C, vf18); a moving mouse moves a
 * tooltip that is due, else resets the time and hides a shown one (vf5C, vf50). The mouse log (+0x66C / +0x670): a left
 * press over it starts a press (+0x255, its time +0x258 and repeat +0x25C cleared, vf100), a release ends it; a held
 * press repeats vf100 each K after the delay 0x0060A208 when it may repeat (+0x28C). Returns what the original leaves
 * in EAX, approximated */
/* @conv ECX,EAX 4 */
/* @func 00582870 custom */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_004ABE70(void *self, unsigned int eax, float dt);
DECOMP_C char *__cdecl sub_00421680(void);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C char d_00609648[], d_0061E230[], d_0060A208[], d_008D1234[];
typedef int (__thiscall *vf_582870)(void *self);
typedef float *(__thiscall *pos_582870)(void *self);
typedef char (__thiscall *hit_582870)(void *self, float *pos, int a);
typedef int (__thiscall *set_582870)(void *self, float *pos);

#define VT(o) (*(void ***)(o))
#define K (*(double *)d_00609648)

static float *cursor_582870(void)
{
    char *c = sub_00421680();
    return ((pos_582870)VT(c)[0x88 / 4])(c);
}

static int show_582870(char *s)
{
    char *t = *(char **)d_008D1234, *tip;
    float *p, v[2];
    if (t)
        ((vf_582870)VT(t)[0x50 / 4])(t);
    *(void **)d_008D1234 = *(void **)(s + 0x26c);
    p = cursor_582870();
    v[1] = (float)(p[1] + *(double *)d_0061E230);
    v[0] = (float)(*(double *)d_0061E230 + p[0]);
    tip = *(char **)(s + 0x26c);
    ((set_582870)VT(tip)[0x6c / 4])(tip, v);
    tip = *(char **)(s + 0x26c);
    ((vf_582870)VT(tip)[0x4c / 4])(tip);
    tip = *(char **)(s + 0x26c);
    return ((vf_582870)VT(tip)[0x18 / 4])(tip);
}

DECOMP(00582870)
unsigned int __cdecl f_00582870(void *this, unsigned int eax, float dt)
{
    char *s = (char *)this, *m, *tip;
    unsigned int i, n, *log;
    int r = 0;
    float t;
    *(float *)(s + 0x260) = dt + *(float *)(s + 0x260);
    if (!s[0x49])
        return eax;
    sub_004ABE70(this, eax, dt);
    if (((hit_582870)VT(s)[0xfc / 4])(s, cursor_582870(), 1)) {
        if (!s[0x254]) {
            s[0x254] = 1;
            ((vf_582870)VT(s)[0x108 / 4])(s);
        }
    } else if (s[0x254]) {
        s[0x254] = 0;
        s[0x255] = 0;
        ((vf_582870)VT(s)[0x10c / 4])(s);
    }
    m = sub_004215D0();
    if (!m[0x7c9]) {
        if (s[0x264]) {
            t = *(float *)(s + 0x268) + dt;
            *(float *)(s + 0x268) = t;
            tip = *(char **)(s + 0x26c);
            if (!(t < K) && tip && ((char (__thiscall *)(void *))VT(tip)[0x60 / 4])(tip))
                r = show_582870(s);
        }
    } else if (s[0x264] && *(void **)(s + 0x26c) && !(*(float *)(s + 0x268) < K))
        r = show_582870(s);
    else {
        *(float *)(s + 0x268) = 0;
        tip = *(char **)(s + 0x26c);
        if (tip && ((char (__thiscall *)(void *))VT(tip)[0x5c / 4])(tip)) {
            *(void **)d_008D1234 = tip;
            tip = *(char **)(s + 0x26c);
            r = ((vf_582870)VT(tip)[0x50 / 4])(tip);
        }
    }
    m = sub_004215D0();
    n = *(unsigned int *)(m + 0x670);
    log = *(unsigned int **)(m + 0x66c);
    for (i = 0; i < n; i++) {
        if (log[i] == 0) {
            if (s[0x254]) {
                s[0x255] = 1;
                *(float *)(s + 0x258) = 0;
                s[0x25c] = 0;
                r = ((vf_582870)VT(s)[0x100 / 4])(s);
            }
        } else if (log[i] == 1 && s[0x254])
            s[0x255] = 0;
    }
    if (!s[0x255])
        return (unsigned int)r;
    t = dt + *(float *)(s + 0x258);
    *(float *)(s + 0x258) = t;
    if (s[0x25c]) {
        while (t > K) {
            r = ((vf_582870)VT(s)[0x100 / 4])(s);
            t = (float)(*(float *)(s + 0x258) - K);
            *(float *)(s + 0x258) = t;
        }
    } else if (t > *(double *)d_0060A208 && s[0x28c]) {
        s[0x25c] = 1;
        *(float *)(s + 0x258) = 0;
    }
    return (unsigned int)r;
}
