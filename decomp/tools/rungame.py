#!/usr/bin/env python3
"""Run the real game under Wine on a virtual X server (software OpenGL) and drive it with a small script, so a
rebuilt exe can be checked in the game itself on a machine without a GPU or a screen.

    rungame.py EXE NAME 'wait 25; key Escape; wait 5; shot menu; click 640 480; wait 10; shot after'

Actions (separated by ';'): wait SECONDS | key XDOTOOL_KEY | click X Y | move DX DY [TIMES] | press | focus | geom | shot LABEL
(the game moves its own cursor by DirectInput, which sees relative motion: use move, then press)
The game folder is made in $WORK/game/NAME from symlinks to the installed game ($GAME_DIR) plus a copy of EXE;
the startup videos are skipped (-nologo) unless LOGOS=1; screenshots go to $WORK/shots/NAME_LABEL.png; Wine's output, including the engine's errors of a build made with
build.py -D DECOMP_DEBUG_LOG, to $WORK/game/NAME/wine.txt.  Prints whether the game was still running at the end
and the engine's error log if it wrote one.

DXVK=dir uses DXVK's d3d9.dll (with 32-bit mesa-vulkan-drivers: lavapipe), RES=800x600 sets the resolution.
Needs: wine (32-bit), Xvfb, matchbox-window-manager, xdotool, ImageMagick (import), 32-bit Mesa (libgl1-mesa-dri:i386, libglx-mesa0:i386).
The Wine prefix ($WINEPREFIX, made with wineboot) needs the native d3dx9_29.dll of the DirectX redistributable
(Feb2006_d3dx9_29_x86.cab in directx_Jun2010_redist.exe) in system32 with the override d3dx9_29=native: Wine's
own d3dx9 cannot compile the game's effects.  The X screen is 1280x960, the resolution of the default graphic.cfg,
because Wine cannot change the mode of a virtual X server."""
import os, sys, subprocess, time, random, shutil

exe, name, script = sys.argv[1], sys.argv[2], sys.argv[3]
G = os.environ.get('GAME_DIR', '/opt/re/gamewt/original_files/depot_289201')
W = os.environ.get('WORK', '/opt/re')
PREFIX = os.environ.get('WINEPREFIX', os.path.join(W, 'gameprefix'))
D = os.path.join(W, 'game', name)
SHOTS = os.path.join(W, 'shots')
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D + '/Saves')
os.makedirs(D + '/Screenshots')
os.makedirs(SHOTS, exist_ok=True)
for f in os.listdir(G):
    if f not in ('ATThrone.exe', 'Saves', 'Screenshots', 'graphic.cfg'):
        os.symlink(os.path.join(G, f), os.path.join(D, f))
shutil.copy(os.environ.get('GRAPHIC_CFG') or os.path.join(G, 'graphic.cfg'), os.path.join(D, 'graphic.cfg'))  # a player's settings
RES = os.environ.get('RES', '1280x960')    # the game's resolution (graphic.cfg starts with width, height) = X screen
W, H = (int(x) for x in RES.split('x'))
cfg = bytearray(open(os.path.join(D, 'graphic.cfg'), 'rb').read())
cfg[0:8] = W.to_bytes(4, 'little') + H.to_bytes(4, 'little')
WINDOWED = os.environ.get('WINDOWED')      # byte 0x10 of graphic.cfg: 1 = fullscreen, 0 = a window on a larger screen
if WINDOWED:
    cfg[0x10] = 0
open(os.path.join(D, 'graphic.cfg'), 'wb').write(cfg)
shutil.copy(exe, os.path.join(D, 'ATThrone.exe'))
# DXVK (Direct3D 9 on Vulkan, here Mesa's lavapipe) is much faster than Wine's own Direct3D on software OpenGL:
# DXVK=folder of DXVK's x32 DLLs
if os.environ.get('DXVK'):
    shutil.copy(os.path.join(os.environ['DXVK'], 'd3d9.dll'), D)
for dll in filter(None, os.environ.get('DLLS', '').split(':')):   # e.g. DXVK's d3d9.dll (with WINEDLLOVERRIDES=d3d9=n)
    shutil.copy(dll, D)
if os.environ.get('TESTINPUT'):            # scripted input for a build made with -D DECOMP_TEST_INPUT
    shutil.copy(os.environ['TESTINPUT'], os.path.join(D, 'testinput.txt'))
saves = os.environ.get('SAVES')            # a folder of save games to start with
if saves:
    for f in os.listdir(saves):
        shutil.copy(os.path.join(saves, f), D + '/Saves')

