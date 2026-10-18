#!/usr/bin/env python3
"""Run the real game under Wine on a virtual X server (software OpenGL) and drive it with a small script, so a
rebuilt exe can be checked in the game itself on a machine without a GPU or a screen.

    rungame.py EXE NAME 'wait 25; key Escape; wait 5; shot menu; click 640 480; wait 10; shot after'

Actions (separated by ';'): wait SECONDS | key XDOTOOL_KEY | click X Y | shot LABEL
The game folder is made in $WORK/game/NAME from symlinks to the installed game ($GAME_DIR) plus a copy of EXE;
screenshots go to $WORK/shots/NAME_LABEL.png; Wine's output, including the engine's errors of a build made with
build.py -D DECOMP_DEBUG_LOG, to $WORK/game/NAME/wine.txt.  Prints whether the game was still running at the end
and the engine's error log if it wrote one.

Needs: wine (32-bit), Xvfb, xdotool, ImageMagick (import), 32-bit Mesa (libgl1-mesa-dri:i386, libglx-mesa0:i386).
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
shutil.copy(os.path.join(G, 'graphic.cfg'), D)
shutil.copy(exe, os.path.join(D, 'ATThrone.exe'))
saves = os.environ.get('SAVES')            # a folder of save games to start with
if saves:
    for f in os.listdir(saves):
        shutil.copy(os.path.join(saves, f), D + '/Saves')

disp = ':%d' % random.randint(100, 400)
xv = subprocess.Popen(['Xvfb', disp, '-screen', '0', '1280x960x24', '+extension', 'GLX'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
env = dict(os.environ, DISPLAY=disp, WINEPREFIX=PREFIX, WINEDEBUG=os.environ.get('WINEDEBUG', 'err+all,+debugstr'))
out = open(os.path.join(D, 'wine.txt'), 'w')
game = subprocess.Popen(['wine', 'ATThrone.exe'], cwd=D, env=env, stdout=out, stderr=subprocess.STDOUT)


def xdo(*a):
    subprocess.run(['xdotool'] + list(a), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)


for act in [s.strip() for s in script.split(';') if s.strip()]:
    q = act.split()
    if game.poll() is not None:
        print('the game exited (%s) before: %s' % (game.returncode, act))
        break
    if q[0] == 'wait':
        time.sleep(float(q[1]))
    elif q[0] == 'key':
        xdo('key', q[1])
    elif q[0] == 'click':
        xdo('mousemove', q[1], q[2]); time.sleep(0.3)
        xdo('mousedown', '1'); time.sleep(0.15); xdo('mouseup', '1')
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
xv.kill()
print('running at the end' if alive else 'exited with %s' % game.returncode)
for f in os.listdir(D):
    if f.startswith('__ATThrone__ERRORS'):
        print(open(os.path.join(D, f), encoding='cp1251').read())
