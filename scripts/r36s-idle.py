#!/usr/bin/env python3
"""Descanso de tela do R36S: escurece o painel e mostra imagens quando ninguem mexe.

Por que nao usar o screensaver do EmulationStation: nesta versao ele nao zera o
contador ao sair, entao volta em menos de 2 s. Alem disso ele so cobre a tela com
preto, sem baixar o brilho do painel.

Aqui:
  - apos DIM_SECONDS parado, baixa o brilho de verdade (sysfs) e o volume do
    sistema acompanha a proporcao do brilho; o ES segue tocando a musica;
  - apos SLIDE_SECONDS parado, para o EmulationStation (ele precisa soltar o
    display e o audio) e mostra as imagens com image-viewer; a musica de fundo
    segue por um player proprio (ffmpeg | aplay) no mesmo volume reduzido;
  - depois de MAX_SLIDE_MIN de slideshow sem toque, entra no descanso profundo:
    o player desliga e o painel fica minimo;
  - qualquer evento de entrada volta tudo: fecha as imagens, para o player,
    restaura o volume e o brilho e sobe o EmulationStation;
  - nunca age com um jogo rodando, para nao atrapalhar a partida nem matar o jogo.
"""
import glob
import math
import os
import re
import select
import shlex
import signal
import subprocess
import sys
import time

BRIGHT = os.environ.get("BRIGHT", "/sys/class/backlight/backlight/brightness")
NORMAL_FILE = os.environ.get("NORMAL_FILE", "/etc/r36s-idle.normal")
VOLUME_NORMAL_FILE = os.environ.get("VOLUME_NORMAL_FILE", "/etc/r36s-idle.volume")
LOG_FILE = os.environ.get("LOG_FILE", "/var/log/r36s-idle.log")
IMAGES = "/home/ark/.emulationstation/slideshow/images"
GAMES = ("drastic", "retroarch", "mupen64plus", "love", "ppsspp")

MUSIC_RAW = os.environ.get("MUSIC_RAW", "/home/ark/.r36s-idle/musica/lain_menu_chill.raw")
MUSIC_FLOOR = float(os.environ.get("MUSIC_FLOOR", "0.20"))
AMIXER_CARD = os.environ.get("AMIXER_CARD", "0")

DIM_SECONDS = float(os.environ.get("DIM_SECONDS", "60"))
SLIDE_SECONDS = float(os.environ.get("SLIDE_SECONDS", "90"))
DIM_PERCENT = float(os.environ.get("DIM_PERCENT", "45"))
SLIDE_PERCENT = float(os.environ.get("SLIDE_PERCENT", str(DIM_PERCENT)))
SLIDE_SECONDS_EACH = float(os.environ.get("SLIDE_SECONDS_EACH", "8"))
MAX_SLIDE_MIN = float(os.environ.get("MAX_SLIDE_MIN", "30"))
# Ao fim do slideshow (MAX_SLIDE_MIN) sem ninguem: descanso profundo, menu fora e brilho minimo.
# Sem isso o aparelho passa o dia alternando slideshow e menu, gastando CPU e calor.
RESTING_PERCENT = float(os.environ.get("RESTING_PERCENT", "1"))


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def write_bright(v):
    with open(BRIGHT, "w") as f:
        f.write(str(int(v)))
    log(f"brilho={int(v)}")


def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except OSError:
        pass


def amixer(*args):
    return subprocess.run(["amixer", "-c", AMIXER_CARD, *args],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          universal_newlines=True).stdout


def volume_ler():
    """Devolve (valor bruto, dB) do canal Playback."""
    m = re.search(r"(\d+) \[\d+%\] \[(-?[\d.]+)dB\]", amixer("get", "Playback"))
    if not m:
        raise RuntimeError("canal Playback sem leitura em dB")
    return int(m.group(1)), float(m.group(2))


def volume_normal():
    with open(VOLUME_NORMAL_FILE) as f:
        bruto, db = f.read().split()
    return int(bruto), float(db)


