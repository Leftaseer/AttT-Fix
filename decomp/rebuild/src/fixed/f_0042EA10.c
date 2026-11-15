/* 0x0042EA10: reports a Win32 failure of operation `what`: the text of GetLastError (FormatMessageA), the line
 * "%s failed with error %d: %s" (what, error, text), the error log (0x0042E930) and a MessageBoxA titled "Error" */
/* @func 0042EA10 */
#include "auto_pre.h"
DECOMP_C unsigned int (__stdcall *imp_00607148)(void) __asm__("__imp__GetLastError");
DECOMP_C unsigned int (__stdcall *imp_0060714C)(unsigned int, const void *, unsigned int, unsigned int, char *,
                                                unsigned int, void *) __asm__("__imp__FormatMessageA");
DECOMP_C void *(__stdcall *imp_00607150)(void *) __asm__("__imp__LocalFree");
DECOMP_C int (__cdecl *imp_006076C4)(char *, const char *, ...) __asm__("__imp__wsprintfA");
DECOMP_C int (__stdcall *imp_006076C8)(void *, const char *, const char *, unsigned int) __asm__("__imp__MessageBoxA");
DECOMP_C void __cdecl sub_0042E930(const char *text);                  /* WriteErrorLog */
DECOMP_C char d_00608C68[], d_00608C70[];                              /* "Error", the format string */

DECOMP(0042EA10)
void __cdecl f_0042EA10(const char *what)
{
    unsigned int error = imp_00607148();
    char *text = 0, line[80];
    imp_0060714C(0x1100, 0, error, 0x400, (char *)&text, 0, 0);            /* ALLOCATE_BUFFER | FROM_SYSTEM */
    imp_006076C4(line, d_00608C70, what, error, text);
    sub_0042E930(line);
    imp_006076C8(0, line, d_00608C68, 0);
    imp_00607150(text);
}
