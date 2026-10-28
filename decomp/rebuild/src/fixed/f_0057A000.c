/* 0x0057A000: appends the date and time (ctime without its newline), two spaces and "Игра закончилась." (the game
 * is over) to the log line, writes it (0x00579DE0) and empties it */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00579DE0(void *line);
DECOMP_C char d_0060B10C[], d_0061D8F8[], d_0060FA8B[];
DECOMP_C long long (__cdecl *imp_006073EC)(long long *) __asm__("__imp___time64");
DECOMP_C char *(__cdecl *imp_0060748C)(const long long *) __asm__("__imp___ctime64");
DECOMP_C void *(__thiscall *imp_00607320)(void *, const char *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");

DECOMP(0057A000)
void __thiscall f_0057A000(void *this)
{
    long long t;
    char *p, *e;
    imp_006073EC(&t);
    p = imp_0060748C(&t);
    for (e = p; *e; e++)
        ;
    e[-1] = 0;
    imp_00607320(this, p);
    imp_00607320(this, d_0060B10C);
    imp_00607320(this, d_0061D8F8);
    sub_00579DE0(this);
    imp_006072F8(this, d_0060FA8B);
}
