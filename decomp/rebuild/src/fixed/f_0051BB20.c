/* 0x0051BB20: CTacticLevel start (the armies of the list argument): with a loading screen (0x004FE010, steps by
 * 0x004FDFD0) the attacking army (TacticLevel.armyWhoAttack) gives the battle centre (+0xAC, armyPos x / z) and
 * SpellCenterTL; TacticLevel.Init runs and gets the scene; the camera (+0x130), the 3D view (+0x84), the battle
 * Radius (0x006CA914), the rings (+0x218, +0x214) and the troop marks; each army's leader joins the list +0xA0
 * and the update list, and the continent leader builds the battlefield (+0x98, 0x004FD520) and the battle logic
 * (+0xBC, 0x0050C3C0); then the GlowViewAll overlay (+0x22C) with its detail matrix 0x006CA918, the input, the
 * GUIScene.TacticLevel script (+0x220: scene, Load with the troops, NextTroop), the camera settings
 * (TacticLevel camera: FOV, clipping, aspect; saved at +0x188 / +0x1CC), the Kill function, the Battle music, the
 * attacker's world marker and the starting sound */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_51BB20;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_51BB20;                 /* nScript::Table */
typedef struct { unsigned int w[6]; } Get_51BB20;                 /* nScript::TableGet */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0051B460(void *self);
DECOMP_C void __thiscall sub_004FE010(void *self);
DECOMP_C void __thiscall sub_004FDFD0(void *self, int step);
DECOMP_C void __thiscall sub_004FDEF0(void *self);
DECOMP_C void __thiscall sub_004FDE90(void *self);
DECOMP_C void *__thiscall sub_0057B770(void *t, void *out, const char *key);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void __thiscall sub_0057C2D0(void *self, const char *key, void *obj);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004EB690(void *self, void *level);
DECOMP_C void __thiscall sub_004EB4F0(void *self);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C void *__thiscall sub_004AF7A0(void *self);
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const void *key);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_00435E00(void *self, int a);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void *__thiscall sub_0045C7E0(void *self, int idx);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, void *val);
DECOMP_C void *__thiscall sub_004F62C0(void *self);
DECOMP_C void *__thiscall sub_00525610(void *self, float x, float z, float r);
DECOMP_C void *__thiscall sub_004CC170(void *self);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void __thiscall sub_005296B0(void *self);
DECOMP_C char *__cdecl sub_004F9ED0(void);
DECOMP_C void __thiscall sub_004FD520(void *self, float x, float y, float z, float r);
DECOMP_C void __cdecl sub_004F9FB0(void);
DECOMP_C void *__cdecl sub_004FF9A0(void);
DECOMP_C void *__thiscall sub_0050C3C0(void *self, void *army, void *leader, void *level, float x, float y, float z,
                                       void *b8, void *marks);
DECOMP_C void *__thiscall sub_00448C50(void *self, void *name);
DECOMP_C void *__thiscall sub_004FDAF0(void *self, void *tex, int w, int h, int a);
DECOMP_C float *__stdcall sub_005B8044(float *out, float x, float y, float z);   /* D3DXMatrixScaling */
DECOMP_C void *__stdcall sub_005B8020(void *out, void *a, void *b);   /* D3DXMatrixMultiply */
DECOMP_C void __cdecl sub_00432EA0(void *eax);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __thiscall sub_005193E0(void *self);
DECOMP_C void __thiscall sub_00519680(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__thiscall sub_0057D070(void *self, void *t);
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void __thiscall sub_00422000(void *self);
DECOMP_C void __cdecl sub_00403120(void *L, const char *s);          /* lua_pushstring */
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C char *__cdecl sub_00518B10(void);
DECOMP_C char *__cdecl sub_0044B080(void);
DECOMP_C void *__thiscall sub_004EB130(void *self);
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);      /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034F0(void *L, int idx, const char *k);   /* lua_setfield */
DECOMP_C void __thiscall sub_0047D5C0(void *self, void *name, int vol);
DECOMP_C void *__thiscall sub_00518D10(void *self);
DECOMP_C int __thiscall sub_0046CF30(void *self);
DECOMP_C char *__cdecl sub_00435C50(void);
DECOMP_C void __thiscall sub_004E4200(void *self);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __thiscall sub_0055C610(void *self, float x, float y, float z, float r);
DECOMP_C void *__cdecl sub_0044E7A0(void *name);
DECOMP_C float __thiscall sub_004ED000(void *self);
DECOMP_C char d_0060AB58[], d_0060AB48[], d_00609978[], d_00613FD8[], d_006141B0[], d_006098D0[], d_006098C8[],
    d_006098CC[], d_0060B9C4[], d_006141A0[], d_00614198[], d_006CA914[], d_006CA9BC[], d_0061418C[], d_00614180[],
    d_00614174[], d_006CA990[], d_00614168[], d_006C8714[], d_006C3450[], d_006CA918[], d_006CA938[], d_006CA93C[],
    d_0060B874[], d_00614154[], d_006CA8F4[], d_006CA8F0[], d_008D1230[], d_006CAAE8[], d_0060AD08[], d_0061414C[],
    d_0060826C[], d_0060FF88[], d_00607CB8[], d_00613A90[], d_008D122C[], d_008D10A0[], d_006CA260[], d_00609850[],
    d_00614144[], d_00614138[], d_0061412C[], d_00614128[], d_00518CF0[], d_00614120[], d_006C8C38[], d_00614118[],
    d_006C8C3C[], d_00614108[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vfp_51BB20)(void *self, void *p);
