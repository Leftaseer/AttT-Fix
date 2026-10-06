// ---------------------------------------------------------------- 7) forest: visible-tree sort (1.1.1)
// Included into attfix.cpp after effectsm.inc.
//
// Every frame TreeMassive classification (0x55E820) collects the visible trees into 16-byte records
// {index, dist^2, ...} at 0x870F00 and sorts them near-to-far with CRT qsort and an x87 comparator (0x55C500)
// before splitting them into opaque / cross-fading lists. With a few thousand trees this is ~8% of the frame
// (comparator ~5% + qsort itself in msvcr80). Here the qsort call (0x55EA6B) goes to a 3-pass LSD radix sort
// on the float key: same ascending order (ties can come out in a different order, as with qsort itself).
static int g_optSort = 1;                       // [Perf] TreeSort; Ctrl+4 with the other optimizations
static DWORD g_sortCalls = 0, g_sortElems = 0, g_sortFallback = 0;
typedef void (__cdecl *qsort_t)(void*, size_t, size_t, int (__cdecl*)(const void*, const void*));
static qsort_t o_qsort = nullptr;
enum { TS_CAP = 32768 };
struct TsRec { DWORD w[4]; };
static TsRec g_tsTmp[TS_CAP];
static DWORD g_tsKey[TS_CAP], g_tsKey2[TS_CAP];
static inline DWORD TsFlip(DWORD k) { return k ^ ((DWORD)((int)k >> 31) | 0x80000000u); }   // float order -> uint order
static void __cdecl h_TreeQsort(void* base, size_t n, size_t sz, int (__cdecl* cmp)(const void*, const void*)) {
    if (!g_optSort || sz != 16 || (DWORD)(void*)cmp != 0x0055C500 || n > TS_CAP) { ++g_sortFallback; o_qsort(base, n, sz, cmp); return; }
    ++g_sortCalls; g_sortElems += (DWORD)n;
    if (n < 2) return;
    TsRec* a = (TsRec*)base;
    if (n <= 24) {                                                    // tiny: insertion sort
        for (size_t i = 1; i < n; ++i) {
            TsRec r = a[i]; DWORD k = TsFlip(r.w[1]); size_t j = i;
            while (j > 0 && TsFlip(a[j - 1].w[1]) > k) { a[j] = a[j - 1]; --j; }
            a[j] = r;
        }
        return;
    }
    static DWORD cnt[3][2048];
    memset(cnt, 0, sizeof cnt);
    for (size_t i = 0; i < n; ++i) {
        DWORD k = TsFlip(a[i].w[1]); g_tsKey[i] = k;
        ++cnt[0][k & 2047]; ++cnt[1][(k >> 11) & 2047]; ++cnt[2][k >> 22];
    }
    TsRec* src = a; TsRec* dst = g_tsTmp; DWORD* ks = g_tsKey; DWORD* kd = g_tsKey2;
    for (int p = 0; p < 3; ++p) {
        int sh = p * 11; DWORD* c = cnt[p];
        DWORD first = (ks[0] >> sh) & 2047;
        if (c[first] == n) continue;                                  // every key has the same digit: pass not needed
        DWORD sum = 0;
        for (int d = 0; d < 2048; ++d) { DWORD t = c[d]; c[d] = sum; sum += t; }
        for (size_t i = 0; i < n; ++i) { DWORD k = ks[i]; DWORD pos = c[(k >> sh) & 2047]++; dst[pos] = src[i]; kd[pos] = k; }
        TsRec* t = src; src = dst; dst = t; DWORD* tk = ks; ks = kd; kd = tk;
    }
    if (src != a) memcpy(a, src, n * sizeof(TsRec));
}
static void InstallTreeSort() {
    BYTE* at = (BYTE*)0x0055EA6B;
    static const BYTE c[6] = { 0xFF, 0x15, 0x88, 0x74, 0x60, 0x00 };   // call [__imp_qsort]
    if (memcmp(at, c, 6) || memcmp((void*)0x0055EA5D, "\x68\x00\xC5\x55\x00\x6A\x10", 7)) { g_optSort = 0; LOG("tree sort: unexpected code, not installed"); return; }
    o_qsort = *(qsort_t*)0x00607488;
    BYTE b[6]; b[0] = 0xE8; *(DWORD*)(b + 1) = (DWORD)(void*)h_TreeQsort - (DWORD)(at + 5); b[5] = 0x90;
    PatchBytes(at, b, 6);
    LOG("tree sort: radix sort installed (TreeSort=%d)", g_optSort);
}
static void TreeSortStats() {
    PLOG("TREESORT radix=%d: sorts=%lu trees=%lu (avg %lu) fallback=%lu", g_optSort, g_sortCalls, g_sortElems,
         g_sortCalls ? g_sortElems / g_sortCalls : 0, g_sortFallback);
    g_sortCalls = g_sortElems = g_sortFallback = 0;
}
