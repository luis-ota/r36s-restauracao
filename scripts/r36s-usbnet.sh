#!/bin/bash
# Sobe a rede por USB (gadget) para acessar o R36S pelo cabo OTG.
# O IP do aparelho e 192.168.7.2; no PC, use 192.168.7.1/24.
set -u
IP=${USB_IP:-192.168.7.2}
CIDR=${USB_CIDR:-24}

modprobe dwc2 2>/dev/null
modprobe libcomposite 2>/dev/null
modprobe g_ether 2>/dev/null

# O controlador pode estar em modo host quando o Wi-Fi esta na porta.
# Espera ele virar dispositivo (udc) por ate 60 s.
for _ in $(seq 1 60); do
  [ -e /sys/class/udc ] && [ -n "$(ls /sys/class/udc 2>/dev/null)" ] && [ -e /sys/class/net/usb0 ] && break
  sleep 1
done

[ -e /sys/class/net/usb0 ] || { echo "usb0 nao apareceu (porta em modo host?)"; exit 0; }

ip link set usb0 up
ip addr replace "$IP/$CIDR" dev usb0
ip -br addr show usb0
