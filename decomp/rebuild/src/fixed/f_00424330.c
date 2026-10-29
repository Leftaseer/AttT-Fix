/* 0x00424330: C2DScene vf15 (load): the layer (+4) is cleared (vf18), the scene's root (+0x74) made current
 * (0x004AD530); the description of this scene's name (+0x1C) in the manager (0x00421510, 0x00424270) gives the
 * background picture (0x0047A120, size 0x224; +0x80) centred on the screen (0x006C8958/C) whose corner is kept at
 * +0xA0; its labels (+0xDC, 0x64 bytes) and pairs (+0x11C, 0xE4 bytes) become texts (0x00420700, +0x98 / +0x9C), its
 * pictures (+0xCC, 0x2C bytes) new pictures (+0xAC / +0xB0); all are moved by the corner (vf78); the root is added;
 * without a font name (+0xE8 empty) its buttons (+0xA0, 0x48 bytes) go to a button group (0x00426DF0, +0xBC), else
 * its choices (+0x74, 0x4C bytes) to a choice group (0x00473F10, +0xB8), which becomes the scene's controls
 * (0x004205C0) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C char *__cdecl sub_00421510(void);
DECOMP_C char *__thiscall sub_00424270(void *self, void *name);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                                   /* operator delete[] */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                        /* operator new[] */
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void *__thiscall sub_00420700(void *self, void *desc);
DECOMP_C void *__thiscall sub_00426DF0(void *self);
DECOMP_C char *__thiscall sub_004263A0(void *self, void *scene, void *desc, void *style);
DECOMP_C void __thiscall sub_00426EC0(void *self, void *btn);
DECOMP_C void *__thiscall sub_00473F10(void *self);
DECOMP_C char *__thiscall sub_004735C0(void *self, void *scene, void *style, void *desc);
DECOMP_C void __thiscall sub_00473AC0(void *self, void *choice, int key);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char d_006C8958[], d_006C895C[], d_0060FA8B[];
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef unsigned int (__thiscall *vf0_424330)(void *self);
typedef void (__thiscall *vf1_424330)(void *self, void *a);
typedef void (__thiscall *vf2_424330)(void *self, void *a, int b);
typedef void (__thiscall *vff_424330)(void *self, float a, float b);

#define VT(o) (*(void ***)(o))

static void add_424330(char *list, char *text)
{
    (*(void ***)(list + 0x98))[(*(unsigned int *)(list + 0x9c))++] = text;
}

