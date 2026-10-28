/* 0x00428350: NSound::AmbientSoundManager::UpdateAt(where): numpad 4 / 6 held (GetKeyState) turn the ambient volume
 * (+0x94) down / up by the double at 0x6082A0, kept within 0 and the maximum at 0x68AE40 and passed on (0x00427CE0
 * of +0x98, which takes the GetKeyState result in EAX too; the sound system's +0x90); then the random restarts
 * (0x00428090) and, when the place (0x004270C0: two dwords) changed, it is kept (+0x80) and the sounds switched
 * (0x004281D0) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00427CE0(void *self, unsigned int eax, float volume);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __thiscall sub_00428090(void *self);
DECOMP_C void __thiscall sub_004270C0(void *self, unsigned int *out, unsigned int where);
DECOMP_C void __thiscall sub_004281D0(void *self);
DECOMP_C char d_006082A0[], d_0068AE40[];
DECOMP_C unsigned int (__stdcall *imp_006076D0)(int) __asm__("__imp__GetKeyState@4");   /* (the SHORT in AX, as EAX) */

DECOMP(00428350)
void __thiscall f_00428350(void *this, unsigned int where)
{
    char *s = (char *)this;
    unsigned int k, place[2];
    int i;
    for (i = 0; i < 2; i++) {
        float v;
        k = imp_006076D0(i ? 0x66 : 0x64);              /* VK_NUMPAD6, VK_NUMPAD4 */
        if ((short)k >= 0)
            continue;
        v = (float)(i ? *(float *)(s + 0x94) + *(double *)d_006082A0 : *(float *)(s + 0x94) - *(double *)d_006082A0);
        if (0.0f > v)
            v = 0.0f;
        else if (v > *(float *)d_0068AE40)
            v = *(float *)d_0068AE40;
        sub_00427CE0(s + 0x98, k, v);
        *(float *)(s + 0x94) = v;
        *(float *)(sub_00427990() + 0x90) = v;
    }
    sub_00428090(this);
    sub_004270C0(this, place, where);
    if (place[0] != *(unsigned int *)(s + 0x80) || place[1] != *(unsigned int *)(s + 0x84)) {
        *(unsigned int *)(s + 0x84) = place[1];
        *(unsigned int *)(s + 0x80) = place[0];
        sub_004281D0(this);
    }
}
