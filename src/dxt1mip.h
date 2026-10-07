// DXT1 mip chain builder (CPU): decode level N-1, 2x2 box filter, encode level N.
// Used for the game's own DDS loader, which creates textures with the level count of the file (1 in hi-res packs).
#pragma once
#include <stdint.h>
#include <string.h>
static inline void Dxt1Unpack565(uint16_t c, int* r, int* g, int* b) {
    int r5 = (c >> 11) & 31, g6 = (c >> 5) & 63, b5 = c & 31;
    *r = (r5 << 3) | (r5 >> 2); *g = (g6 << 2) | (g6 >> 4); *b = (b5 << 3) | (b5 >> 2);
}
// decode a DXT1 level (w x h, blocks of 4x4) into RGBA (w x h)
static void Dxt1Decode(const uint8_t* src, int pitch, int w, int h, uint8_t* rgba) {
    int bw = (w + 3) / 4, bh = (h + 3) / 4;
    for (int by = 0; by < bh; ++by) {
        const uint8_t* row = src + by * pitch;
        for (int bx = 0; bx < bw; ++bx) {
            const uint8_t* b = row + bx * 8;
            uint16_t c0 = (uint16_t)(b[0] | (b[1] << 8)), c1 = (uint16_t)(b[2] | (b[3] << 8));
            uint32_t idx = (uint32_t)b[4] | ((uint32_t)b[5] << 8) | ((uint32_t)b[6] << 16) | ((uint32_t)b[7] << 24);
            int p[4][4];
            Dxt1Unpack565(c0, &p[0][0], &p[0][1], &p[0][2]); Dxt1Unpack565(c1, &p[1][0], &p[1][1], &p[1][2]);
            p[0][3] = p[1][3] = 255;
            if (c0 > c1) {
                for (int k = 0; k < 3; ++k) { p[2][k] = (2 * p[0][k] + p[1][k]) / 3; p[3][k] = (p[0][k] + 2 * p[1][k]) / 3; }
                p[2][3] = p[3][3] = 255;
            } else {
                for (int k = 0; k < 3; ++k) { p[2][k] = (p[0][k] + p[1][k]) / 2; p[3][k] = 0; }
                p[2][3] = 255; p[3][3] = 0;
            }
            for (int y = 0; y < 4; ++y) for (int x = 0; x < 4; ++x) {
                int px = bx * 4 + x, py = by * 4 + y;
                int i = (idx >> (2 * (y * 4 + x))) & 3;
                if (px < w && py < h) { uint8_t* d = rgba + (py * w + px) * 4; d[0] = (uint8_t)p[i][0]; d[1] = (uint8_t)p[i][1]; d[2] = (uint8_t)p[i][2]; d[3] = (uint8_t)p[i][3]; }
            }
        }
    }
}

