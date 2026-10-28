/* 0x0047D880: MusicManager::Update: numpad 7 / 9 (GetKeyState) lower / raise the music volume (+0xA8) by 0x006082A0
 * within 0..0x0068AE40, applied to the channel group +0xAC (0x00427CE0) and the settings (0x00427990, +0x88). With no
 * transition running (+0x84 at 0) and the track (+0x8C) finished (vf20), the state (+0x68) is replayed (cleared and
 * 0x0047D5C0 with a copy over 1 frame). A transition step fades the old track (+0x9C less +0x94) and the new one
 * (+0xA0 plus +0x98); its last step settles them at 0 and full (0x0047D140, +0xA4 cleared); both volumes are applied
 * (vf18). The EAX input of 0x00427CE0 and 0x0047D140 only passes through them; it is approximated here */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int (__stdcall *imp_006076D0)(int) __asm__("__imp__GetKeyState@4");   /* (the SHORT in AX, as EAX) */
DECOMP_C void __cdecl sub_00427CE0(void *self, unsigned int eax, float v);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __thiscall sub_0047D5C0(void *self, void *state, unsigned int frames);
DECOMP_C void __cdecl sub_0047D140(void *self, unsigned int eax);
DECOMP_C char d_0068AE40[], d_006082A0[], d_0060FA8B[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef char (__thiscall *vfb_47D880)(void *self);
typedef void (__thiscall *vol_47D880)(void *self, float v, int a);

static void set_47D880(char *s, float v, unsigned int k)
{
    if (0.0f > v)
        v = 0.0f;
    else if (v > *(float *)d_0068AE40)
        v = *(float *)d_0068AE40;
    sub_00427CE0(s + 0xac, k, v);
    *(float *)(s + 0xa8) = v;
    *(float *)(sub_00427990() + 0x88) = v;
}

DECOMP(0047D880)
void __thiscall f_0047D880(void *this)
{
    char *s = (char *)this;
    unsigned int k;
    void **t;
    int c;
    k = imp_006076D0(0x67);
    if ((short)k < 0)
        set_47D880(s, (float)(*(float *)(s + 0xa8) - *(double *)d_006082A0), k);
    k = imp_006076D0(0x69);
    if ((short)k < 0)
        set_47D880(s, (float)(*(float *)(s + 0xa8) + *(double *)d_006082A0), k);
    if (!*(int *)(s + 0x84)) {
        unsigned int copy[7];
        t = *(void ***)(s + 0x8c);
        if (!t || ((vfb_47D880)(*(void ***)t)[0x20 / 4])(t))
            return;
        imp_00607334(copy, s + 0x68);
        imp_006072F8(s + 0x68, d_0060FA8B);
        sub_0047D5C0(this, copy, 1);
        imp_00607330(copy);
    }
    c = --*(int *)(s + 0x84);
    *(float *)(s + 0x9c) = *(float *)(s + 0x9c) - *(float *)(s + 0x94);
    *(float *)(s + 0xa0) = *(float *)(s + 0x98) + *(float *)(s + 0xa0);
    if (!c) {
        *(float *)(s + 0x9c) = 0.0f;
        *(unsigned int *)(s + 0xa0) = *(unsigned int *)d_0068AE40;
        sub_0047D140(this, k);
        s[0xa4] = 0;
    }
    t = *(void ***)(s + 0x8c);
    if (t)
        ((vol_47D880)(*(void ***)t)[0x18 / 4])(t, *(float *)(s + 0x9c), 0);
    t = *(void ***)(s + 0x90);
    if (t)
        ((vol_47D880)(*(void ***)t)[0x18 / 4])(t, *(float *)(s + 0xa0), 0);
}
