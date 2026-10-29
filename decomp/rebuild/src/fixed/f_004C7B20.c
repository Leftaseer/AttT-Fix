/* 0x004C7B20: SpellBookScene: makes the icon of spell (elem, slot): SpellIconPos.dat (0x00459290; missing: an
 * exception from SpellBookScene.cpp line 0x36C) is read as text, per element (fire, water, air, earth, super) three
 * corner points offset by the view's origin (+0xB8 vf88) and per slot an (x, y) pair; at the matching one the glow
 * video "<elem><NN>Glow.bik" / "<elem><NN>.bik" becomes +0xBC[elem*10+slot] (0x004C6640) placed at height y through
 * the view (vf90, vf8C) and the logo "<elem>Glow.bik" / "<elem>Appearance.bik" / "<elem><NN>.tga" becomes
 * +0x188[...] (0x004C5DC0) on the three points (0x004C6290); both get their handlers (0x004C6D30) and join the
 * scene's list (+4) */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4C7B20;                 /* std::string */
DECOMP_C void __thiscall sub_00459290(void *self, void *name, int a);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004C6640(void *self, void *scene, void *video, void *glow);
DECOMP_C void *__cdecl sub_004C6D30(void *fn, int a);
DECOMP_C void *__thiscall sub_004C5DC0(void *self, void *scene, void *tex, void *appear, void *glow, void *n1, void *n2,
                                       void *n3, int a);
DECOMP_C void __thiscall sub_004C6290(void *self, float *pts);
DECOMP_C char d_00611BC4[], d_00611BBC[], d_00611BB8[], d_00611BB0[], d_00611BA8[], d_00611B34[], d_00611B04[],
    d_00611AEC[], d_0069916C[], d_00611BA0[], d_00611B94[], d_00611B8C[], d_00611B7C[], d_00611B68[], d_00611B5C[],
    d_00611B54[], d_00611B48[], d_00608B14[], d_004C74E0[], d_004C6C10[], d_004C6D10[], d_004C75B0[], d_004C6C80[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607364)(void *, const void *, int, int) __asm__("__imp_??0?$basic_stringstream@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@1@H@Z");
DECOMP_C void (__thiscall *imp_00607360)(void *) __asm__("__imp_??_D?$basic_stringstream@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEXXZ");
DECOMP_C void *(__thiscall *imp_006072EC)(void *, float *) __asm__("__imp_??5?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV01@AAM@Z");
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
typedef float *(__thiscall *vfp_4C7B20)(void *self);
typedef float (__thiscall *vff_4C7B20)(void *self);
typedef float (__thiscall *vfx_4C7B20)(void *self, float v);
typedef void (__thiscall *vf0_4C7B20)(void *self);
typedef void (__thiscall *vfo_4C7B20)(void *self, void *o);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])

static void handlers_4C7B20(char *o, char *a, char *b, char *c)
{
    *(void **)(o + 0x230) = sub_004C6D30(a, 0);
    *(void **)(o + 0x234) = sub_004C6D30(b, 0);
    *(void **)(o + 0x238) = sub_004C6D30(c, 0);
}

