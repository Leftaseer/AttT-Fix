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

ORIG_DATA(00607C88); /* Object::vftable */
ORIG_DATA(00607CC4); /* nScript::Table::vftable */
ORIG_DATA(00607CB8); /* nScript::VMObjImpl::vftable */
ORIG_DATA(00608260); /* nScript::TableGet::vftable */
ORIG_DATA(006098F0); /* nScript::Function::vftable */
ORIG_DATA(0061D90C); /* the nScript::Table the calls read their results through */

ORIG_THISCALL(00422000, void, (void *self)); /* Object::~Object */

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

/* Object / nScript::VMObjImpl: the script-object base of the wrappers (vtable 0x607C88).  +04 is the child the
 * object is registered with; Object::~Object throws while it is still set.  VMObjImpl adds no data, it only
 * switches the vtable to 0x607CB8 before the base goes. */
struct NsObject {
    void *vftable; /* +00 */
    void *owner;   /* +04 */

    NsObject() : vftable(nullptr), owner(nullptr) {}
    ~NsObject() { ORIG_CALL(00422000)(this); }
};

struct NsVMObjImpl : NsObject {
    ~NsVMObjImpl() { vftable = d_00607CB8; }
};

struct NsTableGet;

/* nScript::Function (0x18): a reference to a Lua function and the table the wrapper carries.  The constructor
 * references the value at a stack index (0x46F790); the assignment (0x436FD0) and the destructor (0x4378D0)
 * move / drop the registry references.  Calling it (0x57A180) pushes the function, passes its table as the single
 * argument when there is one, and wraps the results in a TableGet. */
struct NsFunction : NsVMObjImpl {
    NsTable table;  /* +08 the table the function is called with; its reference at +10 is -1 when there is none */
    int reference;  /* +14 registry reference of the function */

    NsFunction() : reference(-1) { vftable = d_006098F0; }
    explicit NsFunction(int index);                 /* 0x46F790 */
    ~NsFunction();                                  /* 0x4378D0 */
    NsFunction &operator=(const NsFunction &other); /* 0x436FD0 */
    NsTableGet *Call(NsTableGet *out, int results); /* 0x57A180 */
};
static_assert(sizeof(NsFunction) == 0x18, "NsFunction is 0x18 bytes");
static_assert(__builtin_offsetof(NsFunction, table) == 0x08, "NsFunction::table");
static_assert(__builtin_offsetof(NsFunction, reference) == 0x14, "NsFunction::reference");

/* nScript::TableGet (0x18): the values a table read or a function call left on the Lua stack.  The constructor
 * (0x4277B0) remembers where they start (+10) and how many there are (+0C); the destructor (0x427820) pops them
 * when the read owns them (+14). */
struct NsTableGet : NsVMObjImpl {
    NsTable *table; /* +08 the table the values were read from */
    int count;      /* +0C number of values on the stack */
    int base;       /* +10 stack index before the first value */
    bool owns;      /* +14 pops the values when the wrapper dies */

    NsTableGet(NsTable *table, int count, bool owns);            /* 0x4277B0 */
    ~NsTableGet();                                               /* 0x427820 */
    NsFunction *FunctionAt(NsFunction *out, int position) const; /* 0x46F810 */
};
static_assert(sizeof(NsTableGet) == 0x18, "NsTableGet is 0x18 bytes");
static_assert(__builtin_offsetof(NsTableGet, base) == 0x10, "NsTableGet::base");
static_assert(__builtin_offsetof(NsTableGet, owns) == 0x14, "NsTableGet::owns");

/* A value of a TableGet read and its position (1 = the first value).  The handlers of the Lua globals build it
 * inline and turn it into a function (0x46FA90), a bool (0x437040), a number (0x547CD0) or a pointer (0x547D00). */
struct NsValueRef {
    NsTableGet *values; /* +00 */
    int position;       /* +04 */

    NsFunction *ToFunction(NsFunction *out) const; /* 0x46FA90 */
};


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