def volume_baixar(fracao):
    """Baixa o volume para a fracao do brilho normal, sem perder o volume de uso."""
    if not os.path.exists(VOLUME_NORMAL_FILE):
        bruto, db = volume_ler()
        with open(VOLUME_NORMAL_FILE, "w") as f:
            f.write(f"{bruto} {db}")
    _, db = volume_normal()
    fracao = max(MUSIC_FLOOR, min(1.0, fracao))
    alvo = db + 20 * math.log10(fracao)
    amixer("set", "Playback", "--", f"{alvo:.2f}dB")
    log(f"volume={alvo:.2f}dB fracao={fracao:.2f}")


def volume_restaurar():
    if not os.path.exists(VOLUME_NORMAL_FILE):
        return
    bruto, _ = volume_normal()
    amixer("set", "Playback", str(bruto))
    os.remove(VOLUME_NORMAL_FILE)
    log(f"volume restaurado={bruto}")


music_proc = None


def musica_ligar():
    global music_proc
    musica_desligar()
    if not os.path.exists(MUSIC_RAW):
        log(f"musica: arquivo ausente {MUSIC_RAW}")
        return
    # cat relê o PCM em loop sem reiniciar o aplay: a emenda nao tem pausa
    cmd = (f"while :; do cat {shlex.quote(MUSIC_RAW)}; done | "
           "aplay -q -t raw -f S16_LE -c 1 -r 44100")
    music_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, start_new_session=True)
    log("musica: ligada")


def musica_desligar():
    global music_proc
    if music_proc is None:
        return
    if music_proc.poll() is None:
        try:
            os.killpg(music_proc.pid, signal.SIGTERM)
            music_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(music_proc.pid, signal.SIGKILL)
            music_proc.wait()
        except OSError:
            pass
        log("musica: desligada")
    music_proc = None


NOMES_OK = ("gamepad", "joypad", "keys", "keyboard")


def nome_do_evento(dev):
    base = os.path.basename(dev)
    try:
        with open(f"/sys/class/input/{base}/device/name") as f:
            return f.read().strip().lower()
    except OSError:
        return ""


def entradas(abertos=()):
    """Abre so os controles ainda fechados. Dispositivo morto devolve EOF e nao pode contar como toque."""
    fds = {}
    for dev in glob.glob("/dev/input/event*"):
        if dev in abertos or not any(n in nome_do_evento(dev) for n in NOMES_OK):
            continue
        try:
            fds[dev] = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return fds


CONSOLE_LOCK = "/tmp/r36s-console.lock"


def app_de_console():
    """Launcher de console (opencode, btop, PortMaster) avisa por arquivo."""
    return os.path.exists(CONSOLE_LOCK)


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


def app_pelo_menu():
    """O menu nao tem filhos parado; com jogo ou port aberto, tem. Parar o menu mataria esse app."""
    pais = {}
    nomes = {}
    for caminho in glob.glob("/proc/[0-9]*/stat"):
        try:
            with open(caminho, "rb") as f:
                inicio, resto = f.read().rsplit(b")", 1)
            pid = int(caminho.split("/")[2])
            nomes[pid] = inicio.split(b"(", 1)[1]
            pais[pid] = int(resto.split()[1])
        except (OSError, IndexError, ValueError):
            continue
    menu = b"emulationstatio"
    binarios = {p for p, n in nomes.items() if n == menu and nomes.get(pais[p]) == menu}
    return any(pai in binarios for pai in pais.values())


def imagens():
    return sorted(glob.glob(IMAGES + "/*.jpg"))


