/* 0x00505FC0: the battle standard's animation update (vtable +0x08 of 0x613784): the standard's position (its own
 * vtable +0x68 returns +0x64) becomes the animation's previous (+0x58) and current (+0x64) position (+0x70 is set);
 * the +0x74 vector and the +0x98 vector doubled by 0x0060A308 (2.0) go to the animation (+0x80, +0xA4 are set); the
 * animation updates (vtable +0x18), its +0x168 matrix becomes the device's world transform (0x100, also kept at
 * 0x006CA0A4) and the 8 box corners (vtable +0xEC, 0x60 bytes) are world transformed (D3DXVec3TransformCoord) into
 * 0x00458120 with the camera 0x006CA2C8: when they are in view the animation draws (vtable +0x08) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006C8C10[], d_006CA0A4[], d_006CA2C8[], d_0060A308[];
DECOMP_C unsigned int __cdecl sub_00458120(void *this, unsigned int in_eax, void *pos);
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
typedef float *(__thiscall *pos_505FC0)(void *self);
typedef float *(__thiscall *box_505FC0)(void *self);
typedef void (__thiscall *vf_505FC0)(void *self);
typedef long (__stdcall *set_transform_505FC0)(void *dev, unsigned int state, const void *m);
#define VT(o) (*(void ***)(o))

DECOMP(00505FC0)
void __thiscall f_00505FC0(char *this)
{
    char *anim = *(char **)(this + 0x1e8);
    float *pos = ((pos_505FC0)VT(this)[0x68 / 4])(this);
    float matrix[16];
    float box[24];
    float *src;
    int i;

    *(unsigned int *)(anim + 0x58) = *(unsigned int *)(anim + 0x64);
    *(unsigned int *)(anim + 0x5c) = *(unsigned int *)(anim + 0x68);
    *(unsigned int *)(anim + 0x60) = *(unsigned int *)(anim + 0x6c);
    *(unsigned int *)(anim + 0x64) = ((unsigned int *)pos)[0];
    *(unsigned int *)(anim + 0x68) = ((unsigned int *)pos)[1];
    *(unsigned int *)(anim + 0x6c) = ((unsigned int *)pos)[2];
    anim[0x70] = 1;

    anim = *(char **)(this + 0x1e8);
    *(unsigned int *)(anim + 0x74) = *(unsigned int *)(this + 0x74);
    *(unsigned int *)(anim + 0x78) = *(unsigned int *)(this + 0x78);
    *(unsigned int *)(anim + 0x7c) = *(unsigned int *)(this + 0x7c);
    anim[0x80] = 1;
    *(float *)(anim + 0x98) = (float)(*(float *)(this + 0x98) * *(double *)d_0060A308);
    *(float *)(anim + 0x9c) = (float)(*(float *)(this + 0x9c) * *(double *)d_0060A308);
    anim[0xa4] = 1;
    *(float *)(anim + 0xa0) = (float)(*(float *)(this + 0xa0) * *(double *)d_0060A308);
    ((vf_505FC0)VT(anim)[0x18 / 4])(anim);

    anim = *(char **)(this + 0x1e8);
    __builtin_memcpy(matrix, anim + 0x168, sizeof matrix);
    ((set_transform_505FC0)VT(*(void **)d_006C8C10)[0xb0 / 4])(*(void **)d_006C8C10, 0x100, matrix);
    *(void **)d_006CA0A4 = matrix;
    anim = *(char **)(this + 0x1e8);
    src = ((box_505FC0)VT(anim)[0xec / 4])(anim);
    __builtin_memcpy(box, src, sizeof box);
    for (i = 0; i < 8; i++)
        sub_005B8026(box + i * 3, box + i * 3, matrix);
    if ((unsigned char)sub_00458120(*(void **)d_006CA2C8, 0, box)) {
        anim = *(char **)(this + 0x1e8);
        ((vf_505FC0)VT(anim)[0x8 / 4])(anim);
    }
}
