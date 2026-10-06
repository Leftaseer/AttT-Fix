// Randomized test of skin_core.h against a straightforward reference of the game's skinning (0x4B9110):
// D3DXMatrixRotationYawPitchRoll (Wine's formula), TransformCoord with the divide by w, TransformNormal, blends.
//   g++ -O2 -msse2 -o skintest skintest.cpp && ./skintest
#include "../skin_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include <random>

static void RefMatrix(const float* k, double m[4][4]) {
    double sp = sin(k[0]), cp = cos(k[0]), sy = sin(k[1]), cy = cos(k[1]), sr = sin(k[2]), cr = cos(k[2]);
    double r[4][4] = {
        { sr * sp * sy + cr * cy, sr * cp, sr * sp * cy - cr * sy, 0 },
        { cr * sp * sy - sr * cy, cr * cp, cr * sp * cy + sr * sy, 0 },
        { cp * sy, -sp, cp * cy, 0 },
        { k[3], k[4], k[5], 1 } };
    memcpy(m, r, sizeof r);
}

int main() {
    std::mt19937 rng(12345);
    std::uniform_real_distribution<float> U(-1, 1);
    static float tp[65536 * 4] __attribute__((aligned(16))), tn[65536 * 4] __attribute__((aligned(16)));
    double worst = 0;
    for (int it = 0; it < 2000; ++it) {
        int nb = 1 + rng() % 60;
        std::vector<float> keys(nb * 6);
        for (int b = 0; b < nb; ++b) { for (int k = 0; k < 3; ++k) keys[b * 6 + k] = U(rng) * 3.5f; for (int k = 3; k < 6; ++k) keys[b * 6 + k] = U(rng) * 50; }
        std::vector<int> ranges(nb * 2); int s = 0;
        for (int b = 0; b < nb; ++b) { int c = rng() % 5 == 0 ? 0 : rng() % 80; ranges[b * 2] = s; ranges[b * 2 + 1] = s + c; s += c; }
        if (!s) continue;
        std::vector<float> pos(s * 3), nrm(s * 3);
        for (auto& v : pos) v = U(rng) * 2; for (auto& v : nrm) v = U(rng);
        int n1 = rng() % 200, n2 = rng() % 200, n3 = rng() % 100, n4 = rng() % 100, n = n1 + n2 + n3 + n4;
        std::vector<unsigned short> l1(n1); std::vector<unsigned char> l2(n2 * 12), l3(n3 * 20), l4(n4 * 24);
        for (auto& x : l1) x = rng() % s;
        auto fill = [&](unsigned char* r, int ni) {
            float w[4], sum = 0; for (int k = 0; k < ni; ++k) { w[k] = 0.05f + (U(rng) + 1); sum += w[k]; }
            for (int k = 0; k < ni; ++k) { ((unsigned short*)r)[k] = rng() % s; ((float*)(r + (ni == 2 ? 4 : 8)))[k] = w[k] / sum; }
        };
        for (int i = 0; i < n2; ++i) fill(&l2[i * 12], 2);
        for (int i = 0; i < n3; ++i) fill(&l3[i * 20], 3);
        for (int i = 0; i < n4; ++i) fill(&l4[i * 24], 4);
        std::vector<float> out(n * 8, 777.0f);
        SkinMesh m = { keys.data(), nb, ranges.data(), pos.data(), nrm.data(), l1.data(), n1, l2.data(), n2, l3.data(), n3, l4.data(), n4, out.data() };
        if (SkinMaxIndex(m) > s) { printf("max index wrong\n"); return 1; }
        if (SkinTransform(m, tp, tn, 65536) != s) { printf("transform count wrong\n"); return 1; }
        if (SkinBlend(m, tp, tn) != n) { printf("blend count wrong\n"); return 1; }
        // reference
        std::vector<double> rp(s * 3), rn(s * 3); int c = 0;
        for (int b = 0; b < nb; ++b) {
            double M[4][4]; RefMatrix(&keys[b * 6], M);
            for (int i = ranges[b * 2]; i < ranges[b * 2 + 1]; ++i, ++c) {
                const float* p = &pos[c * 3]; const float* q = &nrm[c * 3];
                double w = p[0] * M[0][3] + p[1] * M[1][3] + p[2] * M[2][3] + M[3][3];
                for (int k = 0; k < 3; ++k) {
                    rp[c * 3 + k] = (p[0] * M[0][k] + p[1] * M[1][k] + p[2] * M[2][k] + M[3][k]) / w;
                    rn[c * 3 + k] = q[0] * M[0][k] + q[1] * M[1][k] + q[2] * M[2][k];
                }
            }
        }
        int o = 0; double err = 0;
        auto chk = [&](const unsigned short* idx, const float* w, int ni) {
            for (int k = 0; k < 3; ++k) {
                double a = 0, b = 0;
                for (int j = 0; j < ni; ++j) { a += rp[idx[j] * 3 + k] * (w ? w[j] : 1); b += rn[idx[j] * 3 + k] * (w ? w[j] : 1); }
                double ea = fabs(a - out[o * 8 + k]) / (fabs(a) > 1 ? fabs(a) : 1), eb = fabs(b - out[o * 8 + 3 + k]);
                if (ea > err) err = ea; if (eb > err) err = eb;
            }
            if (out[o * 8 + 6] != 777.0f || out[o * 8 + 7] != 777.0f) { printf("uv clobbered\n"); exit(1); }
            ++o;
        };
        for (int i = 0; i < n1; ++i) chk(&l1[i], nullptr, 1);
        for (int i = 0; i < n2; ++i) chk((unsigned short*)&l2[i * 12], (float*)&l2[i * 12 + 4], 2);
        for (int i = 0; i < n3; ++i) chk((unsigned short*)&l3[i * 20], (float*)&l3[i * 20 + 8], 3);
        for (int i = 0; i < n4; ++i) chk((unsigned short*)&l4[i * 24], (float*)&l4[i * 24 + 8], 4);
        if (err > worst) worst = err;
    }
    printf("max relative error %.3g -> %s\n", worst, worst < 1e-5 ? "OK" : "FAIL");
    return worst < 1e-5 ? 0 : 1;
}
