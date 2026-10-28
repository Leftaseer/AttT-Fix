/* 0x004BAFB0: creates the skeleton mesh's vertex buffers, one per copy (the byte at +0x14): 32 bytes for each element
 * of its four arrays (+0x88 of 2 bytes, +0x98 of 12, +0xA8 of 20, +0xB8 of 24), CreateVertexBuffer(D3DUSAGE_DYNAMIC
 * | WRITEONLY, XYZ | NORMAL | TEX1, default pool) checked by 0x00458940, filled while locked (0x004B9AA0), and
 * appended to the list at +0xEC (its current position +0xF8 set when it was at the end) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void __thiscall sub_004B9AA0(void *self, void *data);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C char d_006C8C10[], d_006111AC[];
typedef long (__stdcall *CreateVB_4BAFB0)(void *dev, unsigned int len, unsigned int usage, unsigned int fvf,
                                          unsigned int pool, void **vb, void *shared);
typedef long (__stdcall *Lock_4BAFB0)(void *vb, unsigned int off, unsigned int len, void **data, unsigned int flags);
typedef long (__stdcall *Unlock_4BAFB0)(void *vb);

#define COUNT(o, sz) (*(char **)(s + (o)) ? (int)(*(char **)(s + (o) + 4) - *(char **)(s + (o))) / (sz) : 0)

DECOMP(004BAFB0)
void __thiscall f_004BAFB0(void *this)
{
    char *s = (char *)this;
    int a = COUNT(0x88, 2), b = COUNT(0x98, 0xc), c = COUNT(0xa8, 0x14), d = COUNT(0xb8, 0x18);
    unsigned int k, size;
    if (!s[0x14])
        return;
    size = (d + c + b + a) * 0x20;
    for (k = 0; k < (unsigned char)s[0x14]; k++) {
        void **dev = *(void ***)d_006C8C10, **vb, *data;
        char *list = s + 0xec;
        char **head, **node;
        sub_00458940(((CreateVB_4BAFB0)(*(void ***)dev)[0x68 / 4])(dev, size, 0x208, 0x112, 0, (void **)&vb, 0),
                     d_006111AC, 0x59);
        ((Lock_4BAFB0)(*(void ***)vb)[0x2c / 4])(vb, 0, 0, &data, 0);
        sub_004B9AA0(this, data);
        ((Unlock_4BAFB0)(*(void ***)vb)[0x30 / 4])(vb);
        head = *(char ***)(list + 4);
        node = sub_005AD6C0(head, (char **)head[1], &vb);
        sub_004E0EF0(list, 1);
        head[1] = (char *)node;
        *(char ***)node[1] = node;
        if (*(char ***)(list + 0xc) == *(char ***)(list + 4))
            *(char **)(list + 0xc) = **(char ***)(list + 4);
    }
}
