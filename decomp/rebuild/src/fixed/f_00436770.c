/* 0x00436770: exports the camera state into the script table `save` as "Camera".  ECX is the camera's interface
 * at +0x3C; 0x00435550 copies its position (+0x44), target position (+0x50) and rotation (+0x5C) as three float
 * triples plus distance (+0x68), fov (+0x74), zNear / zFar / aspect (+0x78 / +0x7C / +0x80), the flags at +0x211
 * and +0x218 (forwarded as whole dwords) and the height at +0x214 into a 0x44-byte record.  A table holding x, y
 * and z (0x00435E00 / 0x0057BC80) is stored as the outer table's "position" (0x0057BF50) and then reset by
 * assigning a fresh empty table (0x0057A860); the same table is reused for "tgPosition" and "rotation".  The
 * outer table also receives distance, fov, zNear, zFar, aspect and height as floats and onGround / needTgHeight
 * as ints (0x0057BB20), is stored in the argument as "Camera", and both temporaries are destroyed (0x004220A0). */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef struct { unsigned int w[3]; } Tbl_436770;

typedef struct {
    float position[3];            /* +0x00: camera +0x44 .. +0x4C */
    float target_position[3];     /* +0x0C: camera +0x50 .. +0x58 */
    float rotation[3];            /* +0x18: camera +0x5C .. +0x64 */
    float distance;               /* +0x24: camera +0x68 */
    float fov;                    /* +0x28: camera +0x74 */
    float z_near;                 /* +0x2C: camera +0x78 */
    float z_far;                  /* +0x30: camera +0x7C */
    float aspect;                 /* +0x34: camera +0x80 */
    unsigned int on_ground;       /* +0x38: camera +0x211 */
    float height;                 /* +0x3C: camera +0x214 */
    unsigned int need_tg_height;  /* +0x40: camera +0x218 */
} Cam_436770;

DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C void *__thiscall sub_00435E00(void *self, int allocator);
DECOMP_C void __thiscall sub_0057BC80(void *self, const char *key, float value);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, const void *value);
DECOMP_C void __thiscall sub_0057BB20(void *self, const char *key, int value);
DECOMP_C void __thiscall sub_0057A860(void *self, const void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C char d_00609850[], d_00609858[], d_00609868[], d_00609870[], d_0060987C[], d_00609884[],
    d_0060988C[], d_00609894[], d_00609898[], d_006098A4[], d_006098B0[], d_006098BC[], d_006098C8[],
    d_006098CC[], d_006098D0[];

DECOMP(00436770)
void __thiscall f_00436770(char *this, void *save)
{
    Tbl_436770 camera, part, empty;
    Cam_436770 cam;

    sub_00435550(this - 0x3c, &cam);
    sub_00435E00(&camera, 0);
    sub_00435E00(&part, 0);

    sub_0057BC80(&part, d_006098D0, cam.position[0]);
    sub_0057BC80(&part, d_006098CC, cam.position[1]);
    sub_0057BC80(&part, d_006098C8, cam.position[2]);
    sub_0057BF50(&camera, d_006098BC, &part);
    sub_00435E00(&empty, 0);
    sub_0057A860(&part, &empty);
    sub_004220A0(&empty);

    sub_0057BC80(&part, d_006098D0, cam.target_position[0]);
    sub_0057BC80(&part, d_006098CC, cam.target_position[1]);
    sub_0057BC80(&part, d_006098C8, cam.target_position[2]);
    sub_0057BF50(&camera, d_006098B0, &part);
    sub_00435E00(&empty, 0);
    sub_0057A860(&part, &empty);
    sub_004220A0(&empty);

    sub_0057BC80(&part, d_006098D0, cam.rotation[0]);
    sub_0057BC80(&part, d_006098CC, cam.rotation[1]);
    sub_0057BC80(&part, d_006098C8, cam.rotation[2]);
    sub_0057BF50(&camera, d_006098A4, &part);

    sub_0057BC80(&camera, d_00609898, cam.distance);
    sub_0057BC80(&camera, d_00609894, cam.fov);
    sub_0057BC80(&camera, d_0060988C, cam.z_near);
    sub_0057BC80(&camera, d_00609884, cam.z_far);
    sub_0057BC80(&camera, d_0060987C, cam.aspect);
    sub_0057BB20(&camera, d_00609870, (int)cam.on_ground);
    sub_0057BC80(&camera, d_00609868, cam.height);
    sub_0057BB20(&camera, d_00609858, (int)cam.need_tg_height);
    sub_0057BF50(save, d_00609850, &camera);
    sub_004220A0(&part);
    sub_004220A0(&camera);
}
