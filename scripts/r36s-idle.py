#!/usr/bin/env python3
"""Descanso de tela do R36S: escurece o painel e mostra imagens quando ninguem mexe.

Por que nao usar o screensaver do EmulationStation: nesta versao ele nao zera o
contador ao sair, entao volta em menos de 2 s. Alem disso ele so cobre a tela com
preto, sem baixar o brilho do painel.

Aqui:
  - apos DIM_SECONDS parado, baixa o brilho de verdade (sysfs);
  - apos SLIDE_SECONDS parado, para o EmulationStation (ele precisa soltar o
    display) e mostra as imagens com image-viewer;
  - qualquer evento de entrada volta tudo: fecha as imagens, restaura o brilho e
    sobe o EmulationStation;
  - nunca age com um jogo rodando, para nao atrapalhar a partida nem matar o jogo.
"""
import glob
import os
import select
import subprocess
import sys
import time

BRIGHT = "/sys/class/backlight/backlight/brightness"
NORMAL_FILE = "/etc/r36s-idle.normal"
IMAGES = "/home/ark/.emulationstation/slideshow/images"
GAMES = ("drastic", "retroarch", "mupen64plus", "love", "ppsspp")

DIM_SECONDS = float(os.environ.get("DIM_SECONDS", "60"))
SLIDE_SECONDS = float(os.environ.get("SLIDE_SECONDS", "90"))
DIM_PERCENT = float(os.environ.get("DIM_PERCENT", "45"))
SLIDE_SECONDS_EACH = float(os.environ.get("SLIDE_SECONDS_EACH", "8"))
MAX_SLIDE_MIN = float(os.environ.get("MAX_SLIDE_MIN", "30"))


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def write_bright(v):
    with open(BRIGHT, "w") as f:
        f.write(str(int(v)))
    log(f"brilho={int(v)}")


