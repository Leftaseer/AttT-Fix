/* CUpdateObject: the updatable base of the engine's object tree, its construction (0x424D00) and its frame update
 * (0x424D90). */
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

/* The elapsed time accumulates and every full interval runs one fixed Tick; the number of the steps of this frame
 * then goes to the ninth slot (a no-op in every vtable of this build).  The original callers reach the entry with
 * the this pointer in ECX and an unused EAX, so the replacement names the registers first (cdecl). */
DECOMP(00424D90)
void UpdateObjectFrame(CUpdateObject *self, void *unusedEax, float dt)
{
    (void)unusedEax;
    self->accumulator += dt;
    if (self->accumulator < self->interval)
        return;
    int steps = 0;
    do {
        self->Tick();
        self->accumulator -= self->interval;
        steps++;
    } while (self->accumulator >= self->interval);
    self->StepsDone(steps);
}
