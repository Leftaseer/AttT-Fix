/* 0x0055A830: CForestsCreator::Generate (the forest line record: its name (a string), the model name +0x1C, scale
 * +0x38, the first tree's x / z +0x3C / +0x40, the line +0x44), the editor's forest generator, reporting on a
 * console: the trees around (0x0055A570 from <path +0x4250><name>.dat) are split between three kinds by the
 * shares 0.5 / 0.3 (0x0061BF68 / 0x0061BF60) and within a kind by the trees' weights (+0x3438, normalised to sum
 * 1; a kind without trees ends the generation at once), copied (0x2C bytes from +0x90) into three lists and
 * shuffled (0x005599E0). Then groups (10000 of 0x1C0 bytes) are laid out (0x0055BD70) from the first tree, which
 * must be inside the line (0x00559880; else an error); each next group is put around the last placed one at a
 * random distance (the radii sums, 0x004F6550) and any angle (0x0061BF50 steps, shuffled) until 0x00559D20 lets
 * it; a group that fits nowhere drops back to an earlier one still open. Every tree above the ground limit
 * (0x00613AFC) is written to <path><name>.fst (+8) as its id (0x0055BD20) and its matrix: a random turn, the
 * position 0x0068AE18 under the ground height (0x00473110) and a random scale (sx 0x0061BF10..14, sy
 * 0x00613974..0x0061BF18, sx pulled across 1 to the side of sy) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_55A830;                 /* std::string */
typedef struct { unsigned int v[3]; } V3_559D20;
DECOMP_C void __cdecl sub_00485690(int a, int b, int c, int d);
DECOMP_C void *__thiscall sub_0049E330(void *self, void *name);
DECOMP_C void __thiscall sub_00559B40(void *self, void *model, float scale);
DECOMP_C void __thiscall sub_00559CA0(void *self, void *line);
DECOMP_C void *__thiscall sub_0043BBC0(void *self);
DECOMP_C void __thiscall sub_0047F690(void *self);
DECOMP_C unsigned int __thiscall sub_0055A570(void *self, void *name, void *around);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);              /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                        /* operator delete[] */
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C void *__cdecl sub_005E40BE(void *p, int c, unsigned int n);   /* memset */
DECOMP_C void __stdcall sub_005599E0(void *list, int n);
DECOMP_C char __stdcall sub_00559880(V3_559D20 p, void *a);
DECOMP_C int __thiscall sub_0055BD70(void *self, char **lists, int *next, int *count);
DECOMP_C void __thiscall sub_0055BA90(void *self, V3_559D20 p);
DECOMP_C int __thiscall sub_0055BBF0(void *self);
DECOMP_C float *__thiscall sub_0055BB60(void *self, void *out, int i);
DECOMP_C double __thiscall sub_0055BC20(void *self, int i);
DECOMP_C double __thiscall sub_0055BC40(void *self, int i);
DECOMP_C void __thiscall sub_0055BAE0(void *self, int i, V3_559D20 p);
DECOMP_C unsigned char __thiscall sub_00559D20(void *self, char *groups, int idx, void *a3);
DECOMP_C int __thiscall sub_0055BD20(void *self, int i);
DECOMP_C float __cdecl sub_004F6550(float lo, float hi, float steps);
DECOMP_C void __stdcall sub_00559A60(float *a, int n);
DECOMP_C void *__cdecl sub_0042F050(void);
DECOMP_C void __cdecl sub_0054B510(void *eax, void *msg, int a);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C void *__stdcall sub_005B8020(void *out, void *a, void *b);   /* D3DXMatrixMultiply */
DECOMP_C float *__stdcall sub_005B8032(float *out, float a);          /* D3DXMatrixRotationY */
DECOMP_C float *__stdcall sub_005B803E(float *out, float x, float y, float z);   /* D3DXMatrixTranslation */
DECOMP_C float *__stdcall sub_005B8044(float *out, float x, float y, float z);   /* D3DXMatrixScaling */
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C void *__thiscall sub_0055BA60(void *self);
DECOMP_C void __thiscall sub_0055BA80(void *self);
DECOMP_C char d_006105B8[], d_0061BF70[], d_0068AE40[], d_00609E18[], d_0061BF68[], d_0061BF60[], d_00608B4C[],
    d_0061BF58[], d_0061BF50[], d_006CB0A4[], d_006CB0A0[], d_006CAFA0[], d_0061BF1C[], d_0061BEFC[], d_0061BD40[],
    d_00613AFC[], d_00614478[], d_006099D8[], d_0068AE18[], d_00613974[], d_0061BF18[], d_0061BF10[], d_0061BF14[];
