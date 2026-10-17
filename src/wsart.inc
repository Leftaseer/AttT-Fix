// ---- widescreen menu art (included by attfix.cpp)
// The menu pictures are 4:3 torn parchment on black. On a wider screen attfix.lua draws them centered and fills
// the sides with a dim, blurred copy of the same picture; the black margin around the parchment is made
// transparent so the torn edges lie on that backdrop instead of ending in a black frame.
// The textures are made here at the first start from the game's own packs (nothing of the game is shipped) and
// stored in AttTFix.pak next to the game; it is made again when the source pictures change (texture mods).
#include <vector>
#include <string>
#include <algorithm>

namespace wsart {

struct Img { int w = 0, h = 0; std::vector<BYTE> p; };   // RGBA, top row first

struct Ent { std::string name; DWORD off = 0, len = 0; std::string pak; };

static bool ReadFat(const char* path, std::vector<Ent>& out) {
    FILE* f = fopen(path, "rb"); if (!f) return false;
    BYTE h[12]; bool ok = fread(h, 1, 12, f) == 12 && !memcmp(h, "GRES", 4) && *(int*)(h + 4) == 100;
    int n = ok ? *(int*)(h + 8) : 0;
    if (ok && (n < 0 || n > 200000)) ok = false;
    for (int i = 0; ok && i < n; ++i) {
        BYTE e[136]; if (fread(e, 1, 136, f) != 136) { ok = false; break; }
        Ent t; e[127] = 0; t.name = (const char*)e; t.off = *(DWORD*)(e + 128); t.len = *(DWORD*)(e + 132); t.pak = path;
        for (auto& c : t.name) c = (char)tolower((unsigned char)c);
        out.push_back(t);
    }
    fclose(f); return ok;
}
static bool ReadEnt(const Ent& e, std::vector<BYTE>& d) {
    FILE* f = fopen(e.pak.c_str(), "rb"); if (!f) return false;
    d.resize(e.len); bool ok = fseek(f, (long)e.off, SEEK_SET) == 0 && fread(d.data(), 1, e.len, f) == e.len;
    fclose(f); return ok;
}

static bool DecodeTga(const std::vector<BYTE>& d, Img& im) {
    if (d.size() < 18) return false;
    int idl = d[0], type = d[2], w = *(WORD*)&d[12], h = *(WORD*)&d[14], bpp = d[16], desc = d[17];
    if (d[1] != 0 || (type != 2 && type != 10) || (bpp != 24 && bpp != 32) || w <= 0 || h <= 0 || w > 8192 || h > 8192) return false;
    int bp = bpp / 8; size_t pos = 18 + idl, n = (size_t)w * h;
    std::vector<BYTE> px(n * 4);
    size_t i = 0;
    auto put = [&](const BYTE* s) { BYTE* o = &px[i * 4]; o[0] = s[2]; o[1] = s[1]; o[2] = s[0]; o[3] = bp == 4 ? s[3] : 255; ++i; };
    if (type == 2) {
        if (pos + n * bp > d.size()) return false;
        for (; i < n; pos += bp) put(&d[pos]);
    } else {
        while (i < n) {
            if (pos >= d.size()) return false;
            int c = d[pos++], cnt = (c & 0x7F) + 1;
            if (i + cnt > n) return false;
            if (c & 0x80) { if (pos + bp > d.size()) return false; for (int k = 0; k < cnt; ++k) put(&d[pos]); pos += bp; }
            else { if (pos + (size_t)cnt * bp > d.size()) return false; for (int k = 0; k < cnt; ++k, pos += bp) put(&d[pos]); }
        }
    }
    im.w = w; im.h = h; im.p.resize(n * 4);
    bool top = (desc & 0x20) != 0;
    for (int y = 0; y < h; ++y) memcpy(&im.p[(size_t)y * w * 4], &px[(size_t)(top ? y : h - 1 - y) * w * 4], (size_t)w * 4);
    return true;
}
static std::vector<BYTE> EncodeTga(const Img& im) {
    std::vector<BYTE> d(18 + (size_t)im.w * im.h * 4, 0);
    d[2] = 2; *(WORD*)&d[12] = (WORD)im.w; *(WORD*)&d[14] = (WORD)im.h; d[16] = 32; d[17] = 0x28;   // top-left, 8 alpha bits
    BYTE* o = &d[18];
    for (size_t i = 0; i < (size_t)im.w * im.h; ++i, o += 4) { const BYTE* s = &im.p[i * 4]; o[0] = s[2]; o[1] = s[1]; o[2] = s[0]; o[3] = s[3]; }
    return d;
}

// separable gaussian on a float plane (edge clamp)
static void Blur(std::vector<float>& v, int w, int h, int ch, float sigma) {
    int r = (int)ceilf(sigma * 3); std::vector<float> k(r * 2 + 1); float s = 0;
    for (int i = -r; i <= r; ++i) s += k[i + r] = expf(-(float)(i * i) / (2 * sigma * sigma));
    for (auto& x : k) x /= s;
    std::vector<float> t(v.size());
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) for (int c = 0; c < ch; ++c) {
        float a = 0; for (int i = -r; i <= r; ++i) { int xx = x + i < 0 ? 0 : x + i >= w ? w - 1 : x + i; a += k[i + r] * v[((size_t)y * w + xx) * ch + c]; }
        t[((size_t)y * w + x) * ch + c] = a;
    }
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) for (int c = 0; c < ch; ++c) {
        float a = 0; for (int i = -r; i <= r; ++i) { int yy = y + i < 0 ? 0 : y + i >= h ? h - 1 : y + i; a += k[i + r] * t[((size_t)yy * w + x) * ch + c]; }
        v[((size_t)y * w + x) * ch + c] = a;
    }
}

