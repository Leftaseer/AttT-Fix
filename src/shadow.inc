// ---------------------------------------------------------------- 12) world shadows: resolution and filtering (1.2.2)
// Included into attfix.cpp after instance.inc.
//
// The sun shadows of objects on the world map are a projected texture owned by the level's sky/clouds object
// (serializer 0x527DF0: sName, dwLevel, fCloudsSpeed, dwShadowTexSize at +0x2D4 = 1024 in the level data): the objects
// are drawn as flat grey silhouettes from the sun (objectstoshadow.ef / unittoshadow.ef) into ONE R5G6B5 render
// target of dwShadowTexSize (engine texture +0x27C, ID3DXRenderToSurface +0x2C0, full-surface viewport; created at
// 0x52919D, re-created after a device reset at 0x52A47A), which cm_shadow.ef then projects onto the ground with
// TextureTransform[0] = mShadow and a reverse-subtract blend. (ChoosePlaneShadow, 0x58E6E0, has a 1024 target of
// its own but is not used on the map.) Spread over the visible area 1024 texels
// make blocky shadows that crawl as the sun moves, and cm_shadow.ef sets no sampler filter, so the projection uses
// whatever stage 0 had (often POINT: hard texel blocks).
//  - [Video] ShadowSize: before the texture is created (0x52919D) dwShadowTexSize is raised to this size (a stub
//    in place of "mov ecx,[esi+2D4h]"); the render-to-surface and the restore path read the same field. Clamped to
//    the device maximum.
//  - while that texture is bound to stage 0, MIN/MAG filters are LINEAR (restored when another texture is bound).
static int g_shadowProj = 0;                    // [Video] ShadowProjection (see below; experimental, off)
static float g_shV[16], g_shP[16]; static DWORD g_shCamFrame = 0xFFFFFFFF, g_shProjFrame = 0xFFFFFFFF;
static bool g_shTci = false; static DWORD g_shOldTci = 0, g_shOldTtf = 0;
static DWORD g_shProjN = 0, g_shProjSkip = 0;
static DWORD g_shCapBefore = 0, g_shCapAfter = 0, g_shCapNone = 0; static DWORD g_shMsFrames;
static int g_shadowSize = 4096;                 // [Video] ShadowSize (1024 = original)
// Shadow casters are picked per frame by cells (0x4B6B20: cell near the camera ([+0x98] radius) and its box inside
// the frustum 0x435B00(), 0x458120) and then per object (0x4B6D70 -> 0x58EB50: the object's box against the frustum
// [0x6CA2C8]). A building whose shadow is on screen but which itself is not in that frustum lost its shadow (shadows
// blinked / vanished when the hero walked into them). [Video] ShadowCasterCull=0: the two frustum tests of
// buildings pass (the cell radius stays); units (0x4B6C4C) are left as they are. The game's own "every object" path
// (0x4B6880, level flag +0x3AD) is NOT usable: its list holds no buildings.
static int g_shadowCull = 0;
static int g_unitShadowSize = 1024;             // [Video] UnitShadowSize (256 = original)
static void* g_shTex[8]; static int g_shTexN = 0;
static bool g_shFilt = false; static DWORD g_shOldMin = 0, g_shOldMag = 0;
static DWORD g_shBinds = 0, g_shFixed = 0;
typedef HRESULT (__stdcall *CreateTex_t)(void*, UINT, UINT, UINT, DWORD, DWORD, DWORD, void**, HANDLE*);
typedef HRESULT (__stdcall *SetTex_t)(void*, DWORD, void*);
static CreateTex_t o_ShCreateTex = nullptr; static SetTex_t o_ShSetTex = nullptr;
static HRESULT __stdcall h_ShCreateTex(void* dev, UINT w, UINT h, UINT lv, DWORD usage, DWORD fmt, DWORD pool, void** out, HANDLE* sh) {
    void* ret = __builtin_return_address(0);
    UINT lv2 = MipCreateLevels(ret, w, h, lv, usage, fmt, pool);
    HRESULT hr = o_ShCreateTex(dev, w, h, lv2, usage, fmt, pool, out, sh);
    if (hr < 0 && lv2 != lv) { lv2 = lv; hr = o_ShCreateTex(dev, w, h, lv, usage, fmt, pool, out, sh); }
    if (hr >= 0) { MipNoteCreate(ret, w, h, lv2, usage, fmt, pool); if (lv2 != lv && pool == 2 && out && *out) MipTrackSys(*out); }
    bool unitSh = g_unitShadowSize > 256 && w == (UINT)g_unitShadowSize && h == w && fmt != 0x17;
    if (hr >= 0 && out && *out && (usage & 1 /*RENDERTARGET*/) && ((fmt == 0x17 /*R5G6B5*/ && w == h && w >= (UINT)g_shadowSize) || unitSh)) {
        if (g_shTexN < 8) g_shTex[g_shTexN++] = *out; else g_shTex[7] = *out;
        LOG("shadows: shadow texture %ux%u created (%p)", w, h, *out);
    }
    return hr;
}
static inline bool IsShadowTex(void* t) { for (int i = 0; i < g_shTexN; ++i) if (g_shTex[i] == t) return true; return false; }
static HRESULT __stdcall h_ShSetTex(void* dev, DWORD stage, void* tex) {
    HRESULT hr = o_ShSetTex(dev, stage, tex);
    if (stage == 0 && g_shTexN) {
        typedef HRESULT (__stdcall *GSS_t)(void*, DWORD, DWORD, DWORD*);
        typedef HRESULT (__stdcall *SSS_t)(void*, DWORD, DWORD, DWORD);
        void** vt = *(void***)dev;
        if (tex && IsShadowTex(tex)) {
            ++g_shBinds;
            if (!g_shTci && g_shProjFrame == g_curFrame) {          // mShadow is the camera-space projection this frame
                ((GSS_t)vt[66])(dev, 0, 11 /*TEXCOORDINDEX*/, &g_shOldTci); ((GSS_t)vt[66])(dev, 0, 24 /*TEXTURETRANSFORMFLAGS*/, &g_shOldTtf);
                ((SSS_t)vt[67])(dev, 0, 11, 0x00020000 /*CAMERASPACEPOSITION*/); ((SSS_t)vt[67])(dev, 0, 24, 2 /*COUNT2*/);
                g_shTci = true;
            }
            if (!g_shFilt) {
                ((GSS_t)vt[68])(dev, 0, 6 /*MAGFILTER*/, &g_shOldMag); ((GSS_t)vt[68])(dev, 0, 5 /*MINFILTER*/, &g_shOldMin);
                if (g_shOldMag != 2 || g_shOldMin != 2) {
                    ((SSS_t)vt[69])(dev, 0, 6, 2 /*LINEAR*/); ((SSS_t)vt[69])(dev, 0, 5, 2); ++g_shFixed;
                }
                g_shFilt = true;
            }
        } else if (g_shFilt || g_shTci) {
            if (g_shTci) { g_shTci = false; ((SSS_t)vt[67])(dev, 0, 11, g_shOldTci); ((SSS_t)vt[67])(dev, 0, 24, g_shOldTtf); }
            if (!g_shFilt) return hr;
            g_shFilt = false;
            if (g_shOldMag != 2 || g_shOldMin != 2) { ((SSS_t)vt[69])(dev, 0, 6, g_shOldMag); ((SSS_t)vt[69])(dev, 0, 5, g_shOldMin); }
        }
    }
    return hr;
}
static void InstallShadowProjection(); static void ShadowMsaaRelease(); static void InstallShadowMsaa();
// ---- shadow-aware caster culling (ShadowCasterCull=0)
// The game draws a shadow caster only if its box (8 world-space corners) is inside the camera frustum, so a building
// just off screen lost the shadow it throws onto the screen (shadows vanished when the hero walked into them). 1.3
// simply drew every caster near the camera - on a slow CPU about a third of the frame (hundreds of extra draws).
// Now the box is tested together with its shadow: the 8 corners plus the same corners moved along the sun's direction
// (device light 0, as the shadow pass uses) down to the base of the box, horizontally at most 4000 units. A caster is
// drawn when, for each of the 6 frustum planes, one of the 16 points is in front of it (the same rule as 0x458120).
static float g_shL[3]; static DWORD g_shLFrame = 0xFFFFFFFF; static bool g_shLOk = false;
static DWORD g_shCullIn = 0, g_shCullOut = 0;
static void ShLight() {
    if (g_shLFrame == g_curFrame) return;
    g_shLFrame = g_curFrame; g_shLOk = false;
    void* dev = *(void**)0x006C8C10; if (!dev) return;
    BYTE l[104] = {};
    if (((HRESULT (__stdcall*)(void*, DWORD, void*))(*(void***)dev)[52])(dev, 0, l) < 0) return;   // GetLight(0)
    const float* d = (const float*)(l + 0x40);                                                       // D3DLIGHT9.Direction
    float len = sqrtf(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    if (len < 1e-6f || d[1] > -0.02f * len) return;   // sun at or below the horizon: box only
    g_shL[0] = d[0] / len; g_shL[1] = d[1] / len; g_shL[2] = d[2] / len; g_shLOk = true;
}
static bool ShadowBoxVisible(const float* fr, const float* c) {
    float p[16][3]; int n = 8;
    memcpy(p, c, sizeof(float) * 24);
    ShLight();
    if (g_shLOk) {
        float miny = c[1]; for (int i = 1; i < 8; ++i) if (c[i * 3 + 1] < miny) miny = c[i * 3 + 1];
        float hl = sqrtf(g_shL[0] * g_shL[0] + g_shL[2] * g_shL[2]);
        float tmax = hl > 1e-4f ? 4000.0f / hl : 1e9f;
        for (int i = 0; i < 8; ++i) {
            float t = (c[i * 3 + 1] - (miny - 20.0f)) / -g_shL[1]; if (t > tmax) t = tmax; if (t < 0) t = 0;
            for (int k = 0; k < 3; ++k) p[8 + i][k] = c[i * 3 + k] + g_shL[k] * t;
        }
        n = 16;
    }
    const float* pl = fr + 1;                           // 6 planes (a, b, c, d) at frustum + 4
    for (int k = 0; k < 6; ++k, pl += 4) {
        bool in = false;
        for (int i = 0; i < n && !in; ++i) in = pl[0] * p[i][0] + pl[1] * p[i][1] + pl[2] * p[i][2] + pl[3] > 0.0f;
        if (!in) { ++g_shCullOut; return false; }
    }
    ++g_shCullIn; return true;
}
static bool __attribute__((thiscall)) h_CullCell(const float* frustum, const float* corners) { return ShadowBoxVisible(frustum, corners); }
static bool __attribute__((thiscall)) h_CullObj(const BYTE* obj) { return ShadowBoxVisible(*(const float**)0x006CA2C8, (const float*)(obj + 0x244)); }
static void ShadowDeviceReset() { g_shTexN = 0; g_shFilt = false; g_shTci = false; ShadowMsaaRelease(); }   // textures are re-created after a reset
static void ShadowDeviceHooks(void* dev) {
    if (g_shadowSize <= 0) return;
    BYTE caps[512]; memset(caps, 0, sizeof caps);
    UINT maxW = 4096, maxH = 4096;
    if (((HRESULT (__stdcall*)(void*, void*))(*(void***)dev)[7])(dev, caps) >= 0) { maxW = *(DWORD*)(caps + 0x58); maxH = *(DWORD*)(caps + 0x5C); }
    int sz = g_shadowSize, lim = (int)(maxW < maxH ? maxW : maxH);
    if (sz > lim && lim >= 1024) sz = lim;
    int p2 = 1024; while (p2 * 2 <= sz) p2 *= 2;                 // power of two, at least the original 1024
    g_shadowSize = p2;
    static bool patched = false;
    if (!patched) {
        patched = true;
        static DWORD target; target = (DWORD)g_shadowSize;
        BYTE* at = (BYTE*)0x0052919D;
        if (memcmp(at, "\x8B\x8E\xD4\x02\x00\x00\x6A\x00\x6A\x17", 10) || memcmp((void*)0x0052A47A, "\x8B\x86\xD4\x02\x00\x00", 6)) {
            LOG("shadows: unexpected code, shadow size not changed"); g_shadowSize = 1024;
        } else if (g_shadowSize != 1024) {
            BYTE* st = (BYTE*)VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
            if (st) {
                BYTE c[] = { 0x50,                                   // push eax (the new texture object)
                             0xA1, 0, 0, 0, 0,                       // mov eax, [target]
                             0x3B, 0x86, 0xD4, 0x02, 0x00, 0x00,     // cmp eax, [esi+2D4h]
                             0x76, 0x06,                             // jbe +6 (never smaller than the level's own)
                             0x89, 0x86, 0xD4, 0x02, 0x00, 0x00,     // mov [esi+2D4h], eax
                             0x58,                                   // pop eax
                             0x8B, 0x8E, 0xD4, 0x02, 0x00, 0x00,     // mov ecx, [esi+2D4h]   (the replaced instruction)
                             0x68, 0xA3, 0x91, 0x52, 0x00,           // push 0x5291A3
                             0xC3 };                                 // ret
                *(DWORD*)(c + 2) = (DWORD)&target;
                memcpy(st, c, sizeof c); FlushInstructionCache(GetCurrentProcess(), st, sizeof c);
                BYTE j[6] = { 0xE9, 0, 0, 0, 0, 0x90 }; *(DWORD*)(j + 1) = (DWORD)st - (DWORD)(at + 5);
                PatchBytes(at, j, 6);
            } else { LOG("shadows: stub allocation failed"); g_shadowSize = 1024; }
        }
    }
    static bool cullPatched = false;
    if (!cullPatched && !g_shadowCull) {
        cullPatched = true;
        // the four frustum tests of shadow casters call our shadow-aware tests instead (same calling conventions:
        // 0x458120 thiscall(frustum, corners) ret 4; 0x58EB50 thiscall(object))
        static const struct { DWORD at, to; void* fn; } cs[4] = {
            { 0x004B6BC5, 0x00458120, (void*)h_CullCell }, { 0x004B6BEF, 0x00458120, (void*)h_CullCell },
            { 0x004B6DA8, 0x0058EB50, (void*)h_CullObj },  { 0x004B6DE6, 0x0058EB50, (void*)h_CullObj } };
        bool ok = true;
        for (auto& c : cs) if (*(BYTE*)c.at != 0xE8 || c.at + 5 + *(int*)(c.at + 1) != c.to) ok = false;
        if (ok) {
            for (auto& c : cs) { BYTE j[5] = { 0xE8 }; *(int*)(j + 1) = (int)((DWORD)c.fn - (c.at + 5)); PatchBytes((void*)c.at, j, 5); }
            LOG("shadows: shadow casters culled together with their shadow (ShadowCasterCull=0)");
        } else LOG("shadows: unexpected code, caster culling unchanged");
    }
    // unit shadows (CUnitShadow): one 256x256 render target, re-used per unit
    static bool unitPatched = false;
    if (!unitPatched && g_unitShadowSize > 256) {
        unitPatched = true;
        int us = 256; while (us * 2 <= g_unitShadowSize && us * 2 <= lim) us *= 2;
        static const DWORD ua[6] = { 0x004EC793, 0x004EC798, 0x004EC7C4, 0x004EC7C9, 0x004ECF43, 0x004ECF48 };
        bool ok = true; for (DWORD a : ua) if (memcmp((void*)a, "\x68\x00\x01\x00\x00", 5)) ok = false;
        if (ok) { DWORD v = (DWORD)us; for (DWORD a : ua) PatchBytes((void*)(a + 1), &v, 4); g_unitShadowSize = us; LOG("shadows: unit shadow texture %dx%d (original 256)", us, us); }
        else { g_unitShadowSize = 256; LOG("shadows: unexpected code, unit shadow size unchanged"); }
    }
    static bool projInstalled = false;
    if (!projInstalled) { projInstalled = true; InstallShadowProjection(); InstallShadowMsaa(); }
    if (!o_ShSetTex) {
        void** vt = *(void***)dev;
        o_ShCreateTex = (CreateTex_t)PatchVtbl(vt, 23, (void*)h_ShCreateTex);
        o_ShSetTex = (SetTex_t)PatchVtbl(vt, 65, (void*)h_ShSetTex);
    }
    LOG("shadows: world shadow texture at least %dx%d (level data: 1024; device max %ux%u), linear filtering", g_shadowSize, g_shadowSize, maxW, maxH);
}
static void ShadowStats() {
    if (g_shCullIn + g_shCullOut) PLOG("SHADOWS casters (cells + objects) drawn %lu, culled %lu (with their shadow, ShadowCasterCull=0)", g_shCullIn, g_shCullOut);
    g_shCullIn = g_shCullOut = 0;
    if (g_shBinds) PLOG("SHADOWS size=%d: shadow texture binds=%lu filter set to linear=%lu | projection from the sun camera=%lu (game formula kept %lu; sun camera found before %lu / after %lu / not %lu) msaa frames=%lu", g_shadowSize, g_shBinds, g_shFixed, g_shProjN, g_shProjSkip, g_shCapBefore, g_shCapAfter, g_shCapNone, g_shMsFrames);
    g_shBinds = g_shFixed = 0; g_shProjN = g_shProjSkip = 0; g_shCapBefore = g_shCapAfter = g_shCapNone = 0; g_shMsFrames = 0;
}

// ---- exact projection of the map shadow (ShadowProjection=1)
// The shadow texture is rendered by an orthographic camera looking from the sun (eye = cell centre - D*2000, its
// height kept >= 1414), but the continent's shadow pass (continent*.ef P4: Texture[0] = tShadow,
// TextureTransform[0] = mShadow on the ground's own UVs) maps it with a planar formula (cell offset, scale,
// rotation by the sun azimuth, 0x529DAC) that does not follow that camera: as the sun moved the shadows slid
// against it and jumped back. Here the shadow camera's view and projection are taken while the casters are drawn
// (call 0x4B6E70 at 0x52818E), mShadow is replaced (SetMatrix at 0x52A04A) by
//   inverse(main view) * shadow view * shadow projection * texture bias
// and while the shadow texture is bound to stage 0 the ground's texture coordinates are its camera-space position
// (TEXCOORDINDEX = CAMERASPACEPOSITION, TEXTURETRANSFORMFLAGS = COUNT2) - the usual projective texturing.
static void Mat4Mul(const float* a, const float* b, float* o) {
    for (int r = 0; r < 4; ++r) for (int c = 0; c < 4; ++c) { float s = 0; for (int k = 0; k < 4; ++k) s += a[r * 4 + k] * b[k * 4 + c]; o[r * 4 + c] = s; }
}
static bool Mat4InvAffine(const float* m, float* o) {   // view matrices: rotation (orthonormal or scaled) + translation
    float a = m[0], b = m[1], c = m[2], d = m[4], e = m[5], f = m[6], g = m[8], h = m[9], i = m[10];
    float det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
    if (fabsf(det) < 1e-12f) return false;
    float id = 1.0f / det;
    float r[9] = { (e * i - f * h) * id, (c * h - b * i) * id, (b * f - c * e) * id,
                   (f * g - d * i) * id, (a * i - c * g) * id, (c * d - a * f) * id,
                   (d * h - e * g) * id, (b * g - a * h) * id, (a * e - b * d) * id };
    o[0] = r[0]; o[1] = r[1]; o[2] = r[2]; o[3] = 0; o[4] = r[3]; o[5] = r[4]; o[6] = r[5]; o[7] = 0; o[8] = r[6]; o[9] = r[7]; o[10] = r[8]; o[11] = 0;
    float tx = m[12], ty = m[13], tz = m[14];
    o[12] = -(tx * r[0] + ty * r[3] + tz * r[6]); o[13] = -(tx * r[1] + ty * r[4] + tz * r[7]); o[14] = -(tx * r[2] + ty * r[5] + tz * r[8]); o[15] = 1;
    return true;
}
typedef HRESULT (__stdcall *GetXf_t)(void*, DWORD, float*);
static void __fastcall h_ShCasters(void* self, void*) {                // 0x4B6E70 (thiscall, no stack arguments)
    // the casters are drawn with the sun camera's VIEW / PROJECTION on the device; they may be set only by the first
    // caster draw, so they are read before and (if not orthographic yet) after the call
    void* dev = *pDevice;
    GetXf_t gx = dev ? (GetXf_t)(*(void***)dev)[45] : nullptr;
    bool ok = false;
    if (gx) { gx(dev, 2, g_shV); gx(dev, 3, g_shP); ok = fabsf(g_shP[11]) < 1e-6f && fabsf(g_shP[15] - 1.0f) < 1e-4f; if (ok) ++g_shCapBefore; }
    ((void (__fastcall*)(void*, void*))0x004B6E70)(self, nullptr);
    if (!ok && gx) { gx(dev, 2, g_shV); gx(dev, 3, g_shP); ok = fabsf(g_shP[11]) < 1e-6f && fabsf(g_shP[15] - 1.0f) < 1e-4f; if (ok) ++g_shCapAfter; }
    if (ok) g_shCamFrame = g_curFrame;
    else {
        ++g_shCapNone;
        static int logged = 0;
        if (logged < 3) { ++logged; LOG("shadows: sun camera projection not found on the device (P: %.3f %.3f %.3f %.3f / %.3f %.3f %.3f %.3f)",
                                        g_shP[0], g_shP[5], g_shP[10], g_shP[11], g_shP[12], g_shP[13], g_shP[14], g_shP[15]); }
    }
}
static void __cdecl ShSetMShadow(float* m) {                            // from the stub at 0x52A04A: m = the game's mShadow
    if (!g_shadowProj || g_shCamFrame != g_curFrame) { ++g_shProjSkip; return; }
    void* dev = *pDevice; if (!dev) return;
    float V[16], Vi[16], T[16], T2[16];
    ((GetXf_t)(*(void***)dev)[45])(dev, 2, V);
    if (!memcmp(V, g_shV, sizeof V) || !Mat4InvAffine(V, Vi)) { ++g_shProjSkip; return; }
    float h = 0.5f / (float)(g_shadowSize > 0 ? g_shadowSize : 1024);
    const float B[16] = { 0.5f, 0, 0, 0,  0, -0.5f, 0, 0,  0, 0, 1, 0,  0.5f + h, 0.5f + h, 0, 1 };
    Mat4Mul(Vi, g_shV, T); Mat4Mul(T, g_shP, T2); Mat4Mul(T2, B, m);
    g_shProjFrame = g_curFrame; ++g_shProjN;
}
static void InstallShadowProjection() {
    if (!g_shadowProj) return;
    BYTE* c1 = (BYTE*)0x0052818E; BYTE* c2 = (BYTE*)0x0052A04A;
    if (memcmp((void*)0x00528188, "\x8B\x8E\x74\x02\x00\x00\xE8", 7) || (DWORD)c1 + 5 + *(int*)(c1 + 1) != 0x004B6E70 ||
        memcmp(c2, "\x8B\x4B\x3C\x8B\x11\x8B\x42\x50\x55\x68\xE4\x2B\x61\x00", 14)) {
        g_shadowProj = 0; LOG("shadows: unexpected code, shadow projection unchanged"); return;
    }
    BYTE* st = (BYTE*)VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!st) { g_shadowProj = 0; return; }
    BYTE s[] = { 0x60,                                   // pushad
                 0x55,                                   // push ebp (the matrix)
                 0xE8, 0, 0, 0, 0,                       // call ShSetMShadow
                 0x83, 0xC4, 0x04,                       // add esp, 4
                 0x61,                                   // popad
                 0x8B, 0x4B, 0x3C, 0x8B, 0x11,           // mov ecx,[ebx+3Ch] / mov edx,[ecx]   (replaced)
                 0x68, 0x4F, 0xA0, 0x52, 0x00, 0xC3 };   // push 0x52A04F / ret
    *(DWORD*)(s + 3) = (DWORD)(void*)ShSetMShadow - (DWORD)(st + 7);
    memcpy(st, s, sizeof s); FlushInstructionCache(GetCurrentProcess(), st, sizeof s);
    BYTE j[5] = { 0xE9 }; *(DWORD*)(j + 1) = (DWORD)st - (DWORD)(c2 + 5); PatchBytes(c2, j, 5);
    BYTE k[5] = { 0xE8 }; *(DWORD*)(k + 1) = (DWORD)(void*)h_ShCasters - (DWORD)(c1 + 5); PatchBytes(c1, k, 5);
    LOG("shadows: map shadow projected from the sun camera (ShadowProjection=1)");
}

