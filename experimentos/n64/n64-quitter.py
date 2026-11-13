#!/usr/bin/env python3
"""Fecha o emulador de N64 quando SELECT + START sao apertados juntos.

O mupen64plus deste ArkOS nao tem atalho de saida: sem isso, o unico jeito de
voltar ao EmulationStation e matar o processo. Le o mesmo controle que o jogo
usa (evdev permite varios leitores) e mata o alvo ao detectar o combo.

Variaveis de ambiente:
  QUIT_DEV     device do controle      (padrao /dev/input/event1)
  QUIT_SELECT  codigo do SELECT        (padrao 704)
  QUIT_START   codigo do START         (padrao 705)
  QUIT_TARGET  nome do processo alvo   (padrao mupen64plus)
"""
import os
import select
import subprocess
import sys

import evdev
from evdev import ecodes

DEV = os.environ.get("QUIT_DEV", "/dev/input/event1")
SELECT = int(os.environ.get("QUIT_SELECT", "704"))
START = int(os.environ.get("QUIT_START", "705"))
TARGET = os.environ.get("QUIT_TARGET", "mupen64plus")


def alvo_vivo():
    return subprocess.run(["pgrep", "-x", TARGET],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


def main():
    try:
        dev = evdev.InputDevice(DEV)
    except OSError as e:
        print("quitter: nao consegui abrir %s: %s" % (DEV, e), file=sys.stderr)
        return 1

    estado = {SELECT: False, START: False}
    while True:
        pronto, _, _ = select.select([dev.fd], [], [], 1.0)
        if not pronto:
            if not alvo_vivo():
                return 0
            continue
        for ev in dev.read():
            if ev.type != ecodes.EV_KEY or ev.code not in estado:
                continue
            estado[ev.code] = ev.value != 0
            if estado[SELECT] and estado[START]:
                subprocess.run(["pkill", "-x", TARGET])
                return 0


if __name__ == "__main__":
    sys.exit(main())
