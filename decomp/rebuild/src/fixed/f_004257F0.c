/* 0x004257F0: C3DLine's vertex write (six floats, ret 0x18): the mesh at +0x1C4 (whose first field is the vertex
 * buffer, handed in ECX) locks 0x18 bytes (slot 0x2C with the mesh, 0, 0x18, &vertices, 0); when the call does not
 * fail, the six arguments are stored as two 3D points and the mesh's slot 0x30 (one stack argument) unlocks. */
/* @conv ECX 24 */
#include "auto_pre.h"
typedef long (__thiscall *lock_4257F0)(void *buffer, void *mesh, unsigned int offset, unsigned int size,
                                       void **vertices, unsigned int flags);
typedef void (__stdcall *unlock_4257F0)(void *mesh);

DECOMP(004257F0)
void __thiscall f_004257F0(void *this, float x1, float y1, float z1, float x2, float y2, float z2)
{
    char *s = (char *)this;
    void **mesh = *(void ***)(s + 0x1c4);
    void *buffer = *mesh;
    float *vertices;
    if (((lock_4257F0)((void **)buffer)[0x2c / 4])(buffer, mesh, 0, 0x18, (void **)&vertices, 0) >= 0) {
        vertices[0] = x1;
        vertices[1] = y1;
        vertices[2] = z1;
        vertices[3] = x2;
        vertices[4] = y2;
        vertices[5] = z2;
        ((unlock_4257F0)((void **)buffer)[0x30 / 4])(mesh);
    }
}
