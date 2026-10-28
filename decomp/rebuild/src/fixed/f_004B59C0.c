/* 0x004B59C0: pmain of the embedded luac (lua_cpcall'ed with the arguments in a userdata {argc, argv}): loads every
 * file ("-" for stdin) or dies with the error message (0x004B4240, the message in EAX), combines them (0x004B44C0,
 * L in EDI) and, when dumping (0x6C1FA8), writes the chunk (luaU_dump, 0x00405C80 with L in EBX and the function in
 * EDI; stripping 0x6CA354) to the output (0x6C1FB8, "wb"; stdout without one), dying on open/write/close errors
 * (0x004B4270) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C int *__cdecl sub_00402FD0(void *L, int idx);                  /* lua_touserdata */
DECOMP_C int __cdecl sub_00402960(void *L, int n);                     /* lua_checkstack */
DECOMP_C int __cdecl sub_00402410(void *L, const char *file);          /* luaL_loadfile */
DECOMP_C const char *__cdecl sub_00402ED0(void *ebx, void *L, int idx, unsigned int *len);   /* lua_tolstring */
DECOMP_C void *__cdecl sub_004B44C0(void *edi, int n);                 /* combine */
DECOMP_C int __cdecl sub_00405C80(void *ebx, void *edi, void *L, void *f, void *writer, void *data, int strip);
DECOMP_C void __cdecl sub_004B4240(const char *eax);                   /* fatal */
DECOMP_C void __stdcall sub_004B4270(const char *what);                /* cannot */
DECOMP_C char d_006C1FA8[], d_006C1FB8[], d_006CA354[], d_00610F74[], d_0068AA14[], d_00610F70[], d_00688B68[],
              d_0068A65C[], d_0068A684[], d_004B58E0[];
DECOMP_C char *(__cdecl *imp_0060743C)(void) __asm__("__imp____iob_func");
DECOMP_C void *(__cdecl *imp_0060746C)(const char *, const char *) __asm__("__imp__fopen");
DECOMP_C int (__cdecl *imp_00607468)(void *) __asm__("__imp__ferror");
DECOMP_C int (__cdecl *imp_00607464)(void *) __asm__("__imp__fclose");

DECOMP(004B59C0)
int __cdecl f_004B59C0(void *L)
{
    int *sm = sub_00402FD0(L, 1);
    int argc = sm[0], i;
    char **argv = (char **)sm[1];
    void *f, *d;
    if (!sub_00402960(L, argc))
        sub_004B4240(d_00610F74);                      /* "too many input files" */
    for (i = 0; i < argc; i++) {
        const char *a = argv[i], *b = d_0068AA14;       /* "-" */
        int k = 2, same = 1;
        while (k-- && (same = *a == *b))                /* (repe cmpsb over the two bytes) */
            a++, b++;
        if (sub_00402410(L, same ? 0 : argv[i]))
            sub_004B4240(sub_00402ED0(L, L, -1, 0));
    }
    f = sub_004B44C0(L, argc);
    if (*(int *)d_006C1FA8) {
        const char *out = *(const char **)d_006C1FB8;
        d = out ? imp_0060746C(out, d_00610F70) : imp_0060743C() + 0x20;
        if (!d)
            sub_004B4270(d_00688B68);                   /* "open" */
        sub_00405C80(L, f, L, f, d_004B58E0, d, *(int *)d_006CA354);
        if (imp_00607468(d))
            sub_004B4270(d_0068A65C);                   /* "write" */
        if (imp_00607464(d))
            sub_004B4270(d_0068A684);                   /* "close" */
    }
    return 0;
}
