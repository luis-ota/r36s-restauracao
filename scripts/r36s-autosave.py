#!/usr/bin/env python3
"""Load ao abrir e autosave real para o DraStic, por um teclado virtual.

O jogo sempre abre do zero, entao salvar antes de um load apagaria o progresso.
Ao abrir, o servico aperta F7 (carrega o slot ativo). O autosave so liga depois
de confirmar que o DraStic leu um .dss logo apos o F7 ou o L1, e desliga quando
o jogo fecha. Sem nenhum botao apertado desde o ultimo save, nao salva de novo.
"""
import ctypes
import fcntl
import glob
import os
import select
import signal
import struct
import time

INTERVALO = int(os.environ.get("AUTOSAVE_SEG", "180"))
SAVESTATES = os.environ.get("AUTOSAVE_DIR", "/mnt/jogos/nds/savestates")
LOCK_BACKUP = "/home/ark/pokemon-backups/.lock"
CONTROLE = "GO-Super Gamepad"
JANELA_LOAD = 3.0    # segundos entre o L1/F7 e a leitura do .dss
JOGO_NOVO = 30       # so faz load automatico em processo mais novo que isso
ESPERA_LOAD = 6.0    # segundos entre as tentativas de load automatico
MAX_TENTATIVAS = 3
SEGURAR_FECHAR = 1.0  # segundos segurando SELECT + START para fechar
ESPERA_SAVE = 3.0     # o DraStic grava em segundo plano

BTN_L1 = 310
BTN_R1 = 311
COMBO_FECHAR = {704, 705}  # SELECT e START
KEY_F5 = 63
KEY_F7 = 65
EV_KEY = 1
EV_ABS = 3
ABS_HAT0X = 16
ABS_HAT0Y = 17

IN_ACCESS = 0x1
IN_OPEN = 0x20
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
EVENTO = struct.Struct("llHHi")


def log(msg):
    print(msg, flush=True)


def achar_controle():
    for caminho in sorted(glob.glob("/sys/class/input/event*/device/name")):
        with open(caminho) as f:
            if f.read().strip() == CONTROLE:
                return "/dev/input/" + caminho.split("/")[4]
    raise SystemExit("controle nao encontrado")


def pid_drastic():
    for caminho in glob.glob("/proc/[0-9]*/comm"):
        try:
            with open(caminho, "rb") as f:
                if f.read().strip() == b"drastic":
                    return int(caminho.split("/")[2])
        except OSError:
            continue
    return None


def idade_processo(pid):
    """Segundos desde que o processo comecou; infinito se nao der para saber."""
    try:
        with open("/proc/%d/stat" % pid, "rb") as f:
            campos = f.read().rsplit(b")", 1)[1].split()
        with open("/proc/uptime") as f:
            uptime = float(f.read().split()[0])
    except (OSError, IndexError, ValueError):
        return float("inf")
    return uptime - int(campos[19]) / os.sysconf("SC_CLK_TCK")


def backup_rodando():
    """O backup tambem le os .dss; essas leituras nao contam como load."""
    try:
        fd = os.open(LOCK_BACKUP, os.O_RDONLY)
    except OSError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except OSError:
        return True
    finally:
        os.close(fd)


def abrir_inotify():
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    fd = libc.inotify_init()
    if fd < 0 or libc.inotify_add_watch(fd, SAVESTATES.encode(), IN_OPEN | IN_ACCESS) < 0:
        raise SystemExit("inotify falhou em " + SAVESTATES)
    os.set_blocking(fd, False)
    return fd


def leu_savestate(fd):
    try:
        dados = os.read(fd, 8192)
    except BlockingIOError:
        return False
    pos = 0
    achou = False
    while pos + 16 <= len(dados):
        tamanho = struct.unpack_from("iIII", dados, pos)[3]
        nome = dados[pos + 16 : pos + 16 + tamanho].rstrip(b"\0")
        achou = achou or nome.endswith(b".dss")
        pos += 16 + tamanho
    return achou


