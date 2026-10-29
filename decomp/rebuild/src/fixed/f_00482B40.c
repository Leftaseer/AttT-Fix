/* 0x00482B40: CNotesBook constructor (base 0x0047A120 "Notesbook", the owner a at +0x294, b at +0x29C): the
 * Notes.bik backdrop (+0x23C, 0x004DF920) registered as "tNotesbook" and sizing the book (0x00479D80), the ten
 * page pictures Notcl*.tga (+0x240..), their selection masks maskSelectNotes*.bmp (+0x268.., 0x004740C0) and the
 * NotesPage (+0x290, showing the first picture at 0, 0, added to the owner's list); then page 0 (0x004827B0).
 * Returns this */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_482B40;                 /* std::string */
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int a);
DECOMP_C void __cdecl sub_00479D80(void *self, unsigned int eax, float w, float h);
DECOMP_C void *__thiscall sub_004740C0(void *self, void *name);
DECOMP_C void __thiscall sub_004827B0(void *self, int page);
DECOMP_C char d_0060F574[], d_0060F48C[], d_0060F478[], d_0060F46C[], d_0060F45C[], d_0060F44C[], d_0060F43C[],
    d_0060F42C[], d_0060F41C[], d_0060F40C[], d_0060F3FC[], d_0060F3EC[], d_0060F3DC[], d_0060F3CC[], d_0060F3B4[],
    d_0060F39C[], d_0060F384[], d_0060F36C[], d_0060F354[], d_0060F33C[], d_0060F324[], d_0060F30C[], d_0060F2F4[],
    d_0060F2DC[], d_0060F2D0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef unsigned int (__thiscall *vfi_482B40)(void *self);
typedef void (__thiscall *vfp_482B40)(void *self, void *p);
typedef void (__thiscall *reg_482B40)(void *self, void *name, void *o);
typedef void (__thiscall *pos_482B40)(void *self, float x, float y);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])

/* a picture of the file name */
static void *pic_482B40(const char *name)
{
    void *mem = sub_005E3EAE(0x54), *o = 0;
    if (mem) {
        Str_482B40 s;
        imp_00607324(&s, name);
        o = sub_004DF920(mem, &s, 0);
        imp_00607330(&s);
    }
    return o;
}

/* a selection mask of the file name */
static void *mask_482B40(const char *name)
{
    void *mem = sub_005E3EAE(0x1c), *o = 0;
    if (mem) {
        Str_482B40 s;
        imp_00607324(&s, name);
        o = sub_004740C0(mem, &s);
        imp_00607330(&s);
    }
    return o;
}

/* the size of the current frame of picture p through vf */
static unsigned int size_482B40(char *p, int vf)
{
    void *e = (*(void ***)(p + 0x38))[*(int *)(p + 0x40)];
    return ((vfi_482B40)VF(e, vf))(e);
}

DECOMP(00482B40)
void *__thiscall f_00482B40(void *self, void *owner, int b)
{
    static const char *const pics[10] = {
        d_0060F45C, d_0060F44C, d_0060F43C, d_0060F42C, d_0060F41C,
        d_0060F40C, d_0060F3FC, d_0060F3EC, d_0060F3DC, d_0060F3CC,
    };
    static const char *const masks[10] = {
        d_0060F3B4, d_0060F39C, d_0060F384, d_0060F36C, d_0060F354,
        d_0060F33C, d_0060F324, d_0060F30C, d_0060F2F4, d_0060F2DC,
    };
    char *this = (char *)self;
    void *mem;
    int i;

    {
        Str_482B40 s;
        imp_00607324(&s, d_0060F574);
        sub_0047A120(this, &s);
        imp_00607330(&s);
    }
    *(void **)this = d_0060F48C;
    *(int *)(this + 0x22c) = 0;
    *(int *)(this + 0x230) = 0;
    *(int *)(this + 0x234) = 0;
    {
        Str_482B40 s;
        imp_00607324(&s, d_0060F574);
        sub_004AB810(this, &s, 1);
        imp_00607330(&s);
    }
    *(void **)(this + 0x294) = owner;
    *(int *)(this + 0x29c) = b;
    *(void **)(this + 0x23c) = pic_482B40(d_0060F478);
    {
        Str_482B40 s;
        void *list = *(void **)(this + 0x3c);
        imp_00607324(&s, d_0060F46C);
        ((reg_482B40)VF(list, 0xc))(list, &s, *(void **)(this + 0x23c));
        imp_00607330(&s);
    }
    {
        unsigned int h = size_482B40(*(char **)(this + 0x23c), 0x14);
        unsigned int w = size_482B40(*(char **)(this + 0x23c), 0x10);
        sub_00479D80(this, w, (float)w, (float)h);
    }
    *(int *)(this + 0x224) = 0;
    *(int *)(this + 0x290) = 0;
    *(unsigned short *)(this + 0x29a) = 0;
    for (i = 0; i < 10; i++)
        *(void **)(this + 0x240 + i * 4) = pic_482B40(pics[i]);
    for (i = 0; i < 10; i++)
        *(void **)(this + 0x268 + i * 4) = mask_482B40(masks[i]);
    mem = sub_005E3EAE(0x224);
    if (mem) {
        Str_482B40 s;
        imp_00607324(&s, d_0060F2D0);
        *(void **)(this + 0x290) = sub_0047A120(mem, &s);
        imp_00607330(&s);
    } else
        *(void **)(this + 0x290) = 0;
    {
        void *page = *(void **)(this + 0x290);
        char *own;
        ((vfp_482B40)VF(page, 0x34))(page, *(void **)(this + 0x240));
        page = *(void **)(this + 0x290);
        ((pos_482B40)VF(page, 0x94))(page, 0.0f, 0.0f);
        own = *(char **)(this + 0x294) + 4;
        ((vfp_482B40)VF(own, 4))(own, *(void **)(this + 0x290));
    }
    this[0x298] = 0;
    this[0x2a0] = 0;
    sub_004827B0(this, 0);
    return this;
}
