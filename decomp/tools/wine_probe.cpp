/* Standalone 32-bit environment probe. It contains no game code and never loads a game EXE or game assets. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <mmreg.h>
#include <dsound.h>

extern "C" { int _fltused = 0; }

static void log(const char *text)
{
    DWORD written;
    unsigned length = 0;
    while (text[length]) ++length;
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), text, length, &written, nullptr);
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), "\r\n", 2, &written, nullptr);
}

static void require(bool condition, const char *message)
{
    if (!condition) {
        log(message);
        ExitProcess(1);
    }
}

extern "C" void __cdecl probe_entry()
{
    require(sizeof(void *) == 4, "FAIL: probe must be 32-bit");
    log("PE32 process running");
    require(LoadLibraryA("msvcr80.dll") && LoadLibraryA("msvcp80.dll"), "FAIL: VC80 libraries unavailable");
    log("VC80 libraries loaded");
    HMODULE d3dx = LoadLibraryA("d3dx9_29.dll");
    require(d3dx != nullptr, "FAIL: native D3DX9_29 unavailable");
    auto check = (BOOL (WINAPI *)(UINT, UINT))GetProcAddress(d3dx, "D3DXCheckVersion");
    require(check && check(32, 29), "FAIL: D3DX9_29 version check");
    log("D3DX9_29 version check passed");

    WNDCLASSA wc = {};
    wc.lpfnWndProc = DefWindowProcA;
    wc.hInstance = GetModuleHandleA(nullptr);
    wc.lpszClassName = "AttTEnvironmentProbe";
    require(RegisterClassA(&wc) != 0, "FAIL: window class");
    HWND window = CreateWindowExA(0, wc.lpszClassName, "Wine environment probe (not the game)",
                                  WS_OVERLAPPEDWINDOW | WS_VISIBLE, 20, 20, 360, 300,
                                  nullptr, nullptr, wc.hInstance, nullptr);
    require(window != nullptr, "FAIL: window creation");

    HMODULE d3dModule = LoadLibraryA("d3d9.dll");
    auto create = (IDirect3D9 *(WINAPI *)(UINT))GetProcAddress(d3dModule, "Direct3DCreate9");
    require(create != nullptr, "FAIL: Direct3DCreate9 unavailable");
    IDirect3D9 *d3d = create(D3D_SDK_VERSION);
    require(d3d != nullptr, "FAIL: Direct3D9 initialization");
    D3DPRESENT_PARAMETERS present = {};
    present.BackBufferWidth = 320;
    present.BackBufferHeight = 240;
    present.BackBufferFormat = D3DFMT_X8R8G8B8;
    present.BackBufferCount = 1;
    present.SwapEffect = D3DSWAPEFFECT_DISCARD;
    present.hDeviceWindow = window;
    present.Windowed = TRUE;
    present.PresentationInterval = D3DPRESENT_INTERVAL_IMMEDIATE;
    IDirect3DDevice9 *device = nullptr;
    require(SUCCEEDED(d3d->CreateDevice(0, D3DDEVTYPE_HAL, window, D3DCREATE_SOFTWARE_VERTEXPROCESSING,
                                       &present, &device)), "FAIL: Direct3D9 device");
    log("Direct3D9 device created");
    require(SUCCEEDED(device->Clear(0, nullptr, D3DCLEAR_TARGET, 0xFF123456, 1.0f, 0)), "FAIL: clear");
    IDirect3DSurface9 *target = nullptr, *copy = nullptr;
    require(SUCCEEDED(device->GetRenderTarget(0, &target)), "FAIL: render target");
    require(SUCCEEDED(device->CreateOffscreenPlainSurface(320, 240, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM,
                                                         &copy, nullptr)), "FAIL: readback allocation");
    require(SUCCEEDED(device->GetRenderTargetData(target, copy)), "FAIL: readback");
    D3DLOCKED_RECT pixels;
    require(SUCCEEDED(copy->LockRect(&pixels, nullptr, D3DLOCK_READONLY)), "FAIL: readback lock");
    bool color = (*(DWORD *)pixels.pBits & 0xFFFFFF) == 0x123456;
    copy->UnlockRect();
    require(color, "FAIL: render/readback color mismatch");
    log("Render/readback color matched");

    const char shader[] = "float4 shade():COLOR0{return float4(0.25,0.5,0.75,1);} "
                          "technique T {pass P {PixelShader=compile ps_2_0 shade();}}";
    auto effectCreate = (HRESULT (WINAPI *)(IDirect3DDevice9 *, const void *, UINT, const D3DXMACRO *,
                         ID3DXInclude *, DWORD, ID3DXEffectPool *, ID3DXEffect **, ID3DXBuffer **))
                         GetProcAddress(d3dx, "D3DXCreateEffect");
    require(effectCreate != nullptr, "FAIL: effect compiler unavailable");
    ID3DXEffect *effect = nullptr;
    ID3DXBuffer *errors = nullptr;
    HRESULT status = effectCreate(device, shader, sizeof(shader) - 1, nullptr, nullptr, 0, nullptr, &effect, &errors);
    if (errors) log((const char *)errors->GetBufferPointer());
    require(SUCCEEDED(status), "FAIL: native effect compilation");
    log("Native D3DX effect compiled");
    device->Present(nullptr, nullptr, nullptr, nullptr);

    HMODULE sound = LoadLibraryA("dsound.dll");
    auto soundCreate = (HRESULT (WINAPI *)(const GUID *, IDirectSound8 **, IUnknown *))
                        GetProcAddress(sound, "DirectSoundCreate8");
    IDirectSound8 *audio = nullptr;
    require(soundCreate && SUCCEEDED(soundCreate(nullptr, &audio, nullptr)), "FAIL: DirectSound8 initialization");
    require(SUCCEEDED(audio->SetCooperativeLevel(window, DSSCL_PRIORITY)), "FAIL: audio cooperative level");
    log("DirectSound8 null device created");
    log("PROBE_PASSED");
    Sleep(2000);
    audio->Release();
    if (errors) errors->Release();
    effect->Release();
    copy->Release();
    target->Release();
    device->Release();
    d3d->Release();
    DestroyWindow(window);
    ExitProcess(0);
}
