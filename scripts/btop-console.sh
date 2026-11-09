#!/bin/bash
# Abre o btop no console do R36S e fecha com START/SELECT (evdev 704-708) ou L+R.
# Instale em /usr/local/bin/btop-console.sh e chame com systemd-run a partir do menu.
# Nunca parar o EmulationStation com jogo aberto: o jogo e filho dele e morre junto.
if pgrep -x drastic >/dev/null || pgrep -x retroarch >/dev/null || pgrep -x mupen64plus >/dev/null \
   || pgrep -x love >/dev/null || pgrep -x ppsspp >/dev/null; then
  echo "Jogo aberto: feche o jogo antes de abrir este app."
  sleep 4
  exit 1
fi
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty1 /dev/tty0 /dev/input/event1

# 8x16: 80 colunas x 30 linhas em 640x480. A fonte de 6px cabe mas é ilegível.
setfont /usr/share/consolefonts/Lat15-TerminusBold16.psf.gz < /dev/tty1
stty -F /dev/tty1 cols 80 rows 30
printf "\033c" > /dev/tty1
printf "START, SELECT ou L+R fecha\n" > /dev/tty1

openvt -c 1 -f -s -- btop
sleep 0.6
BPID=$(pgrep -n -x btop)
# ignora o botão que acabou de abrir o menu
sleep 1.2

while [ -n "$BPID" ] && kill -0 "$BPID" 2>/dev/null; do
  hit=0
  for k in 704 705 706 707 708; do
    evtest --query /dev/input/event1 EV_KEY "$k"
    [ "$?" -eq 10 ] && hit=1
  done
  evtest --query /dev/input/event1 EV_KEY 310; l=$?
  evtest --query /dev/input/event1 EV_KEY 311; r=$?
  if [ "$hit" -eq 1 ] || { [ "$l" -eq 10 ] && [ "$r" -eq 10 ]; }; then
    kill "$BPID" 2>/dev/null
    break
  fi
  sleep 0.12
done

wait "$BPID" 2>/dev/null
setfont /usr/share/consolefonts/Lat7-Terminus20x10.psf.gz < /dev/tty1
printf "\033c" > /dev/tty1
systemctl start emulationstation