// decode a DXT1 level and box-filter it 2x2 in one pass (w, h >= 4 and multiples of 4): output (w/2) x (h/2)
static void Dxt1DecodeHalf(const uint8_t* src, int pitch, int w, int h, uint8_t* out) {
    int bw = w / 4, bh = h / 4, ow = w / 2;
    for (int by = 0; by < bh; ++by) {
        const uint8_t* row = src + by * pitch;
        for (int bx = 0; bx < bw; ++bx) {
            const uint8_t* b = row + bx * 8;
            uint16_t c0 = (uint16_t)(b[0] | (b[1] << 8)), c1 = (uint16_t)(b[2] | (b[3] << 8));
            uint32_t idx = (uint32_t)b[4] | ((uint32_t)b[5] << 8) | ((uint32_t)b[6] << 16) | ((uint32_t)b[7] << 24);
            int p[4][4];
            Dxt1Unpack565(c0, &p[0][0], &p[0][1], &p[0][2]); Dxt1Unpack565(c1, &p[1][0], &p[1][1], &p[1][2]);
            p[0][3] = p[1][3] = 1;
            if (c0 > c1) { for (int k = 0; k < 3; ++k) { p[2][k] = (2 * p[0][k] + p[1][k]) / 3; p[3][k] = (p[0][k] + 2 * p[1][k]) / 3; } p[2][3] = p[3][3] = 1; }
            else { for (int k = 0; k < 3; ++k) { p[2][k] = (p[0][k] + p[1][k]) / 2; p[3][k] = 0; } p[2][3] = 1; p[3][3] = 0; }
            for (int qy = 0; qy < 2; ++qy) for (int qx = 0; qx < 2; ++qx) {
                int s[3] = { 0, 0, 0 }, sa[3] = { 0, 0, 0 }, an = 0;
                for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                    int i = (idx >> (2 * ((qy * 2 + y) * 4 + qx * 2 + x))) & 3;
                    for (int k = 0; k < 3; ++k) s[k] += p[i][k];
                    if (p[i][3]) { ++an; for (int k = 0; k < 3; ++k) sa[k] += p[i][k]; }
                }
                uint8_t* o = out + ((by * 2 + qy) * ow + bx * 2 + qx) * 4;
                if (an == 4 || an == 0) for (int k = 0; k < 3; ++k) o[k] = (uint8_t)((s[k] + 2) >> 2);
                else for (int k = 0; k < 3; ++k) o[k] = (uint8_t)((sa[k] + an / 2) / an);
                o[3] = an >= 2 ? 255 : 0;
            }
        }
    }
}
// 2x2 box filter (sizes halve, min 1); alpha averaged and thresholded later by the encoder
static void Dxt1Down(const uint8_t* s, int w, int h, uint8_t* d, int nw, int nh) {
    for (int y = 0; y < nh; ++y) for (int x = 0; x < nw; ++x) {
        int x0 = x * 2, y0 = y * 2, x1 = x0 + 1 < w ? x0 + 1 : x0, y1 = y0 + 1 < h ? y0 + 1 : y0;
        const uint8_t* a = s + (y0 * w + x0) * 4; const uint8_t* b = s + (y0 * w + x1) * 4;
        const uint8_t* c = s + (y1 * w + x0) * 4; const uint8_t* e = s + (y1 * w + x1) * 4;
        uint8_t* o = d + (y * nw + x) * 4;
        int an = (a[3] >= 128) + (b[3] >= 128) + (c[3] >= 128) + (e[3] >= 128);
        if (an == 4 || an == 0) {
            for (int k = 0; k < 3; ++k) o[k] = (uint8_t)((a[k] + b[k] + c[k] + e[k] + 2) / 4);
        } else {    // average colour of the opaque texels only (no dark fringe from the transparent black)
            int sum[3] = { 0, 0, 0 };
            const uint8_t* q[4] = { a, b, c, e };
            for (int i = 0; i < 4; ++i) if (q[i][3] >= 128) for (int k = 0; k < 3; ++k) sum[k] += q[i][k];
            for (int k = 0; k < 3; ++k) o[k] = (uint8_t)((sum[k] + an / 2) / an);
        }
        o[3] = an >= 2 ? 255 : 0;
    }
}
static inline uint16_t Dxt1Pack565(int r, int g, int b) {
    return (uint16_t)((((r * 31 + 128) >> 8) << 11) | (((g * 63 + 128) >> 8) << 5) | ((b * 31 + 128) >> 8));
}
static void Dxt1Encode(const uint8_t* rgba, int w, int h, uint8_t* dst, int pitch) {
    int bw = (w + 3) / 4, bh = (h + 3) / 4;
    for (int by = 0; by < bh; ++by) for (int bx = 0; bx < bw; ++bx) {
        int px[16][4]; bool trans = false;
        for (int y = 0; y < 4; ++y) for (int x = 0; x < 4; ++x) {
            int sx = bx * 4 + x, sy = by * 4 + y; if (sx >= w) sx = w - 1; if (sy >= h) sy = h - 1;
            const uint8_t* s = rgba + (sy * w + sx) * 4;
            int* p = px[y * 4 + x]; p[0] = s[0]; p[1] = s[1]; p[2] = s[2]; p[3] = s[3];
            if (s[3] < 128) trans = true;
        }
        // endpoints: the two opaque texels farthest apart along the colour bounding box diagonal
        int mn[3] = { 255, 255, 255 }, mx[3] = { 0, 0, 0 }, nOp = 0;
        for (int i = 0; i < 16; ++i) if (px[i][3] >= 128) { ++nOp; for (int k = 0; k < 3; ++k) { if (px[i][k] < mn[k]) mn[k] = px[i][k]; if (px[i][k] > mx[k]) mx[k] = px[i][k]; } }
        uint8_t* o = dst + by * pitch + bx * 8;
        if (!nOp) { o[0] = 0; o[1] = 0; o[2] = 0; o[3] = 0; o[4] = o[5] = o[6] = o[7] = 0xFF; continue; }   // all transparent: c0 <= c1, index 3
        int ax[3] = { mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2] };
        int lo = 1 << 30, hi = -(1 << 30), ilo = 0, ihi = 0;
        for (int i = 0; i < 16; ++i) if (px[i][3] >= 128) {
            int t = px[i][0] * ax[0] + px[i][1] * ax[1] + px[i][2] * ax[2];
            if (t < lo) { lo = t; ilo = i; } if (t > hi) { hi = t; ihi = i; }
        }
        uint16_t ca = Dxt1Pack565(px[ihi][0], px[ihi][1], px[ihi][2]), cb = Dxt1Pack565(px[ilo][0], px[ilo][1], px[ilo][2]);
        uint16_t c0, c1;
        if (trans) { c0 = ca < cb ? ca : cb; c1 = ca < cb ? cb : ca; }          // 3 colours + transparent
        else if (ca == cb) { c0 = ca; c1 = ca; }                                // one colour: index 0 everywhere
        else { c0 = ca > cb ? ca : cb; c1 = ca > cb ? cb : ca; }               // 4 colours
        int pal[4][3]; Dxt1Unpack565(c0, &pal[0][0], &pal[0][1], &pal[0][2]); Dxt1Unpack565(c1, &pal[1][0], &pal[1][1], &pal[1][2]);
        int np;
        if (c0 > c1) { for (int k = 0; k < 3; ++k) { pal[2][k] = (2 * pal[0][k] + pal[1][k]) / 3; pal[3][k] = (pal[0][k] + 2 * pal[1][k]) / 3; } np = 4; }
        else { for (int k = 0; k < 3; ++k) pal[2][k] = (pal[0][k] + pal[1][k]) / 2; np = 3; }
        uint32_t idx = 0;
        if (np == 4) {   // opaque block: project onto the c1 -> c0 line (palette order 1, 3, 2, 0 along it)
            int d[3] = { pal[0][0] - pal[1][0], pal[0][1] - pal[1][1], pal[0][2] - pal[1][2] };
            int dd = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
            static const int map[4] = { 1, 3, 2, 0 };
            for (int i = 0; i < 16; ++i) {
                int s = (px[i][0] - pal[1][0]) * d[0] + (px[i][1] - pal[1][1]) * d[1] + (px[i][2] - pal[1][2]) * d[2];
                int q = dd > 0 ? (s * 6 + dd) / (2 * dd) : 0;      // round(3 * s / dd)
                if (q < 0) q = 0; if (q > 3) q = 3;
                idx |= (uint32_t)map[q] << (2 * i);
            }
        } else for (int i = 0; i < 16; ++i) {
            int best = 0;
            if (px[i][3] < 128) best = 3;
            else {
                int bd = 1 << 30;
                for (int j = 0; j < np; ++j) {
                    int dr = px[i][0] - pal[j][0], dg = px[i][1] - pal[j][1], db = px[i][2] - pal[j][2];
                    int dd = dr * dr * 3 + dg * dg * 4 + db * db * 2;
                    if (dd < bd) { bd = dd; best = j; }
                }
            }
            idx |= (uint32_t)best << (2 * i);
        }
        o[0] = (uint8_t)c0; o[1] = (uint8_t)(c0 >> 8); o[2] = (uint8_t)c1; o[3] = (uint8_t)(c1 >> 8);
        o[4] = (uint8_t)idx; o[5] = (uint8_t)(idx >> 8); o[6] = (uint8_t)(idx >> 16); o[7] = (uint8_t)(idx >> 24);
    }
}

// build levels 1..n-1 from level 0 (all DXT1). lv[i]/pitch[i]: locked level memory. tmp: >= (w/2)*(h/2)*4*2 bytes.
static void Dxt1BuildChain(uint8_t** lv, const int* pitch, int n, int w, int h, uint8_t* tmp) {
    if (n < 2 || w < 4 || h < 4 || (w & 3) || (h & 3)) return;
    int cw = w / 2, ch = h / 2;
    uint8_t* cur = tmp; uint8_t* nxt = tmp + (size_t)cw * ch * 4;
    Dxt1DecodeHalf(lv[0], pitch[0], w, h, cur);
    for (int i = 1; i < n; ++i) {
        Dxt1Encode(cur, cw, ch, lv[i], pitch[i]);
        if (i + 1 >= n) break;
        int nw = cw > 1 ? cw / 2 : 1, nh = ch > 1 ? ch / 2 : 1;
        Dxt1Down(cur, cw, ch, nxt, nw, nh);
        uint8_t* t = cur; cur = nxt; nxt = t; cw = nw; ch = nh;
    }
}
