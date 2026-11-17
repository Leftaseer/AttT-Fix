/* 0x00557260: replaces the 12-byte element array at +4, constructing `count` elements, and resets the used count at +8. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void (__thiscall *vector_dtor_557260)(void *self, unsigned int flags);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void __cdecl sub_005E3EBA(void *block);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C char d_00555E60[], d_00556D10[];

DECOMP(00557260)
void __thiscall f_00557260(char *this, unsigned int count)
{
    char *data = *(char **)(this + 4);
    unsigned int *block;
    unsigned int bytes;
    if (data) {
        block = (unsigned int *)data;
        if (block[-1]) {
            vector_dtor_557260 *dtors = *(vector_dtor_557260 **)data;
            dtors[0](data, 3);
        } else
            sub_005E3EBA(block - 1);
        *(void **)(this + 4) = 0;
    }
    if (count) {
        bytes = count * 12;
        if (count > 0xffffffffu / 12 || bytes > 0xfffffffbu)
            bytes = 0xffffffffu;
        else
            bytes += 4;
        block = sub_005E3B10(bytes);
        if (block) {
            block[0] = count;
            data = (char *)(block + 1);
            sub_005E4197(data, 12, count, d_00555E60, d_00556D10);
        } else
            data = 0;
        *(char **)(this + 4) = data;
    }
    *(unsigned int *)(this + 8) = 0;
}
