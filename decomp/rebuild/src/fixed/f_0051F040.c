/* 0x0051F040: constructor of a script-backed object.  It installs the vtable 0x006143E4, clears +0x04..+0x1C,
 * places an empty nScript::Table at +0x20 (vtable 0x00607CC4, count -1) and an empty std::string at +0x2C
 * (default constructor 0x006071E0), marks the three list sentinels at +0x60 / +0x6C / +0x78 with 0x0060FE3C,
 * clears the vector-like member +0x84 (its +4..+0xC here, the rest by 0x004D6040 with 0x10), zeroes the float
 * +0xA8, builds a circular list head for +0xB0 (0x004C2F40, which ignores its this pointer) and an empty table
 * at +0xBC that is assigned a fresh table (0x00435E00 / 0x0057A860, the temporary dies through 0x004220A0).
 * A 0x10-byte node {vtable 0x00614388, previous global, this, callback 0x0051D450} is pushed onto the global
 * list at 0x006CA8E0.  The bytes +0x9C and +0xB8 are cleared and +0xA0 is zeroed last.  Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_51F040;                 /* nScript::Table */
DECOMP_C char d_006143E4[], d_00607CC4[], d_00613608[], d_0060FE3C[], d_00614388[], d_006CA8E0[];
DECOMP_C void *__thiscall sub_004C2F40(void *self);               /* circular list head */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);            /* operator new */
DECOMP_C void *__thiscall sub_00435E00(void *self, int allocator); /* nScript::Table::Table */
DECOMP_C void __thiscall sub_0057A860(void *self, const void *src); /* nScript::Table::operator= */
DECOMP_C int __thiscall sub_004220A0(void *self);                  /* nScript::Table::~Table */
DECOMP_C void __thiscall sub_004D6040(void *self, unsigned int n);
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0051F040)
void *__thiscall f_0051F040(char *this)
{
    Tbl_51F040 empty;
    void **node;
    char *head;

    *(void **)(this + 0x00) = d_006143E4;
    *(unsigned int *)(this + 0x04) = 0;
    *(unsigned int *)(this + 0x08) = 0;
    *(unsigned int *)(this + 0x0c) = 0;
    *(unsigned int *)(this + 0x10) = 0;
    *(unsigned int *)(this + 0x14) = 0;
    *(unsigned int *)(this + 0x18) = 0;
    *(unsigned int *)(this + 0x1c) = 0;
    *(void **)(this + 0x20) = d_00607CC4;
    *(unsigned int *)(this + 0x24) = 0;
    *(int *)(this + 0x28) = -1;
    imp_006071E0(this + 0x2c);
    *(void **)(this + 0x54) = d_00613608;
    *(unsigned int *)(this + 0x58) = 0;
    *(unsigned int *)(this + 0x5c) = 0;
    *(void **)(this + 0x60) = d_0060FE3C;
    *(unsigned int *)(this + 0x64) = 0;
    *(unsigned int *)(this + 0x68) = 0;
    *(void **)(this + 0x6c) = d_0060FE3C;
    *(unsigned int *)(this + 0x70) = 0;
    *(unsigned int *)(this + 0x74) = 0;
    *(void **)(this + 0x78) = d_0060FE3C;
    *(unsigned int *)(this + 0x7c) = 0;
    *(unsigned int *)(this + 0x80) = 0;
    *(unsigned int *)(this + 0x88) = 0;
    *(unsigned int *)(this + 0x8c) = 0;
    *(unsigned int *)(this + 0x90) = 0;
    *(float *)(this + 0xa8) = 0.0f;
    head = sub_004C2F40(this + 0xac);
    *(void **)(this + 0xb0) = head;
    *(unsigned int *)(this + 0xb4) = 0;
    *(void **)(this + 0xbc) = d_00607CC4;
    *(unsigned int *)(this + 0xc0) = 0;
    *(int *)(this + 0xc4) = -1;
    *(unsigned char *)(this + 0x9c) = 0;
    *(unsigned char *)(this + 0xb8) = 0;
    node = sub_005E3EAE(0x10);
    if (node) {
        node[1] = *(void **)d_006CA8E0;
        node[0] = d_00614388;
        node[2] = this;
        node[3] = (void *)0x0051D450;
    }
    *(void **)d_006CA8E0 = node;
    sub_00435E00(&empty, 0);
    sub_0057A860(this + 0xbc, &empty);
    sub_004220A0(&empty);
    sub_004D6040(this + 0x84, 0x10);
    *(unsigned int *)(this + 0xa0) = 0;
    return this;
}
