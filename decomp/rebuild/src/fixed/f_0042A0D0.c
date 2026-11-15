/* Mesh object factory 0x0042A0D0: the suffix of the file name picks the class.  ".lgdl" builds a CLGDLObject
 * (0x25C) from the stem, ".ska" a skin mesh (0x248) and any other name a base mesh (0x1DC); the two mesh
 * constructors get a lowercased copy of the whole name. */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_42A0D0;                        /* std::string */

DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00471FB0(void *self, void *name, unsigned int kind);
DECOMP_C void *__thiscall sub_004C0FE0(void *self, void *name, void *arg);
DECOMP_C void *__thiscall sub_004308F0(void *self, void *name, void *arg, unsigned int kind);
DECOMP_C char d_0060840C[], d_00608414[];                                /* ".ska", ".lgdl" */
DECOMP_C void *(__thiscall *imp_006071CC)(void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char *(__stdcall *imp_006076CC)(const char *) __asm__("__imp__CharLowerA@4");

DECOMP(0042A0D0)
void *__cdecl f_0042A0D0(Str_42A0D0 *name, void *arg, unsigned int kind)
{
    unsigned int len = name->w[5];
    Str_42A0D0 suffix;
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
            Str_42A0D0 lower;
            void *result;
            if (!object)
                return 0;
            imp_00607324(&lower, imp_006076CC(imp_0060732C(name)));
            result = sub_004C0FE0(object, &lower, arg);
            imp_00607330(&lower);
            return result;
        }
    }
    {
        void *object = sub_005E3EAE(0x1dc);
        Str_42A0D0 lower;
        void *result;
        if (!object)
            return 0;
        imp_00607324(&lower, imp_006076CC(imp_0060732C(name)));
        result = sub_004308F0(object, &lower, arg, kind);
        imp_00607330(&lower);
        return result;
    }
}
