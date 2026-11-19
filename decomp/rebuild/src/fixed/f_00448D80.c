/* 0x00448D80: the resource manager's delete by name (this is the manager, arg 1 the name string): the hash map at
 * +4 is asked for the node (0x00422D80, which also reports the map's end node at +0xC when the name is unknown);
 * an unknown name builds "Попытка удалить не загруженный ресурс с именем " (0x0060AB10) plus the name and throws
 * it (the std::string copy at 0x0069916C's throw info).  The node's +0x24 object, if any, is released through its
 * vtable slot 0x74 with flag 1, and the node is erased from the map (0x0047CA20). */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void (__thiscall *release_00448D80)(void *self, int flag);
DECOMP_C char d_0060AB10[], d_0069916C[];
DECOMP_C void __thiscall sub_00422D80(void *self, void **slot, const void *key);
DECOMP_C void __thiscall sub_0047CA20(void *self, void **slot, void *node);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(00448D80)
void __thiscall f_00448D80(void *self, void *name)
{
    void *node;
    void *child;

    sub_00422D80((char *)self + 4, &node, name);
    if (node == *(void **)((char *)self + 0xc)) {
        unsigned int prefix[7], message[7], error[7];
        imp_00607324(prefix, d_0060AB10);
        imp_006071C0(message, prefix, name);
        imp_00607334(error, message);
        sub_005E3EC0(error, d_0069916C);
    }
    child = *(void **)((char *)node + 0x24);
    if (child)
        ((release_00448D80)(*(void ***)child)[0x74 / 4])(child, 1);
    sub_0047CA20((char *)self + 4, &node, node);
}
