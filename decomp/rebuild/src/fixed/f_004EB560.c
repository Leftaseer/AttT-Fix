/* 0x004EB560: CTriggersManager::~CTriggersManager: noted as the one being destroyed (0x6CA718, its owner at
 * 0x6CA71C), deletes the triggers of its three lists (+0x3C, 12 bytes apart), destroys the three texture updaters
 * at +0x38 (`eh vector destructor iterator'), then the CUpdateObject part: unregisters from its manager (+0x2C vf14),
 * the name string, and the CGameObject base (0x00424C70) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void __thiscall sub_00424C70(void *self);
DECOMP_C char d_00612B14[], d_00607D5C[], d_006CA718[], d_006CA71C[], d_0044D6E0[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *dtor_4EB560)(void *self, int flags);
typedef void (__thiscall *vf14_4EB560)(void *self, void *o);

DECOMP(004EB560)
void __thiscall f_004EB560(void *this)
{
    char *s = (char *)this;
    void ***l = (void ***)(s + 0x3c);
    int k;
    *(void **)s = d_00612B14;
    *(void **)d_006CA718 = this;
    *(unsigned int *)d_006CA71C = *(unsigned int *)(s + 0x5c);
    for (k = 3; k; k--, l += 3) {
        void **head = *l, **n = (void **)*head;
        if (n != head) {
            void **next = (void **)*n;
            for (;;) {
                void **o = (void **)n[2];
                if (o)
                    ((dtor_4EB560)(*(void ***)o)[0])(o, 1);
                if (next == head)
                    break;
                n = next;
                next = (void **)*next;
            }
        }
    }
    sub_005E4134(s + 0x38, 0xc, 3, d_0044D6E0);
    *(void **)s = d_00607D5C;
    if (*(void **)(s + 0x2c)) {
        void **m = *(void ***)(s + 0x2c);
        ((vf14_4EB560)(*(void ***)m)[0x14 / 4])(m, this);
    }
    imp_00607330(s + 8);
    sub_00424C70(this);
}
