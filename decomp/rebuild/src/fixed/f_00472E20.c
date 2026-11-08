/* 0x00472E20: CMainMenuScene vf15.  Runs the base GUIScene vf15 (0x00584190: scene name, arguments,
 * modal), loads the scene's script table (0x0060AD08) and takes its GUI table (0x0060E72C).  The camera
 * factory (0x00424E70, the global CCamera) gets its default fields (distances/angles 0x00607F84,
 * 0x0060A158, 0x0068AE40, 0x0060B080, 0x0060B07C, the +0x211/+0x218 flags and the +0x214 float), its
 * vtbl+0x18 method runs, and the 0x44-byte camera state (0x00435550) is copied into the scene at +0xA8.
 * Both tables are destroyed; the last destructor's result is returned.  The decompiler lost the frame in
 * the SEH prologue and the rep movsd, and invented a by-value GUIScene argument (the machine only pushes
 * three dwords), so this is written from the machine code. */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_472E20;                 /* nScript::Table */
DECOMP_C int __thiscall sub_00584190(char *self, void *name, void *args, int modal);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00437870(void *self, void *out, void *name);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C char d_0060AD08[], d_0060E72C[], d_00607F84[], d_0060A158[], d_0068AE40[], d_0060B080[], d_0060B07C[];
typedef void (__thiscall *vf1_472E20)(void *self);

DECOMP(00472E20)
int __thiscall f_00472E20(char *this, void *name, void *args, int modal)
{
    Tbl_472E20 t, sc, res;
    unsigned int cam[0x44 / 4];
    unsigned int *src;
    char *o;
    int i;

    sub_00584190(this, name, args, modal);

    sub_004323E0(&t, d_0060AD08);
    sub_00437870(&t, &sc, name);
    sub_004220A0(&t);
    sub_0057B4E0(&sc, &res, d_0060E72C);

    o = sub_00424E70();
    *(float *)(o + 0x50) = 0.0f;
    *(float *)(o + 0x54) = 0.0f;
    *(float *)(o + 0x58) = *(float *)d_00607F84;
    *(float *)(o + 0x5c) = 0.0f;
    *(int *)(o + 0x60) = 0;
    *(int *)(o + 0x64) = 0;
    *(float *)(o + 0x68) = *(float *)d_00607F84;
    o[0x70] = 1;
    *(float *)(o + 0x74) = *(float *)d_0060A158;
    *(float *)(o + 0x78) = *(float *)d_0068AE40;
    *(float *)(o + 0x7c) = *(float *)d_0060B080;
    *(float *)(o + 0x80) = *(float *)d_0060B07C;
    o[0x84] = 1;
    o[0x211] = 0;
    *(float *)(o + 0x214) = 0.0f;
    o[0x218] = 0;
    ((vf1_472E20)(*(void ***)(o + 4))[0x18 / 4])(o + 4);

    src = sub_00435550(o, cam);
    for (i = 0; i < 17; i++)
        ((unsigned int *)(this + 0xa8))[i] = src[i];

    sub_004220A0(&res);
    return sub_004220A0(&sc);
}
