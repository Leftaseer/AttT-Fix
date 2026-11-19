/* 0x00465950: CHero::CHero.  The base constructor 0x004AD180 gets the "WorldUnit" name (std::string built through
 * 0x00607324, destroyed with 0x00607330), the constructor argument and a zero.  The sub-objects at +0x1C4 (vtable
 * 0x0060B900 replaced later by 0x0060C1A0), +0x1C8 (0x004B40E0, vtable 0x0060C18C), +0x1D0 (0x004B8640 with 1,
 * vtable 0x0060C180) and +0x230 (0x004AD9B0) are initialised, this vtable becomes 0x0060C1AC and the fields
 * +0x1EC..+0x21C are cleared.  +0x4CC and +0x4D8 receive empty lists (0x00464630 / 0x004C2F40 put a node into
 * +4 and clear +8) and +0x4E8 a default std::string (0x006071E0).  A hero already published at 0x006C8EF8 makes the
 * constructor throw the Hero.cpp:0x39 error from 0x0060C150 with the 0x005E3EC0 throw info 0x0069916C.  The
 * reader +0x2C, if any, is released through its vtable +0x14 and +0x1D8/+0x22C are cleared; the new hero is then
 * published.  Timer fields +0x4A4/+0x4AC/+0x4B0 become 1000/100/123 and the device singleton [0x006C8C10] fills a
 * capabilities record (vtable +0x1C, two arguments); its dword at +0xA4 (MaxUserClipPlanes-like, compared against
 * 2) sets the byte +0x1E8.  Returns the object. */
/* @conv ECX 8 */
#include "auto_pre.h"

typedef struct { unsigned int w[7]; } Str_465950;                  /* std::string */

DECOMP_C char d_006C8C10[], d_0060C26C[], d_0060C150[], d_0060C144[], d_0069916C[];
DECOMP_C void *d_006C8EF8;
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, void *a, int b);
DECOMP_C void __thiscall sub_004B40E0(void *self);
DECOMP_C void __thiscall sub_004B8640(void *self, int flag);
DECOMP_C void __thiscall sub_004AD9B0(void *self);
DECOMP_C void *__thiscall sub_00464630(void *self);
DECOMP_C void *__thiscall sub_004C2F40(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00465950)
void *__thiscall f_00465950(void *self, void *arg, void *unused)
{
    char *this = (char *)self;

    {
        Str_465950 name;
        unsigned int caps[0x2c];
        void *reader;

        imp_00607324(&name, d_0060C26C);
        sub_004AD180(this, &name, arg, 0);
        imp_00607330(&name);
        *(unsigned int *)(this + 0x1c4) = 0x0060b900;
        sub_004B40E0(this + 0x1c8);
        sub_004B8640(this + 0x1d0, 1);
        *(unsigned int *)this = 0x0060c1ac;
        *(unsigned int *)(this + 0x1c4) = 0x0060c1a0;
        *(unsigned int *)(this + 0x1c8) = 0x0060c18c;
        *(unsigned int *)(this + 0x1d0) = 0x0060c180;
        *(unsigned int *)(this + 0x1ec) = 0;
        *(unsigned int *)(this + 0x1f0) = 0;
        *(unsigned int *)(this + 0x1f4) = 0;
        *(unsigned int *)(this + 0x1f8) = 0;
        *(unsigned int *)(this + 0x1fc) = 0;
        *(unsigned int *)(this + 0x204) = 0;
        *(unsigned int *)(this + 0x208) = 0;
        *(unsigned int *)(this + 0x20c) = 0;
        *(unsigned int *)(this + 0x214) = 0;
        *(unsigned int *)(this + 0x218) = 0;
        *(unsigned int *)(this + 0x21c) = 0;
        sub_004AD9B0(this + 0x230);
        *(unsigned int *)(this + 0x4d0) = (unsigned int)sub_00464630(this + 0x4cc);
        *(unsigned int *)(this + 0x4d4) = 0;
        *(unsigned int *)(this + 0x4dc) = (unsigned int)sub_004C2F40(this + 0x4d8);
        *(unsigned int *)(this + 0x4e0) = 0;
        imp_006071E0(this + 0x4e8);
        if (d_006C8EF8) {
            unsigned int msg[7], exc[9];
            imp_00607324(msg, d_0060C150);
            sub_00421220(exc, msg, d_0060C144, 0x39);
            sub_005E3EC0(exc, d_0069916C);
        }
        reader = *(void **)(this + 0x2c);
        *(unsigned int *)(this + 0x1d8) = 0;
        *(unsigned int *)(this + 0x22c) = 0;
        if (reader) {
            (*(void (__thiscall **)(void *, void *))((char *)*(void **)reader + 0x14))(reader, this);
            *(unsigned int *)(this + 0x2c) = 0;
        }
        d_006C8EF8 = this;
        *(unsigned int *)(this + 0x4a4) = 1000;
        *(unsigned int *)(this + 0x4ac) = 100;
        *(unsigned int *)(this + 0x4b0) = 123;
        *(unsigned int *)(this + 0x4a8) = 0;
        *(unsigned int *)(this + 0x4bc) = 0;
        this[0x1eb] = 0;
        {
            void *dev = *(void **)d_006C8C10;
            (*(void (__stdcall **)(void *, void *))((char *)*(void **)dev + 0x1c))(dev, caps);
        }
        this[0x1e8] = (unsigned int)caps[0x29] >= 2;
    }
    return self;
}
