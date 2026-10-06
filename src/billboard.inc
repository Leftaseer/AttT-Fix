// ---------------------------------------------------------------- 10) forest billboards: one effect pass per batch (1.1.1)
// Included into attfix.cpp after effectsm.inc.
//
// TreeMassive draws the flat (billboard) trees in 0x55DF60 (called only from 0x55EDFA): the trees fading in and the
// ones fading out are drawn one by one - per tree two CEffect::SetInt (tint, alpha), Begin, BeginPass, draw, EndPass,
// End (~650 Begin per frame in a forest or a town). While that function runs, consecutive trees of the same effect
// stay inside one Begin/BeginPass: per tree only SetInt + ID3DXEffect::CommitChanges + the draw. The batch is closed
// on SetTechnique and when the function returns. Follows [Perf] TreeBatch (Ctrl+4 / F7).
typedef void (__fastcall *CEPass_t)(BYTE* ce, void* edx, UINT p);
typedef void (__fastcall *CEVoid_t)(BYTE* ce, void* edx);
typedef void (__fastcall *BBRender_t)(BYTE* T, void* edx);
static CEPass_t o_CEBeginPass = nullptr, o_CESetTech = nullptr; static CEVoid_t o_CEEndPass = nullptr;
static DWORD g_bbCalls = 0, g_bbCommits = 0;
static void BBClose() {
    if (!g_bbOpen) return;
    BYTE* ce = g_bbCe;
    if (g_bbPass >= 0) o_CEEndPass(ce, nullptr);
    g_bbPass = -1;
    g_bbClosing = true; h_CEEnd(ce, nullptr); g_bbClosing = false;
    g_bbOpen = false; g_bbCe = nullptr;
}
static void __fastcall h_CEBeginPass(BYTE* ce, void* edx, UINT p) {
    if (g_bbOpen && ce == g_bbCe) {
        if (g_bbPass == (int)p) {                                        // pass already active: commit the new SetInt values
            void* fx = *(void**)(ce + 0x20);
            ((HRESULT (__stdcall*)(void*))(*(void***)fx)[65])(fx);        // ID3DXEffect::CommitChanges
            ++g_bbCommits; return;
        }
        if (g_bbPass >= 0) o_CEEndPass(ce, nullptr);
        o_CEBeginPass(ce, edx, p); g_bbPass = (int)p; return;
    }
    o_CEBeginPass(ce, edx, p);
}
static void __fastcall h_CEEndPass(BYTE* ce, void* edx) {
    if (g_bbOpen && ce == g_bbCe) return;                                // the pass stays active for the next tree
    o_CEEndPass(ce, edx);
}
static void __fastcall h_CESetTech(BYTE* ce, void* edx, UINT t) {
    if (g_bbOpen) BBClose();
    o_CESetTech(ce, edx, t);
}
static void __fastcall h_BBRender(BYTE* T, void* edx) {
    if (!g_optTrees) { ((BBRender_t)0x0055DF60)(T, edx); return; }
    ++g_bbCalls;
    g_bbMode = true;
    ((BBRender_t)0x0055DF60)(T, edx);
    BBClose();
    g_bbMode = false;
}
static void InstallBillboards() {
    static const BYTE bp[7] = { 0x8B, 0x41, 0x20, 0x8B, 0x54, 0x24, 0x04 };   // BeginPass / SetTechnique
    static const BYTE ep[5] = { 0x8B, 0x41, 0x20, 0x8B, 0x08 };               // EndPass
    BYTE* call = (BYTE*)0x0055EDFA;
    if (!g_fxInstalled || call[0] != 0xE8 || (DWORD)(call + 5) + *(int*)(call + 1) != 0x0055DF60 ||
        memcmp((void*)0x00448110, bp, 7) || memcmp((void*)0x00448180, bp, 7) || memcmp((void*)0x00448140, ep, 5)) {
        LOG("billboards: unexpected code, batching not installed"); return;
    }
    o_CEBeginPass = (CEPass_t)Detour((BYTE*)0x00448110, bp, 7, (void*)h_CEBeginPass);
    o_CEEndPass = (CEVoid_t)Detour((BYTE*)0x00448140, ep, 5, (void*)h_CEEndPass);
    o_CESetTech = (CEPass_t)Detour((BYTE*)0x00448180, bp, 7, (void*)h_CESetTech);
    if (!o_CEBeginPass || !o_CEEndPass || !o_CESetTech) { LOG("billboards: detours failed"); return; }
    BYTE b[5]; b[0] = 0xE8; *(DWORD*)(b + 1) = (DWORD)(void*)h_BBRender - (DWORD)(call + 5);
    PatchBytes(call, b, 5);
    LOG("billboards: fading billboard trees batched per effect pass");
}
static void BillboardStats() {
    PLOG("BILLBOARDS batch=%d: calls=%lu batches=%lu trees kept in a batch=%lu commits=%lu", g_optTrees, g_bbCalls, g_bbBegins, g_bbKept, g_bbCommits);
    g_bbCalls = g_bbBegins = g_bbKept = g_bbCommits = 0;
}
