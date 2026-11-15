/* 0x00428740: on first use fills the record table at 0x006BF528 with the three AmbientSoundManager script methods
 * (each record's handler at +8 and the next record's name at +0x10): "SetVolume" (the name pre-set at 0x006BF528)
 * with 0x00427F10, "GetVolume" with 0x004278F0 and "UpdateSoundInPoint" with 0x00428570; then always hands the
 * table to the Lua registration (0x00427E40). */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00427E40(char **entry);
DECOMP_C char d_006C8850[], d_006BF528[], d_00427F10[], d_004278F0[], d_00428570[],
                d_006082BC[], d_006082A8[];

DECOMP(00428740)
void __cdecl f_00428740(void)
{
    char *t = d_006BF528;

    if (!(*(unsigned char *)d_006C8850 & 1)) {
        *(unsigned int *)d_006C8850 |= 1;
        *(void **)(t + 8) = d_00427F10;
        *(void **)(t + 0x18) = d_004278F0;
        *(void **)(t + 0x28) = d_00428570;
        *(void **)(t + 0xc) = 0;
        *(void **)(t + 0x10) = d_006082BC;
        *(void **)(t + 0x1c) = 0;
        *(void **)(t + 0x20) = d_006082A8;
        *(void **)(t + 0x2c) = 0;
        *(void **)(t + 0x30) = 0;
        *(void **)(t + 0x38) = 0;
        *(void **)(t + 0x3c) = 0;
    }
    sub_00427E40((char **)t);
}
