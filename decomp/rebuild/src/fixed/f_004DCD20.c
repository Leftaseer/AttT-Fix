/* 0x004DCD20: CTestShaderScene::CTestShaderScene: the CScene base (0x004B20D0(0)), the vtables, its viewer mesh at
 * +0x84 and 10000 more at +0xE8 (`eh vector constructor iterator', CViewerMesh 0x004F7A40 / ~ 0x004F7AD0), and its
 * settings zeroed (the original destroys the base if a member constructor throws; this C does not) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B20D0(void *self, int a);
DECOMP_C void __thiscall sub_004F7A40(void *self);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C char d_0061246C[], d_0061244C[], d_004F7A40[], d_004F7AD0[];

DECOMP(004DCD20)
void *__thiscall f_004DCD20(void *this)
{
    char *s = (char *)this;
    unsigned int o;
    sub_004B20D0(this, 0);
    *(void **)s = d_0061246C;
    *(void **)(s + 4) = d_0061244C;
    sub_004F7A40(s + 0x84);
    sub_005E4197(s + 0xe8, 100, 10000, d_004F7A40, d_004F7AD0);
    for (o = 0xf4384; o <= 0xf4404; o += 4)
        *(float *)(s + o) = 0.0f;
    s[0xf43bc] = 0;                     /* (bytes of the same range) */
    s[0xf43c4] = 0;
    s[0xf4400] = 0;
    s[0xf4408] = 0;
    *(unsigned int *)(s + 0x78) = 0;
    *(unsigned int *)(s + 0x74) = 0;
    *(unsigned int *)(s + 0xf4334) = 0;
    *(unsigned int *)(s + 0xf4338) = 0;
    return this;
}
