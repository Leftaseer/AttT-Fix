/* CReadRenderInfo: the "render_info" chunk - the light record (0x4A8D70 / 0x4A90D0), the vector<RenderLight>
 * instantiations the loader links (0x4A8C00 ... 0x4A95C0), the singleton's lifetime (0x4A9480 / 0x4A94C0 /
 * 0x4A9570), the loader (0x4A9650) and the singleton accessor (0x44AE70).
 *
 * Read follows the entry table: "Enable" and "Type" (3 = directional), then for a directional light the
 * "Direction" (normalised), "Diffuse", "Ambient" and "Specular" sub-tables.  The light record is a POD copied as
 * 0x6C bytes, so the vector helpers are the plain copy/fill loops of the original's STL.
 *
 * Load runs the chunk, reads the "GlobalAmbient" colour straight from the global table and walks the "Light"
 * array with the inlined nScript::Table::i_iterator: lua_objlen counts the entries, lua_rawgeti fetches each one
 * and the loop pops them with lua_settop as it goes. */
#include "game/common.h"
#include "game/globals.h"
#include "game/lua.h"
#include "game/nscript.h"
#include "game/renderinfo.h"
#include "game/fsarchive.h"

ORIG_DATA(006100F0); /* CSingleton<CReadRenderInfo>::vftable */
ORIG_DATA(00610128); /* CReadRenderInfo::vftable */
ORIG_DATA(0061011C); /* "Enable" */
ORIG_DATA(0060C3AC); /* "Type" */
ORIG_DATA(00610110); /* "Direction" */
ORIG_DATA(00610108); /* "Diffuse" */
ORIG_DATA(00610100); /* "Ambient" */
ORIG_DATA(006100F4); /* "Specular" */
ORIG_DATA(00610144); /* "render_info" */
ORIG_DATA(00610134); /* "GlobalAmbient" */
ORIG_DATA(0061012C); /* "Light" */
ORIG_DATA(0060C044); /* nScript::Table::i_iterator::vftable */
ORIG_DATA(00607CB8); /* nScript::Object::vftable */
ORIG_DATA(00607B0C); /* std::bad_alloc::vftable */
ORIG_DATA(006990C4); /* std::bad_alloc _ThrowInfo */
ORIG_DATA(006C88D4); /* the script machine (CLuaWrapper*) */
ORIG_DATA(00607BC8); /* "Ошибка при создании m_instance в CSingleton" */
ORIG_DATA(00607E98); /* "e:\\prog\\att1\\singleton.h" */

ORIG_STDCALL(005B8074, float *, (float *out, const float *v)); /* D3DXVec3Normalize */
ORIG_THISCALL(00422000, void, (void *self));                  /* nScript::Object::~Object */

DECOMP_C void (__thiscall *imp_006073B4)(void *self, const char *const *message)
    __asm__("__imp_??0exception@std@@QAE@ABQBD@Z");

inline void *operator new(unsigned int, void *p) { return p; }

/* the overflow guard of the element allocator: a std::bad_alloc with no message, as VC8's _Allocate throws */
static void ThrowRenderLightBadAlloc()
{
    struct {
        void *vftable;    /* +00 */
        const char *what; /* +04 */
        int doFree;       /* +08 */
    } error;
    const char *message = nullptr;
    imp_006073B4(&error, &message);
    error.vftable = d_00607B0C;
    _CxxThrowException(&error, d_006990C4);
    __builtin_unreachable();
}

DECOMP(004A8C00)
unsigned __thiscall RenderLightCount(const RenderLightVector *self)
{
    if (self->begin == nullptr)
        return 0;
    return (unsigned)(self->end - self->begin);
}

DECOMP(004A8C40)
RenderLight *__cdecl AllocateRenderLights(unsigned count)
{
    if (count != 0 && 0xFFFFFFFFu / count < sizeof(RenderLight))
        ThrowRenderLightBadAlloc();
    return (RenderLight *)operator new(count * sizeof(RenderLight));
}

DECOMP(004A8CF0)
RenderLight *__cdecl FillRenderLights(RenderLight *first, RenderLight *last, const RenderLight *value)
{
    while (first != last) {
        *first = *value;
        ++first;
    }
    return first;
}

/* the fill_n of the STL: the original takes a dead EAX input besides the stack arguments */
DECOMP(004A9070)
void __cdecl FillRenderLightsRaw(unsigned eax, RenderLight *dst, unsigned count, const RenderLight *value)
{
    (void)eax;
    for (; count != 0; --count, ++dst) {
        if (dst)
            *dst = *value;
    }
}