def log(msg):
    try:
        with open("/var/log/r36s-idle.log", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except OSError:
        pass


NOMES_OK = ("gamepad", "joypad", "keys", "keyboard")


def nome_do_evento(dev):
    base = os.path.basename(dev)
    try:
        with open(f"/sys/class/input/{base}/device/name") as f:
            return f.read().strip().lower()
    except OSError:
        return ""


def entradas():
    """Abre so os controles. Dispositivo morto devolve EOF e nao pode contar como toque."""
    fds = {}
    for dev in glob.glob("/dev/input/event*"):
        if not any(n in nome_do_evento(dev) for n in NOMES_OK):
            continue
        try:
            fds[dev] = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return fds


def jogo_rodando():
    for pid in glob.glob("/proc/[0-9]*"):
        try:
            with open(pid + "/comm", "rb") as f:
                nome = f.read().strip().decode("utf-8", "replace")
        except OSError:
            continue
        if nome in GAMES:
            return True
    return False


def imagens():
    return sorted(glob.glob(IMAGES + "/*.jpg"))


def parar_es():
    subprocess.run(["systemctl", "stop", "emulationstation"], check=False)


def subir_es():
    subprocess.run(["systemctl", "start", "emulationstation"], check=False)


def entradas_js():
    """Interface legada do joystick: nao e bloqueada quando outro programa pega o evdev."""
    fds = {}
    for dev in glob.glob("/dev/input/js*"):
        try:
            fds[dev] = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return fds


def slideshow(baixo):
    """Mostra as imagens ate alguem mexer. Devolve True se houve entrada."""
    lista = imagens()
    if not lista:
        return False
    write_bright(baixo)  # parar o ES devolve o brilho ao maximo
    limite = time.monotonic() + MAX_SLIDE_MIN * 60
    fds = entradas_js()
    if not fds:
        fds = entradas()
    # ao abrir o joystick vem um lote com o estado inicial; nao e toque
    time.sleep(0.2)
    for dev, fd in list(fds.items()):
        try:
            while os.read(fd, 256):
                pass
        except OSError:
            pass
    graca = time.monotonic() + 1.5
    i = 0
    while time.monotonic() < limite:
        proc = subprocess.Popen(
            ["image-viewer", lista[i % len(lista)]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        i += 1
        write_bright(baixo)
        proximo_scan = time.monotonic() + 2.0
        fim = time.monotonic() + SLIDE_SECONDS_EACH
        while time.monotonic() < fim:
            r, _, _ = select.select(list(fds.values()), [], [], 0.2)
            if jogo_rodando():
                proc.terminate()
                return False
            if r and time.monotonic() >= graca:
                teve = False
                for dev, fd in list(fds.items()):
                    try:
                        dados = os.read(fd, 4096)
                    except OSError:
                        dados = b""
                    if not dados and dev.startswith("/dev/input/event"):
                        try:
                            os.close(fds.pop(dev))
                        except OSError:
                            pass
                        continue
                    if dados:
                        teve = True
                if teve:
                    proc.terminate()
                    proc.wait(timeout=5)
                    return True
            if time.monotonic() >= proximo_scan:
                proximo_scan = time.monotonic() + 2.0
                for dev, fd2 in entradas_js().items():
                    if dev not in fds:
                        fds[dev] = fd2
            if proc.poll() is not None:
                break
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    return False


maxb = read_int("/sys/class/backlight/backlight/max_brightness")


def brilho_normal():
    """Guarda o brilho de uso em arquivo: se o servico subir ja escurecido, nao perde a referencia."""
    try:
        with open(NORMAL_FILE) as f:
            v = int(f.read().strip())
        if 0 < v <= maxb:
            return v
    except (OSError, ValueError):
        pass
    v = read_int(BRIGHT)
    if v < maxb * 0.5:
        v = int(maxb * 0.55)
    try:
        with open(NORMAL_FILE, "w") as f:
            f.write(str(v))
    except OSError:
        pass
    return v


normal = brilho_normal()
baixo = max(1, min(normal, int(maxb * DIM_PERCENT / 100.0)))

if len(sys.argv) > 1 and sys.argv[1] == "--once":
    print(
        f"max={maxb} normal={normal} baixo={baixo} imagens={len(imagens())} "
        f"dim={DIM_SECONDS:g}s slide={SLIDE_SECONDS:g}s"
    )
    sys.exit(0)

fds = entradas()
if not fds:
    sys.exit("sem dispositivos de entrada")

dimmed = False
shown = False
last = time.monotonic()
last_scan = last


def tocar():
    global last, dimmed, shown
    last = time.monotonic()
    log(f"toque: shown={shown} dimmed={dimmed} normal={normal}")
    if shown:
        shown = False
        subir_es()
    if dimmed:
        write_bright(normal)
        dimmed = False


while True:
    r, _, _ = select.select(list(fds.values()), [], [], 1.0)
    if r:
        teve = False
        for dev, fd in list(fds.items()):
            try:
                dados = os.read(fd, 4096)
            except OSError:
                dados = b""
            if not dados:
                # dispositivo saiu (EOF): fecha e nao conta como atividade
                try:
                    os.close(fds.pop(dev))
                except OSError:
                    pass
                continue
            teve = True
        if teve:
            tocar()
    else:
        parado = time.monotonic() - last
        if not jogo_rodando():
            if not dimmed and parado >= DIM_SECONDS:
                write_bright(baixo)
                dimmed = True
            if not shown and parado >= SLIDE_SECONDS and not jogo_rodando():
                parar_es()
                dimmed = True
                shown = True
                if not slideshow(baixo):
                    shown = False
                    subir_es()
                else:
                    tocar()

    agora = time.monotonic()
    if agora - last_scan >= 5:
        last_scan = agora
        novos = entradas()
        for dev, fd in novos.items():
            if dev not in fds:
                fds[dev] = fd
        for dev in [d for d in fds if d not in novos]:
            try:
                os.close(fds.pop(dev))
            except OSError:
                pass
