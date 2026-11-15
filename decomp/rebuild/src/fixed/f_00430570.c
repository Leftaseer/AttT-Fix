/* 0x00430570: CBaseMeshObject3D vf48: unless the flag at +0x49 is clear (then the input EAX passes through),
 * releases 0x4AC890 and draws every sub-object of the object at +0x3C: slot 0x18 counts them into a local,
 * slot 0x20 selects the i-th one, the mesh at +0x1C4 is drawn with the argument, slot 0x24 finishes it and
 * slot 0x1C closes the pass, whose result becomes the return value. */
/* @conv EAX,ECX 4 */
/* @func 00430570 custom */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C undefined4 __thiscall sub_00477610(void *self, unsigned int p1, unsigned int p2);
typedef void (__thiscall *vf_430570_begin)(void *self, unsigned int *count, int zero);
typedef void (__thiscall *vf_430570_one)(void *self, unsigned int index);
typedef int (__thiscall *vf_430570_end)(void *self);

DECOMP(00430570)
int __cdecl f_00430570(undefined4 in_eax, char *this, undefined4 arg)
{
    char *o;
    unsigned int count = 0, i;

    if (!this[0x49])
        return in_eax;
    sub_004AC890(this);
    o = *(char **)(this + 0x3c);
    ((vf_430570_begin)(*(void ***)o)[0x18 / 4])(o, &count, 0);
    for (i = 0; i < count; i++) {
        o = *(char **)(this + 0x3c);
        ((vf_430570_one)(*(void ***)o)[0x20 / 4])(o, i);
        sub_00477610(*(void **)(this + 0x1c4), *(unsigned int *)(this + 0x1d8), arg);
        o = *(char **)(this + 0x3c);
        ((vf_430570_end)(*(void ***)o)[0x24 / 4])(o);
    }
    o = *(char **)(this + 0x3c);
    return ((vf_430570_end)(*(void ***)o)[0x1c / 4])(o);
}
