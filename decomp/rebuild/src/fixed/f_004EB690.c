/* 0x004EB690: CTriggersManager::CTriggersManager(owner): the CUpdateObject base with an empty name (0x00424D00), the
 * vtable, three 12-byte texture updaters at +0x38 (`eh vector constructor iterator', 0x004C38E0 /
 * TextureUpdator::~TextureUpdator), the owner at +0x5C (the original destroys the name string if the base throws;
 * this C does not) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00424D00(void *self, void *name, int flag);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C char d_0060FA8B[], d_00612B14[];
DECOMP_C char d_004C38E0[], d_0044D6E0[];                 /* (the code addresses themselves) */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(004EB690)
void *__thiscall f_004EB690(void *this, unsigned int owner)
{
    unsigned int name[7];
    imp_00607324(name, d_0060FA8B);
    sub_00424D00(this, name, 0);
    imp_00607330(name);
    *(void **)this = d_00612B14;
    sub_005E4197((char *)this + 0x38, 0xc, 3, d_004C38E0, d_0044D6E0);
    *(unsigned int *)((char *)this + 0x5c) = owner;
    return this;
}
