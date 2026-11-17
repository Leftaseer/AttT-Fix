/* 0x004268C0: renders all scene passes with the object's transform, stream and optional texture. */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef void (__stdcall *device_transform_4268C0)(void *device, unsigned int state, const void *matrix);
typedef void (__stdcall *device_stream_4268C0)(void *device, unsigned int stream, void *data,
                                                unsigned int offset, unsigned int stride);
typedef void (__stdcall *device_texture_4268C0)(void *device, unsigned int stage, void *texture);
typedef void (__stdcall *device_draw_4268C0)(void *device, unsigned int primitive, unsigned int first,
                                              unsigned int count);
typedef void (__thiscall *pass_count_4268C0)(void *self, unsigned int *count, unsigned int unused);
typedef void (__thiscall *pass_index_4268C0)(void *self, unsigned int index);
typedef void (__thiscall *pass_simple_4268C0)(void *self);
typedef void *(__thiscall *texture_get_4268C0)(void *self);
DECOMP_C void __thiscall sub_004357F0(void *self);
DECOMP_C char d_006CA2C4[], d_006C8C10[];

DECOMP(004268C0)
void __thiscall f_004268C0(char *this)
{
    void *device, *scene, *texture;
    unsigned int count = 0, pass;
    sub_004357F0(*(void **)d_006CA2C4);
    device = *(void **)d_006C8C10;
    (*(device_transform_4268C0 **)device)[0xb0 / 4](device, 0x100, this + 0x140);
    device = *(void **)d_006C8C10;
    (*(device_stream_4268C0 **)device)[0x190 / 4](device, 0, *(void **)(this + 0x208), 0, 0x14);
    scene = *(void **)(this + 0x3c);
    ((pass_count_4268C0)(*(void ***)scene)[0x18 / 4])(scene, &count, 0);
    for (pass = 0; pass < count; pass++) {
        ((pass_index_4268C0)(*(void ***)scene)[0x20 / 4])(scene, pass);
        texture = *(void **)(this + 0x44);
        if (texture) {
            void *value = ((texture_get_4268C0)(*(void ***)texture)[0x28 / 4])(texture);
            device = *(void **)d_006C8C10;
            (*(device_texture_4268C0 **)device)[0x104 / 4](device, 0, value);
        }
        device = *(void **)d_006C8C10;
        (*(device_draw_4268C0 **)device)[0x144 / 4](device, 5, 0, 2);
        ((pass_simple_4268C0)(*(void ***)scene)[0x24 / 4])(scene);
    }
    ((pass_simple_4268C0)(*(void ***)scene)[0x1c / 4])(scene);
}