def apertar(tecla_alvo):
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    try:
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
        for tecla in range(1, 249):
            fcntl.ioctl(fd, UI_SET_KEYBIT, tecla)
        dev = struct.pack("80sHHHHI", b"r36s-kbd\0", 3, 0x1, 0x1, 0x1, 0)
        os.write(fd, dev.ljust(1116, b"\0"))
        fcntl.ioctl(fd, UI_DEV_CREATE)
        time.sleep(2.5)  # tempo para o SDL enxergar o teclado novo
        os.write(fd, EVENTO.pack(0, 0, EV_KEY, tecla_alvo, 1) + EVENTO.pack(0, 0, 0, 0, 0))
        time.sleep(0.25)
        os.write(fd, EVENTO.pack(0, 0, EV_KEY, tecla_alvo, 0) + EVENTO.pack(0, 0, 0, 0, 0))
        time.sleep(0.5)
        fcntl.ioctl(fd, UI_DEV_DESTROY)
    finally:
        os.close(fd)


def main():
    controle = os.open(achar_controle(), os.O_RDONLY | os.O_NONBLOCK)
    inotify = abrir_inotify()
    log("servico iniciado: a cada %d s, depois de um load" % INTERVALO)

    pid = None
    armado = False
    proximo = 0.0
    atividade = False
    ultimo_load = ultimo_read = None
    tentativas = MAX_TENTATIVAS
    proximo_load = 0.0
    apertados = set()
    combo_desde = None

    while True:
        espera = 0.25 if combo_desde is not None else 2.0
        prontos, _, _ = select.select([controle, inotify], [], [], espera)
        agora = time.monotonic()

        if controle in prontos:
            dados = os.read(controle, EVENTO.size * 64)
            for i in range(0, len(dados), EVENTO.size):
                _, _, tipo, codigo, valor = EVENTO.unpack_from(dados, i)
                if tipo == EV_KEY and codigo in COMBO_FECHAR:
                    (apertados.add if valor else apertados.discard)(codigo)
                if tipo == EV_KEY and valor == 1:
                    atividade = True
                    if codigo == BTN_L1:
                        ultimo_load = agora
                    elif codigo == BTN_R1 and armado:
                        proximo = agora + INTERVALO
                elif tipo == EV_ABS and codigo in (ABS_HAT0X, ABS_HAT0Y) and valor:
                    atividade = True

        if apertados != COMBO_FECHAR:
            combo_desde = None
        elif combo_desde is None:
            combo_desde = agora

        if inotify in prontos and leu_savestate(inotify) and not backup_rodando():
            ultimo_read = agora

        # com o jogo aberto, confere so o proprio processo em vez de varrer o /proc
        atual = pid if pid and os.path.exists("/proc/%d/comm" % pid) else pid_drastic()
        if atual != pid:
            pid = atual
            armado = False
            ultimo_load = ultimo_read = None
            if pid and idade_processo(pid) < JOGO_NOVO:
                tentativas = 0
                proximo_load = agora + ESPERA_LOAD
                log("jogo aberto, vou carregar o state")
            else:
                tentativas = MAX_TENTATIVAS
                log("jogo aberto, aguardando L1" if pid else "jogo fechado, autosave desligado")

        if (
            pid
            and ultimo_load is not None
            and ultimo_read is not None
            and abs(ultimo_load - ultimo_read) <= JANELA_LOAD
        ):
            ultimo_load = ultimo_read = None
            armado = True
            atividade = False
            tentativas = MAX_TENTATIVAS
            proximo = agora + INTERVALO
            log("load detectado, autosave ligado")

        if pid and not armado and tentativas < MAX_TENTATIVAS and agora >= proximo_load:
            leu_savestate(inotify)  # descarta leituras antigas
            ultimo_read = None
            apertar(KEY_F7)
            tentativas += 1
            ultimo_load = proximo_load = time.monotonic()
            proximo_load += ESPERA_LOAD
            log("F7 enviado, tentativa %d de %d" % (tentativas, MAX_TENTATIVAS))
            if tentativas == MAX_TENTATIVAS:
                log("se o state nao carregou, aperte L1")

        if pid and combo_desde is not None and agora - combo_desde >= SEGURAR_FECHAR:
            combo_desde = None
            apertados.clear()
            if armado and pid_drastic() == pid:
                apertar(KEY_F5)
                time.sleep(ESPERA_SAVE)
                log("salvo antes de fechar")
            armado = False
            try:
                os.kill(pid, signal.SIGTERM)
                log("atalho SELECT + START: jogo fechado")
            except ProcessLookupError:
                pass
            continue

        if armado and agora >= proximo:
            proximo = agora + INTERVALO
            if atividade and pid_drastic() == pid:
                atividade = False
                apertar(KEY_F5)
                log("state salvo automaticamente")
            elif not atividade:
                log("sem botao apertado desde o ultimo save, pulei")


if __name__ == "__main__":
    main()
