/* 0x004273F0: registers the debug-dump item: 0x00402FD0 names the value at 0x008D122C, the item's pointer and name
 * are formatted into the buffer at 0x006C8748, and 0x00403120 records the buffer under that value. Returns 1. */
#include "auto_pre.h"
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
DECOMP_C void *__cdecl sub_00402FD0(unsigned int value, int flag);
DECOMP_C void __cdecl sub_00403120(unsigned int value, void *name);
DECOMP_C unsigned int d_008D122C, d_006C8848;
DECOMP_C char d_006C8748[], d_00608254[];                                /* "%s (%p)" */

DECOMP(004273F0)
unsigned int __cdecl f_004273F0(void)
{
    void *item = sub_00402FD0(d_008D122C, 1);
    imp_006073D0(d_006C8748, d_00608254, d_006C8848, *(unsigned int *)item);
    sub_00403120(d_008D122C, d_006C8748);
    return 1;
}
