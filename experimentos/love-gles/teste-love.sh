#!/bin/bash
# Teste do LÖVE no aparelho: roda main.lua, captura a tela e devolve o menu.
# Uso no PC: ./teste-love.sh
# Pré-requisitos: ssh sem senha para o host "r36s", drmcap instalado no aparelho
# (/usr/local/bin/drmcap, ver doc 08), main.lua em /mnt/jogos/love-test/.
# Nunca para o EmulationStation com jogo aberto: o script confere antes.

set -u
HOST=r36s
L=/opt/system/Tools/PortMaster/runtimes/love_11.5

ssh "$HOST" bash -s <<REMOTO
if pgrep -x drastic >/dev/null || pgrep -x retroarch >/dev/null; then
  echo "JOGO ABERTO: nao mexi no menu"; exit 0
fi
sudo mkdir -p /run/user/1002 && sudo chown ark:ark /run/user/1002 && sudo chmod 700 /run/user/1002
sudo systemctl stop emulationstation 2>/dev/null; sleep 2
sudo -u ark env LD_LIBRARY_PATH=$L/libs.aarch64 XDG_RUNTIME_DIR=/run/user/1002 SDL_AUDIODRIVER=alsa \
  timeout 30 $L/love.aarch64 /mnt/jogos/love-test >/tmp/love.log 2>&1 &
sleep 9
sudo drmcap /tmp/love.raw && sudo chmod 644 /tmp/love.raw
wait
echo "=== log do LÖVE ==="; tail -n 6 /tmp/love.log
sudo systemctl start emulationstation; sleep 6
echo "emulationstation: \$(systemctl is-active emulationstation)"
REMOTO

scp -q "$HOST:/tmp/love.raw" love.raw && \
  ffmpeg -y -v error -f rawvideo -pix_fmt bgra -s 640x480 -i love.raw love.png && \
  echo "captura em love.png"
