/* CMeshObject2D::vf38 0x00479790: sets the position (0x74, 0x78) from the given one, or the default position
 * (0x20C, 0x210) where its x is the 'unset' marker at 0x60FAC0; marks it changed (0x7C).  The original leaves EAX
 * as it found it (its AH the flags of the comparison): a leftover */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_0060FAC0[];

DECOMP(00479790)
void __thiscall f_00479790(char *this, const float *p)
{
    if (p[0] == *(float *)d_0060FAC0) {
        *(unsigned char *)(this + 0x7c) = 1;
        *(float *)(this + 0x74) = *(float *)(this + 0x20c);
        *(float *)(this + 0x78) = *(float *)(this + 0x210);
        return;
    }
    *(unsigned int *)(this + 0x74) = ((const unsigned int *)p)[0];
    *(unsigned int *)(this + 0x78) = ((const unsigned int *)p)[1];
    *(unsigned char *)(this + 0x7c) = 1;
}
