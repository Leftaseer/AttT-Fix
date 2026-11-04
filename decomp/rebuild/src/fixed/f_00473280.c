#include "auto_pre.h"

static inline int truncate_coordinate(float value)
{
    int result;
    __asm__ volatile("cvttss2si %1, %0" : "=r"(result) : "m"(value));
    return result;
}

/* The native fcomi/jbe branches take the jump for unordered inputs.
 * Convert the selected values with the native signed float32 instruction. */
/* @func 00473280 */
DECOMP(00473280)
void __stdcall f_00473280(float a, float b, float c, int *lower, int *upper)
{
    float low, high;
    bool b_larger = b > a;
    if (b_larger && c > a) {
        low = a;
        high = b > c ? b : c;
    } else if (!b_larger && c > b) {
        low = b;
        high = a > c ? a : c;
    } else {
        low = c;
        high = a > b ? a : b;
    }
    *lower = truncate_coordinate(low);
    *upper = truncate_coordinate(high);
}
