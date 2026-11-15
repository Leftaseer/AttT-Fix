/* 0x004253D0: C3DLine::~C3DLine: stores the vtable 0x00607DB4 and drops the shared line effect's reference count
 * (0x006C8710); the drop to zero releases the effect (0x006C870C, its slot 0x6C).  A non-null object at +0x1C4 is
 * released through the second slot of its vtable (the vtable comes in ECX, the object on the stack) and cleared,
 * then the CRenderObject3D base destructor (0x004AD020) runs. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607DB4[];
DECOMP_C void *d_006C870C;
DECOMP_C int d_006C8710;
DECOMP_C void __thiscall sub_004AD020(void *self);
typedef void (__thiscall *vf_4253D0)(void *self, void *arg);

DECOMP(004253D0)
void __thiscall f_004253D0(void *this)
{
    char *s = (char *)this;
    void **obj;
    *(const void **)s = d_00607DB4;
    if (--d_006C8710 == 0)
        ((void (__thiscall *)(void *))((void **)(*(void **)d_006C870C))[0x6c / 4])(d_006C870C);
    obj = *(void ***)(s + 0x1c4);
    if (obj) {
        void *vt = (void *)*obj;
        ((vf_4253D0)((void **)vt)[2])(vt, obj);
        *(void **)(s + 0x1c4) = 0;
    }
    sub_004AD020(s);
}
