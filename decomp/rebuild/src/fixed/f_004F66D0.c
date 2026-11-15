/* 0x004F66D0: fills a 0x104-wide-character buffer with the executable's path (KERNEL32!GetModuleFileNameW, no
 * module), terminates it when the call fills the buffer or reads nothing, strips the directory (SHLWAPI!
 * PathStripPathW) and constructs the wide string the caller points at from what is left; that pointer is
 * returned. */
#include "auto_pre.h"
DECOMP_C unsigned int (__stdcall *imp_006070A0)(void *module, wchar_t *name, unsigned int size) __asm__("__imp__GetModuleFileNameW");
DECOMP_C void (__stdcall *imp_006075F8)(wchar_t *path) __asm__("__imp__PathStripPathW");
DECOMP_C void (__thiscall *imp_00607374)(void *self, const wchar_t *s) __asm__("__imp_??0?$basic_string@_WU?$char_traits@_W@std@@V?$allocator@_W@2@@std@@QAE@PB_W@Z");

DECOMP(004F66D0)
void *__cdecl f_004F66D0(void *result)
{
    wchar_t name[0x104];
    unsigned int len = imp_006070A0(0, name, 0x104);

    if (len == 0x104)
        name[0x103] = 0;
    else if (!len)
        name[0] = 0;
    imp_006075F8(name);
    imp_00607374(result, name);
    return result;
}
