/* 0x004F7430: constructs a movie-backed GUI element: vtable 0x612D6C, a Bink player at +4 (0x00430B80 with the
 * device 0x6C8C10) and an animation at +0x1C (0x004CAA00 with the device).  The by-value name is opened as a
 * CGameFile without reading it (0x00459290), that file and its size (the FsFile's +8) go to the player (0x00430EA0)
 * with the int argument as the flags, the animation takes the player's sound system (0x004CA710), and is placed at
 * the origin with the movie's width and height (0x00430DC0 / 0x00430DD0, unsigned ints as floats; 0x004CA820).
 * The CGameFile (0x00459170) and the name (the string destructor import) are destroyed; returns this. */
/* @conv ECX 32 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[7];
} String_004F7430;

DECOMP_C void __thiscall sub_00430B80(void *self, void *device);
DECOMP_C void __thiscall sub_004CAA00(void *self, void *device);
DECOMP_C void *__thiscall sub_00459290(void *self, const void *name, int no_load);
DECOMP_C void __thiscall sub_00430EA0(void *self, void *file, unsigned int size, unsigned int flags);
DECOMP_C void __thiscall sub_004CA710(void *self, void *sound);
DECOMP_C int __thiscall sub_00430DD0(void *self);
DECOMP_C int __thiscall sub_00430DC0(void *self);
DECOMP_C void __thiscall sub_004CA820(void *self, float x, float y, float w, float h);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_006C8C10[], d_00612D6C[];

DECOMP(004F7430)
void *__thiscall f_004F7430(void *this, String_004F7430 name, int mode)
{
    char *s = (char *)this;
    unsigned int file[0xc];                     /* CGameFile, 0x30 bytes; its FsFile is at +0x24 */
    void *device = *(void **)d_006C8C10;
    void *fs_file;
    float w, h;

    sub_00430B80(s + 4, device);
    *(char **)s = d_00612D6C;
    sub_004CAA00(s + 0x1c, device);
    sub_00459290(file, &name, 1);
    fs_file = *(void **)((char *)file + 0x24);
    sub_00430EA0(s + 4, file, *(unsigned int *)((char *)fs_file + 8), (unsigned int)mode);
    sub_004CA710(s + 0x1c, *(void **)(s + 8));
    h = (float)(unsigned int)sub_00430DD0(s + 4);
    w = (float)(unsigned int)sub_00430DC0(s + 4);
    sub_004CA820(s + 0x1c, 0.0f, 0.0f, w, h);
    sub_00459170(file);
    imp_00607330(&name);
    return s;
}
