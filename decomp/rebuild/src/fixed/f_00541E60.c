/* 0x00541E60: CWorldLevel vf3, the world level becoming the current scene again, by how it was left (+0x118):
 * 1 back from a battle (the hero's ground height and the saved camera restored when the hero lives (+0x120
 * +0x118), else unless WorldLevel.SaveLoad the game menu (+0x110, 0x00582FA0) is shown with isDeadHero and the
 * state becomes 9); 2, 3, 11, 6 back from a dialogue; 4, 5 back from a screen (the script's world 0x006CA990, 5
 * also restoring the camera +0x23C); 8, 9 back from the game menu (0x006CAAD0 too; 9 resets the input +0x88);
 * 10 back from the battle request (GUIScene.RequestBeforeBattle.select: a new tactic army name reloads the game
 * and the state becomes 1 with the camera kept, else the camera is placed radius + 5 (then + 0.5 when nearer than
 * 4.5) away from the attacking army TacticLevel.armyWhoAttack.armyPos towards the camera); every case uses the
 * Default effect (+0x348) and resumes the music (+0xE0); then the level is the current world (0x008D1230,
 * 0x006CAAE8) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_541E60;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_541E60;                 /* nScript::Table */
typedef struct { Tbl_541E60 t; const char *k; } RefC_541E60;
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_004B63E0(void *self);
DECOMP_C int __thiscall sub_0046CF30(void *self);
DECOMP_C char *__cdecl sub_00432260(void);
DECOMP_C void __thiscall sub_0053A510(void *self, float *out);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C unsigned int __thiscall sub_0043BAD0(void *self, void *pos);
DECOMP_C void __thiscall sub_0051A260(void *self);
DECOMP_C void __thiscall sub_004354C0(void *self, const void *m);
DECOMP_C void __thiscall sub_004EB4F0(void *self);
DECOMP_C void __thiscall sub_00437AC0(void *self, void *name, float a, int b);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004EB130(void *self);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C unsigned char __thiscall sub_0046A920(void *self, const char *key);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_00582FA0(void *self, int a);
DECOMP_C void *__thiscall sub_00435E00(void *self, int a);
DECOMP_C void __thiscall sub_0057BB20(void *t, const char *key, int v);
DECOMP_C void __thiscall sub_00518000(void *self);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const void *key);
DECOMP_C unsigned char __thiscall sub_0057AA20(void *self, const char *key);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_004638C0(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_0053FEF0(void *self, int a);
DECOMP_C void __thiscall sub_004B5BA0(void *self, void *name);
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C RefC_541E60 *__thiscall sub_0044D030(void *self, RefC_541E60 *out, const void *key);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C float *__stdcall sub_005B8074(float *out, const float *v);  /* D3DXVec3Normalize */
DECOMP_C char *__cdecl sub_00435C50(void);
DECOMP_C void __thiscall sub_004E4200(void *self);
DECOMP_C char d_0060FA8B[], d_00607C00[], d_006CA5A4[], d_0060C07C[], d_0060AB6C[], d_00613FC4[], d_0061AFD0[],
    d_0061405C[], d_006CA990[], d_006CAAD0[], d_0060AD08[], d_0061AE64[], d_0068A2D8[], d_0060AB58[], d_0060AB48[],
    d_0061AFC8[], d_0061AFC0[], d_006C88BC[], d_00613B8C[], d_006141B0[], d_006098C8[], d_006098D0[], d_0060B7A0[],
    d_0068AE18[], d_0061AFBC[], d_0061AFB8[], d_00607CE0[], d_008D1230[], d_006CAAE8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_00607368)(const void *, const void *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@0@Z");
typedef void (__thiscall *vf0_541E60)(void *self);
typedef void (__thiscall *vfd_541E60)(void *self, int a);
typedef void (__thiscall *vff_541E60)(void *self, float v);
typedef float *(__thiscall *vfv_541E60)(void *self);
typedef void (__thiscall *show_541E60)(void *self, void *name, void *args, int a);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define D(a) (*(double *)(a))

static void default_541E60(char *this)
{
    imp_006072F8(this + 0x348, d_00607C00);
}

static void music_541E60(char *this)
{
    void *m = *(void **)(this + 0xe0);
    ((vf0_541E60)VF(m, 0x18))(m);
}

static void menu_541E60(char *this)
{
    void *m = *(void **)(this + 0x110);
    if (m)
        ((vfd_541E60)VF(m, 0))(m, 1);
}

/* the camera's (+0x160) vf18 on its part +4 */
static void camera_541E60(char *this)
{
    char *c = *(char **)(this + 0x160) + 4;
    ((vf0_541E60)VF(c, 0x18))(c);
}

static void restore_541E60(char *this)
{
    sub_004B63E0(*(void **)(this + 0xcc));
    sub_004354C0(*(void **)(this + 0x160), this + 0x23c);
    camera_541E60(this);
    sub_004EB4F0(*(void **)(this + 0xe4));
    *(char **)(*(char **)d_006CA5A4 + 0x2c) = this + 4;
}

/* armyPos[key] of the attacking army (+0xBC) */
static RefC_541E60 *pos_541E60(char *this, RefC_541E60 *out, const char *key)
{
    struct { void *t; const char *k; } ref;
    ref.t = this + 0xbc;
    ref.k = d_006141B0;
    return sub_0044D030(&ref, out, key);
}

/* the camera placed d away from (x, z) along the ground direction to it */
static void place_541E60(char *this, float x, float z, float d)
{
    void *cam = *(void **)(this + 0x90);
    float *p = ((vfv_541E60)VF(cam, 0x68))(cam);
    float v[3], pos[3], t[3];
    int i;
    v[0] = p[0] - x;
    v[1] = 0.0f;
    v[2] = p[2] - z;
    sub_005B8074(v, v);
    for (i = 0; i < 3; i++)
        t[i] = v[i] * d;
    pos[0] = t[0] + x;
    pos[1] = (float)(t[1] + D(d_0068AE18));
    pos[2] = t[2] + z;
    sub_0043BAD0(*(void **)(this + 0x90), pos);
}

static void request_541E60(char *this)
{
    unsigned char sel;
    {
        Tbl_541E60 gs, r;
        sel = sub_0057AA20(sub_0057B4E0(sub_004323E0(&gs, d_0060AD08), &r, d_0061AE64), d_0068A2D8) == 1;
        sub_004220A0(&r);
        sub_004220A0(&gs);
    }
    {
        struct { void *t; const char *k; } ref;
        Tbl_541E60 ta, o;
        ref.t = sub_004323E0(&ta, d_0060AB58);
        ref.k = d_0060AB48;
        sub_004369F0(&ref, &o);
        sub_0057A860(this + 0xbc, &o);
        sub_004220A0(&o);
        sub_004220A0(&ta);
    }
    if (sel) {
        struct { void *t; const char *k; } ref;
        Str_541E60 n, name;
        unsigned int cam[0x44 / 4];
        ref.t = this + 0xbc;
        ref.k = d_0061AFC8;
        sub_004638C0(&ref, 0xffffffffu, &n);
        imp_00607334(&name, &n);
        imp_00607330(&n);
        if (imp_00607368(this + 0x3b0, &name)) {
            Str_541E60 s;
            sub_0053FEF0(this, 2);
            imp_00607324(&s, d_0061AFC0);
            sub_004B5BA0(*(void **)d_006C88BC, &s);
            imp_00607330(&s);
        }
        *(int *)(this + 0x118) = 1;
        __builtin_memcpy(this + 0x23c, sub_00435550(*(void **)(this + 0x160), cam), 0x44);
        sub_00518000(*(void **)(this + 0x38));
        imp_00607330(&name);
    } else {
        RefC_541E60 rr, rz, rx, *pz, *px;
        float radius, z, x;
        void *cam;
        {
            struct { void *t; const char *k; } ref;
            RefC_541E60 *p;
            ref.t = this + 0xbc;
            ref.k = d_006141B0;
            p = sub_0044D030(&ref, &rr, d_00613B8C);
            radius = sub_0057AD40(p, p->k);
            sub_004220A0(&rr);
        }
        pz = pos_541E60(this, &rz, d_006098C8);
        px = pos_541E60(this, &rx, d_006098D0);
        z = sub_0057AD40(pz, pz->k);
        x = sub_0057AD40(px, px->k);
        sub_004220A0(&rx);
        sub_004220A0(&rz);
        place_541E60(this, x, z, (float)(radius + D(d_0060B7A0)));
        cam = *(void **)(this + 0x90);
        ((vff_541E60)VF(cam, 4))(cam, *(float *)d_0061AFBC);
        cam = *(void **)(this + 0x90);
        ((vf0_541E60)VF(cam, 0x14))(cam);
        cam = *(void **)(this + 0x90);
        if (*(float *)d_0061AFB8 > *(float *)((char *)cam + 0x68)) {
            char *c;
            float h, a, b;
            place_541E60(this, x, z, (float)(radius + D(d_00607CE0)));
            c = *(char **)(this + 0x90);
            b = *(float *)(c + 0x6c);
            a = *(float *)(c + 0x64);
            h = sub_00473110(*(void **)(this + 0x94), a, b);
            c = *(char **)(this + 0x90);
            c[0x70] = 1;
            *(float *)(c + 0x5c) = *(float *)(c + 0x68);
            *(float *)(c + 0x68) = h;
        }
    }
    imp_006072F8(this + 0x3b0, d_0060FA8B);
}

/* back from a battle */
static void battle_541E60(char *this)
{
    char *cam;
    this[0x3ad] = 0;
    imp_006072F8(this + 0x3b0, d_0060FA8B);
    cam = *(char **)(this + 0x160);
    cam[0x228] = 1;
    (*(char **)(this + 0x160))[0x218] = 1;
    if ((*(char **)(this + 0x120))[0x118]) {
        float v[3];
        sub_0053A510(sub_00432260(), v);
        sub_00473110(*(void **)(this + 0x94), v[0], v[2]);
        sub_0043BAD0(*(void **)(this + 0x90), this + 0x398);
        cam = *(char **)(this + 0x90);
        *(float *)(cam + 0x78) = *(float *)(this + 0x3a4);
        cam[0x80] = 1;
        sub_0051A260(*(void **)(this + 0x120));
        default_541E60(this);
        restore_541E60(this);
        {
            Str_541E60 s;
            void *mem;
            imp_00607324(&s, d_0060C07C);
            sub_00437AC0(*(void **)(this + 0x10c), &s, 0.0f, 0);
            imp_00607330(&s);
            mem = sub_005E3EAE(0x44);
            if (mem)
                sub_004EB130(mem);
        }
        return;
    }
    sub_0051A260(*(void **)(this + 0x120));
    default_541E60(this);
    restore_541E60(this);
    {
        Tbl_541E60 wl;
        unsigned char none = sub_0046A920(sub_004323E0(&wl, d_0060AB6C), d_00613FC4) == 0;
        sub_004220A0(&wl);
        if (none) {
            void *mem = sub_005E3EAE(0x194), *m;
            Tbl_541E60 args;
            Str_541E60 s;
            *(void **)(this + 0x110) = mem ? sub_00582FA0(mem, 1) : 0;
            sub_00435E00(&args, 0);
            sub_0057BB20(&args, d_0061AFD0, 1);
            imp_00607324(&s, d_0061405C);
            m = *(void **)(this + 0x110);
            ((show_541E60)VF(m, 0x3c))(m, &s, &args, 1);
            imp_00607330(&s);
            *(int *)(this + 0x118) = 9;
            sub_00518000(*(void **)(this + 0x38));
            sub_004220A0(&args);
        }
    }
}

DECOMP(00541E60)
void __thiscall f_00541E60(void *self)
{
    char *this = (char *)self;
    sub_004AD530(*(void **)(this + 0x80), 0);
    sub_004B63E0(*(void **)(this + 0xcc));
    sub_0046CF30(*(void **)(this + 0x88));
    switch (*(unsigned int *)(this + 0x118)) {
    case 1:
        battle_541E60(this);
        break;
    case 2: case 3: case 11:
        default_541E60(this);
        music_541E60(this);
        menu_541E60(this);
        camera_541E60(this);
        break;
    case 4:
        default_541E60(this);
        music_541E60(this);
        *(char **)d_006CA990 = this + 4;
        menu_541E60(this);
        break;
    case 5:
        default_541E60(this);
        music_541E60(this);
        *(char **)d_006CA990 = this + 4;
        menu_541E60(this);
        sub_004354C0(*(void **)(this + 0x160), this + 0x23c);
        camera_541E60(this);
        break;
    case 6:
        default_541E60(this);
        music_541E60(this);
        menu_541E60(this);
        camera_541E60(this);
        break;
    case 8: case 9:
        default_541E60(this);
        music_541E60(this);
        *(char **)d_006CA990 = this + 4;
        *(char **)d_006CAAD0 = this + 4;
        menu_541E60(this);
        if (*(unsigned int *)(this + 0x118) == 9)
            sub_0046CF30(*(void **)(this + 0x88));
        break;
    case 10:
        default_541E60(this);
        music_541E60(this);
        menu_541E60(this);
        camera_541E60(this);
        request_541E60(this);
        break;
    }
    *(char **)d_008D1230 = this;
    *(char **)d_006CAAE8 = this;
    sub_004AD530(*(void **)(this + 0x80), 0);
    sub_004E4200(sub_00435C50() + 8);
}
