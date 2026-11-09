#!/bin/bash
# Atalho do menu Ports: /roms/ports/AbrirPortMaster.sh (o nome PortMaster.sh some ao abrir)
sudo systemd-run --unit=portmaster --collect /usr/local/bin/portmaster-console.sh
