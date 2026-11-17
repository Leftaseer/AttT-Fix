/* 0x00557F50: replaces the 76-byte element array at +4, constructing `count` elements, and resets the used count at +8. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void (__thiscall *vector_dtor_557F50)(void *self, unsigned int flags);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void __cdecl sub_005E3EBA(void *block);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C char d_00557A00[], d_00557E40[];

DECOMP(00557F50)
void __thiscall f_00557F50(char *this, unsigned int count)
{
    char *data = *(char **)(this + 4);
    unsigned int *block;
    unsigned int bytes;
    if (data) {
        block = (unsigned int *)data;
        if (block[-1]) {
            vector_dtor_557F50 *dtors = *(vector_dtor_557F50 **)data;
            dtors[0](data, 3);
        } else
            sub_005E3EBA(block - 1);
        *(void **)(this + 4) = 0;
    }
    if (count) {
        bytes = count * 0x4c;
        if (count > 0xffffffffu / 0x4c || bytes > 0xfffffffbu)
            bytes = 0xffffffffu;
        else
            bytes += 4;
        block = sub_005E3B10(bytes);
        if (block) {
            block[0] = count;
            data = (char *)(block + 1);
            sub_005E4197(data, 0x4c, count, d_00557A00, d_00557E40);
        } else
            data = 0;
        *(char **)(this + 4) = data;
    }
    *(unsigned int *)(this + 8) = 0;
}