// dark pixels connected to the picture border -> transparent, with a soft 1-2 px edge
static void KeyMargin(Img& im, int thr = 28) {
    int w = im.w, h = im.h; size_t n = (size_t)w * h;
    std::vector<BYTE> dark(n), out(n, 0);
    for (size_t i = 0; i < n; ++i) {
        const BYTE* s = &im.p[i * 4];
        int l = (s[0] * 299 + s[1] * 587 + s[2] * 114) / 1000 * s[3] / 255;
        dark[i] = l < thr;
    }
    std::vector<int> st;
    auto seed = [&](int x, int y) { size_t i = (size_t)y * w + x; if (dark[i] && !out[i]) { out[i] = 1; st.push_back((int)i); } };
    for (int x = 0; x < w; ++x) { seed(x, 0); seed(x, h - 1); }
    for (int y = 0; y < h; ++y) { seed(0, y); seed(w - 1, y); }
    while (!st.empty()) {
        int i = st.back(); st.pop_back(); int x = i % w, y = i / w;
        if (x > 0) seed(x - 1, y);
        if (x < w - 1) seed(x + 1, y);
        if (y > 0) seed(x, y - 1);
        if (y < h - 1) seed(x, y + 1);
    }
    std::vector<float> m(n, 0);   // 3x3 dilation
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
        bool any = false;
        for (int dy = -1; dy <= 1 && !any; ++dy) for (int dx = -1; dx <= 1; ++dx) {
            int xx = x + dx, yy = y + dy; if (xx >= 0 && yy >= 0 && xx < w && yy < h && out[(size_t)yy * w + xx]) { any = true; break; }
        }
        m[(size_t)y * w + x] = any ? 1.0f : 0.0f;
    }
    Blur(m, w, h, 1, 1.5f);
    for (size_t i = 0; i < n; ++i) { float k = 1.0f - m[i]; if (k < 0) k = 0; im.p[i * 4 + 3] = (BYTE)(im.p[i * 4 + 3] * k + 0.5f); }
}

