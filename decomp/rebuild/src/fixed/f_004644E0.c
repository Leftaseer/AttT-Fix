/* 0x004644E0: exports the hero into a script table (arg; this is the hero's interface at +0x1C8, so the hero's
 * position x (+0x64), z (+0x6C) and heading "roty" (+0x78) are at -0x164 / -0x15C / -0x150): a "pos" table gets x,
 * z and roty as floats (0x00435E00, 0x0057BC80, keys 0x6098D0 / 0x6098C8 / 0x60C098), an outer table takes that
 * table as "pos" (0x0057BF50, 0x6098E8) and the class "type" (0x68A2C4) as the float of +0x2E0, and the argument
 * receives the outer table as "HeroPos" (0x60C090). Both temporaries are destroyed (0x004220A0; the original leaves
 * nothing of its own in EAX -- it is just the last destructor's scratch result). */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00435E00(void *self, int pool);
DECOMP_C void __thiscall sub_0057BC80(void *self, const char *key, float value);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, const void *value);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C char d_006098D0[], d_006098C8[], d_0060C098[], d_006098E8[], d_0068A2C4[], d_0060C090[];

DECOMP(004644E0)
void __thiscall f_004644E0(char *this, void *save)
{
    char pos[0xc], hero[0xc];
    sub_00435E00(hero, 0);
    sub_00435E00(pos, 0);
    sub_0057BC80(pos, d_006098D0, *(float *)(this - 0x164));
    sub_0057BC80(pos, d_006098C8, *(float *)(this - 0x15c));
    sub_0057BC80(pos, d_0060C098, *(float *)(this - 0x150));
    sub_0057BF50(hero, d_006098E8, pos);
    sub_0057BC80(hero, d_0068A2C4, (float)*(int *)(this + 0x2e0));
    sub_0057BF50(save, d_0060C090, hero);
    sub_004220A0(pos);
    sub_004220A0(hero);
}
