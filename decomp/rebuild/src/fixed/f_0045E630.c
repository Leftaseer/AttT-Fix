/* 0x0045E630: spawns a 0x380-byte scripted world object: operator new (0x005E3EAE) and the 0x004B0E80
 * constructor take the script table, the registry [0x006C8E40], [0x006C8E4C] and this object.  When the world
 * screen is up ([world +0x40] of 0x006C88D8 is not zero) the object is linked into this object's +0x1B4 list
 * (0x0045E230, which also sets its +0x1BC back-pointer) and handed to the world (0x005AD210).  Otherwise the pose
 * comes from 0x004ACE70: the floats at +0x64/+0x68/+0x6C move down to +0x58/+0x5C/+0x60 and the pose floats at
 * +0x30/+0x34/+0x38 take their place, +0x70 and +0x80 are raised, +0x1BC is cleared and +0x78 gains this object's
 * +0x78 plus the parent's ([[this +0x1BC] + 0x78]).  Field 1 of the script table is then turned into a name
 * (0x0045BB70 on a {table, 1} reference) and compared with "saoMagicBarrier": on a match the object joins the
 * list at [this +0x240] (grown through 0x004E0EF0 on this +0x23C), otherwise the list at [this +0x210] (this
 * +0x20C); the 0x005AD6C0 node is prepended and the object's +0x1FC goes to the registry through 0x00425390. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef struct { unsigned int w[7]; } Str_45E630;                  /* std::string */
typedef struct { void *table; unsigned int index; } Ref_45E630;    /* script value reference */

DECOMP_C char d_006C88D8[], d_006C8E40[], d_006C8E4C[], d_0060BAE4[];
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                    /* operator new */
DECOMP_C void *__thiscall sub_004B0E80(void *self, void *tbl, void *reg, void *other, void *owner);
DECOMP_C void __thiscall sub_0045E230(void *self, void *obj);
DECOMP_C void __thiscall sub_005AD210(void *self, void *obj);
DECOMP_C void *__thiscall sub_004ACE70(void *self, void *pose);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, void *out);
DECOMP_C void *__stdcall sub_005AD6C0(void *list, void *first, void **obj);
DECOMP_C void __thiscall sub_004E0EF0(void *self, int count);
DECOMP_C void __thiscall sub_00425390(void *self, void *obj);
DECOMP_C int (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0045E630)
void __thiscall f_0045E630(void *self, void *tbl)
{
    char *this = (char *)self;
    char *mem = (char *)sub_005E3EAE(0x380);
    char *obj = mem ? (char *)sub_004B0E80(mem, tbl, *(void **)d_006C8E40,
                                           *(void **)d_006C8E4C, self) : 0;
    char *world = *(char **)d_006C88D8;

    if (world[0x40]) {
        sub_0045E230(this, obj);
        sub_005AD210(world, obj);
        return;
    }
    {
        float pose[15];
        unsigned int old0, old1, old2;
        Ref_45E630 ref;
        Str_45E630 name;
        char *list, *base, *node;
        void *first;

        sub_004ACE70(obj, pose);
        old0 = *(unsigned int *)(obj + 0x64);
        old1 = *(unsigned int *)(obj + 0x68);
        old2 = *(unsigned int *)(obj + 0x6c);
        *(float *)(obj + 0x64) = pose[0x30 / 4];
        *(unsigned int *)(obj + 0x58) = old0;
        *(float *)(obj + 0x68) = pose[0x34 / 4];
        *(unsigned int *)(obj + 0x5c) = old1;
        *(float *)(obj + 0x6c) = pose[0x38 / 4];
        *(unsigned int *)(obj + 0x60) = old2;
        obj[0x70] = 1;
        *(float *)(obj + 0x78) = *(float *)(*(char **)(this + 0x1bc) + 0x78) + *(float *)(this + 0x78) +
            *(float *)(obj + 0x78);
        obj[0x80] = 1;
        *(void **)(obj + 0x1bc) = 0;
        ref.table = tbl;
        ref.index = 1;
        sub_0045BB70(&ref, 1, &name);
        if (imp_006071E4(&name, d_0060BAE4)) {
            base = this + 0x23c;
            list = *(char **)(this + 0x240);
        } else {
            base = this + 0x20c;
            list = *(char **)(this + 0x210);
        }
        first = *(void **)(list + 4);
        node = (char *)sub_005AD6C0(list, first, (void **)&obj);
        sub_004E0EF0(base, 1);
        *(void **)(list + 4) = node;
        *(void **)first = node;
        sub_00425390(*(void **)d_006C8E40, obj + 0x1fc);
        imp_00607330(&name);
    }
}
