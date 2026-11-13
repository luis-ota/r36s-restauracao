#!/bin/bash
# Teste parametrizado do N64 no R36S.
# Uso: sudo bash teste-n64.sh <glide|rice> [duração] [low]
# "low" aplica o preset de menor custo gráfico. Restaura a config no fim.
PLUGIN="${1:-glide}"
DUR="${2:-60}"
LOW="${3:-}"
ROM="/mnt/jogos/n64/Legend of Zelda, The - Ocarina of Time (USA) (Rev 2).z64"
M=/opt/mupen64plus
CFG=/home/ark/.config/mupen64plus/mupen64plus.cfg
TAG="$PLUGIN${LOW:+-$LOW}"

if pgrep -x drastic >/dev/null || pgrep -x retroarch >/dev/null || pgrep -x mupen64plus >/dev/null || pgrep -x love.aarch64 >/dev/null; then
  echo "JOGO ABERTO, NAO MEXI"; exit 0
fi

cp "$CFG" /tmp/mupen64plus.cfg.bak
case "$PLUGIN" in
  glide)
    GFX=mupen64plus-video-glide64mk2.so
    sed -i 's/^vsync = True/vsync = False/' "$CFG"
    sed -i 's/^show_fps = .*/show_fps = 7/' "$CFG"
    if [ "$LOW" = "low" ]; then
      sed -i 's/^wrpResolution = .*/wrpResolution = 0/' "$CFG"
      sed -i 's/^ghq_fltr = .*/ghq_fltr = 1/' "$CFG"
      sed -i 's/^ghq_enht = .*/ghq_enht = 0/' "$CFG"
      sed -i 's/^ghq_hirs = .*/ghq_hirs = 0/' "$CFG"
      sed -i 's/^ghq_cmpr = .*/ghq_cmpr = 0/' "$CFG"
      sed -i 's/^wrpAntiAliasing = .*/wrpAntiAliasing = 0/' "$CFG"
    fi
    ;;
  rice)
    GFX=mupen64plus-video-rice.so
    sed -i 's/^VerticalSync = True/VerticalSync = False/' "$CFG"
    sed -i 's/^ShowFPS = .*/ShowFPS = True/' "$CFG"
    if [ "$LOW" = "low" ]; then
      sed -i 's/^InN64Resolution = .*/InN64Resolution = True/' "$CFG"
      sed -i 's/^TextureEnhancement = .*/TextureEnhancement = 0/' "$CFG"
      sed -i 's/^ForceTextureFilter = .*/ForceTextureFilter = 0/' "$CFG"
      sed -i 's/^Mipmapping = .*/Mipmapping = 0/' "$CFG"
      sed -i 's/^AnisotropicFiltering = .*/AnisotropicFiltering = 0/' "$CFG"
    fi
    ;;
  *) echo "plugin invalido"; exit 2 ;;
esac

[ -x /usr/local/bin/r36s-perf.sh ] && /usr/local/bin/r36s-perf.sh >/dev/null 2>&1
systemctl stop r36s-idle
systemctl stop emulationstation
sleep 2
mkdir -p /run/user/1002 && chown ark:ark /run/user/1002 && chmod 700 /run/user/1002
rm -f /tmp/zcap_*.raw

(
  for n in $(seq -w 1 8); do
    sleep 10
    drmcap /tmp/zcap_$n.raw >/dev/null 2>&1
  done
) &

sudo -u ark env XDG_RUNTIME_DIR=/run/user/1002 SDL_AUDIODRIVER=alsa \
  timeout "$DUR" "$M/mupen64plus" --resolution 640x480 --plugindir "$M" \
  --gfx "$GFX" --corelib "$M/libmupen64plus.so.2" \
  --datadir "$M" --configdir /home/ark/.config/mupen64plus "$ROM" >/tmp/mupen-$TAG.log 2>&1 &
EMU=$!

: > /tmp/mupen-stats-$TAG.txt
for t in $(seq 10 10 "$DUR"); do
  sleep 10
  P=$(pgrep -x mupen64plus | head -n1)
  [ -n "$P" ] && ps -o rss=,pcpu= -p "$P" | awk -v t="$t" '{print t"s rss="int($1/1024)"MB cpu="$2"%"}' >> /tmp/mupen-stats-$TAG.txt
done
wait
echo "mupen rc=$?"
echo "=== stats ==="; cat /tmp/mupen-stats-$TAG.txt
echo "capturas: $(ls /tmp/zcap_*.raw 2>/dev/null | wc -l)"
for f in /tmp/zcap_*.raw; do [ -e "$f" ] && mv "$f" "${f/zcap_/zcap-$TAG-}"; done
chmod 644 /tmp/zcap-$TAG-*.raw 2>/dev/null

cp /tmp/mupen64plus.cfg.bak "$CFG"
systemctl start emulationstation
systemctl start r36s-idle
sleep 3
cat /etc/r36s-idle.normal | tee /sys/class/backlight/backlight/brightness >/dev/null
echo "fim: es=$(systemctl is-active emulationstation) idle=$(systemctl is-active r36s-idle) brilho=$(cat /sys/class/backlight/backlight/brightness)"
