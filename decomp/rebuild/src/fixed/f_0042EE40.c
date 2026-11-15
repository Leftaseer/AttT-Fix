/* 0x0042EE40: the nCfg::GamePath destructor: vtable 0x00608CE8, the strings at +0x20 and +4 destroyed, then the
 * Singleton base vtable 0x00608CD4 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607330)(void *self)
    __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_00608CE8[], d_00608CD4[];                              /* vftables */

DECOMP(0042EE40)
void __thiscall f_0042EE40(void *this)
{
    char *s = (char *)this;
    *(const void **)s = d_00608CE8;
    imp_00607330(s + 0x20);
    imp_00607330(s + 4);
    *(const void **)s = d_00608CD4;
}
