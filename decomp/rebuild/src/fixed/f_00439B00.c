/* 0x00439B00: builds a camera path from a script track: the camera's state (0x00435550) is kept at +0x70, the node
 * list (+0x5C: head +0x60, size +0x64) is emptied; the first key's "pos" and "rot" (0x005619C0, 0x00561830,
 * 0x0055F4A0 for 1..3) and its time (1000*[1] + 33.3*[2]) with the camera globals (0x006CA2C4 +0x44, +0x5C) start
 * the path (0x00439500); every further key i (2..count) adds a segment from the keys i-1, i, i+1 (the first key
 * again after the last; 0x00437060); all keys are refcounted handles; the first node (+0x68) is applied to the
 * camera (0x004396C0, 0x00437720) and +0x6C set */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { float x, y, z; } V3_439B00;
typedef struct { float x, y, z, w; } V4_439B00;
typedef struct { unsigned int w[0x4c / 4]; } Node_439B00;
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C void __cdecl sub_005E3E9C(void *p);                                   /* operator delete */
DECOMP_C unsigned int *__thiscall sub_005619C0(void *self, float i);
DECOMP_C unsigned int *__thiscall sub_00561830(void *self, void *name);
DECOMP_C float __thiscall sub_0055F4A0(void *self, float i);
DECOMP_C Node_439B00 *__thiscall sub_00439500(Node_439B00 *self, V3_439B00 a, V3_439B00 p, V3_439B00 b,
                                              V4_439B00 r, V3_439B00 p2, V3_439B00 a2);
DECOMP_C void **__stdcall sub_00439790(void *next, void *prev, void *val);
DECOMP_C void __thiscall sub_004397D0(void *self, unsigned int n);
DECOMP_C unsigned int __thiscall sub_005605D0(void *self);
DECOMP_C void __thiscall sub_00437060(Node_439B00 *self, void *k0, void *k1, void *k2, void *k3);
DECOMP_C void *__cdecl sub_004396C0(void);
DECOMP_C void __thiscall sub_00437720(void *self, void *node);
DECOMP_C char d_006098E8[], d_006098E4[], d_00608A70[], d_006097EC[], d_006CA2C4[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *rel_439B00)(void *self, int flag);

static void ref_439B00(unsigned int *o)
{
    if (o)
        o[1]++;
}

static void unref_439B00(unsigned int *o)
{
    if (o && --o[1] == 0)
        ((rel_439B00)(*(void ***)o)[0])(o, 1);
}

static void push_439B00(char *list, void *val)
{
    void **head = *(void ***)(list + 4);
    void **n = sub_00439790(head, head[1], val);
    sub_004397D0(list, 1);
    head[1] = n;
    *(void ***)n[1] = n;
}

DECOMP(00439B00)
void __thiscall f_00439B00(char *this, void *track)
{
    unsigned int cam[0x44 / 4], s[7];
    unsigned int *key, *pos, *rot, *q, *cur = 0, *prev = 0, *next = 0;
    char *list = this + 0x5c, *g;
    void **head, **n;
    float p[3], r[3], f;
    double a;
    V3_439B00 va, vp, vb;
    V4_439B00 vr;
    Node_439B00 node;
    unsigned int i, cnt;

    __builtin_memcpy(this + 0x70, sub_00435550(sub_00424E70(), cam), 0x44);
    head = *(void ***)(list + 4);
    n = (void **)head[0];
    head[0] = head;
    (*(void ***)(list + 4))[1] = *(void **)(list + 4);
    *(int *)(list + 8) = 0;
    while (n != *(void ***)(list + 4)) {
        void **nx = (void **)n[0];
        sub_005E3E9C(n);
        n = nx;
    }

    key = sub_005619C0(track, 1.0f);
    ref_439B00(key);
    imp_00607324(s, d_006098E8);
    pos = sub_00561830(key, s);
    ref_439B00(pos);
    imp_00607330(s);
    p[0] = sub_0055F4A0(pos, 1.0f);
    p[1] = sub_0055F4A0(pos, *(float *)d_00608A70);
    p[2] = sub_0055F4A0(pos, *(float *)d_006097EC);
    imp_00607324(s, d_006098E4);
    rot = sub_00561830(key, s);
    ref_439B00(rot);
    unref_439B00(pos);
    imp_00607330(s);
    r[0] = sub_0055F4A0(rot, 1.0f);
    r[1] = sub_0055F4A0(rot, *(float *)d_00608A70);
    r[2] = sub_0055F4A0(rot, *(float *)d_006097EC);
    q = sub_005619C0(key, 1.0f);
    ref_439B00(q);
    a = sub_0055F4A0(q, *(float *)d_00608A70) * 33.33333206176758;
    f = (float)((long double)sub_0055F4A0(q, 1.0f) * 1000.0L + a);

    g = *(char **)d_006CA2C4;
    va = *(V3_439B00 *)(g + 0x44);
    vb = *(V3_439B00 *)(g + 0x5c);
    vp.x = p[0];
    vp.y = p[1];
    vp.z = p[2];
    vr.x = r[0];
    vr.y = r[1];
    vr.z = r[2];
    vr.w = f;
    push_439B00(list, sub_00439500(&node, va, vp, vb, vr, vp, va));

    cnt = sub_005605D0(track);
    for (i = 2; i <= cnt; i++) {
        float fi = (float)i;
        unsigned int *k = sub_005619C0(track, fi);
        ref_439B00(k);
        unref_439B00(cur);
        cur = k;
        if (i == 2) {
            ref_439B00(cur);
            unref_439B00(prev);
            prev = cur;
        } else {
            unsigned int *pp = sub_005619C0(track, (float)(fi - 1.0));
            ref_439B00(pp);
            unref_439B00(prev);
            prev = pp;
        }
        if (i != cnt) {
            unsigned int *np = sub_005619C0(track, (float)(fi + 1.0));
            ref_439B00(np);
            unref_439B00(next);
            next = np;
        } else {
            ref_439B00(key);
            unref_439B00(next);
            next = key;
        }
        sub_00437060(&node, key, cur, prev, next);
        push_439B00(list, &node);
        ref_439B00(cur);
        unref_439B00(key);
        key = cur;
    }

    n = (void **)**(void ***)(this + 0x60);
    *(void ***)(this + 0x68) = n;
    sub_00437720(sub_004396C0(), n + 2);
    *(int *)(this + 0x6c) = 1;
    unref_439B00(next);
    unref_439B00(prev);
    unref_439B00(cur);
    unref_439B00(q);
    unref_439B00(rot);
    unref_439B00(key);
}
