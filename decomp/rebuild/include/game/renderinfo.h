/* CReadRenderInfo: the data of the "render_info" Lua chunk.  The loader (0x4A9650) runs the chunk, takes the
 * "GlobalAmbient" colour and walks the "Light" array: every entry is a RenderLight (0x6C bytes: the enabled flag,
 * then the D3D9 light) that Read (0x4A8D70) fills from the entry's table.  The array is one MSVC 8 vector at
 * +0x14 of the singleton (0x44AE70), whose element operations are the instantiations 0x4A8C00 ... 0x4A95C0. */
#pragma once
#include "game/common.h"
#include "game/nscript.h"

/* One "Light" entry: the flag and the light the entry's table describes.  Read fills the light with D3DLIGHT9
 * fields from the "Type" (3 = directional), "Direction", "Diffuse", "Ambient" and "Specular" fields; with
 * full=false it takes the default Enable/Type of a directional light, but still reads the four fields. */
struct RenderLight {
    unsigned char enabled; /* +00 */
    D3DLIGHT9 light;       /* +04 */

    RenderLight() {}                        /* the loader's stack record: Read fills it */
    RenderLight(NsTable *value, bool full); /* 0x4A90D0: Read, returns this in EAX */
    void Read(NsTable *value, bool full);   /* 0x4A8D70 */
};
static_assert(sizeof(RenderLight) == 0x6C, "RenderLight is 0x6C bytes");
static_assert(__builtin_offsetof(RenderLight, light) == 0x04, "RenderLight::light");
static_assert(__builtin_offsetof(RenderLight, light.Type) == 0x04, "RenderLight::light.Type");
static_assert(__builtin_offsetof(RenderLight, light.Diffuse) == 0x08, "RenderLight::light.Diffuse");
static_assert(__builtin_offsetof(RenderLight, light.Ambient) == 0x28, "RenderLight::light.Ambient");
static_assert(__builtin_offsetof(RenderLight, light.Direction) == 0x44, "RenderLight::light.Direction");

/* std::vector<RenderLight>: the MSVC 8 layout (the empty allocator, begin, end, limit). */
struct RenderLightVector {
    unsigned char allocator[4]; /* +00 */
    RenderLight *begin;         /* +04 */
    RenderLight *end;           /* +08 */
    RenderLight *limit;         /* +0C */
};
static_assert(sizeof(RenderLightVector) == 0x10, "RenderLightVector is 0x10 bytes");
static_assert(__builtin_offsetof(RenderLightVector, begin) == 0x04, "RenderLightVector::begin");
static_assert(__builtin_offsetof(RenderLightVector, end) == 0x08, "RenderLightVector::end");
static_assert(__builtin_offsetof(RenderLightVector, limit) == 0x0C, "RenderLightVector::limit");

struct CReadRenderInfo {
    void *vftable;            /* +00 CSingleton<CReadRenderInfo> */
    float globalAmbient[4];   /* +04 the "GlobalAmbient" RGBA */
    RenderLightVector lights; /* +14 the "Light" entries */

    CReadRenderInfo();  /* 0x4A9480 */
    ~CReadRenderInfo(); /* 0x4A94C0 */
};
static_assert(sizeof(CReadRenderInfo) == 0x24, "CReadRenderInfo is 0x24 bytes");
static_assert(__builtin_offsetof(CReadRenderInfo, globalAmbient) == 0x04, "CReadRenderInfo::globalAmbient");
static_assert(__builtin_offsetof(CReadRenderInfo, lights) == 0x14, "CReadRenderInfo::lights");

/* the vector<RenderLight> instantiations of the original (the element is copied as 0x6C bytes) */
unsigned __thiscall RenderLightCount(const RenderLightVector *self);                          /* 0x4A8C00 */
RenderLight *__cdecl AllocateRenderLights(unsigned count);                                    /* 0x4A8C40 */
RenderLight *__cdecl FillRenderLights(RenderLight *first, RenderLight *last,
                                      const RenderLight *value);                              /* 0x4A8CF0 */
void __cdecl FillRenderLightsRaw(unsigned eax, RenderLight *dst, unsigned count,
                                 const RenderLight *value);                                   /* 0x4A9070 */
RenderLight *__cdecl CopyRenderLights(const RenderLight *first, const RenderLight *last,
                                      RenderLight *dst);                                      /* 0x4A8D40 */
void __cdecl CopyRenderLightsBackward(const RenderLight *first, const RenderLight *last,
                                      RenderLight *dstEnd);                                   /* 0x4A9040 */
RenderLight *__stdcall FillRenderLightsEnd(RenderLight *dst, unsigned count,
                                           const RenderLight *value);                         /* 0x4A9140 */
RenderLight *__stdcall CopyRenderLightsEnd(const RenderLight *first, const RenderLight *last,
                                           RenderLight *dst);                                 /* 0x4A91B0 */
void __thiscall InsertRenderLights(RenderLightVector *self, RenderLight *position, unsigned count,
                                   const RenderLight *value);                                 /* 0x4A91E0 */
void __thiscall InsertRenderLight(RenderLightVector *self, RenderLight **result, RenderLight *position,
                                  const RenderLight *value);                                  /* 0x4A9500 */
void __thiscall PushRenderLight(RenderLightVector *self, const RenderLight *value);           /* 0x4A95C0 */

/* the deleting destructor behind the singleton vtable slot 0 */
CReadRenderInfo *__thiscall DeleteReadRenderInfo(CReadRenderInfo *info, unsigned char flags); /* 0x4A9570 */

/* runs "render_info" and fills the singleton.  The original takes EBX as well (the Lua calls below hand it on),
 * so the replacement names it after the this in ECX. */
void __cdecl LoadRenderInfo(CReadRenderInfo *self, unsigned ebx);                             /* 0x4A9650 */

/* CSingleton<CReadRenderInfo>::Instance */
CReadRenderInfo *__cdecl GetReadRenderInfo();                                                 /* 0x44AE70 */
