/* 0x004740C0: CMaskTexture constructor; reads a bitmap through its pixel callback and stores
 * the middle byte of each 32-bit color in a newly allocated width*height mask. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00458AF0(void *self);
DECOMP_C void __thiscall sub_00458B20(void *self);
DECOMP_C void __thiscall sub_00458B50(void *self, void *source);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void __cdecl sub_005E3EBA(void *memory);
DECOMP_C char d_0060E9D0[], d_0060E9C8[];
typedef unsigned int *(__thiscall *pixel_4740C0)(void *self, void *source_ref,
                                                 unsigned int x, unsigned int y);

DECOMP(004740C0)
void *__thiscall f_004740C0(char *this, void *source)
{
    unsigned int bitmap[8];
    unsigned int width, height, size, x, y;
    unsigned char *mask;

    *(void **)(this + 4) = 0;
    *(void **)this = d_0060E9D0;
    *(void **)(this + 8) = d_0060E9C8;
    *(void **)(this + 0x0c) = 0;
    *(unsigned int *)(this + 0x10) = 0;
    sub_00458AF0(bitmap);
    sub_00458B50(bitmap, source);
    width = bitmap[6];
    height = bitmap[7];
    *(unsigned int *)(this + 0x14) = width;
    *(unsigned int *)(this + 0x18) = height;
    size = width * height;
    mask = *(unsigned char **)(this + 0x0c);
    if (mask) {
        sub_005E3EBA(mask);
        *(void **)(this + 0x0c) = 0;
    }
    if (size)
        *(void **)(this + 0x0c) = sub_005E3B10(size);
    *(unsigned int *)(this + 0x10) = 0;
    mask = *(unsigned char **)(this + 0x0c);
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            unsigned int *color = ((pixel_4740C0)bitmap[2])(bitmap, &source, x, y);
            mask[*(unsigned int *)(this + 0x10)] = (unsigned char)(*color >> 8);
            *(unsigned int *)(this + 0x10) += 1;
        }
    }
    sub_00458B20(bitmap);
    return this;
}
