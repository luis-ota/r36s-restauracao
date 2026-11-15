#!/bin/bash
# Usa o celular como fonte de internet pela porta OTG, sem o dongle de Wi-Fi.
#
# Como funciona: a mesma porta USB-C que roda o dongle roda em modo host. Para
# isso e preciso tirar o R36S do modo "gadget" (g_ether), que e o que o PC usa.
#
# Requer: adaptador OTG (USB-C macho -> USB-A femea), cabo do celular e
# "Tethering USB" ligado no celular. Android (RNDIS) funciona; iPhone nao,
# porque o kernel 4.4 deste aparelho nao tem o modulo ipheth.
#
# Uso:
#   sudo r36s-tether.sh          liga (espera o celular aparecer)
#   sudo r36s-tether.sh --off    volta ao modo gadget (PC ve o R36S de novo)
set -u

erro() { echo "erro: $*" >&2; exit 1; }

if [ "${1:-}" = "--off" ]; then
  modprobe -r rndis_host 2>/dev/null
  modprobe g_ether 2>/dev/null
  systemctl start r36s-usbnet 2>/dev/null
  sleep 1
  echo "modo gadget restaurado: $(ls /sys/class/net | tr '\n' ' ')"
  exit 0
fi

[ -x /usr/sbin/dhclient ] || erro "sem dhclient"

# 1) libera a porta (o R36S deixa de aparecer como dispositivo USB)
systemctl stop r36s-usbnet 2>/dev/null
modprobe -r g_ether 2>/dev/null
sleep 1

# 2) drivers de host
for m in usbnet rndis_host cdc_ether; do modprobe "$m" 2>/dev/null; done

# 3) espera a interface do celular (usb0/eth1, tipicamente)
IF=""
for _ in $(seq 1 25); do
  for d in /sys/class/net/usb* /sys/class/net/eth*; do
    [ -e "$d" ] || continue
    n=$(basename "$d")
    case "$n" in
      usb0|usb1|eth0|eth1) IF=$n; break 2 ;;
    esac
  done
  sleep 1
done

if [ -z "$IF" ]; then
  echo "nenhuma interface do celular apareceu."
  echo "Confira o adaptador OTG, o cabo e o 'Tethering USB' ligado no celular."
  modprobe g_ether 2>/dev/null
  systemctl start r36s-usbnet 2>/dev/null
  exit 1
fi

echo "interface do celular: $IF"
ip link set "$IF" up
sleep 1
/usr/sbin/dhclient -v "$IF" 2>&1 | tail -n 4
ip -4 -br addr show "$IF"

echo "--- teste de internet"
if ping -c 2 -W 3 1.1.1.1 >/dev/null 2>&1; then
  echo "internet ok pelo celular"
else
  echo "sem internet: confira se o celular esta com dados moveis e tethering ligado"
fi
