/* 0x00427190: builds a sound sample object for a configuration entry: a new 0x44-byte Sound2D (0x004C3AE0) is
 * created from the entry's "FileName" string (the map lookup 0x00561520 gives an existing or fresh string), and the
 * entry's "MaxRandomEmitRange" and "RandomEmitKeyValue" values become its +4 and +8 dwords. The three strings are
 * built from the literals and destroyed again. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef struct { unsigned int raw[7]; } Str_427190;                        /* std::string */

DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                   /* operator new */
DECOMP_C void *__thiscall sub_00561520(void *self, void *out, void *name);
DECOMP_C float __thiscall sub_005613A0(void *self, void *name);
DECOMP_C void *__thiscall sub_004C3AE0(void *self, void *name);
DECOMP_C char d_00608240[], d_0060822C[], d_00608218[];                   /* "FileName", "MaxRandomEmitRange", "RandomEmitKeyValue" */

DECOMP(00427190)
void __thiscall f_00427190(void *this, void *entry)
{
    char *s = (char *)this;
    Str_427190 name, result, key;
    void *sample = sub_005E3EAE(0x44);
    void *found;

    if (sample) {
        imp_00607324(&name, d_00608240);
        found = sub_00561520(entry, &result, &name);
        *(void **)s = sub_004C3AE0(sample, found);
        imp_00607330(&result);
        imp_00607330(&name);
    } else {
        *(void **)s = 0;
    }
    imp_00607324(&key, d_0060822C);
    *(int *)(s + 4) = (int)sub_005613A0(entry, &key);
    imp_00607330(&key);
    imp_00607324(&key, d_00608218);
    *(int *)(s + 8) = (int)sub_005613A0(entry, &key);
    imp_00607330(&key);
}
