/* CConfig: the settings object (graphic.cfg / game.cfg), its lifetime and the graphic.cfg format. */
#include "game/common.h"
#include "game/config.h"
#include "msvc8/fstream.h"

ORIG_DATA(0060A290);                    /* CSingleton<CConfig>::vftable */
ORIG_DATA(0060A298);                    /* CConfig::vftable */
ORIG_DATA(0060A2A8);                    /* "graphic.cfg" */
ORIG_DATA(006C8958);                    /* float: screen height of the current mode */
ORIG_DATA(006C895C);                    /* float: screen width */
ORIG_DATA(006C8960);                    /* int: screen height */
ORIG_DATA(006C8964);                    /* int: screen width */

#define GRAPHIC_CFG ORIG_STR(0060A2A8)

/* The game folder follows the exe path ("<folder>\"); CConfig copies it to +0x20 and makes +0x04 the config folder
 * from it and the directory passed to LoadGraphicCfg. */
DECOMP(00441C50)
std::string &CConsole::GameFolder()
{
    return *(std::string *)((char *)this + 0x1638);
}

/* Despite the name, the original never reads the log file name: it recomputes the game folder from the exe's full
 * path - cut after its last backslash, with a trailing backslash - and only the caller's "game.log" is unused. */
DECOMP(004425E0)
void CConsole::OpenLog(const std::string &name)
{
    char path[MAX_PATH];
    GetModuleFileNameA(GetModuleHandleA(nullptr), path, MAX_PATH);

    std::string &folder = GameFolder();
    folder = path;
    folder = folder.substr(0, folder.rfind("\\", std::string::npos));
    folder += "\\";
}

DECOMP(00441D10)
CConfig::CConfig() : configDir(""), gameDir()
{
    vftable = d_0060A298;
}

/* the original restores the CConfig vtable before the strings go and the base vtable after them; the member
 * destructors make no virtual calls, so only the last store matters */
DECOMP(00441D70)
CConfig::~CConfig()
{
    vftable = d_0060A290;
}

/* the current screen size is cached for the rest of the engine (the original converts unsigned) */
static void StoreScreenSize(const CConfig &cfg)
{
    ORIG_VAR(006C8964, int) = cfg.width;
    ORIG_VAR(006C8960, int) = cfg.height;
    ORIG_VAR(006C895C, float) = (float)(unsigned int)cfg.width;
    ORIG_VAR(006C8958, float) = (float)(unsigned int)cfg.height;
}

/* fullscreen: centred on the desktop; windowed: the client is placed at 0,0 */
static void PlaceWindow(CConfig &cfg)
{
    if (cfg.windowed) {
        cfg.x = 0;
        cfg.y = 0;
    } else {
        cfg.x = (unsigned int)(GetSystemMetrics(SM_CXSCREEN) - cfg.width) >> 1;
        cfg.y = (unsigned int)(GetSystemMetrics(SM_CYSCREEN) - cfg.height) >> 1;
    }
}

