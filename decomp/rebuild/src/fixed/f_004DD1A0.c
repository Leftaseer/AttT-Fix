/* 0x004DD1A0: CTestShaderScene::~CTestShaderScene: the vtables, deletes its three objects (+0xF4328, +0xF4334,
 * +0xF4338), releases the two shared ones (0x6CA6C4, 0x6CA6C0: their counts at +4), destroys the 10000 viewer meshes
 * at +0xE8 (100 bytes each) and the one at +0x84 (CViewerMesh::~CViewerMesh), then the CScene base */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void __thiscall sub_004F7AD0(void *self);
DECOMP_C void __thiscall sub_004B2010(void *self);
DECOMP_C char d_0061246C[], d_0061244C[], d_006CA6C4[], d_006CA6C0[], d_004F7AD0[];
typedef void (__thiscall *dtor_4DD1A0)(void *self, int flags);

#define DELETE(o) ((dtor_4DD1A0)(*(void ***)(o))[0])((o), 1)

DECOMP(004DD1A0)
void __thiscall f_004DD1A0(void *this)
{
    char *s = (char *)this;
    static const unsigned int offs[3] = { 0xf4328, 0xf4334, 0xf4338 };
    char *p;
    int i;
    *(void **)s = d_0061246C;
    *(void **)(s + 4) = d_0061244C;
    for (i = 0; i < 3; i++)
        if (*(void **)(s + offs[i])) {
            DELETE(*(void **)(s + offs[i]));
            *(void **)(s + offs[i]) = 0;
        }
    p = *(char **)d_006CA6C4;
    if (--*(int *)(p + 4) == 0)
        DELETE(p);
    p = *(char **)d_006CA6C0;
    if (--*(int *)(p + 4) == 0)
        DELETE(p);
    sub_005E4134(s + 0xe8, 100, 10000, d_004F7AD0);
    sub_004F7AD0(s + 0x84);
    sub_004B2010(this);
}
