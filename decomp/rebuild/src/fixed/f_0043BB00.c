/* 0x0043BB00: sets the console cursor to (x, y) (SetConsoleCursorPosition on the standard output; the COORD
 * built from the two shorts in place of the first argument) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void * (__stdcall *imp_00607118)(unsigned int) __asm__("__imp__GetStdHandle@4");
DECOMP_C int (__stdcall *imp_0060711C)(void *, unsigned int) __asm__("__imp__SetConsoleCursorPosition@8");

DECOMP(0043BB00)
void __cdecl f_0043BB00(short x, short y)
{
    imp_0060711C(imp_00607118(0xfffffff5), (unsigned short)x | (unsigned int)(unsigned short)y << 16);
}