# the game crashes at the first scene (0x4C1530) without a sound device: a PulseAudio null sink stands in for one
if shutil.which('pulseaudio') and subprocess.run(['pulseaudio', '--check']).returncode:
    subprocess.run(['pulseaudio', '--system=false', '--exit-idle-time=-1', '--daemonize=yes', '-n',
                    '--load=module-null-sink sink_name=null', '--load=module-native-protocol-unix'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

disp = ':%d' % random.randint(100, 400)
xv = subprocess.Popen(['Xvfb', disp, '-screen', '0', '%dx%dx24' % ((W + 200, H + 150) if WINDOWED else (W, H)), '+extension', 'GLX'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
# a window manager keeps the game window active (without one it loses activation after the videos and the main
# loop stops running the engine)
wm = None
if shutil.which('matchbox-window-manager') and not os.environ.get('NOWM'):   # NOWM=1: windows keep their geometry
    wm = subprocess.Popen(['matchbox-window-manager', '-use_titlebar', 'no'], env=dict(os.environ, DISPLAY=disp),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
if os.environ.get('DXVK'):
    os.environ['WINEDLLOVERRIDES'] = 'd3d9=n;' + os.environ.get('WINEDLLOVERRIDES', '')
env = dict(os.environ, DISPLAY=disp, WINEPREFIX=PREFIX, WINEDEBUG=os.environ.get('WINEDEBUG', 'err+all,+debugstr'))
out = open(os.path.join(D, 'wine.txt'), 'w')
# -nologo: the engine's own switch that skips the startup videos (1C logo, logo, intro), as AttTFix's SkipIntro
args = ['wine', 'ATThrone.exe'] + ([] if os.environ.get('LOGOS') else ['-nologo'])
game = subprocess.Popen(args, cwd=D, env=env, stdout=out, stderr=subprocess.STDOUT)


def xdo(*a):
    subprocess.run(['xdotool'] + list(a), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)


for act in [s.strip() for s in script.split(';') if s.strip()]:
    q = act.split()
    if game.poll() is not None:
        print('the game exited (%s) before: %s' % (game.returncode, act))
        break
    if q[0] == 'wait':
        time.sleep(float(q[1]))
    elif q[0] == 'key':                     # held for a while: DirectInput reads the key state once a frame
        xdo('keydown', q[1]); time.sleep(0.4); xdo('keyup', q[1])
    elif q[0] == 'click':
        xdo('mousemove', q[1], q[2]); time.sleep(0.3)
        xdo('mousedown', '1'); time.sleep(0.15); xdo('mouseup', '1')
    elif q[0] == 'move':                    # relative motion (DirectInput sees only relative movement)
        for _ in range(int(q[3]) if len(q) > 3 else 1):
            xdo('mousemove_relative', '--', q[1], q[2]); time.sleep(0.05)
    elif q[0] == 'press':                   # mouse button at the current position
        xdo('mousedown', '1'); time.sleep(0.4); xdo('mouseup', '1')
    elif q[0] == 'focus':                   # give the game window the keyboard and mouse (no window manager)
        r = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.'], env=env, capture_output=True, text=True)
        for w in r.stdout.split():
            n = subprocess.run(['xdotool', 'getwindowname', w], env=env, capture_output=True, text=True).stdout.strip()
            print('window', w, repr(n), flush=True)
            if 'scension' in n or 'ATThrone' in n or 'Trone' in n:
                xdo('windowfocus', '--sync', w)
    elif q[0] == 'geom':                    # position and size of the game's windows (with NOWM=1 as the game set them)
        r = subprocess.run(['xdotool', 'search', '--name', 'ATThrone'], env=env, capture_output=True, text=True)
        for w in r.stdout.split():
            g = subprocess.run(['xdotool', 'getwindowgeometry', w], env=env, capture_output=True, text=True).stdout
            print('geom', w, ' '.join(g.split()[2:]), flush=True)
    elif q[0] == 'shot':
        subprocess.run(['import', '-window', 'root', os.path.join(SHOTS, '%s_%s.png' % (name, q[1]))], env=env,
                       stderr=subprocess.DEVNULL, timeout=30)
alive = game.poll() is None
game.kill()
try:
    game.wait(timeout=20)
except subprocess.TimeoutExpired:
    pass
subprocess.run(['wineserver', '-k'], env=env, timeout=30)
if wm:
    wm.kill()
xv.kill()
print('running at the end' if alive else 'exited with %s' % game.returncode)
for f in os.listdir(D):
    if f.startswith('__ATThrone__ERRORS'):
        print(open(os.path.join(D, f), encoding='cp1251').read())
