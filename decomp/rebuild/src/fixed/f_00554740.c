/* 0x00554740: builds the forest's tree types per terrain patch: clears the type map (+0xB0, 0x005224A0), sets the 9
 * cells (+0xBC) to the map's end, +0xCC / +0xD0 = 1, sizes the per-patch index lists (+0xD4: one empty vector per
 * patch of the terrain 0x00518B10's +0xD8, 0x004909E0 taking it by value); then for each patch (the terrain's list
 * +0xD4, numbered into +0x84 by its name, 0x005542E0) each tree (its +0x24 vector, 0x30 bytes each, 0x00493640) is
 * looked up by name in +0xAC (0x00422D80): a new one gets a new 0x268-byte "FullTree" model (0x004560B0 with its
 * size +0x2C) pushed onto +0x74 and its number recorded; the number is pushed onto the patch's list (+0xD8, 16 bytes
 * per patch). Vector push_back is inline (0x00487860 when full) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[4]; } Vec_554740;
DECOMP_C char *__cdecl sub_00518B10(void);
DECOMP_C void __thiscall sub_005224A0(void *self);
DECOMP_C void __thiscall sub_004EF350(void *self, unsigned int n, void *val);
DECOMP_C void __thiscall sub_004909E0(void *self, unsigned int n, Vec_554740 val);
DECOMP_C int *__thiscall sub_005542E0(void *self, void *key);
DECOMP_C unsigned int __thiscall sub_00493640(void *self);
DECOMP_C void __thiscall sub_00422D80(void *map, char **out, void *key);
DECOMP_C void *__thiscall sub_004560B0(void *self, void *tree, void *name, float size);
DECOMP_C void __thiscall sub_00487860(void *self, void *where, unsigned int n, void *val);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_0061BC94[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

/* std::vector<T *>::push_back as inlined: +0x04 first, +0x08 last, +0x0C end */
static void push_554740(char *v, void *val)
{
    void **b = *(void ***)(v + 4);
    unsigned int n = b ? (unsigned int)((char *)*(void ***)(v + 8) - (char *)b) >> 2 : 0;
    if (b && n < (unsigned int)((char *)*(void ***)(v + 0xc) - (char *)b) >> 2) {
        **(void ***)(v + 8) = *(void **)val;
        *(void ***)(v + 8) += 1;
    } else
        sub_00487860(v, *(void **)(v + 8), 1, val);
}

DECOMP(00554740)
void __thiscall f_00554740(void *this)
{
    char *s = (char *)this, *g, *node, *res, *item;
    unsigned int i, j, idx;
    void *fill, *obj;
    Vec_554740 empty = { { 0, 0, 0, 0 } };
    g = sub_00518B10();
    node = **(char ***)(g + 0xd4);
    sub_005224A0(s + 0xb0);
    fill = *(void **)(s + 0xb4);
    sub_004EF350(s + 0xbc, 9, &fill);
    *(int *)(s + 0xcc) = 1;
    *(int *)(s + 0xd0) = 1;
    sub_004909E0(s + 0xd4, *(unsigned int *)(g + 0xd8), empty);
    for (i = 0; node != *(char **)(g + 0xd4); node = *(char **)node, i++) {
        *sub_005542E0(s + 0x84, node + 8) = i;
        for (j = 0; j < sub_00493640(node + 0x24); j++) {
            item = *(char **)(node + 0x28) + j * 0x30;
            sub_00422D80(s + 0xac, &res, item);
            if (res == *(char **)(s + 0xb4)) {
                obj = sub_005E3EAE(0x268);
                if (obj) {
                    unsigned int name[7];
                    imp_00607324(name, d_0061BC94);
                    obj = sub_004560B0(obj, item, name, *(float *)(item + 0x2c));
                    imp_00607330(name);
                }
                {
                    void **b = *(void ***)(s + 0x78);
                    idx = b ? (unsigned int)((char *)*(void ***)(s + 0x7c) - (char *)b) >> 2 : 0;
                }
                push_554740(s + 0x74, &obj);
                *sub_005542E0(s + 0xac, item) = idx;
            } else
                idx = *(unsigned int *)(res + 0x24);
            push_554740(*(char **)(s + 0xd8) + i * 16, &idx);
        }
    }
}
