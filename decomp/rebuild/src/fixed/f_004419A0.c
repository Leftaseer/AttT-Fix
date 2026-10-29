/* 0x004419A0: builds a unit's path from points (arg 1: 12-byte {x, ., z} offsets from the unit's position, vf68 of
 * +0x428; arg 2 of them): after a reset (0x00440A80) a new 8-byte path (0x0043BBC0) gets each point (0x004205A0 /
 * 0x0047F760) and each leg's grid cells (0x004412E0: x from the grid's (0x006C8934) +0x40, z down from its +0x3C, in
 * cells of 0x006089A0, truncated); a path that 0x00480200 accepts is kept (+0x0C) in a new list (+0x08, its head
 * 0x004C2F40) of one, else it is wrapped (0x0047FD30) and its legs listed (0x00480B50). The first time (+0x21) the
 * length (0x0043F510) is kept squared (+0x414) and plain (+0x410, _CIsqrt); +0x20 set and the two work buffers sized
 * for 150 entries (+0x24: 16 bytes each, +0x28 / +0x2C; +0x418: 8 bytes each, +0x420), +0x41C cleared */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_4419A0;
DECOMP_C void __thiscall sub_00440A80(void *self);
DECOMP_C void *__thiscall sub_0043BBC0(void *self);
DECOMP_C V2_4419A0 *__thiscall sub_004205A0(V2_4419A0 *self, float x, float y);
DECOMP_C void __thiscall sub_0047F760(void *self, void *pt);
DECOMP_C void __thiscall sub_004412E0(void *self, int x0, int z0, int x1, int z1);
DECOMP_C unsigned char __thiscall sub_00480200(void *self);
DECOMP_C char **__cdecl sub_004C2F40(void);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void *__thiscall sub_0047FD30(void *self, void *path);
DECOMP_C void *__cdecl sub_00480B50(void *path);
DECOMP_C float __stdcall sub_0043F510(void *path);
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_006C8934[], d_006089A0[];
DECOMP_C void *(__cdecl *imp_00607410)(void *, unsigned int) __asm__("__imp__realloc");
typedef unsigned int *(__thiscall *pos_4419A0)(void *self);

#define K (*(double *)d_006089A0)

DECOMP(004419A0)
void __thiscall f_004419A0(void *this, float *pts, unsigned int n)
{
    char *s = (char *)this, *g;
    void *m, *path, **o;
    unsigned int org[3], i;
    float ox, oz, gx, gz, *p, d;
    V2_4419A0 v;
    sub_00440A80(this);
    m = sub_005E3EAE(8);
    path = m ? sub_0043BBC0(m) : 0;
    o = *(void ***)(s + 0x428);
    {
        unsigned int *q = ((pos_4419A0)(*(void ***)o)[0x68 / 4])(o);
        org[0] = q[0], org[1] = q[1], org[2] = q[2];
    }
    ox = *(float *)&org[0];
    oz = *(float *)&org[2];
    for (i = 0, p = pts; i < n; i++, p += 3) {
        int x0, z0, x1, z1;
        sub_0047F760(path, sub_004205A0(&v, p[0], p[1]));
        g = *(char **)d_006C8934;
        gx = *(float *)(g + 0x40);
        x0 = (int)(long long)((p[0] + ox - gx) / K);
        gz = *(float *)(g + 0x3c);
        z0 = (int)(long long)((gz - (p[2] + oz)) / K);
        if (i + 1 >= n)
            continue;
        x1 = (int)(long long)((p[3] + ox - gx) / K);
        z1 = (int)(long long)((gz - (p[5] + oz)) / K);
        sub_004412E0(this, x0, z0, x1, z1);
    }
    if (sub_00480200(path)) {
        char **l, **head, **nn;
        *(void **)(s + 0xc) = path;
        l = sub_005E3EAE(0xc);
        if (l) {
            l[1] = (char *)sub_004C2F40();
            l[2] = 0;
        }
        *(char ***)(s + 8) = l;
        head = (char **)l[1];
        nn = sub_005AD6C0(head, (char **)head[1], &path);
        sub_004E0EF0(l, 1);
        head[1] = (char *)nn;
        *(char ***)nn[1] = nn;
    } else {
        m = sub_005E3EAE(8);
        *(void **)(s + 0xc) = m ? sub_0047FD30(m, path) : 0;
        *(void **)(s + 8) = sub_00480B50(path);
    }
    if (!s[0x21]) {
        d = sub_0043F510(*(void **)(s + 0xc));
        *(float *)(s + 0x414) = d;
        s[0x21] = 1;
        *(float *)(s + 0x410) = (float)decomp_CIsqrt(d);
    }
    s[0x20] = 1;
    if (*(int *)(s + 0x2c) != 150) {
        *(void **)(s + 0x24) = imp_00607410(*(void **)(s + 0x24), 0x960);
        *(int *)(s + 0x2c) = 150;
        *(int *)(s + 0x28) = 150;
    }
    if (*(int *)(s + 0x420) != 150) {
        *(void **)(s + 0x418) = imp_00607410(*(void **)(s + 0x418), 0x4b0);
        *(int *)(s + 0x420) = 150;
    }
    *(int *)(s + 0x41c) = 0;
}
