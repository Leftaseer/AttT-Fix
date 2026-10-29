/* 0x00513FA0: CTacticCreature health set: the value clamped to 0 .. max (+0x1E0) at +0x1EC and as a share of the
 * max at +0x1E8 (none left clears +0x3BC); with a script object (+0x2B8) its BattleParams.Health (+0x2B0) is set
 * too; +0x3E0 and +0x3DC are cleared. (The generator split it at 0x00513FC1, a jump target.) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_0044D030(void *self, void *out, const void *key);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C char d_006139FC[], d_00613978[];

DECOMP(00513FA0)
void __thiscall f_00513FA0(void *self, int h)
{
    char *this = (char *)self;
    if (h < 0)
        h = 0;
    else if (h > *(int *)(this + 0x1e0))
        h = *(int *)(this + 0x1e0);
    *(int *)(this + 0x1ec) = h;
    *(float *)(this + 0x1e8) = (float)((long double)h / (long double)*(int *)(this + 0x1e0));
    if (h == 0)
        this[0x3bc] = 0;
    if (*(int *)(this + 0x2b8) > 0) {
        struct { void *t; const char *k; } ref;
        struct { unsigned int t[3]; const char *k; } out, *r;
        ref.t = this + 0x2b0;
        ref.k = d_00613978;
        r = sub_0044D030(&ref, &out, d_006139FC);
        sub_0057BC80(r, r->k, (float)*(int *)(this + 0x1ec));
        sub_004220A0(&out);
    }
    this[0x3e0] = 0;
    *(int *)(this + 0x3dc) = 0;
}