DECOMP(00441DF0)
void CConfig::LoadGraphicCfg(const std::string &dir)
{
    gameDir = CConsole::Instance()->GameFolder();
    configDir = gameDir;
    configDir += dir;

    std::ifstream in;
    in.open((gameDir + GRAPHIC_CFG).c_str(), std::ios_base::_In | std::ios_base::_Binary,
            std::ios_base::_Openprot);

    if (in) {
        in.read((char *)&width, 4);
        in.read((char *)&height, 4);
        StoreScreenSize(*this);
        /* the fields of the file are packed in their CConfig order: the back buffer format, the unused +0x64,
         * windowed, compressed textures, the depth format and the two caps bytes */
        in.read((char *)&backBufferFormat, 4);
        in.read((char *)&unknown64, 4);
        in.read((char *)&windowed, 1);
        in.read((char *)&compressedTextures, 1);
        in.read((char *)&depthFormat, 4);
        in.read((char *)&nonSquareTextures, 1);
        in.read((char *)&tweening, 1);
        PlaceWindow(*this);
        in.read((char *)&grass, 1);
        in.read((char *)&shadow, 1);
        in.read((char *)&reflection, 1);
        in.read((char *)&musicVolume, 4);
        in.read((char *)&soundVolume, 4);
        in.read((char *)&ambientVolume, 4);
        in.read((char *)&unknown6D, 1);
        in.read((char *)&unknown6E, 1);
        in.read((char *)&unknown6F, 1);
        in.read((char *)&unknown70, 4 * 4);     /* unknown70 .. unknown7C */
        in.read((char *)&gamma, 8);
        in.close();
        return;
    }

    /* no graphic.cfg: the defaults are detected on the first adapter and written to a new file */
    in.close();
    in.open((gameDir + GRAPHIC_CFG).c_str(),
            std::ios_base::_Out | std::ios_base::_Trunc | std::ios_base::_Binary, std::ios_base::_Openprot);

    IDirect3D9 *d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if (!d3d)
        return;

    grass = true;
    gamma = 1.0;
    shadow = true;
    reflection = true;
    unknown6D = false;
    unknown6E = true;
    unknown6F = false;
    unknown70 = 100.0f;
    unknown7C = 100.0f;
    musicVolume = 0.6f;
    soundVolume = 1.0f;
    unknown74 = 400.0f;
    unknown78 = 500.0f;
    ambientVolume = 1.0f;

    std::ofstream out((gameDir + GRAPHIC_CFG).c_str(), std::ios_base::_Out | std::ios_base::_Binary,
                      std::ios_base::_Openprot);
    width = 1024;
    height = 768;
    out.write((char *)&width, 4);
    out.write((char *)&height, 4);
    windowed = true;
    StoreScreenSize(*this);
    backBufferFormat = D3DFMT_X8R8G8B8;
    if (d3d->CheckDeviceType(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, D3DFMT_X8R8G8B8, D3DFMT_A8R8G8B8,
                             windowed) >= 0)
        backBufferFormat = D3DFMT_A8R8G8B8;
    out.write((char *)&backBufferFormat, 4);
    unknown64 = 1;
    out.write((char *)&unknown64, 4);
    out.write((char *)&windowed, 1);
    compressedTextures = true;
    for (char c = '1'; c < '6'; c++)
        if (d3d->CheckDeviceFormat(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, D3DFMT_X8R8G8B8, 0, D3DRTYPE_TEXTURE,
                                   (D3DFORMAT)MAKEFOURCC('D', 'X', 'T', c)) < 0) {
            compressedTextures = false;
            break;
        }
    out.write((char *)&compressedTextures, 1);
    static const D3DFORMAT depth[] = {D3DFMT_D32,    D3DFMT_D24X8, D3DFMT_D24S8,
                                      D3DFMT_D24X4S4, D3DFMT_D16,   D3DFMT_D15S1};
    for (unsigned k = 0; k < sizeof depth / sizeof depth[0]; k++)
        if (d3d->CheckDeviceFormat(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, D3DFMT_X8R8G8B8,
                                   D3DUSAGE_DEPTHSTENCIL, D3DRTYPE_SURFACE, depth[k]) >= 0) {
            depthFormat = depth[k];
            break;
        }
    out.write((char *)&depthFormat, 4);
    D3DCAPS9 caps;
    d3d->GetDeviceCaps(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, &caps);
    nonSquareTextures = !(caps.TextureCaps & D3DPTEXTURECAPS_SQUAREONLY);
    out.write((char *)&nonSquareTextures, 1);
    tweening = (caps.VertexProcessingCaps & D3DVTXPCAPS_TWEENING) != 0;
    out.write((char *)&tweening, 1);
    PlaceWindow(*this);
    out.write((char *)&grass, 1);
    out.write((char *)&shadow, 1);
    out.write((char *)&reflection, 1);
    out.write((char *)&musicVolume, 4);
    out.write((char *)&soundVolume, 4);
    out.write((char *)&ambientVolume, 4);
    out.write((char *)&unknown6D, 1);
    out.write((char *)&unknown6E, 1);
    out.write((char *)&unknown6F, 1);
    out.write((char *)&unknown70, 4 * 4);
    out.write((char *)&gamma, 8);
    out.close();
}
