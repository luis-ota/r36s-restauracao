#!/bin/bash
# Abre o opencode no console do R36S, como o btop.
# O menu para, o opencode roda na tty1 (com o teclado virtual) e o menu volta ao sair.
set -u
BIN=/mnt/jogos/opencode/opencode

[ -x "$BIN" ] || { echo "opencode nao encontrado em $BIN"; sleep 5; exit 1; }

touch /tmp/r36s-console.lock
trap 'rm -f /tmp/r36s-console.lock' EXIT
# Nunca parar o EmulationStation com jogo aberto: o jogo e filho dele e morre junto.
if pgrep -x drastic >/dev/null || pgrep -x retroarch >/dev/null || pgrep -x mupen64plus >/dev/null \
   || pgrep -x love >/dev/null || pgrep -x ppsspp >/dev/null; then
  echo "Jogo aberto: feche o jogo antes de abrir este app."
  sleep 4
  exit 1
fi
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty1 /dev/tty0 2>/dev/null
setfont /usr/share/consolefonts/Lat15-TerminusBold16.psf.gz < /dev/tty1 2>/dev/null
stty -F /dev/tty1 cols 80 rows 30 2>/dev/null
printf "\033c" > /dev/tty1

/usr/local/bin/r36s-keys.py >/tmp/r36s-keys.log 2>&1 &
KPID=$!

cd /home/ark
# -w espera o programa terminar; sem isso o menu voltaria por cima
setsid openvt -c 1 -f -s -- "$BIN" "$@" < /dev/tty1 > /dev/tty1 2>&1
# espera o processo do opencode terminar
for _ in $(seq 1 3600); do
  pgrep -x opencode >/dev/null || break
  sleep 1
done

kill "$KPID" 2>/dev/null
pkill -f "opencode serve --service" 2>/dev/null
setfont /usr/share/consolefonts/Lat7-Terminus20x10.psf.gz < /dev/tty1 2>/dev/null
printf "\033c" > /dev/tty1
systemctl start emulationstation
