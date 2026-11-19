/* 0x005020B0: the tactical level's action step (the level is CTacticAI+0xD8; its phase is +0x64).  A unit whose
 * action state (+0x394) is 0 or 9 is between actions.  Phase 0 (deploy): once every unit of the board vector
 * (+0x14, count +0x18) is between actions, each {unit, slot} pair (+0xE0, count +0xE4) is sent to its board slot
 * (0x00511B30) and the step reports done.  Phase 1: with the attacker army's creatures (+0xE8, +0x58/+0x5C) all
 * between actions the pending placements run, 0x00501EB0(level, 1) starts the army and the phase becomes 2; the
 * step reports not done.  Phases 2 and 3: wait for both the attacker (+0xE8) and the defender (+0xEC) army;
 * phase 2 then drops the target set (+0x11C: the tree freed through 0x004FB660 and the head relinked empty,
 * count +0x124 = 0) and reports done, phase 3 just reports done.  Phase 4 (the blow of 0x00504400 / 0x00504D70):
 * same wait, the target set dropped and the defender army's +0xB8 marked once, then done.  Other phases report
 * not done. */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { void *unit; int slot; } Place_5020B0;          /* the 8-byte entries at +0xE0 */

DECOMP_C void __thiscall sub_004FB660(void *container, void *node);
DECOMP_C void __thiscall sub_00511B30(void *self, int slot);
DECOMP_C void __thiscall sub_00501EB0(void *self, int a);

/* the unit has no action running */
static int idle_5020B0(void *unit)
{
    int state = *(int *)((char *)unit + 0x394);
    return state == 0 || state == 9;
}

/* every unit of the board vector (+0x14, count +0x18) is between actions */
static int board_idle_5020B0(char *lvl)
{
    void **board = *(void ***)(lvl + 0x14);
    int i;

    for (i = 0; i < *(int *)(lvl + 0x18); i++)
        if (!idle_5020B0(board[i]))
            return 0;
    return 1;
}

/* every creature of a troop (+0x58, count +0x5C) is between actions */
static int troop_idle_5020B0(char *troop)
{
    void **creatures = *(void ***)(troop + 0x58);
    int i;

    for (i = 0; i < *(int *)(troop + 0x5c); i++)
        if (!idle_5020B0(creatures[i]))
            return 0;
    return 1;
}

/* every pending {unit, slot} pair to its board slot */
static void place_5020B0(char *lvl)
{
    Place_5020B0 *p = *(Place_5020B0 **)(lvl + 0xe0);
    int i;

    for (i = 0; i < *(int *)(lvl + 0xe4); i++)
        sub_00511B30(p[i].unit, p[i].slot);
}

/* the target tree at +0x11C freed and its head node relinked as an empty list (count +0x124 = 0) */
static void clear_targets_5020B0(char *lvl)
{
    char *head = *(char **)(lvl + 0x120);

    sub_004FB660(lvl + 0x11c, *(void **)(head + 4));
    head = *(char **)(lvl + 0x120);
    *(unsigned int *)(head + 4) = (unsigned int)head;
    *(unsigned int *)(lvl + 0x124) = 0;
    *(unsigned int *)head = (unsigned int)head;
    *(unsigned int *)(*(char **)(lvl + 0x120) + 8) = *(unsigned int *)(lvl + 0x120);
}

DECOMP(005020B0)
int __thiscall f_005020B0(void *this)
{
    char *lvl = (char *)this;

    switch (*(int *)(lvl + 0x64)) {
    case 0:
        if (!board_idle_5020B0(lvl))
            return 0;
        place_5020B0(lvl);
        return 1;
    case 1:
        if (!troop_idle_5020B0(*(char **)(lvl + 0xe8)))
            return 0;
        place_5020B0(lvl);
        sub_00501EB0(lvl, 1);
        *(int *)(lvl + 0x64) = 2;
        return 0;
    case 2:
        if (!troop_idle_5020B0(*(char **)(lvl + 0xe8)) || !troop_idle_5020B0(*(char **)(lvl + 0xec)))
            return 0;
        clear_targets_5020B0(lvl);
        return 1;
    case 3:
        if (!troop_idle_5020B0(*(char **)(lvl + 0xe8)) || !troop_idle_5020B0(*(char **)(lvl + 0xec)))
            return 0;
        return 1;
    case 4:
        if (!troop_idle_5020B0(*(char **)(lvl + 0xe8)) || !troop_idle_5020B0(*(char **)(lvl + 0xec)))
            return 0;
        clear_targets_5020B0(lvl);
        {
            char *defender = *(char **)(lvl + 0xec);
            if (!defender[0xb8])
                defender[0xb8] = 1;
        }
        return 1;
    }
    return 0;
}
