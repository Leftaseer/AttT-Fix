/* 0x00429310: copies the exception object arg 1 (0x00420C80: the std::exception base and the message string) and
 * stores the std::out_of_range vtable 0x00608208 at +0.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608208[];
DECOMP_C void *__thiscall sub_00420C80(void *self, void *src);

DECOMP(00429310)
void *__thiscall f_00429310(void *this, void *src)
{
    sub_00420C80(this, src);
    *(void **)this = d_00608208;
    return this;
}
