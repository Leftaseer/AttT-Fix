/* 0x005B4AE0: creates a named resource, copies its key, registers it through virtual interfaces,
 * and appends the object/key pair to the container at this+4. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int zero);
DECOMP_C void __thiscall sub_005B4A50(void *self, void *object_and_key);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_00620B04[];
typedef unsigned int (__thiscall *name_size_5B4AE0)(void *self);
typedef int (__stdcall *register_name_5B4AE0)(void *manager, const char *name, unsigned int size);
typedef void *(__stdcall *find_interface_5B4AE0)(void *manager, int zero, const char *name);

#define VT(o) (*(void ***)(o))

typedef struct {
    void *object;
    char *key;
} ResourcePair_5B4AE0;

DECOMP(005B4AE0)
int __thiscall f_005B4AE0(char *this, const char *name, const char *key)
{
    unsigned int temp_string[7];
    ResourcePair_5B4AE0 pair;
    unsigned int length, i, key_size;
    void *memory, *manager;
    int status;

    pair.object = 0;
    pair.key = 0;
    memory = sub_005E3EAE(0x54);
    pair.object = memory;
    if (memory) {
        imp_00607324(temp_string, name);
        pair.object = sub_004DF920(memory, temp_string, 0);
        imp_00607330(temp_string);
    }
    *(void **)(this + 0x20) = pair.object;

    length = 0;
    while (key[length])
        length++;
    key_size = length + 1;
    pair.key = sub_005E3B10(key_size);
    for (i = 0; i < key_size; i++)
        pair.key[i] = key[i];

    length = ((name_size_5B4AE0)VT(pair.object)[0x30 / 4])(pair.object);
    manager = *(void **)(this + 0x18);
    status = ((register_name_5B4AE0)VT(manager)[0xd0 / 4])(manager, pair.key, length);
    if (status >= 0) {
        manager = *(void **)(this + 0x18);
        *(void **)(this + 0x24) = ((find_interface_5B4AE0)VT(manager)[0x28 / 4])(
            manager, 0, d_00620B04);
        sub_005B4A50(this + 4, &pair);
    }
    return status;
}
