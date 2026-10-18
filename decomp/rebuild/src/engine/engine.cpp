/* CEngine: frame, render, activation, gamma, window messages (Engine.cpp of the original). */
#include "game/common.h"
#include "game/globals.h"
#include "game/engine.h"

#if DECOMP_GAME_ATTT
/* Valkyrie has no Miles sound system: its SetActive only pauses the timer (not decompiled for it yet). */
extern "C" __declspec(dllimport) void __stdcall AIL_set_digital_master_volume_level(void *driver, float level);

DECOMP(00449F80)
void CEngine::SetActive(bool active)
{
    if (active) {
        AIL_set_digital_master_volume_level(g_milesDriver, g_masterVolume);
        timers->frame.Resume();
    } else {
        AIL_set_digital_master_volume_level(g_milesDriver, 0.0f);
        timers->frame.paused = false;
    }
}
#endif

extern "C" __declspec(dllimport) double __cdecl pow(double x, double y);

/* Gamma ramp from CEngine::gamma: value(i) = (i / 256) ^ gamma * 65536, clamped to 0..65535. */
DECOMP(00449E80)
void CEngine::ApplyGamma()
{
    IDirect3DDevice9 *dev = g_d3dDevice;
    D3DCAPS9 caps;
    __builtin_memset(&caps, 0, sizeof(caps));
    dev->GetDeviceCaps(&caps);
    dev->SetRenderState((D3DRENDERSTATETYPE)194 /* D3DRS_SRGBWRITEENABLE */, TRUE);
    D3DGAMMARAMP ramp;
    for (int i = 0; i < 256; i++) {
        double v = pow(i * 0.00390625, gamma) * 65536.0;
        if (v < 0)
            v = 0;
        else if (v > 65535.0)
            v = 65535.0;
        ramp.red[i] = ramp.green[i] = ramp.blue[i] = (WORD)(int)v;
    }
    dev->SetGammaRamp(0, D3DSGR_NO_CALIBRATION, &ramp);
    dev->SetRenderState((D3DRENDERSTATETYPE)194, FALSE);
}

/* Window messages go to the current scene first.  Mouse messages get the position of the game's own cursor
 * (it moves by DirectInput, not by the Windows cursor).  A message the scene used resets the input state. */
static bool IsMouseMessage(UINT msg)
{
    return msg == WM_MOUSEMOVE || msg == WM_LBUTTONDOWN || msg == WM_LBUTTONUP || msg == WM_RBUTTONDOWN ||
           msg == WM_RBUTTONUP || msg == WM_MBUTTONDOWN || msg == WM_MBUTTONUP || msg == WM_LBUTTONDBLCLK;
}

DECOMP(0044BAB0)
bool CEngine::HandleMessage(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (!scene)
        return false;
    if (IsMouseMessage(msg)) {
        const float *pos = CCursor::Instance()->ScreenPos();
        lp = ((int)(long long)pos[1] << 16) | (int)(long long)pos[0];
    }
    bool used = scene->HandleMessage(hwnd, msg, wp, lp);
    if (used) {
        if (msg != WM_MOUSEMOVE && IsMouseMessage(msg)) {
            CInput::Instance()->updater.Update(0.0f);
            CInput::Instance()->ResetMouse();
        }
        if (msg == WM_KEYDOWN || msg == WM_KEYUP || msg == WM_CHAR) {
            CInput::Instance()->updater.Update(0.0f);
            CInput::Instance()->ResetKeys();
        }
    }
    return used;
}

/* State 1 of the engine: timers, input, PrintScreen (screenshot) and Pause (pauses the game clock), then the
 * updaters, the scene and the GUI. */
DECOMP(0044A9C0)
void CEngine::Frame()
{
    state = 2;
    timers->frame.Wait();
    float dt = timers->frame.dt;
    ++frameCount;
    g_updateRoot->Update(dt);
    input->updater.Update(dt);
    for (unsigned i = 0; i < input->keyCount; i++) {
        const CInputKey &k = input->keys[i];
        if (!k.pressed || k.dik == 0x3D /* DIK_F3 */)
            continue;
        if (k.dik == 0xB7)                   /* DIK_SYSRQ */
            Screenshot();
        else if (k.dik == 0xC5)              /* DIK_PAUSE */
            timers->frame.paused = !timers->frame.paused;
    }
    overlay->Update(dt);
    scene->Update(dt);
    gui->updater.Update(dt);
}

/* State 2: draw the scene and the overlay.  A failed Present is retried through a device reset only for
 * D3DERR_DEVICENOTRESET; any other failure (e.g. D3DERR_DEVICELOST while minimised) throws, as in the
 * original. */
DECOMP(0044E480)
void CEngine::Render()
{
    state = 1;
    *(int *)((char *)gui + 0x208) = 0;
    IDirect3DDevice9 *dev = g_d3dDevice;
    dev->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, clearColor, 1.0f, 0);
    dev->BeginScene();
    scene->Render();
    overlay->Render();
    dev->EndScene();
    if (g_d3dDevice->Present(nullptr, nullptr, nullptr, nullptr) < 0) {
        if (g_d3dDevice->TestCooperativeLevel() != D3DERR_DEVICENOTRESET)
            ThrowGameException("D3DERR_DEVICENOTRESET", ".\\Engine.cpp", 0x6F0);
        RestoreDevice();
    }
}
