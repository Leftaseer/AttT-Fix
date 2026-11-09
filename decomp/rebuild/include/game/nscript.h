/* nScript: the engine's wrapper over the Lua state (the "script machine", 0x6C88D4).  The wrapper of a Lua value
 * is nScript::Table (0xC bytes): the vtables 0x607CC4 / 0x607CB8, a spare field and the value's reference in the
 * Lua registry.  The wrappers are built from a stack index (0x45C7E0) or from the value on top of the stack
 * (0x45C850), assigned (0x57A860), read by key or index (0x57AA20 / 0x57AD40 / 0x57AC90 / 0x57B4E0) and drop
 * their registry reference in the destructor (0x4220A0).
 *
 * The loaders that walk a table inline the iterator type over it: 0x14 bytes with the vtable 0x60C044, the
 * owner slot, a done byte, the current stack index and the element count (see NsTableIterator). */
#pragma once
#include "game/common.h"

ORIG_DATA(00607CC4); /* nScript::Table::vftable */

struct NsTable;

ORIG_THISCALL(0045C7E0, NsTable *, (NsTable *self, int index));      /* Table(int): references the value at index */
ORIG_STDCALL(0045C850, NsTable *, (NsTable *out));                   /* Table::FromStack: the value on top */
ORIG_THISCALL(004220A0, void, (NsTable *self));                      /* ~Table: drops the registry reference */
ORIG_THISCALL(0057A860, NsTable *, (NsTable *self, const NsTable *other)); /* operator= */
ORIG_THISCALL(0057AA20, unsigned char, (NsTable *self, const char *key));  /* GetBool */
ORIG_THISCALL(0057AD40, float, (NsTable *self, const char *key));    /* GetFloat */
ORIG_THISCALL(0057AC90, float, (NsTable *self, int index));          /* GetNumber */
ORIG_THISCALL(0057B4E0, NsTable *, (NsTable *self, NsTable *out, const char *key)); /* GetTable */

struct NsTable {
    void *vftable;  /* +00 0x607CC4 */
    int spare;      /* +04 */
    int reference;  /* +08 Lua registry reference; -1 when the wrapper is empty */

    NsTable() : vftable(d_00607CC4), spare(0), reference(-1) {}
    explicit NsTable(int index) { sub_0045C7E0(this, index); }
    ~NsTable() { sub_004220A0(this); }

    unsigned char GetBool(const char *key) const { return sub_0057AA20((NsTable *)this, key); }
    float GetFloat(const char *key) const { return sub_0057AD40((NsTable *)this, key); }
    float GetNumber(int index) const { return sub_0057AC90((NsTable *)this, index); }
    NsTable *GetTable(NsTable *out, const char *key) const
    {
        return sub_0057B4E0((NsTable *)this, out, key);
    }
    NsTable &operator=(const NsTable &other)
    {
        sub_0057A860(this, &other);
        return *this;
    }
    static NsTable *FromStack(NsTable *out) { return sub_0045C850(out); }
};
static_assert(sizeof(NsTable) == 0x0C, "NsTable is 0x0C bytes");
static_assert(__builtin_offsetof(NsTable, reference) == 0x08, "NsTable::reference");

/* nScript::Table::i_iterator (0x14): the inlined table-walking loop of the loaders keeps this shape while it
 * iterates (the constructor 0x463C60 and destructor 0x463D20 are inlined into those loops). */
struct NsTableIterator {
    void *vftable;      /* +00 0x60C044 (0x607CB8 once the base destructor runs) */
    void *owner;        /* +04 */
    unsigned char done; /* +08 */
    int index;          /* +0C the Lua stack index the loop is at */
    int count;          /* +10 the element count lua_objlen reported */
};
static_assert(sizeof(NsTableIterator) == 0x14, "NsTableIterator is 0x14 bytes");
