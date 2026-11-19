/* 0x00478700: makes the mesh's side file <name>.gdl sure to exist (the name is the string at +0, the reader
 * 0x00459290 opens it without loading and its +0x2C flag says whether it did; on failure a "Cannot open file - "
 * + name string is thrown from .\Mesh.cpp:0x690 with info 0x0069916C) and then visits every node of the mesh:
 * the table at +0x30 holds +0x34 entries of 0x44 bytes; each node's interface (+0x2C) gets its vf+0x18 called with
 * a scratch record and the mesh's +0x38 value, and every child (0x44 bytes at +0x40, count +0x3C) is handed to
 * 0x00475AF0, which repeats the visit recursively.  The reader is closed (0x00459010) and destroyed (0x00459170). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_478700;                  /* std::string */
DECOMP_C void __thiscall sub_00459290(void *self, void *name, int no_load);
DECOMP_C void __thiscall sub_00459010(void *self);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C void __thiscall sub_00475AF0(void *self, void *scratch, unsigned int value);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);  /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C char d_0060B9CC[], d_0060EB3C[], d_0060EA44[], d_0069916C[];
typedef void (__thiscall *vf_478700)(void *self, void *scratch, unsigned int value);

DECOMP(00478700)
void __thiscall f_00478700(char *this)
{
    Str_478700 s, part, msg;
    unsigned int rd[0x30 / 4];                                       /* CGameFile; opened flag at +0x2C */
    unsigned int scratch[3];
    unsigned int i, j, off;
    char *node, *child;

    imp_006071DC(&s, this, d_0060B9CC);                              /* "<name>.gdl" */
    sub_00459290(rd, &s, 1);
    imp_00607330(&s);
    if (!((unsigned char *)rd)[0x2c]) {
        unsigned int exc[8];
        imp_00607324(&part, d_0060EB3C);                            /* "Cannot open file - " */
        imp_006071C0(&msg, &part, this);
        sub_00421220(exc, &msg, d_0060EA44, 0x690);                 /* .\Mesh.cpp:1680 */
        sub_005E3EC0(exc, d_0069916C);
    }
    off = 0;
    for (i = 0; i < *(unsigned int *)(this + 0x30); i++, off += 0x44) {
        void *itf;
        node = *(char **)(this + 0x34) + off;
        itf = *(void **)(node + 0x2c);
        ((vf_478700)(*(void ***)itf)[0x18 / 4])(itf, scratch, *(unsigned int *)(this + 0x38));
        for (j = 0; j < *(unsigned int *)(node + 0x3c); j++)
            sub_00475AF0(*(char **)(node + 0x40) + j * 0x44, scratch, *(unsigned int *)(this + 0x38));
    }
    sub_00459010(rd);
    sub_00459170(rd);
}