// ---- multisampled shadow texture (ShadowMSAA)
// The shadow texture is re-rendered every frame by a camera that turns with the sun. Its texel grid turns with it,
// so a building's silhouette edge stays on the same texels while the projection on the ground turns, then jumps a
// texel: shadows slid against the sun and snapped back (shimmering of up to one texel; smaller with a larger
// ShadowSize). With multisampling the silhouette edges are anti-aliased - their coverage changes gradually and the
// edges move smoothly inside a texel. The casters are drawn into a multisampled render target of the same size and
// format (set right after ID3DXRenderToSurface::BeginScene on the shadow texture) and resolved into the texture by
// StretchRect before EndScene.
static int g_shadowMsaa = 4;                    // [Video] ShadowMSAA: 0 / 2 / 4 / 8
static void* g_shMsRT = nullptr; static UINT g_shMsW = 0, g_shMsH = 0; static DWORD g_shMsFmt = 0;
static void* g_shMsSurf = nullptr; static bool g_shMsOn = false, g_shMsBroken = false;
typedef HRESULT (WINAPI *D3DXCRTS_t)(void*, UINT, UINT, DWORD, BOOL, DWORD, void**);
typedef HRESULT (__stdcall *RtsBegin_t)(void*, void*, const void*);
typedef HRESULT (__stdcall *RtsEnd_t)(void*, DWORD);
static D3DXCRTS_t o_D3DXCRTS = nullptr; static RtsBegin_t o_RtsBegin = nullptr; static RtsEnd_t o_RtsEnd = nullptr;
static bool IsShadowSurface(void* surf) {
    if (!surf || !g_shTexN) return false;
    static const GUID IID_Tex9 = { 0x85c31227, 0x3de5, 0x4f00, { 0x9b, 0x3a, 0xf1, 0x1a, 0xc3, 0x8c, 0x18, 0xb5 } };
    void* cont = nullptr;
    if (((HRESULT (__stdcall*)(void*, const GUID&, void**))(*(void***)surf)[11])(surf, IID_Tex9, &cont) < 0 || !cont) return false;   // GetContainer
    bool r = false;
    for (int i = 0; i < g_shTexN; ++i) if (g_shTex[i] == cont) r = true;
    ComRelease(cont);
    // only the map shadow (R5G6B5), not the unit shadows
    BYTE desc[32]; if (r && ((HRESULT (__stdcall*)(void*, void*))(*(void***)surf)[12])(surf, desc) >= 0) r = *(DWORD*)desc == 0x17;   // GetDesc: Format
    return r;
}
static HRESULT __stdcall h_RtsBegin(void* rts, void* surf, const void* vp) {
    HRESULT hr = o_RtsBegin(rts, surf, vp);
    if (hr < 0 || !g_shadowMsaa || g_shMsBroken || !IsShadowSurface(surf)) return hr;
    void* dev = *pDevice;
    BYTE desc[32]; ((HRESULT (__stdcall*)(void*, void*))(*(void***)surf)[12])(surf, desc);
    DWORD fmt = *(DWORD*)desc; UINT w = *(UINT*)(desc + 24), h = *(UINT*)(desc + 28);
    if (!g_shMsRT || w != g_shMsW || h != g_shMsH || fmt != g_shMsFmt) {
        ComRelease(g_shMsRT); g_shMsRT = nullptr;
        typedef HRESULT (__stdcall *CRT_t)(void*, UINT, UINT, DWORD, DWORD, DWORD, BOOL, void**, HANDLE*);
        int ms = g_shadowMsaa;
        while (ms >= 2 && (unsigned long long)w * h * 2 * ms > (512ull << 20)) ms /= 2;   // at most 512 MB for the multisampled target
        while (ms >= 2 && ((CRT_t)(*(void***)dev)[28])(dev, w, h, fmt, (DWORD)ms, 0, FALSE, &g_shMsRT, nullptr) < 0) { g_shMsRT = nullptr; ms /= 2; }
        if (!g_shMsRT) { g_shMsBroken = true; LOG("shadows: multisampled shadow target %ux%u not available, ShadowMSAA off", w, h); return hr; }
        g_shMsW = w; g_shMsH = h; g_shMsFmt = fmt;
        LOG("shadows: shadow texture rendered with %dx MSAA (%ux%u)", ms, w, h);
    }
    ((HRESULT (__stdcall*)(void*, DWORD, void*))(*(void***)dev)[37])(dev, 0, g_shMsRT);   // SetRenderTarget (the RTS viewport stays)
    if (vp) ((HRESULT (__stdcall*)(void*, const void*))(*(void***)dev)[47])(dev, vp);
    else { DWORD v[6] = { 0, 0, w, h, 0, 0 }; float z1 = 1.0f; memcpy(&v[5], &z1, 4); ((HRESULT (__stdcall*)(void*, const void*))(*(void***)dev)[47])(dev, v); }
    g_shMsSurf = surf; g_shMsOn = true; ++g_shMsFrames;
    return hr;
}
static HRESULT __stdcall h_RtsEnd(void* rts, DWORD mip) {
    if (g_shMsOn) {
        g_shMsOn = false;
        void* dev = *pDevice;
        ((HRESULT (__stdcall*)(void*, void*, const RECT*, void*, const RECT*, DWORD))(*(void***)dev)[34])(dev, g_shMsRT, nullptr, g_shMsSurf, nullptr, 0 /*NONE*/);   // resolve
        ((HRESULT (__stdcall*)(void*, DWORD, void*))(*(void***)dev)[37])(dev, 0, g_shMsSurf);
        g_shMsSurf = nullptr;
    }
    return o_RtsEnd(rts, mip);
}
static HRESULT WINAPI h_D3DXCRTS(void* dev, UINT w, UINT h, DWORD fmt, BOOL ds, DWORD dsfmt, void** out) {
    HRESULT hr = o_D3DXCRTS(dev, w, h, fmt, ds, dsfmt, out);
    if (hr >= 0 && out && *out && !o_RtsBegin) {
        void** vt = *(void***)*out;
        o_RtsBegin = (RtsBegin_t)PatchVtbl(vt, 5, (void*)h_RtsBegin);
        o_RtsEnd = (RtsEnd_t)PatchVtbl(vt, 6, (void*)h_RtsEnd);
    }
    return hr;
}
static void ShadowMsaaRelease() { ComRelease(g_shMsRT); g_shMsRT = nullptr; g_shMsOn = false; g_shMsSurf = nullptr; }
static void InstallShadowMsaa() {
    if (!g_shadowMsaa) return;
    o_D3DXCRTS = (D3DXCRTS_t)PatchIAT("d3dx9_29.dll", "D3DXCreateRenderToSurface", (void*)h_D3DXCRTS);
    if (!o_D3DXCRTS) { g_shadowMsaa = 0; LOG("shadows: D3DXCreateRenderToSurface not hooked, ShadowMSAA off"); }
}