// draw src into dst (RGBA, alpha over), scaled bilinearly into the rect
static void Over(Img& dst, const Img& src, int rx, int ry, int rw, int rh) {
    for (int y = 0; y < rh; ++y) {
        int dy = ry + y; if (dy < 0 || dy >= dst.h) continue;
        float sy = (y + 0.5f) * src.h / rh - 0.5f; if (sy < 0) sy = 0; int y0 = (int)sy, y1 = y0 + 1 < src.h ? y0 + 1 : y0; float fy = sy - y0;
        for (int x = 0; x < rw; ++x) {
            int dx = rx + x; if (dx < 0 || dx >= dst.w) continue;
            float sx = (x + 0.5f) * src.w / rw - 0.5f; if (sx < 0) sx = 0; int x0 = (int)sx, x1 = x0 + 1 < src.w ? x0 + 1 : x0; float fx = sx - x0;
            float c[4];
            for (int k = 0; k < 4; ++k) {
                float a = src.p[((size_t)y0 * src.w + x0) * 4 + k] * (1 - fx) + src.p[((size_t)y0 * src.w + x1) * 4 + k] * fx;
                float b = src.p[((size_t)y1 * src.w + x0) * 4 + k] * (1 - fx) + src.p[((size_t)y1 * src.w + x1) * 4 + k] * fx;
                c[k] = a * (1 - fy) + b * fy;
            }
            BYTE* o = &dst.p[((size_t)dy * dst.w + dx) * 4]; float al = c[3] / 255.0f;
            for (int k = 0; k < 3; ++k) o[k] = (BYTE)(c[k] * al + o[k] * (1 - al) + 0.5f);
            o[3] = 255;
        }
    }
}

// dim blurred copy of the composed picture, 384x288
static Img Backdrop(const Img& comp) {
    const int W = 384, H = 288; Img r; r.w = W; r.h = H; r.p.resize((size_t)W * H * 4);
    std::vector<float> v((size_t)W * H * 3, 0);
    for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
        int x0 = x * comp.w / W, x1 = (x + 1) * comp.w / W, y0 = y * comp.h / H, y1 = (y + 1) * comp.h / H;
        if (x1 <= x0) x1 = x0 + 1;
        if (y1 <= y0) y1 = y0 + 1;
        float a[3] = { 0, 0, 0 }; int cnt = 0;
        for (int yy = y0; yy < y1; ++yy) for (int xx = x0; xx < x1; ++xx, ++cnt) for (int k = 0; k < 3; ++k) a[k] += comp.p[((size_t)yy * comp.w + xx) * 4 + k];
        for (int k = 0; k < 3; ++k) v[((size_t)y * W + x) * 3 + k] = a[k] / cnt;
    }
    Blur(v, W, H, 3, 10.0f);
    for (size_t i = 0; i < (size_t)W * H; ++i) {
        for (int k = 0; k < 3; ++k) { float c = v[i * 3 + k] * 0.55f; r.p[i * 4 + k] = (BYTE)(c > 255 ? 255 : c + 0.5f); }
        r.p[i * 4 + 3] = 255;
    }
    return r;
}

