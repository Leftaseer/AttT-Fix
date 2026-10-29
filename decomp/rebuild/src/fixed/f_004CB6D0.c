/* 0x004CB6D0: adds an animation variant from a script table (arg 1) with a texture set name (args 2-8, a std::string
 * by value, destroyed here) and a name (arg 9): the variants (+0x10: 8-byte {animation, cumulative weight}) continue
 * from the last weight; a table of 4, 5 or 6 entries (0x0057C420) gives its weight (entry n, truncated) and the
 * animation's description (0x004A00E0 / 0x004A02C0 / 0x004A01A0) for a new 0x204 / 0x208 / 0x21C-byte animation
 * (0x0042A530 / 0x0042B290 / 0x0042AF50 with the textures 0x0042A0D0), held by reference; it is named (0x004CAC30,
 * by value) and appended (0x004CB660); then a random variant by weight becomes current (+0x0C). Callees taking EBX
 * get the running weight as the original leaves it there */
/* @conv ECX 36 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4CB6D0;                  /* std::string */
DECOMP_C int __cdecl sub_0057C420(void *self, unsigned int ebx);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void __cdecl sub_004A00E0(void *self, unsigned int ebx, void *tbl);
DECOMP_C void __cdecl sub_004A02C0(void *self, unsigned int ebx, void *tbl);
DECOMP_C void __cdecl sub_004A01A0(void *self, unsigned int ebx, void *tbl);
DECOMP_C void *__cdecl sub_0042A0D0(void *desc, void *textures, int a);
DECOMP_C int *__thiscall sub_0042A530(void *self, void *desc, void *tex, int a);
DECOMP_C int *__thiscall sub_0042B290(void *self, void *desc, void *tex, int a);
DECOMP_C int *__thiscall sub_0042AF50(void *self, void *desc, void *tex, int a);
DECOMP_C void __thiscall sub_004B6400(void *self, void *obj);
DECOMP_C void __thiscall sub_004CAC30(void *self, Str_4CB6D0 name);
DECOMP_C void __thiscall sub_004CB660(void *self, void *entry);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef void (__thiscall *del_4CB6D0)(void *self, int flags);

DECOMP(004CB6D0)
void __thiscall f_004CB6D0(void *this, void *tbl, unsigned int t0, unsigned int t1, unsigned int t2, unsigned int t3,
                           unsigned int t4, unsigned int t5, unsigned int t6, void *name)
{
    char *s = (char *)this, *e;
    Str_4CB6D0 *tex = (Str_4CB6D0 *)((unsigned char *)__builtin_frame_address(0) + 0xc);   /* args 2-8 in place */
    unsigned int base = 0, desc[0x2c / 4];   /* the description: its name string and 4 more fields */
    int *obj = 0, kind, pick;
    struct { int *anim; unsigned int w; } entry;
    if (*(char **)(s + 0x14) && (*(char **)(s + 0x18) - *(char **)(s + 0x14)) >> 3)
        base = *(unsigned int *)(*(char **)(s + 0x18) - 4);
    kind = sub_0057C420(tbl, base);
    if (kind == 4 || kind == 5 || kind == 6) {
        void *m;
        base += (int)(long long)sub_0057AC90(tbl, kind);
        imp_006071E0(desc);
        if (kind == 4) {
            sub_004A00E0(desc, base, tbl);
            m = sub_005E3EAE(0x204);
            obj = m ? sub_0042A530(m, desc, sub_0042A0D0(desc, tex, 0xb), 1) : 0;
            if (obj)
                obj[1]++;
        } else if (kind == 5) {
            sub_004A02C0(desc, base, tbl);
            m = sub_005E3EAE(0x208);
            obj = m ? sub_0042B290(m, desc, sub_0042A0D0(desc, tex, 0xb), 1) : 0;
            if (obj)
                obj[1]++;
        } else {
            sub_004A01A0(desc, base, tbl);
            m = sub_005E3EAE(0x21c);
            sub_004B6400(&obj, m ? sub_0042AF50(m, desc, sub_0042A0D0(desc, tex, 0xb), 1) : 0);
        }
        imp_00607330(desc);
    }
    {
        Str_4CB6D0 n;
        imp_00607334(&n, name);
        sub_004CAC30(obj, n);
    }
    entry.anim = obj;
    entry.w = base;
    sub_004CB660(s + 0x10, &entry);
    pick = imp_00607400() % *(int *)(*(char **)(s + 0x18) - 4) + 1;
    for (e = *(char **)(s + 0x14); e != *(char **)(s + 0x18); e += 8)
        if (pick <= *(int *)(e + 4)) {
            *(void **)(s + 0xc) = *(void **)e;
            break;
        }
    if (obj && !--obj[1])
        ((del_4CB6D0)(*(void ***)obj)[0])(obj, 1);
    imp_00607330(tex);
}