// ---- Lua: shadow quality for the options page (applied on the next start: the shadow textures are created with
// the level / device). Levels: 0 original (1024, no MSAA, units 256, original caster culling), 1 medium (2048, 4x, 512),
// 2 high = recommended (4096, 4x, 1024), 3 ultra (8192, 4x, 2048); -1 = something else set in the ini.
static const int kShLevels[4][3] = { { 1024, 0, 256 }, { 2048, 4, 512 }, { 4096, 4, 1024 }, { 8192, 4, 2048 } };
static int ShadowLevelFromIni() {
    int sz = GetPrivateProfileIntA("Video", "ShadowSize", 4096, g_iniPath), ms = GetPrivateProfileIntA("Video", "ShadowMSAA", 4, g_iniPath),
        us = GetPrivateProfileIntA("Video", "UnitShadowSize", 1024, g_iniPath);
    int cull = GetPrivateProfileIntA("Video", "ShadowCasterCull", 0, g_iniPath) != 0;
    if (sz <= 0) sz = 1024;
    for (int i = 0; i < 4; ++i) if (kShLevels[i][0] == sz && kShLevels[i][1] == ms && kShLevels[i][2] == us && cull == (i == 0)) return i;
    return -1;
}
static int L_GetShadows(void* L) { LPushNum(L, (float)ShadowLevelFromIni()); return 1; }
static int L_SetShadows(void* L) {
    int lv = (int)LNum(L, 1); if (lv < 0 || lv > 3) return 0;
    char b[16];
    snprintf(b, sizeof b, "%d", kShLevels[lv][0]); WritePrivateProfileStringA("Video", "ShadowSize", b, g_iniPath);
    snprintf(b, sizeof b, "%d", kShLevels[lv][1]); WritePrivateProfileStringA("Video", "ShadowMSAA", b, g_iniPath);
    snprintf(b, sizeof b, "%d", kShLevels[lv][2]); WritePrivateProfileStringA("Video", "UnitShadowSize", b, g_iniPath);
    WritePrivateProfileStringA("Video", "ShadowCasterCull", lv == 0 ? "1" : "0", g_iniPath);   // "original" = original culling too
    LOG("options: shadow quality %d (map %d, MSAA %d, units %d) - next start", lv, kShLevels[lv][0], kShLevels[lv][1], kShLevels[lv][2]);
    return 0;
}