def es_ativo():
    r = subprocess.run(["systemctl", "is-active", "emulationstation"],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout.strip() == b"active"


def matar_viewer():
    subprocess.run(["pkill", "-x", "image-viewer"], check=False)


def parar_es():
    subprocess.run(["systemctl", "stop", "emulationstation"], check=False)


def subir_es():
    subprocess.run(["systemctl", "start", "emulationstation"], check=False)


def entradas_js(abertos=()):
    """Interface legada do joystick: nao e bloqueada quando outro programa pega o evdev."""
    fds = {}
    for dev in glob.glob("/dev/input/js*"):
        if dev in abertos:
            continue
        try:
            fds[dev] = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return fds


def slideshow(baixo):
    """Mostra as imagens ate alguem mexer. Devolve True se houve entrada."""
    fds = {}
    try:
        return rodar_slideshow(baixo, fds)
    finally:
        for fd in fds.values():
            try:
                os.close(fd)
            except OSError:
                pass


def rodar_slideshow(baixo, fds):
    lista = imagens()
    if not lista:
        return False
    if es_ativo():
        return False
    write_bright(baixo)  # parar o ES devolve o brilho ao maximo
    limite = time.monotonic() + MAX_SLIDE_MIN * 60
    fds.update(entradas_js() or entradas())
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
            if jogo_rodando() or es_ativo():
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
                fds.update(entradas_js(fds))
            if proc.poll() is not None:
                break
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    return False


def brilho_normal(maxb):
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


def tocar():
    global last, dimmed, shown, descanso
    last = time.monotonic()
    descanso = False
    if shown or dimmed:
        log(f"toque: shown={shown} dimmed={dimmed} normal={normal}")
    musica_desligar()
    volume_restaurar()
    if shown:
        shown = False
        matar_viewer()
        subir_es()
    if dimmed:
        write_bright(normal)
        dimmed = False
    if not es_ativo() and not jogo_rodando() and not app_de_console():
        subir_es()


def encerrar(*_):
    musica_desligar()
    volume_restaurar()
    sys.exit(0)


if __name__ == "__main__":
    subprocess.run(["pkill", "-f", MUSIC_RAW], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    signal.signal(signal.SIGTERM, encerrar)
    signal.signal(signal.SIGINT, encerrar)
    maxb = read_int(os.environ.get("MAX_BRIGHT_FILE", "/sys/class/backlight/backlight/max_brightness"))
    normal = brilho_normal(maxb)
    baixo = max(1, min(normal, int(maxb * DIM_PERCENT / 100.0)))
    baixo_slide = max(1, min(normal, int(maxb * SLIDE_PERCENT / 100.0)))

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print(
            f"max={maxb} normal={normal} baixo={baixo} imagens={len(imagens())} "
            f"dim={DIM_SECONDS:g}s slide={SLIDE_SECONDS:g}s brilho_slide={baixo_slide} "
            f"musica={MUSIC_RAW} piso={MUSIC_FLOOR:g}"
        )
        sys.exit(0)

    volume_restaurar()
    fds = entradas()
    if not fds:
        sys.exit("sem dispositivos de entrada")

    dimmed = False
    shown = False
    descanso = False
    last = time.monotonic()
    last_scan = last

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
            if not jogo_rodando() and not app_de_console():
                if not dimmed and parado >= DIM_SECONDS:
                    write_bright(baixo)
                    volume_baixar(baixo / normal)
                    dimmed = True
                if (not descanso and not shown and parado >= SLIDE_SECONDS and not jogo_rodando()
                        and not app_de_console() and not app_pelo_menu()):
                    parar_es()
                    dimmed = True
                    shown = True
                    write_bright(baixo_slide)
                    volume_baixar(baixo_slide / normal)
                    musica_ligar()
                    if not slideshow(baixo_slide):
                        shown = False
                        musica_desligar()
                        volume_restaurar()
                        if jogo_rodando():
                            # um jogo comecou durante o slideshow: nao mexe em nada
                            pass
                        else:
                            # ninguem mexeu em 30 min de slideshow: para de ciclar e
                            # entra no descanso profundo (menu fora, brilho minimo, sem musica)
                            write_bright(int(maxb * RESTING_PERCENT / 100))
                            descanso = True
                            log("descanso profundo: menu fora, musica desligada, aguardando toque")
                    else:
                        tocar()

        agora = time.monotonic()
        if agora - last_scan >= 5:
            last_scan = agora
            fds.update(entradas(fds))
            for dev in [d for d in fds if not os.path.exists(d)]:
                try:
                    os.close(fds.pop(dev))
                except OSError:
                    pass
