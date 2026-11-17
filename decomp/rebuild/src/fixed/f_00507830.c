/* 0x00507830: replaces the 200-byte element array at +4, constructing `count` elements, and resets the used count at +8. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void (__thiscall *vector_dtor_507830)(void *self, unsigned int flags);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void __cdecl sub_005E3EBA(void *block);
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C char d_0051F040[], d_0051E940[];

DECOMP(00507830)
void __thiscall f_00507830(char *this, unsigned int count)
{
    char *data = *(char **)(this + 4);
    unsigned int *block;
    unsigned int bytes;
    if (data) {
        block = (unsigned int *)data;
        if (block[-1]) {
            vector_dtor_507830 *dtors = *(vector_dtor_507830 **)data;
            dtors[0](data, 3);
        } else
            sub_005E3EBA(block - 1);
        *(void **)(this + 4) = 0;
    }
    if (count) {
        bytes = count * 0xc8;
        if (count > 0xffffffffu / 0xc8 || bytes > 0xfffffffbu)
            bytes = 0xffffffffu;
        else
            bytes += 4;
        block = sub_005E3B10(bytes);
        if (block) {
            block[0] = count;
            data = (char *)(block + 1);
            sub_005E4197(data, 0xc8, count, d_0051F040, d_0051E940);
        } else
            data = 0;
        *(char **)(this + 4) = data;
    }
    *(unsigned int *)(this + 8) = 0;
}
