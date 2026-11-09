#!/bin/bash
# Roda o PortMaster com o EmulationStation parado.
# Dois programas usando o display ao mesmo tempo deixam a imagem sobreposta.
# Nunca parar o EmulationStation com jogo aberto: o jogo e filho dele e morre junto.
if pgrep -x drastic >/dev/null || pgrep -x retroarch >/dev/null || pgrep -x mupen64plus >/dev/null \
   || pgrep -x love >/dev/null || pgrep -x ppsspp >/dev/null; then
  echo "Jogo aberto: feche o jogo antes de abrir este app."
  sleep 4
  exit 1
fi
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty0 /dev/tty1 /dev/input/event1 2>/dev/null
printf "\033c" > /dev/tty1
/opt/system/Tools/PortMaster.sh
printf "\033c" > /dev/tty1
systemctl start emulationstation