static void WritePak(const char* path, std::vector<std::pair<std::string, std::vector<BYTE>>>& files) {
    std::sort(files.begin(), files.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    char tmp[MAX_PATH]; snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE* f = fopen(tmp, "wb"); if (!f) { LOG("wsart: cannot write %s", tmp); return; }
    int n = (int)files.size(); BYTE h[12]; memcpy(h, "GRES", 4); *(int*)(h + 4) = 100; *(int*)(h + 8) = n; fwrite(h, 1, 12, f);
    DWORD off = 12 + 136 * n;
    for (auto& e : files) { BYTE t[136] = {}; strncpy((char*)t, e.first.c_str(), 127); *(DWORD*)(t + 128) = off; *(DWORD*)(t + 132) = (DWORD)e.second.size(); fwrite(t, 1, 136, f); off += (DWORD)e.second.size(); }
    for (auto& e : files) fwrite(e.second.data(), 1, e.second.size(), f);
    bool ok = !ferror(f); fclose(f);
    if (!ok || !MoveFileExA(tmp, path, MOVEFILE_REPLACE_EXISTING)) LOG("wsart: cannot write %s", path);
}

static void Make() {
    DWORD t0 = GetTickCount();
    char out[MAX_PATH]; snprintf(out, sizeof out, "%sAttTFix.pak", g_dir);
    // game packs in load order (later ones override), the English Resource1 replacement separately
    std::vector<Ent> ents, loc;
    for (int i = 0; i < 64; ++i) {
        char p[MAX_PATH]; snprintf(p, sizeof p, "%sResource%d.pak", g_dir, i);
        if (GetFileAttributesA(p) == INVALID_FILE_ATTRIBUTES) break;
        if (!ReadFat(p, ents)) LOG("wsart: %s unreadable, skipped", p);
    }
    { char p[MAX_PATH]; snprintf(p, sizeof p, "%sLocalization.pak", g_dir); ReadFat(p, loc); }
    auto find = [&](const char* name, bool en) -> const Ent* {
        const Ent* r = nullptr;
        if (en) { for (auto& e : loc) if (e.name == name) r = &e; return r; }
        for (auto& e : ents) if (e.name == name) r = &e;
        return r;
    };
    struct Src { const char* name; bool en; };
    static const Src srcs[] = { { "scrmainmenu.tga", false }, { "scrmainmenu.tga", true }, { "bgndload.tga", false }, { "scrload.tga", false },
                                { "bgndoptions.tga", false }, { "scroptions.tga", false }, { "scrwarriorpath.tga", false }, { "bgndwarriorpath.tga", false } };
    // signature of the sources: the pack is made again when one of them changes
    std::string sig = "AttTFix widescreen art 1\n";
    for (auto& s : srcs) { const Ent* e = find(s.name, s.en); char b[400]; snprintf(b, sizeof b, "%s%s %s %lu %lu\n", s.en ? "en_" : "", s.name, e ? e->pak.c_str() : "-", e ? e->off : 0, e ? e->len : 0); sig += b; }
    {   std::vector<Ent> mine;
        if (ReadFat(out, mine)) for (auto& e : mine) if (e.name == "attfix_ws.txt") {
            std::vector<BYTE> d; if (ReadEnt(e, d) && std::string(d.begin(), d.end()) == sig) { LOG("wsart: %s is up to date", out); return; }
        }
    }
    std::vector<std::pair<std::string, std::vector<BYTE>>> files;
    std::vector<Img> im(8); bool have[8] = {};
    for (int i = 0; i < 8; ++i) {
        const Ent* e = find(srcs[i].name, srcs[i].en); std::vector<BYTE> d;
        have[i] = e && ReadEnt(*e, d) && DecodeTga(d, im[i]);
        if (!have[i]) LOG("wsart: %s%s not found or not readable", srcs[i].en ? "en " : "", srcs[i].name);
    }
    // backdrops (composed on a 1024x768 4:3 picture as the scenes draw them)
    auto compose = [&](int l0, int l1) {
        const int layers[2] = { l0, l1 };
        Img c; c.w = 1024; c.h = 768; c.p.assign((size_t)c.w * c.h * 4, 0);
        for (size_t i = 0; i < (size_t)c.w * c.h; ++i) c.p[i * 4 + 3] = 255;
        for (int l : layers) if (l >= 0 && have[l]) {
            if (l == 7) Over(c, im[l], 1024 * 325 / 800, (int)(768 * 37.5f / 600), (int)(1024 * 425 / 800.0f), (int)(768 * 537.5f / 600));
            else Over(c, im[l], 0, 0, c.w, c.h);
        }
        return c;
    };
    struct Bd { const char* name; int l0, l1; };   // layers bottom to top, the top one must exist
    static const Bd bds[] = { { "mainmenu", -1, 0 }, { "load", 2, 3 }, { "options", 4, 5 }, { "warriorpath", 7, 6 } };
    for (auto& b : bds) if (have[b.l1]) files.push_back({ std::string("attfix_wsb_") + b.name + ".tga", EncodeTga(Backdrop(compose(b.l0, b.l1))) });
    static const char* keyedNames[7] = { "scrmainmenu", "en_scrmainmenu", "bgndload", "scrload", "bgndoptions", "scroptions", "scrwarriorpath" };
    for (int i = 0; i < 7; ++i) if (have[i]) { KeyMargin(im[i]); files.push_back({ std::string("attfix_ws_") + keyedNames[i] + ".tga", EncodeTga(im[i]) }); }
    files.push_back({ "attfix_ws.txt", std::vector<BYTE>(sig.begin(), sig.end()) });
    WritePak(out, files);
    LOG("wsart: %s made, %d pictures, %lu ms", out, (int)files.size() - 1, GetTickCount() - t0);
}

}  // namespace wsart
