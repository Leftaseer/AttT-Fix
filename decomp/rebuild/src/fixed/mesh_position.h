#ifndef ATTT_FIXED_MESH_POSITION_H
#define ATTT_FIXED_MESH_POSITION_H

#include "auto_pre.h"

DECOMP_C char d_00608850[], d_00608858[], d_0060FAC0[], d_006C8958[], d_006C895C[];

/* Coordinates arrive as float32 stack dwords. Keep the bits intact for MOVSS,
 * which copies even a signaling NaN without an x87 load/store round trip. */
static inline unsigned int mesh_position_flags(unsigned int eax, unsigned int coordinate_bits)
{
    /* UCOMISS sets ZF, PF and CF on NaN. The original returns LAHF's byte in AH. */
    __asm__ volatile("movss %1, %%xmm0\n\tucomiss %2, %%xmm0\n\tlahf"
                     : "+a"(eax) : "m"(coordinate_bits), "m"(*(float *)d_0060FAC0) : "xmm0", "cc");
    return eax;
}

static inline bool mesh_position_uses_default(unsigned int eax)
{
    return (eax & 0x4500) == 0x4000;
}

#endif
