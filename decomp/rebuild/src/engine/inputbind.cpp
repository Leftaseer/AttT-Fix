/* CInput's key bindings: the command table at +0x6BC holds one CInputBinding per command, the bucket map at
 * +0x690 names the commands and stores the command id of a name in the map node at +24.  A binding's sequence
 * starts with one key code; reading the configuration replaces it (0x46ED10 / 0x46EDC0), clearing blanks every
 * binding (0x46CF80) and the lookup gives the command id of a name (0x46F480). */
#include "game/common.h"
#include "game/engine.h"
#include "game/filesystem.h"

/* a node of the command map: the string key at +08 and the command id after it */
struct CInputCommandNode : FsStringNode {
    int command;                             /* +24 */
};
static_assert(__builtin_offsetof(CInputCommandNode, command) == 0x24, "CInputCommandNode::command");

static FsHashMap *CommandMap(CInput *input)
{
    return (FsHashMap *)input->bindingMap;
}

/* 0x46CF80: every binding becomes the sequence of the single terminator byte 0 (length 1). */
DECOMP(0046CF80)
void CInput::ClearBindings()
{
    for (int i = 0; i < bindingCount; i++) {
        CInputBinding &binding = bindings[i];
        binding.length = 0;
        binding.sequence[binding.length] = 0;
        binding.length++;
    }
}

/* 0x46ED10: the name is lowercased and looked up, and the command's sequence is replaced by the one code. */
DECOMP(0046ED10)
void CInput::SetBinding(const std::string &name, unsigned char code)
{
    std::string lower;
    LowercaseCopy(&name, &lower);
    FsStringNode *node;
    CommandMap(this)->FindName(&node, &lower);
    CInputBinding &binding = bindings[((CInputCommandNode *)node)->command];
    binding.length = 0;
    binding.sequence[binding.length] = (char)code;
    binding.length++;
}

/* 0x46EDC0: like SetBinding, but the code comes from a DIK name ("space", "up", ...) that is lowercased first. */
DECOMP(0046EDC0)
void CInput::SetBindingByName(const std::string &name, const std::string &keyName)
{
    std::string lower;
    LowercaseCopy(&name, &lower);
    FsStringNode *node;
    CommandMap(this)->FindName(&node, &lower);
    CInputBinding &binding = bindings[((CInputCommandNode *)node)->command];
    binding.length = 0;
    LowercaseCopy(&keyName, &lower);
    binding.sequence[binding.length] = (char)KeyCodeFromName(lower);
    binding.length++;
}

/* 0x46F480: the command id of a name (both lowercased), 0 when the name is not bound. */
DECOMP(0046F480)
int CInput::BindingCommand(const std::string &name)
{
    std::string lower;
    LowercaseCopy(&name, &lower);
    FsHashMap *map = CommandMap(this);
    FsStringNode *node;
    map->FindName(&node, &lower);
    if (node == (FsStringNode *)map->sentinel)
        return 0;
    return ((CInputCommandNode *)node)->command;
}