DECOMP(004C7B20)
void __thiscall f_004C7B20(void *self, unsigned int elem, unsigned int slot)
{
    char *this = (char *)self;
    Str_4C7B20 names[5];
    unsigned int file[0x30 / 4];
    unsigned int ss[0x100 / 4];
    float pt[6], g[2];
    unsigned int i, j;

    imp_00607324(&names[0], d_00611BC4);
    imp_00607324(&names[1], d_00611BBC);
    imp_00607324(&names[2], d_00611BB8);
    imp_00607324(&names[3], d_00611BB0);
    imp_00607324(&names[4], d_00611BA8);
    {
        Str_4C7B20 s;
        imp_00607324(&s, d_00611B34);
        sub_00459290(file, &s, 0);
        imp_00607330(&s);
    }
    if (!((unsigned char *)file)[0x2c]) {
        Str_4C7B20 msg;
        unsigned int exc[7];
        imp_00607324(&msg, d_00611B04);
        sub_00421220(exc, &msg, d_00611AEC, 0x36c);
        sub_005E3EC0(exc, d_0069916C);
    }
    {
        Str_4C7B20 s;
        imp_00607324(&s, *(const char **)((char *)file + 0x28));
        imp_00607364(ss, &s, 3, 1);
        imp_00607330(&s);
    }
    for (i = 0; i < 4; i++) {
        float *p;
        void *v;
        for (j = 0; j < 6; j++)
            imp_006072EC(ss, &pt[j]);
        v = *(void **)(this + 0xb8);
        p = ((vfp_4C7B20)VF(v, 0x88))(v);
        pt[0] = p[0] + pt[0];
        pt[1] = p[1] + pt[1];
        v = *(void **)(this + 0xb8);
        p = ((vfp_4C7B20)VF(v, 0x88))(v);
        pt[2] = pt[2] + p[0];
        pt[3] = p[1] + pt[3];
        v = *(void **)(this + 0xb8);
        p = ((vfp_4C7B20)VF(v, 0x88))(v);
        pt[4] = pt[4] + p[0];
        pt[5] = p[1] + pt[5];
        for (j = 0; j < 10; j++) {
            imp_006072EC(ss, &g[0]);
            imp_006072EC(ss, &g[1]);
            if (elem == i && slot == j)
                goto found;
        }
    }
    goto done;

found: {
        char num[4];
        void *mem, **icon, **logo, *view, *list;
        unsigned int k = i * 10 + j;
        imp_006073D0(num, d_00611BA0, j + 1);
        mem = sub_005E3EAE(0x288);
        icon = (void **)(this + 0xbc + k * 4);
        if (mem) {
            Str_4C7B20 a, b, c, d;
            imp_006071DC(&a, &names[i], num);
            imp_006071DC(&b, &a, d_00611B94);
            imp_006071DC(&c, &names[i], num);
            imp_006071DC(&d, &c, d_00611B8C);
            *icon = sub_004C6640(mem, this, &d, &b);
            imp_00607330(&d);
            imp_00607330(&c);
            imp_00607330(&b);
            imp_00607330(&a);
        } else
            *icon = 0;
        handlers_4C7B20(*icon, d_004C74E0, d_004C6C10, d_004C6D10);
        *(unsigned int *)((char *)*icon + 0x274) = j;
        view = *(void **)(this + 0xb8);
        {
            void *o = *icon;
            float h = ((vff_4C7B20)VF(view, 0x90))(view) + g[1];
            h = ((vfx_4C7B20)VF(view, 0x8c))(view, h) + g[1];
            ((vfx_4C7B20)VF(o, 0x68))(o, h);
        }
        ((vf0_4C7B20)VF(*icon, 0x50))(*icon);
        list = this + 4;
        ((vfo_4C7B20)VF(list, 4))(list, *icon);

        mem = sub_005E3EAE(0x284);
        logo = (void **)(this + 0x188 + k * 4);
        if (mem) {
            Str_4C7B20 s1, s2, s3, e1, e2, e3, e4, e5, e6;
            imp_00607324(&s1, d_00611B7C);
            imp_00607324(&s2, d_00611B68);
            imp_00607324(&s3, d_00611B5C);
            imp_006071DC(&e1, &names[i], d_00611B54);
            imp_006071DC(&e2, &e1, d_00611B8C);
            imp_006071DC(&e3, &names[i], d_00611B48);
            imp_006071DC(&e4, &e3, d_00611B8C);
            imp_006071DC(&e5, &names[i], num);
            imp_006071DC(&e6, &e5, d_00608B14);
            *logo = sub_004C5DC0(mem, this, &e6, &e4, &e2, &s3, &s2, &s1, 0);
            imp_00607330(&e6);
            imp_00607330(&e5);
            imp_00607330(&e4);
            imp_00607330(&e3);
            imp_00607330(&e2);
            imp_00607330(&e1);
            imp_00607330(&s3);
            imp_00607330(&s2);
            imp_00607330(&s1);
        } else
            *logo = 0;
        sub_004C6290(*logo, pt);
        handlers_4C7B20(*logo, d_004C75B0, d_004C6C80, d_004C6D10);
        ((vf0_4C7B20)VF(*logo, 0x50))(*logo);
        ((vfo_4C7B20)VF(list, 4))(list, *logo);
    }
done:
    imp_00607360(ss);
    sub_00459170(file);
    sub_005E4134(names, 0x1c, 5, (void *)imp_00607330);
}