DECOMP(004A8D40)
RenderLight *__cdecl CopyRenderLights(const RenderLight *first, const RenderLight *last, RenderLight *dst)
{
    while (first != last) {
        if (dst)
            *dst = *first;
        ++first;
        ++dst;
    }
    return dst;
}

DECOMP(004A9040)
void __cdecl CopyRenderLightsBackward(const RenderLight *first, const RenderLight *last, RenderLight *dstEnd)
{
    while (first != last) {
        --last;
        --dstEnd;
        *dstEnd = *last;
    }
}

DECOMP(004A9140)
RenderLight *__stdcall FillRenderLightsEnd(RenderLight *dst, unsigned count, const RenderLight *value)
{
    FillRenderLightsRaw((unsigned)(size_t)value, dst, count, value);
    return dst + count;
}

DECOMP(004A91B0)
RenderLight *__stdcall CopyRenderLightsEnd(const RenderLight *first, const RenderLight *last, RenderLight *dst)
{
    return CopyRenderLights(first, last, dst);
}

/* insert(count copies of value at position): grow by half (but at least past the insertion) when the capacity is
 * short, copy the tail beyond the free space first when the elements after position cannot absorb the shift, and
 * otherwise move the tail backwards; the last free slots always become the new elements. */
DECOMP(004A91E0)
void __thiscall InsertRenderLights(RenderLightVector *self, RenderLight *position, unsigned count,
                                   const RenderLight *value)
{
    if (count == 0)
        return;

    RenderLight *begin = self->begin;
    unsigned capacity = begin ? (unsigned)(self->limit - begin) : 0;
    unsigned size = begin ? (unsigned)(self->end - begin) : 0;

    if (0x25ED097u - size < count)
        ThrowVectorLengthError();

    if (capacity < size + count) {
        unsigned newCapacity = capacity + (capacity >> 1);
        if (0x25ED097u - (capacity >> 1) < capacity)
            newCapacity = 0;
        if (newCapacity < size + count)
            newCapacity = size + count;

        RenderLight *newBegin = AllocateRenderLights(newCapacity);
        RenderLight *newEnd = CopyRenderLights(begin, position, newBegin);
        newEnd = FillRenderLightsEnd(newEnd, count, value);
        CopyRenderLights(position, self->end, newEnd);
        if (begin)
            operator delete(begin);

        self->limit = newBegin + newCapacity;
        self->end = newBegin + (size + count);
        self->begin = newBegin;
        return;
    }

    RenderLight *end = self->end;
    if ((unsigned)(end - position) < count) {
        CopyRenderLightsEnd(position, end, position + count);
        FillRenderLightsEnd(self->end, count - (unsigned)(end - position), value);
        self->end += count;
        FillRenderLights(position, self->end - count, value);
        return;
    }

    self->end = CopyRenderLightsEnd(end - count, end, end);
    CopyRenderLightsBackward(position, end - count, end);
    FillRenderLights(position, position + count, value);
}

DECOMP(004A9500)
void __thiscall InsertRenderLight(RenderLightVector *self, RenderLight **result, RenderLight *position,
                                  const RenderLight *value)
{
    unsigned index = 0;
    if (self->begin && self->end != self->begin)
        index = (unsigned)(position - self->begin);
    InsertRenderLights(self, position, 1, value);
    *result = self->begin + index;
}

DECOMP(004A95C0)
void __thiscall PushRenderLight(RenderLightVector *self, const RenderLight *value)
{
    if (self->begin && (unsigned)(self->end - self->begin) < (unsigned)(self->limit - self->begin)) {
        *self->end = *value;
        ++self->end;
        return;
    }
    RenderLight *result;
    InsertRenderLight(self, &result, self->end, value);
}

/* The constructor and the destructors are the light record's own (the record is a POD): Read fills it, the ctor
 * returns this, the dtor only remembers the record and frees nothing. */
DECOMP(004A90D0)
RenderLight::RenderLight(NsTable *value, bool full)
{
    Read(value, full);
}

/* Read zeroes the D3D9 light first, so only the fields the entry lists are set.  The four sub-tables share one
 * nScript::Table temporary that takes each field table's reference in turn; the field temporary is dropped
 * right after the assignment, as in the original. */
