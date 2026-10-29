/* 0x00584190: GUIScene vf15 (load name, args, modal): the name (+0x1C; an empty one takes the global testSceneName)
 * and the arguments (+0x8C, modal +0xA4) are set, the scene is cleared (0x005840E0) and they are set again; a modal
 * scene shows the back buffer (0x00421730 +0x80, picture 0x0047A0D0 +0x84 over the screen); the root (0x004AF7A0,
 * +0x7C) is made current; GUIScene[name] becomes the script (+0x98) with scene = +0x74; its background picture
 * (0x0057F2F0, +0x78, bgndWidth x bgndHeight) is centred (+0x4C), "Exit" + exitColor names the exit (+0x130); its Load
 * runs (with the +0x94 reference when there is one), its Update is kept (+0x14C); the cursor (+0x88, 0x004207C0
 * "Default") is set, the root added, isChild read (+0xA5) and the camera (+0xEC, 0x004354C0) reset */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_584190;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_584190;                 /* nScript::Table */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_584190;
DECOMP_C void *__thiscall sub_0045C7E0(void *self, int idx);
DECOMP_C void *__cdecl sub_0057B080(void *self, unsigned int ebx, void *out, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_005840E0(void *self);
DECOMP_C char *__cdecl sub_00421730(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_0047A0D0(void *self);
DECOMP_C void *__thiscall sub_004AF7A0(void *self);
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C void __thiscall sub_0057C2D0(void *self, const char *key, void *obj);
DECOMP_C void *__cdecl sub_0057B230(void *self, unsigned int ebx, void *out, const char *key, const char *def);
DECOMP_C void *__thiscall sub_0057F2F0(void *self, void *name);
DECOMP_C float __thiscall sub_0057AED0(void *self, const char *key, float def);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_0057C660(void *t, const char *key);
DECOMP_C void __thiscall sub_00436FD0(void *self, void *f);
DECOMP_C unsigned int *__thiscall sub_004207C0(void *self, void *name);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C unsigned char __thiscall sub_0057ABB0(void *self, const char *key, int def);
DECOMP_C void __thiscall sub_004354C0(void *self, const void *m);
DECOMP_C char d_0060FA8B[], d_0061E320[], d_00607C14[], d_00607C08[], d_006C8958[], d_006C895C[], d_0060AD08[],
    d_0061414C[], d_0061E314[], d_0061E30C[], d_0061E300[], d_0061E2F8[], d_0061E2EC[], d_0061E2E0[], d_0060FF88[],
    d_008D122C[], d_0060826C[], d_00607CB8[], d_0060F180[], d_00607C00[], d_0061E2D8[];
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__cdecl *imp_006071D8)(void *, const char *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBDABV10@@Z");
typedef void (__thiscall *vf1_584190)(void *self, void *a);
typedef void (__thiscall *vf2_584190)(void *self, void *a, int b);
typedef void *(__thiscall *vfp_584190)(void *self);
typedef void (__thiscall *vff_584190)(void *self, float a, float b);
typedef void (__thiscall *vf0_584190)(void *self);
typedef void (__thiscall *rel_584190)(void *self, int flag);

#define VT(o) (*(void ***)(o))
#define LS (*(void **)d_008D122C)

static void name_584190(char *this, void *name)
{
    if (imp_006071E4(name, d_0060FA8B)) {
        Tbl_584190 g;
        Str_584190 s;
        sub_0057B080(sub_0045C7E0(&g, -10002), (unsigned int)(size_t)name, &s, d_0061E320);
        sub_004220A0(&g);
        imp_0060731C(this + 0x1c, &s);
        imp_00607330(&s);
    } else
        imp_0060731C(this + 0x1c, name);
}

DECOMP(00584190)
int __thiscall f_00584190(char *this, void *name, void *args, int modal)
{
    void *layer = this + 4, *cam, *o, *scr = this + 0x98;
    Str_584190 s, bg;

    name_584190(this, name);
    this[0xa4] = (char)modal;
    sub_0057A860(this + 0x8c, args);
    cam = sub_00424E70();
    sub_005840E0(this);
    this[0xa4] = (char)modal;
    sub_0057A860(this + 0x8c, args);
    name_584190(this, name);

    if (this[0xa4]) {
        void *m;
        *(char **)(this + 0x80) = sub_00421730();
        o = sub_005E3EAE(0x224);
        if (o)
            o = sub_0047A0D0(o);
        *(void **)(this + 0x84) = o;
        imp_00607324(&s, d_00607C14);
        o = *(void **)(this + 0x84);
        ((vf2_584190)VT(o)[0x2c / 4])(o, &s, 1);
        imp_00607330(&s);
        imp_00607324(&s, d_00607C08);
        o = *(void **)(this + 0x84);
        m = ((vfp_584190)VT(o)[0x30 / 4])(o);
        ((vf2_584190)VT(m)[0xc / 4])(m, &s, *(int *)(*(char **)(this + 0x80) + 4));
        imp_00607330(&s);
        o = *(void **)(this + 0x84);
        ((vff_584190)VT(o)[0x94 / 4])(o, *(float *)d_006C895C, *(float *)d_006C8958);
        ((vf1_584190)VT(layer)[4 / 4])(layer, *(void **)(this + 0x84));
    }
    o = sub_005E3EAE(0x84);
    if (o)
        o = sub_004AF7A0(o);
    *(void **)(this + 0x7c) = o;
    sub_004AD530(o, (unsigned int)(size_t)o);
    {
        Tbl_584190 gs, t;
        sub_0057A860(scr, sub_0057B4E0(sub_004323E0(&gs, d_0060AD08), &t, imp_0060732C(this + 0x1c)));
        sub_004220A0(&t);
        sub_004220A0(&gs);
    }
    sub_0057C2D0(scr, d_0061414C, this + 0x74);
    sub_0057B230(scr, 0xffffffffu, &bg, d_0061E314, d_0060FA8B);
    {
        Str_584190 ec, ex;
        sub_0057B230(scr, 0xc, &ec, d_0061E300, d_0061E30C);
        imp_0060731C(this + 0x130, imp_006071D8(&ex, d_0061E2F8, &ec));
        imp_00607330(&ex);
        imp_00607330(&ec);
    }

    *(void **)(this + 0x78) = 0;
    if (bg.w[5]) {
        float w, h, a, b;
        o = sub_005E3EAE(0x224);
        if (o)
            o = sub_0057F2F0(o, &bg);
        *(void **)(this + 0x78) = o;
        w = sub_0057AED0(scr, d_0061E2EC, 0.0f);
        h = sub_0057AED0(scr, d_0061E2E0, 0.0f);
        o = *(void **)(this + 0x78);
        ((vff_584190)VT(o)[0x94 / 4])(o, w, h);
        o = *(void **)(this + 0x78);
        {
            float oh = *(float *)((char *)o + 0x78), ow = *(float *)((char *)o + 0x74);
            a = (float)(((double)*(float *)d_006C895C - ow) * 0.5);
            b = (float)(((double)*(float *)d_006C8958 - oh) * 0.5);
        }
        *(float *)(this + 0x4c) = a;
        *(float *)(this + 0x50) = b;
        ((vf1_584190)VT(o)[0x6c / 4])(o, this + 0x4c);
        ((vf1_584190)VT(layer)[4 / 4])(layer, *(void **)(this + 0x78));
    }

    if (*(int *)(this + 0x94) > 0) {
        struct { void *vt; void *child; int n; } a;
        Tmp_584190 fn, res;
        void *f;
        a.child = 0;
        a.vt = d_0060826C;
        a.n = 0;
        f = sub_0057B770(scr, &fn, d_0060FF88);
        sub_00403390(LS, -10000, *(int *)(this + 0x94));
        a.n++;
        sub_0057A230(f, &res, &a, 0);
        sub_00427820(&res);
        sub_004378D0(&fn);
        a.vt = d_00607CB8;
        sub_00422000(&a);
    } else {
        Tmp_584190 fn, res;
        sub_0057A180(sub_0057B770(scr, &fn, d_0060FF88), &res, 0);
        sub_00427820(&res);
        sub_004378D0(&fn);
    }
    if (sub_0057C660(scr, d_0060F180)) {
        Tmp_584190 fn;
        sub_00436FD0(this + 0x14c, sub_0057B770(scr, &fn, d_0060F180));
        sub_004378D0(&fn);
    }

    {
        void *mem = sub_005E3EAE(0x5c);
        unsigned int *c = 0, *old;
        if (mem) {
            imp_00607324(&s, d_00607C00);
            c = sub_004207C0(mem, &s);
        }
        if (c)
            c[1]++;
        old = *(unsigned int **)(this + 0x88);
        if (old && --old[1] == 0)
            ((rel_584190)VT(old)[0])(old, 1);
        *(unsigned int **)(this + 0x88) = c;
        if (mem)
            imp_00607330(&s);
    }
    {
        void *cur = sub_00421680();
        ((vf1_584190)VT(cur)[0xe8 / 4])(cur, *(void **)(this + 0x88));
    }
    ((vf1_584190)VT(layer)[0xc / 4])(layer, *(void **)(this + 0x7c));
    this[0xa5] = sub_0057ABB0(scr, d_0061E2D8, 0);
    sub_004354C0(cam, this + 0xec);
    {
        void *c4 = (char *)cam + 4;
        ((vf0_584190)VT(c4)[0x18 / 4])(c4);
    }
    imp_00607330(&bg);
    return 0;
}
