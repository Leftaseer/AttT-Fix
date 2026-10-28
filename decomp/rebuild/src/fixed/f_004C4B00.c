/* 0x004C4B00: NSound::Sound3D::vf13: vf08, loads the sound named by the string (0x004C46E0 of the sound manager:
 * the buffers at +0x5C and +0x60, the length at +0x34), reads the 3D parameters of the buffer at +0x5C (COM slot 3,
 * the size 0x14 at +0x48 first), marks it loaded (+8) and calls vf18(1.0, 1), returning its result */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004C46E0(void *mgr, void *name, void *buf, void *buf3d, void *len);
DECOMP_C char d_006CA4B4[];
typedef void (__thiscall *vf08_4C4B00)(void *self);
typedef long (__stdcall *com3_4C4B00)(void *self, void *params);
typedef unsigned int (__thiscall *vf18_4C4B00)(void *self, float volume, int flag);

DECOMP(004C4B00)
unsigned int __thiscall f_004C4B00(void *this, void *name)
{
    char *s = (char *)this;
    void **buf;
    ((vf08_4C4B00)(*(void ***)this)[2])(this);
    sub_004C46E0(*(void **)d_006CA4B4, name, s + 0x5c, s + 0x60, s + 0x34);
    buf = *(void ***)(s + 0x5c);
    *(unsigned int *)(s + 0x48) = 0x14;
    ((com3_4C4B00)(*(void ***)buf)[3])(buf, s + 0x48);
    s[8] = 1;
    return ((vf18_4C4B00)(*(void ***)this)[0x18 / 4])(this, 1.0f, 1);
}
