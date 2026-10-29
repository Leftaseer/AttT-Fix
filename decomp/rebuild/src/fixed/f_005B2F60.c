/* 0x005B2F60: world map tool update (EBX passed through, the stack argument is unused): the frame time (+0xBC, from
 * QueryPerformanceCounter and +0xB0); below 200 the queued moves (+0x94, +0x98 entries, down to 0x008D1440) are
 * applied to their objects; unless the input is locked (+0x7C4) a held button with a selection (+0x68) runs
 * 0x005B0ED0; then by tool (+0x9C): 0 (on a fresh frame) hovers: the objects of +0x48 under the cursor
 * (0x00591640) are sorted by distance into +0x80 (0x005AD280, 0x0045B7C0, 0x005B2D60), cycling on a still cursor,
 * the nearest becomes the selection (0x00591AF0, or the hint 0x13F) - an old frame just updates it (0x0058ED40);
 * 1..9 the ground point under the cursor (0x0053BA40) gets an object of the tool (0x005ADCF0 .. 0x005B0C00) and its
 * sound (0x00594600 vf30) */
/* @conv ECX,EBX 4 */
/* @func 005B2F60 custom */
#include "auto_pre.h"
typedef struct { float x, y, z; } V3_5B2F60;
typedef struct { unsigned int w[3]; } Tbl_5B2F60;                 /* nScript::Table */
DECOMP_C int (__stdcall *imp_006070A8)(long long *) __asm__("__imp__QueryPerformanceCounter@4");
DECOMP_C void __cdecl sub_005E3E9C(void *p);                       /* operator delete */
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void __cdecl sub_005B0ED0(void *self, unsigned int ebx, int a);
DECOMP_C void __thiscall sub_0058ED40(void *self);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C unsigned char __thiscall sub_0043C3C0(void *self);
DECOMP_C void __stdcall sub_005ACE70(void *obj);
DECOMP_C void __thiscall sub_005B2480(void *self);
DECOMP_C void *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_004BB120(void *self);
DECOMP_C unsigned char __cdecl sub_00591640(void *self, unsigned int eax, void *pt);
DECOMP_C void __thiscall sub_0043E2D0(void *self, void *pair);
DECOMP_C void __stdcall sub_005AD280(void *out, void *pair);
DECOMP_C float __thiscall sub_0045B7C0(void *self);
DECOMP_C void __cdecl sub_005B2D60(void *first, void *last, int n, unsigned int key);
DECOMP_C void __thiscall sub_00591AF0(void *self, int a);
DECOMP_C void *__thiscall sub_00594600(void *self, int id, int a);
DECOMP_C void __thiscall sub_00595030(void *self, int a);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C unsigned char __thiscall sub_0053BA40(void *self, V3_5B2F60 *out);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __stdcall sub_005ADCF0(V3_5B2F60 pos, void *t);
DECOMP_C void __thiscall sub_005AE220(void *self, V3_5B2F60 pos, void *t);
DECOMP_C void __cdecl sub_005AE620(void *self, unsigned int ebx, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __cdecl sub_005AF030(void *self, unsigned int ebx, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __thiscall sub_005AF580(void *self, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __thiscall sub_005AFBC0(void *self, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __cdecl sub_005B0060(void *self, unsigned int ebx, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __thiscall sub_005B0740(void *self, V3_5B2F60 pos, void *t, int a);
DECOMP_C void __thiscall sub_005B0C00(void *self, V3_5B2F60 pos, void *t, int a);
DECOMP_C char d_006CA5A0[], d_0060A208[], d_008D1440[], d_006C8E70[], d_00607CC4[];
typedef float *(__thiscall *vfp_5B2F60)(void *self);
typedef void (__thiscall *vf0_5B2F60)(void *self);

#define F(a) (*(float *)(a))
#define QUEUED (*(unsigned int *)d_008D1440)

/* the tool's sound */
static void sound_5B2F60(int id)
{
    void *s = sub_00594600(*(void **)d_006C8E70, id, 0);
    ((vf0_5B2F60)(*(void ***)s)[0x30 / 4])(s);
}

DECOMP(005B2F60)
void __cdecl f_005B2F60(char *this, unsigned int ebx, int unused)
{
    long long t, d;
    unsigned char fresh = 0;
    char *inp;
    V3_5B2F60 pos;
    Tbl_5B2F60 tb;

    imp_006070A8(&t);
    d = t - *(long long *)(this + 0xb0);
    *(long long *)(this + 0xb0) = t;
    F(this + 0xbc) = (float)((long double)d * F(d_006CA5A0));
    if (*(double *)d_0060A208 > F(this + 0xbc)) {
        fresh = 1;
        while (*(unsigned int *)(this + 0x98) > QUEUED) {
            char **head = *(char ***)(this + 0x94), *n = head[1], *o = *(char **)(n + 8);
            *(int *)(o + 0x58) = *(int *)(o + 0x64);
            *(int *)(o + 0x5c) = *(int *)(o + 0x68);
            *(int *)(o + 0x60) = *(int *)(o + 0x6c);
            __builtin_memcpy(o + 0x64, n + 0xc, 12);
            o[0x70] = 1;
            o = *(char **)(n + 8);
            __builtin_memcpy(o + 0x74, n + 0x18, 12);
            o[0x80] = 1;
            o = *(char **)(n + 8);
            __builtin_memcpy(o + 0x98, n + 0x24, 12);
            o[0xa4] = 1;
            head = *(char ***)(this + 0x94);
            n = head[1];
            if (n != (char *)head) {
                **(char ***)(n + 4) = *(char **)n;
                *(char **)(*(char **)n + 4) = *(char **)(n + 4);
                sub_005E3E9C(n);
                (*(int *)(this + 0x98))--;
            }
        }
    } else
        QUEUED = *(unsigned int *)(this + 0x98);

    if (sub_004215D0()[0x7c4])
        return;
    if (*(void **)(this + 0x68)) {
        ebx = (ebx & 0xffffff00u) | 0x80;
        if ((sub_004215D0()[0x65] & 0x80) || (sub_004215D0()[0xe5] & 0x80))
            sub_005B0ED0(this, ebx, 0);
    }
    switch (*(unsigned int *)(this + 0x9c)) {
    case 0: {
        char *path = this + 0x80;
        float m[2];
        struct { float d; void *o; } pair;
        if (!fresh) {
            if (*(void **)(this + 0x68))
                sub_0058ED40(*(void **)(this + 0x68));
            return;
        }
        {
            void *c = sub_00421680();
            float *p = ((vfp_5B2F60)(*(void ***)c)[0x88 / 4])(c);
            m[0] = p[0];
            m[1] = p[1];
        }
        if (m[0] == F(this + 0x78) && m[1] == F(this + 0x7c) && !sub_0043C3C0(path)) {
            if (*(void **)(this + 0x68))
                sub_005ACE70(*(void **)(this + 0x68));
            *(void **)(this + 0x68) = *(void **)(*(char **)(this + 0x88) - 4);
            sub_005B2480(path);
        } else {
            char **head, **n;
            sub_00424E70();
            if (*(void **)(this + 0x68))
                sub_005ACE70(*(void **)(this + 0x68));
            if (sub_0043C3C0(path))
                *(void **)(this + 0x68) = 0;
            else
                sub_004BB120(path);
            F(this + 0x7c) = m[1];
            F(this + 0x78) = m[0];
            head = *(char ***)(this + 0x48);
            for (n = (char **)*head; n != *(char ***)(this + 0x48); n = (char **)*n) {
                float pt[3];
                pt[0] = m[0];
                pt[1] = m[1];
                pt[2] = 0.0f;
                if (sub_00591640(n[2], 0, pt)) {
                    pair.d = 0.0f;
                    pair.o = n[2];
                    sub_0043E2D0(path, &pair);
                }
            }
            if (!sub_0043C3C0(path)) {
                unsigned int tmp[2];
                float *e;
                sub_005AD280(tmp, &pair);
                for (e = *(float **)(this + 0x84); e != *(float **)(this + 0x88); e += 2)
                    e[0] = sub_0045B7C0(*(void **)(e + 1));
                sub_005B2D60(*(void **)(this + 0x84), *(void **)(this + 0x88),
                             (int)(*(float **)(this + 0x88) - *(float **)(this + 0x84)) / 2,
                             *(unsigned int *)&m[0]);
                *(void **)(this + 0x68) = *(void **)(*(char **)(this + 0x88) - 4);
                if (*(char **)(path + 4) && (*(char **)(path + 8) - *(char **)(path + 4)) >> 3)
                    *(char **)(path + 8) -= 8;
            } else
                *(void **)(this + 0x68) = 0;
        }
        if (*(void **)(this + 0x68))
            sub_00591AF0(*(void **)(this + 0x68), 1);
        else
            sub_00595030(sub_00594600(*(void **)d_006C8E70, 0x13f, 4), 0);
        return;
    }
    case 1: case 2: case 3: case 4: case 5: case 6: case 7: case 8: case 9: {
        static const short id[10] = { 0, 0x1b4, 0x1b5, 0x1b7, 0x1c0, 0x1e4, 0x1c1, 0x1c5, 0x1c6, 0x1cf };
        unsigned int k = *(unsigned int *)(this + 0x9c);
        if (!sub_0053BA40(*(void **)(sub_0042F160() + 0x5c), &pos))
            return;
        tb.w[1] = 0;
        tb.w[0] = (unsigned int)(size_t)d_00607CC4;
        tb.w[2] = 0xffffffffu;
        switch (k) {
        case 1: sub_005ADCF0(pos, &tb); break;
        case 2: sub_005AE220(this, pos, &tb); break;
        case 3: sub_005AE620(this, ebx, pos, &tb, 0); break;
        case 4: sub_005AF030(this, ebx, pos, &tb, 0); break;
        case 5: sub_005AF580(this, pos, &tb, 0); break;
        case 6: sub_005AFBC0(this, pos, &tb, 0); break;
        case 7: sub_005B0060(this, ebx, pos, &tb, 0); break;
        case 8: sub_005B0740(this, pos, &tb, 0); break;
        default: sub_005B0C00(this, pos, &tb, 0); break;
        }
        sub_004220A0(&tb);
        sound_5B2F60(id[k]);
        return;
    }
    default:
        return;
    }
}