DECOMP_C int (__stdcall *imp_AllocConsole)(void) __asm__("__imp__AllocConsole@0");
DECOMP_C int (__stdcall *imp_FreeConsole)(void) __asm__("__imp__FreeConsole@0");
DECOMP_C void *(__stdcall *imp_00607118)(unsigned int) __asm__("__imp__GetStdHandle@4");
DECOMP_C int (__stdcall *imp_0060711C)(void *, unsigned int) __asm__("__imp__SetConsoleCursorPosition@8");
DECOMP_C int (__stdcall *imp_WriteFile)(void *, const void *, unsigned int, unsigned int *, void *) __asm__("__imp__WriteFile@20");
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
DECOMP_C int (__cdecl *imp_sprintf)(char *, const char *, ...) __asm__("__imp__sprintf");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_00607354)(void *, const char *, int, int) __asm__("__imp_?open@?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXPBDHH@Z");
DECOMP_C void (__thiscall *imp_006071B4)(void *) __asm__("__imp_?close@?$basic_ofstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void *(__thiscall *imp_006071B0)(void *, const void *, int) __asm__("__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z");
typedef void (__thiscall *vfi_55A830)(void *self, int a);

#define GRP 0x1c0
#define ONE (*(float *)d_0068AE40)

/* the console line s (GetStdHandle(-11)) */
static void print_55A830(const char *s, unsigned int *written)
{
    const char *e = s;
    while (*e++)
        ;
    imp_WriteFile(imp_00607118(0xfffffff5), s, (unsigned int)(e - (s + 1)), written, 0);
}

static void identity_55A830(float *m)
{
    int k;
    for (k = 0; k < 16; k++)
        m[k] = 0.0f;
    m[0] = m[5] = m[10] = m[15] = ONE;
}

DECOMP(0055A830)
void __thiscall f_0055A830(void *self, char *rec)
{
    char *this = (char *)self;
    unsigned int around[0x40];                  /* 0x0043BBC0 / 0x0047F690 */
    char *lists[3];
    int counts[3], next[3], saved[3], filled;
    unsigned int idx[300];                      /* the trees of each kind; later the angles */
    float *ang = (float *)idx;
    float dist[1];
    char open[10000];
    char buf[0x100];
    Str_55A830 s1, s2;
    unsigned int written, n, k, total = 0, t;
    unsigned int *arr;
    char *groups;
    unsigned int placed, anchor;
    char *cur;
    long double d;
    imp_AllocConsole();
    sub_00485690(0, 0, 600, 300);
    sub_00485690(0, 600, 400, 100);
    sub_00559B40(this, sub_0049E330(*(char **)(this + 0x424c) + 0xcc, rec + 0x1c), *(float *)(rec + 0x38));
    sub_00559CA0(this, rec + 0x44);
    *(float *)(this + 0x4240) = *(float *)(rec + 0x3c);
    *(float *)(this + 0x4244) = *(float *)(rec + 0x40);
    sub_0043BBC0(around);
    imp_006071C0(&s1, this + 0x4250, rec);
    imp_006071DC(&s2, &s1, d_006105B8);
    n = sub_0055A570(this, &s2, around);
    imp_00607330(&s2);
    imp_00607330(&s1);
    imp_sprintf(buf, d_0061BF70, n);
    print_55A830(buf, &written);
    arr = (unsigned int *)sub_005E3B10(0x445c04);
    if (arr) {
        arr[0] = 10000;
        sub_005E4197(arr + 1, GRP, 10000, (void *)sub_0055BA60, (void *)sub_0055BA80);
        groups = (char *)(arr + 1);
    } else
        groups = 0;
    sub_005E40BE(open, 1, 10000);
    for (k = 0; k < 3; k++)
        lists[k] = (char *)sub_005E3B10(440000);
    d = (long double)n;
    counts[0] = (int)(long long)(*(double *)d_0061BF68 * d);
    counts[1] = (int)(long long)(d * *(double *)d_0061BF60);
    counts[2] = (int)n - counts[1] - counts[0];
    next[0] = next[1] = next[2] = 0;
    for (k = 0; k < *(unsigned int *)(this + 0x342c); k++) {
        int kind = *(int *)(this + 0x3430 + k * 0xc);
        idx[kind * 100 + next[kind]] = k;
        next[kind]++;
    }
    /* the weights of each kind normalised to sum 1 (the last one takes what is left) */
    for (t = 0; t < 3; t++) {
        unsigned int m = (unsigned int)next[t], j;
        float sum = 0.0f, acc;
        if (m == 0)
            goto out;
        for (j = 0; j < m; j++)
            sum = *(float *)(this + 0x3438 + idx[t * 100 + j] * 0xc) + sum;
        if (sum != ONE) {
            acc = 0.0f;
            for (j = 0; j + 1 < m; j++) {
                float *w = (float *)(this + 0x3438 + idx[t * 100 + j] * 0xc);
                float q = *w / sum;
                *w = q;
                acc = q + acc;
            }
            *(float *)(this + 0x3438 + idx[t * 100 + m - 1] * 0xc) = 1.0f - acc;
        }
    }
    /* each kind's list: every tree type its weight's share of the kind's count, the last one the rest */
    for (t = 0; t < 3; t++) {
        unsigned int m = (unsigned int)next[t], last = 0, r;
        filled = 0;
        if (m - 1 != 0) {
            unsigned int j;
            last = m - 1;
            for (j = 0; j < m - 1; j++) {
                unsigned int kk = idx[t * 100 + j], q;
                q = (unsigned int)(long long)(*(float *)(this + 0x3438 + kk * 0xc) * (long double)counts[t]);
                if (q != 0) {
                    int at = filled * 0x2c;
                    filled += q;
                    do {
                        __builtin_memcpy(lists[t] + at,
                                         this + 0x90 + (*(int *)(this + 0x3434 + kk * 0xc) + t * 100) * 0x2c, 0x2c);
                        at += 0x2c;
                    } while (--q);
                }
            }
        }
        r = (unsigned int)(counts[t] - filled);
        if (r != 0) {
            unsigned int kk = idx[t * 100 + last];
            int at = filled * 0x2c;
            do {
                __builtin_memcpy(lists[t] + at,
                                 this + 0x90 + (*(int *)(this + 0x3434 + kk * 0xc) + t * 100) * 0x2c, 0x2c);
                at += 0x2c;
            } while (--r);
        }
    }
    for (t = 0; t < 3; t++)
        sub_005599E0(lists[t], counts[t]);

    /* the first group, laid out from the first tree until all of it is inside the line */
    for (;;) {
        V3_559D20 p;
        float y = 0.0f;
        int j, ok = 1;
        *(float *)&p.v[0] = *(float *)(this + 0x4240);
        *(float *)&p.v[1] = y;
        *(float *)&p.v[2] = *(float *)(this + 0x4244);
        if (!sub_00559880(p, around)) {
            Str_55A830 cp, s;
            if (!(*(unsigned char *)d_006CB0A4 & 1)) {
                *(unsigned int *)d_006CB0A4 |= 1;
                *(void **)d_006CB0A0 = sub_0042F050();
            }
            cp = *(Str_55A830 *)rec;
            imp_sprintf(d_006CAFA0, d_0061BF1C, cp);
            imp_00607324(&s, d_006CAFA0);
            sub_0054B510(&s, &s, 1);
            imp_00607330(&s);
            goto out;
        }
        next[0] = next[1] = next[2] = 0;
        sub_0055BD70(groups, lists, next, counts);
        sub_0055BA90(groups, p);
        for (j = 0; j < sub_0055BBF0(groups); j++) {
            float tmp[3], *q = sub_0055BB60(groups, tmp, j);
            V3_559D20 v;
            v.v[0] = ((unsigned int *)q)[0];
            v.v[1] = ((unsigned int *)q)[1];
            v.v[2] = ((unsigned int *)q)[2];
            if (!sub_00559880(v, around)) {
                ok = 0;
                break;
            }
        }
        if (ok)
            break;
    }
    saved[0] = next[0];
    saved[1] = next[1];
    saved[2] = next[2];
    cur = groups + GRP;
    anchor = 0;
    placed = 1;

    /* each next group around the anchor (the last placed one) */
    for (;;) {
        char *a;
        unsigned char searching = 1;
        int i, j;
        next[0] = saved[0];
        next[1] = saved[1];
        next[2] = saved[2];
        sub_0055BD70(cur, lists, next, counts);
        a = groups + anchor * GRP;
        if (sub_0055BBF0(a) > 0) {
            i = 0;
            do {
                if (!searching)
                    break;
                for (j = 0; j < sub_0055BBF0(cur) && searching; j++) {
                    float r1, r2, ac;
                    int na, kk;
                    r1 = (float)(sub_0055BC20(a, i) + sub_0055BC20(cur, j));
                    r2 = (float)(sub_0055BC40(a, i) + sub_0055BC40(cur, j));
                    dist[0] = sub_004F6550(r1, r2, *(float *)d_00608B4C);
                    ac = 0.0f;
                    na = 0;
                    do {
                        ang[na++] = ac;
                        ac = (float)(ac + *(double *)d_0061BF50);
                    } while (*(double *)d_0061BF58 > ac);
                    sub_00559A60(ang, na);
                    for (kk = 0; kk < 1 && searching; kk++) {
                        double dd;
                        int b;
                        if (na <= 0)
                            continue;
                        dd = dist[kk];
                        for (b = 0; b < na; b++) {
                            float an = ang[b], c, s, X, Z, tmp[3], *q;
                            V3_559D20 v;
                            c = (float)decomp_CIcos(an);
                            q = sub_0055BB60(a, tmp, i);
                            X = (float)(c * dd + q[0]);
                            s = (float)decomp_CIsin(an);
                            q = sub_0055BB60(a, tmp, i);
                            Z = (float)(q[2] + s * dd);
                            *(float *)&v.v[0] = X;
                            *(float *)&v.v[1] = 0.0f;
                            *(float *)&v.v[2] = Z;
                            sub_0055BAE0(cur, j, v);
                            if (sub_00559D20(this, groups, (int)placed, around)) {
                                searching = 0;
                                break;
                            }
                        }
                    }
                }
                i++;
            } while (i < sub_0055BBF0(a));
            if (searching != 1) {
                /* placed: it is the next anchor */
                anchor = placed;
                placed++;
                cur = groups + placed * GRP;
                total += (unsigned int)sub_0055BBF0(cur - GRP);
                imp_sprintf(buf, d_0061BEFC, total);
                imp_0060711C(imp_00607118(0xfffffff5), 0x10000);
                print_55A830(buf, &written);
                saved[0] = next[0];
                saved[1] = next[1];
                saved[2] = next[2];
                continue;
            }
        }
        /* nowhere: back to the last anchor still open */
        open[anchor] = 0;
        if (anchor == 0)
            break;
        anchor--;
        while (!open[anchor]) {
            if ((int)anchor <= 0)
                break;
            anchor--;
        }
        if ((int)anchor <= 0)
            break;
    }

    if (placed != 0) {
        char *g = groups;
        unsigned int c = placed;
        do {
            int j = 0;
            if (sub_0055BBF0(g) > 0)
                do
                    j++;
                while (j < sub_0055BBF0(g));
            g += GRP;
        } while (--c);
    }
    imp_006071C0(&s1, this + 0x4250, rec);
    imp_006071DC(&s2, &s1, d_0061BD40);
    imp_00607354(this + 8, imp_0060732C(&s2), 0x22, 0x40);
    imp_00607330(&s2);
    imp_00607330(&s1);
    if (placed != 0) {
        char *g = groups;
        unsigned int c = placed;
        do {
            int i;
            for (i = 0; i < sub_0055BBF0(g); i++) {
                float t1[3], t2[3], *p1, *p2, h;
                p1 = sub_0055BB60(g, t1, i);
                p2 = sub_0055BB60(g, t2, i);
                h = sub_00473110(*(void **)(this + 0x4248), p1[0], p2[2]);
                if (h > *(float *)d_00613AFC) {
                    float mrot[16], m1[16], mt[16], ms[16], t3[3], t4[3], *p3, *p4, sx, sy;
                    struct { int id; float m[16]; } out;
                    int rem = imp_00607400() % 360;
                    sub_005B8032(mrot, (float)(rem * *(double *)d_00614478 / *(double *)d_006099D8));
                    identity_55A830(m1);
                    sub_005B8020(m1, m1, mrot);
                    identity_55A830(mrot);
                    sub_005B8020(m1, m1, mrot);
                    p3 = sub_0055BB60(g, t3, i);
                    p4 = sub_0055BB60(g, t4, i);
                    sub_005B803E(mt, p3[0], (float)(h - *(double *)d_0068AE18), p4[2]);
                    sub_005B8020(mt, m1, mt);
                    sy = sub_004F6550(*(float *)d_00613974, *(float *)d_0061BF18, *(float *)d_00608B4C);
                    sx = sub_004F6550(*(float *)d_0061BF10, *(float *)d_0061BF14, *(float *)d_00608B4C);
                    if (1.0f > sx && sy > ONE)
                        sx = (1.0f - sx) + 1.0f;
                    else if (sx > ONE && ONE > sy)
                        sx = 1.0f - (1.0f - sx);
                    sub_005B8044(ms, sx, sy, sx);
                    sub_005B8020(mt, ms, mt);
                    out.id = sub_0055BD20(g, i);
                    __builtin_memcpy(out.m, mt, 0x40);
                    imp_006071B0(this + 8, &out, 0x44);
                }
            }
            g += GRP;
        } while (--c);
    }
    imp_006071B4(this + 8);
    imp_006071DC(&s2, rec, d_0061BD40);
    imp_00607330(&s2);
    for (k = 0; k < 3; k++)
        sub_005E3EBA(lists[k]);
    if (groups) {
        if (((unsigned int *)groups)[-1] == 0)
            sub_005E3EBA(groups - 4);
        else
            ((vfi_55A830)(*(void ***)groups)[0])(groups, 3);
    }
    imp_FreeConsole();
out:
    sub_0047F690(around);
}
