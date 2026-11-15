/* Mesh object factory 0x0042A330: like 0x0042A0D0, but the mesh constructors get the name as it is and the class
 * constructors are the 0x4C1100 / 0x430A10 variants. */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_42A330;                        /* std::string */

DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00471FB0(void *self, void *name, unsigned int kind);
DECOMP_C void *__thiscall sub_004C1100(void *self, void *name, void *arg);
DECOMP_C void *__thiscall sub_00430A10(void *self, void *name, void *arg, unsigned int kind);
DECOMP_C char d_0060840C[], d_00608414[];                                /* ".ska", ".lgdl" */
DECOMP_C void *(__thiscall *imp_006071CC)(void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0042A330)
void *__cdecl f_0042A330(Str_42A330 *name, void *arg, unsigned int kind)
{
    unsigned int len = name->w[5];
    Str_42A330 suffix;
    if (len > 5) {
        int matched;
        imp_006071CC(name, &suffix, len - 5, len);
        matched = imp_006071E4(&suffix, d_00608414);
        imp_00607330(&suffix);
        if (matched) {
            void *object = sub_005E3EAE(0x25c);
            void *result;
            if (!object)
                return 0;
            imp_006071CC(name, &suffix, 0, len - 5);
            result = sub_00471FB0(object, &suffix, kind);
            imp_00607330(&suffix);
            return result;
        }
    }
    if (len > 4) {
        int matched;
        imp_006071CC(name, &suffix, len - 4, len);
        matched = imp_006071E4(&suffix, d_0060840C);
        imp_00607330(&suffix);
        if (matched) {
            void *object = sub_005E3EAE(0x248);
            if (!object)
                return 0;
            return sub_004C1100(object, name, arg);
        }
    }
    {
        void *object = sub_005E3EAE(0x1dc);
        if (!object)
            return 0;
        return sub_00430A10(object, name, arg, kind);
    }
}
