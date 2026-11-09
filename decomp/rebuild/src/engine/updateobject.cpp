/* CUpdateObject: the updatable base of the engine's object tree, its construction (0x424D00). */
#include "game/common.h"
#include "game/engine.h"

ORIG_DATA(00607D5C);   /* CUpdateObject::vftable */
ORIG_DATA(00607D54);   /* float: 33.33 ms between the fixed updates */

/* The name is copied into the object and a parent is told about the new child through the third vtable slot (a
 * nullsub in the base vtable of this build). */
DECOMP(00424D00)
CUpdateObject::CUpdateObject(const std::string &name, CUpdateObject *parent) : name(name)
{
    link = nullptr;
    vftable = d_00607D5C;
    interval = ORIG_VAR(00607D54, float);
    this->parent = parent;
    next = nullptr;
    accumulator = 0.0f;
    attached = false;
    if (parent)
        ((void (__thiscall *)(CUpdateObject *, CUpdateObject *))((void **)parent->vftable)[2])(parent, this);
}
