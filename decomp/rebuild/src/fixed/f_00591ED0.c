/* 0x00591ED0: DrawableBBox destructor.  In editor mode the object is unregistered, then the
 * 12-edge and 3-axis line vectors are released and cleared before the base destructor runs. */
/* @conv ECX 0 */
#include "auto_pre.h"

typedef struct {
    void *self;
    void *begin;
    void *end;
    void *capacity;
} Vector_00591ED0;

DECOMP_C void __thiscall sub_005ADCC0(void *editor, void *object);
DECOMP_C void __cdecl sub_004E1BF0(void *eax, void *first, void *last, void *vector, unsigned int owner);
DECOMP_C void __cdecl sub_005E3E9C(void *memory);
DECOMP_C void __thiscall sub_004AD020(void *self);
DECOMP_C char d_006C88D8[], d_0061F6F4[];

static void release_lines_00591ED0(char *this, Vector_00591ED0 *vector)
{
    if (vector->begin) {
        sub_004E1BF0(vector->begin, vector->begin, vector->end, vector, (unsigned int)this);
        sub_005E3E9C(vector->begin);
    }
    vector->begin = 0;
    vector->end = 0;
    vector->capacity = 0;
}

DECOMP(00591ED0)
void __thiscall f_00591ED0(char *this)
{
    char *editor = *(char **)d_006C88D8;

    *(void **)this = d_0061F6F4;
    if (editor[0x40])
        sub_005ADCC0(editor, this);
    *(unsigned int *)(this + 0x1bc) = 0;
    release_lines_00591ED0(this, (Vector_00591ED0 *)(this + 0x1d4));
    release_lines_00591ED0(this, (Vector_00591ED0 *)(this + 0x1c4));
    sub_004AD020(this);
}
