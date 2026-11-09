#!/bin/bash
# Roda o PortMaster com o EmulationStation parado.
# Dois programas usando o display ao mesmo tempo deixam a imagem sobreposta.
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty0 /dev/tty1 /dev/input/event1 2>/dev/null
printf "\033c" > /dev/tty1
/opt/system/Tools/PortMaster.sh
printf "\033c" > /dev/tty1
systemctl start emulationstation
