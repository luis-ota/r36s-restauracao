#!/bin/bash
# Launcher de N64 do ArkOS. Aceita as duas formas de chamada:
#   n64.sh <emulador> <rom>              (standalone, %CORE% vazio)
#   n64.sh <emulador> <core> <rom>       (retroarch, %CORE% preenchido)
# Nos standalone, sobe o n64-quitter.py: SELECT + START fecha o emulador.
ROM="${3:-$2}"

QUITTER=""
iniciar_quitter() {
  /usr/local/bin/n64-quitter.py >/dev/null 2>&1 &
  QUITTER=$!
}
parar_quitter() {
  [ -n "$QUITTER" ] && kill "$QUITTER" 2>/dev/null
  QUITTER=""
}
trap parar_quitter EXIT

if  [[ $1 == "standalone-Rice" ]]; then
iniciar_quitter
/opt/mupen64plus/mupen64plus --resolution 640x480 --plugindir /opt/mupen64plus --gfx mupen64plus-video-rice.so --corelib /opt/mupen64plus/libmupen64plus.so.2 --datadir /opt/mupen64plus "$ROM"
elif [[ $1 == "standalone-Glide64mk2" ]]; then
iniciar_quitter
/opt/mupen64plus/mupen64plus --resolution 640x480 --plugindir /opt/mupen64plus --gfx mupen64plus-video-glide64mk2.so --corelib /opt/mupen64plus/libmupen64plus.so.2 --datadir /opt/mupen64plus "$ROM"
else
/usr/local/bin/"$1" -L /home/ark/.config/"$1"/cores/"$2"_libretro.so "$3"
fi
