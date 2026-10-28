/* 0x004C1C90: NSound::SoundGui2D::vf13: vf08, a Miles sample (handle at +0x38) for the file named by the string,
 * read whole (+0x34: its size, then the data), the volume from the options (+0x40), marks it loaded (+8) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_006CA498[], d_006C8C3C[];
DECOMP_C float __thiscall sub_004ED000(void *self);
DECOMP_C void *(__stdcall *imp_00607884)(void *) __asm__("__imp__AIL_allocate_sample_handle@4");
DECOMP_C void (__stdcall *imp_00607880)(void *) __asm__("__imp__AIL_init_sample@4");
DECOMP_C unsigned int *(__stdcall *imp_0060787C)(const char *, int) __asm__("__imp__AIL_file_read@8");
DECOMP_C int (__stdcall *imp_00607878)(void *, const char *, void *, unsigned int, int) __asm__("__imp__AIL_set_named_sample_file@20");
DECOMP_C const char *(__thiscall *imp_0060732C)(void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
typedef void (__thiscall *vf08_4C1C90)(void *self);

DECOMP(004C1C90)
void __thiscall f_004C1C90(void *this, void *name)
{
    char *s = (char *)this;
    unsigned int *file;
    ((vf08_4C1C90)(*(void ***)this)[2])(this);
    *(void **)(s + 0x38) = imp_00607884(*(void **)d_006CA498);
    imp_00607880(*(void **)(s + 0x38));
    file = imp_0060787C(imp_0060732C(name), -1);
    *(unsigned int **)(s + 0x34) = file;
    imp_00607878(*(void **)(s + 0x38), imp_0060732C(name), file + 1, file[0], 0);
    *(float *)(s + 0x40) = sub_004ED000(*(void **)d_006C8C3C);
    s[8] = 1;
}
