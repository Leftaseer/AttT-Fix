/* 0x00585360: updates render-object sizing; zero width or height is replaced by the selected
 * child's unsigned dimension before virtual slot 0x94 is called. */
/* @conv ECX 24 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_005850A0(void *self);
DECOMP_C char d_0060FAC0[], d_0068AE08[];
typedef void (__thiscall *set_pair_585360)(void *self, void *value, int zero);
typedef void (__thiscall *set_floats_585360)(void *self, float first, float second);
typedef unsigned int (__thiscall *get_dimension_585360)(void *self);

#define VT(o) (*(void ***)(o))

DECOMP(00585360)
void __thiscall f_00585360(char *this, float first, float second, float height, float width,
                           void *fifth, void *sixth)
{
    void **child;
    unsigned int value;
    float converted;

    ((set_pair_585360)VT(this)[0x2c / 4])(this, sixth, 0);
    ((set_pair_585360)VT(this)[0x38 / 4])(this, fifth, 0);
    ((set_floats_585360)VT(this)[0x68 / 4])(this, first, second);

    if (width == *(float *)d_0060FAC0) {
        child = *(void ***)(this + 0x44);
        child = *(void ***)(*(char **)(child + 0x38 / 4) + *(unsigned int *)(child + 0x40 / 4) * 4);
        value = ((get_dimension_585360)VT(child)[0x14 / 4])(child);
        converted = (float)(int)value;
        if ((int)value < 0)
            converted += *(float *)d_0068AE08;
        width = converted;
    }
    if (height == *(float *)d_0060FAC0) {
        child = *(void ***)(this + 0x44);
        child = *(void ***)(*(char **)(child + 0x38 / 4) + *(unsigned int *)(child + 0x40 / 4) * 4);
        value = ((get_dimension_585360)VT(child)[0x10 / 4])(child);
        converted = (float)(int)value;
        if ((int)value < 0)
            converted += *(float *)d_0068AE08;
        height = converted;
    }
    ((set_floats_585360)VT(this)[0x94 / 4])(this, height, width);
    sub_005850A0(this);
}