DECOMP(00424330)
int __thiscall f_00424330(char *this)
{
    void *layer = this + 4, *o;
    char *desc, *e, *pics;
    unsigned int cnt, i, off;
    float a, b;

    sub_004AD530(*(void **)(this + 0x74), ((vf0_424330)VT(layer)[0x18 / 4])(layer));
    desc = sub_00424270(sub_00421510() + 4, this + 0x1c);
    o = sub_005E3EAE(0x224);
    if (o)
        o = sub_0047A120(o, desc + 0x38);
    *(void **)(this + 0x80) = o;
    ((vf2_424330)VT(o)[0x38 / 4])(o, desc + 0x1c, 0);
    o = *(void **)(this + 0x80);
    ((vff_424330)VT(o)[0x94 / 4])(o, 0.0f, 0.0f);
    o = *(void **)(this + 0x80);
    {
        float h = *(float *)((char *)o + 0x78), w = *(float *)((char *)o + 0x74);
        a = (float)(((double)*(float *)d_006C895C - w) * 0.5);
        b = (float)(((double)*(float *)d_006C8958 - h) * 0.5);
    }
    *(float *)(this + 0xa0) = a;
    *(float *)(this + 0xa4) = b;
    ((vf1_424330)VT(o)[0x6c / 4])(o, this + 0xa0);
    ((vf1_424330)VT(layer)[4 / 4])(layer, *(void **)(this + 0x80));
    ((vf1_424330)VT(layer)[0x10 / 4])(layer, *(void **)(this + 0x74));

    for (e = *(char **)(desc + 0xdc); e != *(char **)(desc + 0xe0); e += 0x64)
        add_424330(this, sub_00420700(e + 0x1c, e));
    for (e = *(char **)(desc + 0x11c); e != *(char **)(desc + 0x120); e += 0xe4) {
        add_424330(this, sub_00420700(e + 0x1c, e));
        add_424330(this, sub_00420700(e + 0x64, e + 0xac));
    }

    pics = desc + 0xac;
    cnt = *(char **)(pics + 0x20) ? (unsigned int)((*(char **)(pics + 0x24) - *(char **)(pics + 0x20)) / 0x2c) : 0;
    if (*(void **)(this + 0xac)) {
        sub_005E3EBA(*(void **)(this + 0xac));
        *(void **)(this + 0xac) = 0;
    }
    if (cnt) {
        unsigned long long sz = (unsigned long long)cnt * 4;
        *(void **)(this + 0xac) = sub_005E3B10((sz >> 32) ? 0xffffffffu : (unsigned int)sz);
    }
    *(unsigned int *)(this + 0xb0) = 0;
    for (i = 0, off = 0; *(char **)(pics + 0x20) &&
                         i < (unsigned int)((*(char **)(pics + 0x24) - *(char **)(pics + 0x20)) / 0x2c);
         i++, off += 0x2c) {
        void *p = sub_005E3EAE(0x224);
        char *el;
        if (p)
            p = sub_0047A120(p, pics);
        ((vf2_424330)VT(p)[0x38 / 4])(p, *(char **)(pics + 0x20) + off, 0);
        el = *(char **)(pics + 0x20) + off;
        ((vff_424330)VT(p)[0x68 / 4])(p, *(float *)(el + 0x1c), *(float *)(el + 0x20));
        el = *(char **)(pics + 0x20) + off;
        ((vff_424330)VT(p)[0x94 / 4])(p, *(float *)(el + 0x24), *(float *)(el + 0x28));
        ((vf1_424330)VT(layer)[4 / 4])(layer, p);
        (*(void ***)(this + 0xac))[(*(unsigned int *)(this + 0xb0))++] = p;
    }

    for (i = 0; i < *(unsigned int *)(this + 0x9c); i++) {
        void *t = (*(void ***)(this + 0x98))[i];
        ((vff_424330)VT(t)[0x78 / 4])(t, *(float *)(this + 0xa0), *(float *)(this + 0xa4));
    }
    for (i = 0; i < *(unsigned int *)(this + 0xb0); i++) {
        void *t = (*(void ***)(this + 0xac))[i];
        ((vff_424330)VT(t)[0x78 / 4])(t, *(float *)(this + 0xa0), *(float *)(this + 0xa4));
    }
    ((vf1_424330)VT(layer)[4 / 4])(layer, *(void **)(this + 0x74));

    if (imp_006071E4(desc + 0xe8, d_0060FA8B)) {
        void *g = sub_005E3EAE(0x74);
        if (g)
            g = sub_00426DF0(g);
        *(void **)(this + 0xbc) = g;
        for (e = *(char **)(desc + 0xa0); e != *(char **)(desc + 0xa4); e += 0x48) {
            void *m = sub_005E3EAE(0x26c);
            char *x = m ? sub_004263A0(m, this, e + 0x1c, desc + 0x80) : 0, *ctl = x + 0x54;
            ((vff_424330)VT(ctl)[0x68 / 4])(ctl, (float)(*(float *)(e + 0x38) + *(float *)(this + 0xa0)),
                                            (float)(*(float *)(e + 0x3c) + *(float *)(this + 0xa4)));
            ((vff_424330)VT(ctl)[0x94 / 4])(ctl, *(float *)(e + 0x40), *(float *)(e + 0x44));
            sub_00426EC0(*(void **)(this + 0xbc), x);
            ((vf1_424330)VT(layer)[4 / 4])(layer, ctl);
        }
        return sub_004205C0(this, *(void **)(this + 0xbc));
    } else {
        void *g = sub_005E3EAE(0x458);
        if (g)
            g = sub_00473F10(g);
        *(void **)(this + 0xb8) = g;
        for (e = *(char **)(desc + 0x74); e != *(char **)(desc + 0x78); e += 0x4c) {
            void *m = sub_005E3EAE(0x27c);
            char *x = m ? sub_004735C0(m, this, desc + 0x54, e + 0x1c) : 0, *ctl = x + 0x54;
            ((vff_424330)VT(ctl)[0x68 / 4])(ctl, (float)(*(float *)(e + 0x3c) + *(float *)(this + 0xa0)),
                                            (float)(*(float *)(e + 0x40) + *(float *)(this + 0xa4)));
            ((vff_424330)VT(ctl)[0x94 / 4])(ctl, *(float *)(e + 0x44), *(float *)(e + 0x48));
            sub_00473AC0(*(void **)(this + 0xb8), x, *(unsigned char *)(e + 0x38));
            ((vf1_424330)VT(layer)[4 / 4])(layer, ctl);
        }
        return sub_004205C0(this, *(void **)(this + 0xb8));
    }
}