DECOMP(004A8D70)
void RenderLight::Read(NsTable *value, bool full)
{
    __builtin_memset(&light, 0, sizeof(light));
    if (!full) {
        enabled = 1;
        light.Type = D3DLIGHT_DIRECTIONAL;
    } else {
        enabled = value->GetBool(ORIG_STR(0061011C));
        light.Type = (D3DLIGHTTYPE)(int)value->GetFloat(ORIG_STR(0060C3AC));
    }

    NsTable table;
    if (light.Type == D3DLIGHT_DIRECTIONAL) {
        {
            NsTable field;
            value->GetTable(&field, ORIG_STR(00610110));
            table = field;
        }
        float direction[3];
        direction[0] = table.GetNumber(1);
        direction[1] = table.GetNumber(2);
        direction[2] = table.GetNumber(3);
        sub_005B8074(direction, direction);
        light.Direction.x = direction[0];
        light.Direction.y = direction[1];
        light.Direction.z = direction[2];

        {
            NsTable field;
            value->GetTable(&field, ORIG_STR(00610108));
            table = field;
        }
        light.Diffuse.r = table.GetNumber(1);
        light.Diffuse.g = table.GetNumber(2);
        light.Diffuse.b = table.GetNumber(3);
        light.Diffuse.a = table.GetNumber(4);

        {
            NsTable field;
            value->GetTable(&field, ORIG_STR(00610100));
            table = field;
        }
        light.Ambient.r = table.GetNumber(1);
        light.Ambient.g = table.GetNumber(2);
        light.Ambient.b = table.GetNumber(3);
        light.Ambient.a = table.GetNumber(4);

        {
            NsTable field;
            value->GetTable(&field, ORIG_STR(006100F4));
            table = field;
        }
        light.Specular.r = table.GetNumber(1);
        light.Specular.g = table.GetNumber(2);
        light.Specular.b = table.GetNumber(3);
        light.Specular.a = table.GetNumber(4);
    }
}

/* The singleton: the ctor sets the derived vtable and the empty vector; the dtor frees the vector's buffer and
 * drops to the CSingleton vtable.  The deleting destructor inlines the same stores. */
DECOMP(004A9480)
CReadRenderInfo::CReadRenderInfo()
{
    vftable = d_00610128;
    lights.begin = nullptr;
    lights.end = nullptr;
    lights.limit = nullptr;
}

DECOMP(004A94C0)
CReadRenderInfo::~CReadRenderInfo()
{
    vftable = d_00610128;
    if (lights.begin)
        operator delete(lights.begin);
    lights.begin = nullptr;
    lights.end = nullptr;
    lights.limit = nullptr;
    vftable = d_006100F0;
}

DECOMP(004A9570)
CReadRenderInfo *__thiscall DeleteReadRenderInfo(CReadRenderInfo *info, unsigned char flags)
{
    info->~CReadRenderInfo();
    if (flags & 1)
        operator delete(info);
    return info;
}

/* The loader runs the chunk, takes the ambient colour, pushes the "Light" array's registry reference and walks
 * it with the inlined i_iterator.  The i_iterator's destructor pops the array and the last element
 * (lua_settop -3) and hands the object to its base destructor; then the three tables drop their references. */
DECOMP(004A9650)
void __cdecl LoadRenderInfo(CReadRenderInfo *self, unsigned ebx)
{
    CLuaWrapper *lua = *(CLuaWrapper **)d_006C88D4;
    lua->DoFile("render_info");

    void *L = g_luaState;

    NsTable globals(kLuaGlobalsIndex);
    NsTable ambientTable;
    NsTable lightTable;

    globals.GetTable(&ambientTable, ORIG_STR(00610134));
    self->globalAmbient[0] = ambientTable.GetNumber(1);
    self->globalAmbient[1] = ambientTable.GetNumber(2);
    self->globalAmbient[2] = ambientTable.GetNumber(3);
    self->globalAmbient[3] = ambientTable.GetNumber(4);

    globals.GetTable(&lightTable, ORIG_STR(0061012C));
    sub_00403390(L, kLuaRegistryIndex, lightTable.reference);

    NsTableIterator it;
    it.owner = nullptr;
    it.vftable = d_0060C044;
    it.count = sub_00402F40(ebx, L, -1);
    it.index = 1;
    sub_00403390(L, -1, 1);
    it.done = it.count < 1;
    while (!it.done) {
        {
            NsTable element;
            NsTable::FromStack(&element);
            RenderLight record;
            record.Read(&element, true);
            PushRenderLight(&self->lights, &record);
        }
        sub_00402A70(L, -2);
        ++it.index;
        sub_00403390(L, -1, it.index);
        it.done = it.count < it.index;
    }
    it.vftable = d_0060C044;
    sub_00402A70(L, -3);
    it.vftable = d_00607CB8;
    sub_00422000(&it);
}

DECOMP(0044AE70)
CReadRenderInfo *GetReadRenderInfo()
{
    if (!g_readRenderInfo) {
        void *memory = operator new(sizeof(CReadRenderInfo));
        g_readRenderInfo = memory ? new (memory) CReadRenderInfo() : nullptr;
        if (!g_readRenderInfo)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607E98), 16);
    }
    return g_readRenderInfo;
}