typedef void (__thiscall *vf0_51BB20)(void *self);
typedef void *(__thiscall *vfr_51BB20)(void *self);
typedef void (__thiscall *mat_51BB20)(void *self, const char *name, void *m);
typedef void (__thiscall *vfv_51BB20)(void *self, float v, int a);
typedef void (__thiscall *vf2_51BB20)(void *self, int a, int b);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define LS (*(void **)d_008D122C)
#define RADIUS (*(float *)d_006CA914)
#define F(o) (*(float *)(this + (o)))

/* the level's update list (+4) takes o through vf */
static void add_51BB20(char *this, int vf, void *o)
{
    char *l = this + 4;
    ((vfp_51BB20)VF(l, vf))(l, o);
}

/* f = script function key of t, called with args */
static void call_51BB20(void *t, const char *key, void *args)
{
    unsigned int fn[8];
    Get_51BB20 res;
    sub_0057A230(sub_0057B770(t, fn, key), &res, args, 0);
    sub_00427820(&res);
    sub_004378D0(fn);
}

DECOMP(0051BB20)
void __thiscall f_0051BB20(void *self, char **armies)
{
    char *this = (char *)self;
    Tbl_51BB20 army, args, ct;
    unsigned int loader[0x464 / 4];
    void *mem, *marks;
    char *cam;

    {
        struct { void *t; const char *k; } ref;
        Tbl_51BB20 tl, t;
        ref.t = sub_004323E0(&tl, d_0060AB58);
        ref.k = d_0060AB48;
        sub_004369F0(&ref, &t);
        sub_00435D90(&army, &t);
        sub_004220A0(&t);
        sub_004220A0(&tl);
    }
    this[0x94] = 0;
    sub_0051B460(this);
    sub_004FE010(loader);
    {
        Tbl_51BB20 tl;
        unsigned int fn[8];
        Get_51BB20 res;
        sub_0057A180(sub_0057B770(sub_004323E0(&tl, d_0060AB58), fn, d_00609978), &res, 0);
        sub_00427820(&res);
        sub_004378D0(fn);
        sub_004220A0(&tl);
        sub_0057C2D0(sub_004323E0(&tl, d_0060AB58), d_00613FD8, this + 0x78);
        sub_004220A0(&tl);
    }
    mem = sub_005E3EAE(0x60);
    {
        void *o = mem ? sub_004EB690(mem, this) : 0;
        sub_004EB4F0(o);
        sub_004205C0(this, o);
    }
    mem = sub_005E3EAE(0x84);
    {
        void *v = mem ? sub_004AF7A0(mem) : 0;
        *(void **)(this + 0x84) = v;
        sub_004AD530(v, (unsigned int)(size_t)v);
    }
    sub_004FDFD0(loader, 1);
    {
        Tbl_51BB20 a, b;
        void *pa = sub_0057B4E0(&army, &a, d_006141B0), *pb = sub_0057B4E0(&army, &b, d_006141B0);
        float x = sub_0057AD40(pb, d_006098D0), z = sub_0057AD40(pa, d_006098C8);
        F(0xac) = x;
        F(0xb0) = 0.0f;
        F(0xb4) = z;
        sub_004220A0(&b);
        sub_004220A0(&a);
    }
    cam = sub_00424E70();
    *(char **)(this + 0x130) = cam;
    cam[0x211] = 1;
    *(float *)(cam + 0x214) = *(float *)d_0060B9C4;
    cam = *(char **)(this + 0x130);
    __builtin_memcpy(cam + 0x50, this + 0xa0, 12);
    __builtin_memcpy(cam + 0x44, this + 0xac, 12);
    cam[0x71] = 1;
    cam = *(char **)(this + 0x130) + 4;
    ((vf0_51BB20)VF(cam, 0x18))(cam);
    sub_00435E00(&args, 0);
    sub_0057BC80(&args, d_006098D0, F(0xac));
    sub_0057BC80(&args, d_006098CC, F(0xb0));
    sub_0057BC80(&args, d_006098C8, F(0xb4));
    {
        Tbl_51BB20 g;
        sub_0057BF50(sub_0045C7E0(&g, -10002), d_006141A0, &args);
        sub_004220A0(&g);
        RADIUS = sub_0057AD40(sub_004323E0(&g, d_0060AB58), d_00614198);
        sub_004220A0(&g);
    }
    mem = sub_005E3EAE(0x50);
    *(void **)(this + 0x218) = mem ? sub_004F62C0(mem) : 0;
    *(void **)d_006CA9BC = *(void **)(this + 0x218);
    mem = sub_005E3EAE(0x24);
    *(void **)(this + 0x214) = mem ? sub_00525610(mem, F(0xac), F(0xb4), RADIUS) : 0;
    mem = sub_005E3EAE(0x50);
    marks = mem ? sub_004CC170(mem) : 0;
    {
        char **head = (char **)armies[1], **node;
        for (node = (char **)*head; node != (char **)armies[1]; node = (char **)*node) {
            char *a = (char *)((vfr_51BB20)VF(node[2], 0x1c))(node[2]);
            char **lh, **n;
            if (!a)
                continue;
            add_51BB20(this, 0xc, a);
            lh = *(char ***)(this + 0xa4);
            n = sub_005AD6C0(lh, (char **)lh[1], &a);
            sub_004E0EF0(this + 0xa0, 1);
            lh[1] = (char *)n;
            *(char ***)n[1] = n;
            if (!imp_006071E4(a + 8, d_0061418C) && !imp_006071E4(a + 8, d_00614180) &&
                !imp_006071E4(a + 8, d_00614174))
                continue;
            sub_005296B0(a);
            (*(char **)(this + 0x130))[0x228] = 0;
            {
                char *t = sub_004F9ED0();
                *(char **)(this + 0x98) = t;
                sub_004FD520(t, F(0xac), F(0xb0), F(0xb4), RADIUS);
            }
            sub_004FDFD0(loader, 2);
            add_51BB20(this, 0xc, *(void **)(this + 0x98));
            sub_004F9FB0();
            add_51BB20(this, 0xc, sub_004FF9A0());
            mem = sub_005E3EAE(0x2a8);
            *(void **)(this + 0xbc) = mem ? sub_0050C3C0(mem, &army, a, this, F(0xac), F(0xb0), F(0xb4),
                                                         *(void **)(this + 0xb8), marks) : 0;
            sub_004205C0(this, *(void **)(this + 0xbc));
            sub_004FDFD0(loader, 2);
            *(char **)d_006CA990 = this + 4;
        }
    }
    {
        char *c = *(char **)(this + 0x98), *o;
        float fw = (float)*(int *)(c + 0x78), fh = (float)*(int *)(c + 0x74);
        mem = sub_005E3EAE(0x1ac);
        if (mem) {
            Str_51BB20 s;
            int n;
            imp_00607324(&s, d_00614168);
            n = (int)(long long)(fw + fw + 1.0f);
            o = (char *)sub_004FDAF0(mem, sub_00448C50(*(void **)d_006C8714, &s), n, n, 1);
            *(char **)(this + 0x22c) = o;
            imp_00607330(&s);
        } else
            *(char **)(this + 0x22c) = 0;
        o = *(char **)(this + 0x22c);
        __builtin_memcpy(o + 0x58, this + 0xac, 12);
        o[0x64] = 1;
        {
            float c64 = *(float *)(*(char **)(this + 0x98) + 0x64), a, b, w, sy, sx, t;
            float scale[16], out[16];
            o = *(char **)(this + 0x22c);
            o[0x7c] = 1;
            a = fh * 1.5f;
            a = a + 1.5f;
            t = c64 * a;
            *(float *)(o + 0x70) = t * 2.0f;
            b = fw * 2.0f;
            b = b + 1.0f;
            t = 4.2f * b;
            *(float *)(o + 0x78) = t * 2.0f;
            __builtin_memcpy(d_006CA918, d_006C3450, 0x40);
            w = 2.0f * a;
            w = w / 3.0f;
            *(float *)d_006CA938 = 0.0f;
            *(float *)d_006CA93C = (int)(w + 0.5f) % 2 == 1 ? *(float *)d_0060B874 : 0.0f;
            sy = b * 0.5f;
            sx = w;
            sub_005B8044(scale, sx, sy, 1.0f);
            sub_005B8020(out, d_006CA918, scale);
            __builtin_memcpy(d_006CA918, out, 0x40);
        }
        {
            void *e = ((vfr_51BB20)VF(*(void **)(this + 0x22c), 0x30))(*(void **)(this + 0x22c));
            ((mat_51BB20)VF(e, 0x50))(e, d_00614154, d_006CA918);
        }
    }
    add_51BB20(this, 4, *(void **)(this + 0x22c));
    add_51BB20(this, 0xc, *(char **)d_006CA8F4 ? *(char **)d_006CA8F4 + 4 : 0);
    add_51BB20(this, 0xc, *(char **)d_006CA8F0 ? *(char **)d_006CA8F0 + 4 : 0);
    sub_004FDFD0(loader, 2);
    sub_00432EA0(0);
    add_51BB20(this, 4, *(char **)(this + 0x218) ? *(char **)(this + 0x218) + 0x18 : 0);
    add_51BB20(this, 4, marks ? (char *)marks + 0x18 : 0);
    sub_004FDFD0(loader, 1);
    sub_004FDFD0(loader, 1);
    sub_004FDFD0(loader, 4);
    sub_004FDFD0(loader, 1);
    *(char **)(this + 0x8c) = sub_004215D0();
    *(char **)(this + 0x90) = sub_00427990();
    sub_004FDFD0(loader, 1);
    sub_005193E0(this);
    sub_00519680(this);
    *(char **)d_008D1230 = this;
    *(char **)d_006CAAE8 = this;
    sub_004AD530(*(void **)(this + 0x84), 0);
    {
        Tbl_51BB20 g, t;
        sub_0057A860(this + 0x220, sub_0057B4E0(sub_004323E0(&g, d_0060AD08), &t, d_0060AB58));
        sub_004220A0(&t);
        sub_004220A0(&g);
    }
    sub_0057C2D0(this + 0x220, d_0061414C, this + 0x78);
    {
        unsigned int obj[3];
        void *v = *(char **)(this + 0xbc) ? *(char **)(this + 0xbc) + 0x38 : 0;
        obj[1] = 0;
        obj[0] = (unsigned int)(size_t)d_0060826C;
        obj[2] = 0;
        {
            unsigned int fn[8];
            Get_51BB20 res;
            void *f = sub_0057B770(this + 0x220, fn, d_0060FF88);
            sub_0057A230(f, &res, sub_0057D070(obj, v), 0);
            sub_00427820(&res);
            sub_004378D0(fn);
        }
        obj[0] = (unsigned int)(size_t)d_00607CB8;
        sub_00422000(obj);
    }
    {
        unsigned int obj[3];
        unsigned int fn[8];
        Get_51BB20 res;
        void *f;
        char *troop;
        obj[1] = 0;
        obj[0] = (unsigned int)(size_t)d_0060826C;
        obj[2] = 0;
        f = sub_0057B770(this + 0x220, fn, d_00613A90);
        troop = *(char **)(*(char **)(this + 0xbc) + 0x64);
        sub_00403120(LS, imp_0060732C(troop + 0x2c));
        obj[2]++;
        sub_004030A0(LS, (float)(int)sub_0051DAA0(troop));
        obj[2]++;
        sub_0057A230(f, &res, obj, 0);
        sub_00427820(&res);
        sub_004378D0(fn);
        obj[0] = (unsigned int)(size_t)d_00607CB8;
        sub_00422000(obj);
    }
    *(char **)d_008D10A0 = this;
    *(char **)d_006CA260 = this;
    {
        Tbl_51BB20 g;
        float aspect, maxc, minc, fov;
        sub_0057B4E0(sub_004323E0(&g, d_00609850), &ct, d_0060AB58);
        sub_004220A0(&g);
        aspect = sub_0057AD40(&ct, d_00614144);
        maxc = sub_0057AD40(&ct, d_00614138);
        minc = sub_0057AD40(&ct, d_0061412C);
        fov = sub_0057AD40(&ct, d_00614128);
        cam = *(char **)(this + 0x130);
        *(float *)(cam + 0x74) = fov;
        cam[0x84] = 1;
        *(float *)(cam + 0x78) = minc;
        *(float *)(cam + 0x7c) = maxc;
        *(float *)(cam + 0x80) = aspect;
        cam = *(char **)(this + 0x130) + 4;
        ((vf0_51BB20)VF(cam, 0x18))(cam);
    }
    {
        unsigned int m[0x44 / 4];
        int a0, a1, a2;
        __builtin_memcpy(this + 0x188, sub_00435550(*(void **)(this + 0x130), m), 0x44);
        {
            void *p = sub_00435550(*(void **)(this + 0x130), m);
            a0 = *(int *)(this + 0x188);
            a1 = *(int *)(this + 0x18c);
            __builtin_memcpy(this + 0x1cc, p, 0x44);
        }
        a2 = *(int *)(this + 0x190);
        *(int *)(this + 0x1d8) = a0;
        *(int *)(this + 0x1dc) = a1;
        F(0x1f0) = 0.0f;
        *(int *)(this + 0x1e0) = a2;
    }
    sub_00518B10();
    {
        char *x = sub_0044B080();
        add_51BB20(this, 0xc, x ? x + 4 : 0);
    }
    add_51BB20(this, 0xc, *(void **)(this + 0x84));
    sub_004FDEF0(loader);
    mem = sub_005E3EAE(0x44);
    if (mem)
        sub_004EB130(mem);
    sub_004031F0(LS, d_00518CF0, 0);
    sub_004034F0(LS, -10002, d_00614120);
    add_51BB20(this, 0xc, *(void **)d_006C8C38);
    {
        Str_51BB20 s;
        imp_00607324(&s, d_00614118);
        sub_0047D5C0(*(void **)d_006C8C38, &s, 0x14);
        imp_00607330(&s);
    }
    add_51BB20(this, 0xc, *(void **)d_006C8C3C);
    add_51BB20(this, 0xc, *(void **)(this + 0x210));
    mem = sub_005E3EAE(0x38);
    sub_004205C0(this, mem ? sub_00518D10(mem) : 0);
    sub_004AD530(*(void **)(this + 0x84), 0);
    {
        char *in = *(char **)(this + 0x8c) + 4;
        ((vf0_51BB20)VF(in, 0x18))(in);
    }
    sub_0046CF30(*(void **)(this + 0x8c));
    sub_004E4200(sub_00435C50() + 8);
    {
        char *w = *(char **)(sub_0042F160() + 0x70);
        if (w && *(char **)(w + 0x78))
            sub_0055C610(**(void ***)(*(char **)(w + 0x78) + 0x68), F(0xac), F(0xb0), F(0xb4), RADIUS);
    }
    {
        Str_51BB20 s;
        char *snd;
        imp_00607324(&s, d_00614108);
        snd = (char *)sub_0044E7A0(&s);
        *(char **)(sub_0042F160() + 0x48) = snd;
        imp_00607330(&s);
        snd = *(char **)(sub_0042F160() + 0x48);
        ((vfv_51BB20)VF(snd, 0x18))(snd, sub_004ED000(*(void **)d_006C8C3C), 0);
        snd = *(char **)(sub_0042F160() + 0x48);
        ((vf2_51BB20)VF(snd, 0xc))(snd, 1, 0);
    }
    sub_004220A0(&ct);
    sub_004220A0(&args);
    sub_004FDE90(loader);
    sub_004220A0(&army);
}
