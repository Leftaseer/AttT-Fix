/* 0x0044FD50: CEngine::Step, by the engine's state (+0xAC; returns 0 for state 0 and 4, else 1): 1 and 2 run
 * 0x0044A9C0 and 0x0044E480; 3 makes the main menu (+0x68, 0x00472CB0 on the "dummy" level) with the music, sound
 * and ambient sound managers (+4, +8, +0xC, made when missing) and shows its MainMenu (or Credits, +0xB1) screen;
 * 4 posts the quit event 0x0060AC14 to 0x006C8C14; 5 moves to the next scene (+0x5C vf10; the world level +0x70
 * closes the menu keeping the camera, a MainMenu scene gets the music and ambient managers); 6 skips to the next
 * scene (none: state 4); 7 and 8 drop the scenes, re-run the start-up (0x0044AAB0, 0x0044EA20) and make the world
 * level (+0x70, 0x00543410 / 0x00545400): 7 loads the save of +0xB4 (unless +0xC8: the LocalTexts table serialized
 * by utils.GetTextTable into "Serialize = {...};" and run, Serialize.curContinent set, the continent +0xD4
 * started), 8 starts a new game (+0xD0) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_44FD50;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_44FD50;                 /* nScript::Table */
typedef struct { unsigned int w[6]; } Get_44FD50;                 /* nScript::TableGet */
DECOMP_C unsigned char __thiscall sub_0044A9C0(void *self);
DECOMP_C unsigned char __thiscall sub_0044E480(void *self);
DECOMP_C unsigned int __cdecl sub_0044A3F0(void *self, unsigned int eax, void *ev);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_00437970(void *self, const char *name, int a);
DECOMP_C void *__thiscall sub_00472CB0(void *self, void *level);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __cdecl sub_0044AF10(void);
DECOMP_C void __thiscall sub_0047F0E0(void *self, void *name);
DECOMP_C void __thiscall sub_0047D5C0(void *self, void *name, int vol);
DECOMP_C void __cdecl sub_0047D410(void *self, unsigned int eax, float v);
DECOMP_C int __thiscall sub_0047DFD0(void *self);
DECOMP_C void __cdecl sub_0044AF80(void);
DECOMP_C void __thiscall sub_004EDD60(void *self, float v);
DECOMP_C void __thiscall sub_004EE620(void *self);
DECOMP_C void __cdecl sub_0044AE00(void);
DECOMP_C void __thiscall sub_004299E0(void *self, float *range, void *name);
DECOMP_C void __cdecl sub_00427D70(void *self, unsigned int eax, float v);
DECOMP_C void __thiscall sub_00428A10(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_0046CF30(void *self);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C void __thiscall sub_004354C0(void *self, const void *m);
DECOMP_C void __thiscall sub_005ACBC0(void *self);
DECOMP_C void __cdecl sub_0044A480(void);
DECOMP_C void __cdecl sub_0044AD90(void);
DECOMP_C void __thiscall sub_005ACB40(void *self);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B770(void *t, void *out, const char *key);
DECOMP_C void *__thiscall sub_00449C00(void *self, void *t);
DECOMP_C void *__thiscall sub_004B41B0(void *self, const char *s);
DECOMP_C void *__thiscall sub_00449BA0(void *self, int b);
DECOMP_C void *__thiscall sub_0057A390(void *self, void *out, void *args, int n);
DECOMP_C void *__cdecl sub_00449010(void *self, unsigned int ebx, void *out, int a);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void __thiscall sub_00422000(void *self);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __cdecl sub_0044AAB0(void);
DECOMP_C void __cdecl sub_0044EA20(void *self, unsigned int ebx);
DECOMP_C void __thiscall sub_0057D220(void *self, const char *s, unsigned int n, int a);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void *__thiscall sub_00543410(void *self);
DECOMP_C void __thiscall sub_00545400(void *self, Str_44FD50 name, void *save);
DECOMP_C void __thiscall sub_004B5210(void *self);
DECOMP_C void *__cdecl sub_0043ABA0(void);
DECOMP_C void __thiscall sub_004E34F0(void *self, int a);
DECOMP_C char d_006C8C14[], d_0060AC14[], d_0060B02C[], d_006C8C38[], d_0060AEA0[], d_0060AE90[], d_0060ACC8[],
    d_006C8C3C[], d_006C8C30[], d_0060AE74[], d_0060AE70[], d_00607CC4[], d_0060B130[], d_006C88D8[], d_0060ACB4[],
    d_0060B128[], d_0060826C[], d_0060B120[], d_0060B110[], d_0060B10C[], d_00607CB8[], d_0060B108[], d_006C88D4[],
    d_0060ACA4[], d_0060FA8B[], d_006C88BC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_00607320)(void *, const char *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void (__thiscall *imp_006071FC)(void *, const void *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C unsigned int (__thiscall *imp_006072CC)(const void *) __asm__("__imp_?size@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIXZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
typedef void (__thiscall *vf0_44FD50)(void *self);
typedef void (__thiscall *vfi_44FD50)(void *self, int a);
typedef void (__thiscall *vfp_44FD50)(void *self, void *p);
typedef void *(__thiscall *vfr_44FD50)(void *self);
typedef void (__thiscall *show_44FD50)(void *self, void *name, void *args, int a);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define G(a) (*(void **)(a))
#define CFG (*(char **)(this + 0x54))

static void del_44FD50(void *o)
{
    ((vfi_44FD50)VF(o, 0))(o, 1);
}

/* a scene (+4) takes a sound manager */
static void sound_44FD50(char *scene, void *mgr)
{
    ((vfp_44FD50)VF(scene + 4, 0xc))(scene + 4, mgr);
}

/* drops the current (+0x5C) and the menu (+0x68) scenes and re-runs the start-up */
static void restart_44FD50(char *this)
{
    void *cur = *(void **)(this + 0x5c), *menu = *(void **)(this + 0x68);
    *(int *)(this + 0xac) = 1;
    *(void **)(this + 0x70) = 0;
    if (cur == menu) {
        if (menu) {
            del_44FD50(menu);
            *(void **)(this + 0x68) = 0;
        }
    } else if (cur)
        del_44FD50(cur);
    *(void **)(this + 0x5c) = 0;
    *(int *)((char *)G(d_006C88D8) + 0x2c) = 0;
    sub_005ACBC0(G(d_006C88D8));
    sub_0044A480();
    sub_0044AD90();
    sub_005ACB40(G(d_006C88D8));
}

static void reinit_44FD50(void)
{
    sub_0042F160();
    sub_0044AAB0();
    sub_0044EA20(sub_0042F160(), 0);
}

/* the world level (+0x70) becomes the current scene */
static void start_44FD50(char *this, void *w)
{
    sub_0046CF30(*(void **)(this + 0x80));
    *(int *)(*(char **)(this + 0x8c) + 0x208) = 0;
    *(void **)(this + 0x60) = 0;
    *(void **)(this + 0x5c) = w;
    ((vfi_44FD50)VF(w, 8))(w, 0);
}

static void *level_44FD50(void)
{
    void *mem = sub_005E3EAE(0x3ec);
    return mem ? sub_00543410(mem) : 0;
}

static void menu_44FD50(char *this)
{
    void *mem;
    if (*(void **)(this + 0x70)) {
        del_44FD50(*(void **)(this + 0x70));
        *(void **)(this + 0x70) = 0;
    }
    mem = sub_005E3EAE(0x198);
    if (mem) {
        Get_44FD50 g;
        *(void **)(this + 0x68) = sub_00472CB0(mem, sub_00437970(&g, d_0060B02C, 1));
        sub_00427820(&g);
    } else
        *(void **)(this + 0x68) = 0;
    *(void **)(this + 4) = G(d_006C8C38);
    if (!*(void **)(this + 4)) {
        Str_44FD50 a, name;
        sub_0044AF10();
        *(void **)(this + 4) = G(d_006C8C38);
        imp_00607324(&a, d_0060AEA0);
        imp_006071DC(&name, &a, d_0060AE90);
        imp_00607330(&a);
        sub_0047F0E0(*(void **)(this + 4), &name);
        imp_00607324(&a, d_0060ACC8);
        sub_0047D5C0(*(void **)(this + 4), &a, 100);
        imp_00607330(&a);
        sub_0047D410(*(void **)(this + 4), (unsigned int)(size_t)CFG, *(float *)(CFG + 0x88));
        sub_0047DFD0(*(void **)(this + 4));
        imp_00607330(&name);
    }
    if (*(void **)(this + 4))
        sound_44FD50(*(char **)(this + 0x68), G(d_006C8C38));
    *(void **)(this + 8) = G(d_006C8C3C);
    if (!*(void **)(this + 8)) {
        sub_0044AF80();
        *(void **)(this + 8) = G(d_006C8C3C);
        sub_004EDD60(*(void **)(this + 8), *(float *)(CFG + 0x8c));
        sub_004EE620(*(void **)(this + 8));
    }
    *(void **)(this + 0xc) = G(d_006C8C30);
    if (!*(void **)(this + 0xc)) {
        Str_44FD50 a;
        float range[2];
        sub_0044AE00();
        *(void **)(this + 0xc) = G(d_006C8C30);
        imp_00607324(&a, d_0060AE74);
        range[0] = *(float *)d_0060AE70;
        range[1] = *(float *)d_0060AE70;
        sub_004299E0(*(void **)(this + 0xc), range, &a);
        imp_00607330(&a);
        sub_00427D70(*(void **)(this + 0xc), 0, *(float *)(CFG + 0x90));
        sub_00428A10(*(void **)(this + 0xc));
    }
    {
        Str_44FD50 s;
        Tbl_44FD50 nil;
        void *m = *(void **)(this + 0x68);
        imp_00607324(&s, d_0060ACC8);
        nil.w[1] = 0;
        nil.w[0] = (unsigned int)(size_t)d_00607CC4;
        nil.w[2] = 0xffffffffu;
        ((show_44FD50)VF(m, 0x3c))(m, &s, &nil, 1);
        sub_004220A0(&nil);
        imp_00607330(&s);
    }
    {
        void *m = *(void **)(this + 0x68);
        *(void **)(this + 0x60) = 0;
        *(void **)(this + 0x5c) = m;
        ((vfi_44FD50)VF(m, 8))(m, 0);
    }
    if (*(void **)(this + 0x68) && this[0xb1]) {
        Str_44FD50 s;
        void *m;
        imp_00607324(&s, d_0060B130);
        m = *(void **)(this + 0x68);
        ((vfp_44FD50)VF(m, 0x48))(m, &s);
        imp_00607330(&s);
        *(int *)(this + 0xac) = 5;
    } else
        *(int *)(this + 0xac) = 1;
}

static void next_44FD50(char *this)
{
    void *cur, *n;
    sub_0046CF30(*(void **)(this + 0x80));
    *(int *)(this + 0xac) = 1;
    *(int *)(*(char **)(this + 0x8c) + 0x208) = 0;
    cur = *(void **)(this + 0x5c);
    *(void **)(this + 0x60) = cur;
    n = ((vfr_44FD50)VF(cur, 0x10))(cur);
    *(void **)(this + 0x5c) = n;
    if (n == *(void **)(this + 0x70)) {
        if (*(void **)(this + 0x68)) {
            unsigned int cam[0x44 / 4];
            char *c;
            sub_00435550(sub_00424E70(), cam);
            if (*(void **)(this + 0x68)) {
                del_44FD50(*(void **)(this + 0x68));
                *(void **)(this + 0x68) = 0;
            }
            sub_004354C0(sub_00424E70(), cam);
            c = sub_00424E70();
            ((vf0_44FD50)VF(c + 4, 0x18))(c + 4);
        }
        return;
    }
    if (!n)
        return;
    if (imp_006071E4(*(char **)(this + 0x60) + 0x1c, d_0060ACC8)) {
        sound_44FD50(*(char **)(this + 0x5c), G(d_006C8C38));
        sound_44FD50(*(char **)(this + 0x5c), G(d_006C8C30));
    }
    n = *(void **)(this + 0x5c);
    ((vfp_44FD50)VF(n, 8))(n, *(void **)(this + 0x60));
}

static void load_44FD50(char *this)
{
    Str_44FD50 text;
    void *w;
    restart_44FD50(this);
    imp_006071E0(&text);
    if (!*(int *)(this + 0xc8)) {
        Tbl_44FD50 t1, t2;
        unsigned int obj[3];
        unsigned int fn[8];
        Get_44FD50 res;
        Str_44FD50 s;
        void *ser, *f;
        imp_006072F8(&text, d_0060ACB4);
        imp_00607320(&text, d_0060B128);
        ser = sub_004323E0(&t1, d_0060ACB4);
        obj[1] = 0;
        obj[0] = (unsigned int)(size_t)d_0060826C;
        obj[2] = 0;
        f = sub_0057B770(sub_004323E0(&t2, d_0060B120), fn, d_0060B110);
        imp_006071FC(&text, sub_00449010(sub_0057A390(f, &res, sub_00449BA0(sub_004B41B0(sub_00449C00(obj, ser),
                                                                                         d_0060B10C), 1), -1),
                                         0, &s, 1));
        imp_00607330(&s);
        sub_00427820(&res);
        sub_004378D0(fn);
        sub_004220A0(&t2);
        obj[0] = (unsigned int)(size_t)d_00607CB8;
        sub_00422000(obj);
        sub_004220A0(&t1);
        imp_00607320(&text, d_0060B108);
    }
    reinit_44FD50();
    if (!*(int *)(this + 0xc8)) {
        void *L = G(d_006C88D4);
        unsigned int n = imp_006072CC(&text);
        sub_0057D220(L, imp_0060732C(&text), n, 0);
    }
    {
        char *app = *(char **)(this + 0x8c);
        Tbl_44FD50 t;
        this[0xd0] = 0;
        app[0x228] = 1;
        sub_0057BC80(sub_004323E0(&t, d_0060ACB4), d_0060ACA4, (float)*(int *)(this + 0xd4));
        sub_004220A0(&t);
    }
    w = level_44FD50();
    *(void **)(this + 0x70) = w;
    {
        Str_44FD50 e;
        imp_00607324(&e, d_0060FA8B);
        sub_00545400(w, e, this + 0xb4);
    }
    if (!*(int *)(this + 0xc8)) {
        int c;
        sub_004B5210(G(d_006C88BC));
        c = *(int *)(this + 0xd4);
        sub_004E34F0(sub_0043ABA0(), c);
    }
    start_44FD50(this, w);
    imp_00607330(&text);
}

static void newgame_44FD50(char *this)
{
    void *w;
    Str_44FD50 save, e;
    restart_44FD50(this);
    reinit_44FD50();
    this[0xd0] = 1;
    (*(char **)(this + 0x8c))[0x228] = 1;
    w = level_44FD50();
    *(void **)(this + 0x70) = w;
    imp_00607324(&save, d_0060FA8B);
    imp_00607324(&e, d_0060FA8B);
    sub_00545400(w, e, &save);
    imp_00607330(&save);
    start_44FD50(this, w);
}

DECOMP(0044FD50)
unsigned char __thiscall f_0044FD50(void *self)
{
    char *this = (char *)self;
    switch (*(unsigned int *)(this + 0xac)) {
    case 0:
        return 0;
    case 1:
        sub_0044A9C0(this);
        break;
    case 2:
        sub_0044E480(this);
        break;
    case 3:
        menu_44FD50(this);
        break;
    case 4: {
        void *ev = d_0060AC14;
        sub_0044A3F0(d_006C8C14, (unsigned int)(size_t)&ev, &ev);
        return 0;
    }
    case 5:
        next_44FD50(this);
        break;
    case 6: {
        void *n;
        sub_0046CF30(*(void **)(this + 0x80));
        *(int *)(this + 0xac) = 1;
        *(int *)(*(char **)(this + 0x8c) + 0x208) = 0;
        *(void **)(this + 0x60) = 0;
        n = *(void **)(this + 0x5c);
        n = ((vfr_44FD50)VF(n, 0x10))(n);
        *(void **)(this + 0x5c) = n;
        if (!n)
            *(int *)(this + 0xac) = 4;
        else
            ((vf0_44FD50)VF(n, 0xc))(n);
        break;
    }
    case 7:
        load_44FD50(this);
        break;
    case 8:
        newgame_44FD50(this);
        break;
    }
    return 1;
}
