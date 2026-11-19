/* 0x005A2410: sets the visibility of a dialog element group.  The dialog's group table runs from [this+0x294] to
 * [this+0x298] in 12-byte records whose element list head sits at +4 (nodes are {next, prev, element}); the shared
 * list of record 12 is walked first with 0 so everything is hidden (hiding group 1 instead shows that list with 1
 * and stops the walk at group 12), then the group's record has each element's virtual +0x40 called with the value
 * and the index moves down one group for a non-zero value or up one for a zero until it leaves 0..limit.  A null
 * table counts as no groups; an index at or past the count throws the std::string
 * "Не найдена группа элементов в диалоге" (the element group is not in the dialog) through 0x005E3EC0. */
/* @conv ECX 8 */
#include "auto_pre.h"

typedef struct { unsigned int w[7]; } Str_5A2410;                  /* std::string */
typedef void (__thiscall *visitor_5A2410)(void *elem, int visible);

DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);  /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C char d_0062058C[], d_0069916C[];

DECOMP(005A2410)
void __thiscall f_005A2410(void *self, int group, int visible)
{
    char *c = (char *)self;
    char *table = *(char **)(c + 0x294);
    char *end = *(char **)(c + 0x298);
    int limit = table ? (int)((end - table) / 12) : 0;
    char *head, *node, *elem;
    int total;

    if (group == 1 && (unsigned char)visible == 0) {
        head = *(char **)(table + 0x94);
        for (node = *(char **)head; node != head; node = *(char **)node) {
            elem = *(char **)(node + 8);
            (*(visitor_5A2410)(*(void ***)elem)[0x10])(elem, 1);
            head = *(char **)(*(char **)(c + 0x294) + 0x94);
        }
        limit = 12;
    } else {
        head = *(char **)(table + 0x94);
        for (node = *(char **)head; node != head; node = *(char **)node) {
            elem = *(char **)(node + 8);
            (*(visitor_5A2410)(*(void ***)elem)[0x10])(elem, 0);
            head = *(char **)(*(char **)(c + 0x294) + 0x94);
        }
    }
    table = *(char **)(c + 0x294);
    end = *(char **)(c + 0x298);
    total = table ? (int)((end - table) / 12) : 0;
    if (group >= total) {
        Str_5A2410 msg, thrown;
        imp_00607324(&msg, d_0062058C);
        imp_00607334(&thrown, &msg);
        sub_005E3EC0(&thrown, d_0069916C);
    }
    while (group >= 0 && group < limit) {
        head = *(char **)(*(char **)(c + 0x294) + 12 * group + 4);
        for (node = *(char **)head; node != head; node = *(char **)node) {
            elem = *(char **)(node + 8);
            (*(visitor_5A2410)(*(void ***)elem)[0x10])(elem, visible);
            head = *(char **)(*(char **)(c + 0x294) + 12 * group + 4);
        }
        if ((unsigned char)visible)
            group--;
        else
            group++;
    }
}
