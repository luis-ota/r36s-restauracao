#!/usr/bin/env python3
"""Escurece a luz de fundo quando ninguem mexe no controle, e devolve ao toque.

O screensaver do EmulationStation so cobre a tela com preto: o painel continua
aceso. Este daemon baixa o brilho de verdade, que e o que economiza bateria.

Escuta todos os /dev/input/event* e reexamina a lista de tempos em tempos, para
pegar controle conectado depois.
"""
import glob
import os
import select
import sys
import time

BRIGHT = "/sys/class/backlight/backlight/brightness"
IDLE = float(os.environ.get("IDLE_SECONDS", "60"))
LEVEL = float(os.environ.get("DIM_PERCENT", "45"))
RESCAN = 5.0


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def write_bright(v):
    with open(BRIGHT, "w") as f:
        f.write(str(int(v)))


def abrir():
    fds = {}
    for dev in glob.glob("/dev/input/event*"):
        try:
            fds[dev] = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return fds


maxb = read_int("/sys/class/backlight/backlight/max_brightness")
normal = read_int(BRIGHT)
low = max(1, min(normal, int(maxb * LEVEL / 100.0)))

if len(sys.argv) > 1 and sys.argv[1] == "--once":
    print(f"max={maxb} normal={normal} baixo={low} espera={IDLE:g}s")
    sys.exit(0)

fds = abrir()
if not fds:
    sys.exit("sem dispositivos de entrada")

dimmed = False
last = time.monotonic()
last_scan = last

while True:
    r, _, _ = select.select(list(fds.values()), [], [], 1.0)
    if r:
        for fd in r:
            try:
                os.read(fd, 4096)
            except OSError:
                pass
        last = time.monotonic()
        if dimmed:
            write_bright(normal)
            dimmed = False
    elif not dimmed and time.monotonic() - last >= IDLE:
        write_bright(low)
        dimmed = True

    now = time.monotonic()
    if now - last_scan >= RESCAN:
        last_scan = now
        novos = abrir()
        for dev, fd in novos.items():
            if dev not in fds:
                fds[dev] = fd
        for dev in [d for d in fds if d not in novos]:
            try:
                os.close(fds.pop(dev))
            except OSError:
                pass
