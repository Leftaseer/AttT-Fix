/* 0x004C3C00: searches the AIL filter list for the filter whose name equals the given std::string.
 * The object gets a circular list head at +8 (built for +4 by 0x004C2F40, the helper ignores its this
 * pointer), a zero count at +0xC and a zero result at +0; then the enumeration loop asks
 * _AIL_enumerate_filters (import 0x00607824, three out pointers: handle, filter, name) for entries and
 * compares each name with the string through std::operator==(string, const char*) (import 0x006071E4)
 * until one matches (its filter goes to +0) or the enumeration ends.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_004C2F40(void *self);               /* circular list head */
DECOMP_C unsigned int (__stdcall *imp_00607824)(unsigned int *next, unsigned int *filter, char **name)
    __asm__("__imp___AIL_enumerate_filters@12");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *)
    __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");

DECOMP(004C3C00)
void *__thiscall f_004C3C00(char *this, const void *name)
{
    unsigned int next = 0;
    unsigned int filter;
    char *found;
    void *head;

    head = sub_004C2F40(this + 4);
    *(void **)(this + 8) = head;
    *(unsigned int *)(this + 0x0c) = 0;
    *(unsigned int *)(this + 0) = 0;
    for (;;) {
        if (!imp_00607824(&next, &filter, &found))
            break;
        if (imp_006071E4(name, found)) {
            *(unsigned int *)(this + 0) = filter;
            break;
        }
    }
    return this;
}
