/* 0x00532450: CNpc::Tick: the base tick (0x004AC690, with EAX as it came), the model's vf14 (+0x260), the walk
 * (0x004CB070 of +0x270), vf80 into +0x368, the countdown at +0x314 while +0x310 (ending it sets +0x31C), and with no
 * target (+0x2DC) a free model takes the walk at +0x264 */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 00532450 custom */
DECOMP_C void __cdecl sub_004AC690(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_004CB070(void *self);
typedef char (__thiscall *vf_532450)(void *self);
typedef float (__thiscall *vf80_532450)(void *self);

DECOMP(00532450)
void __cdecl f_00532450(void *this, unsigned int eax)
{
    char *s = (char *)this;
    void **m;
    sub_004AC690(this, eax);
    m = *(void ***)(s + 0x260);
    ((vf_532450)(*(void ***)m)[0x14 / 4])(m);
    sub_004CB070(*(void **)(s + 0x270));
    *(float *)(s + 0x368) = ((vf80_532450)(*(void ***)this)[0x80 / 4])(this);
    if (s[0x310] && --*(int *)(s + 0x314) == 0) {
        s[0x31c] = 1;
        s[0x310] = 0;
    }
    if (!*(int *)(s + 0x2dc)) {
        m = *(void ***)(s + 0x260);
        if (((vf_532450)(*(void ***)m)[0xe4 / 4])(m))
            *(unsigned int *)(s + 0x270) = *(unsigned int *)(s + 0x264);
    }
}
