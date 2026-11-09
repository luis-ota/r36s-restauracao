#!/bin/bash
# Atalho do menu Ports: /roms/ports/btop.sh
sudo systemd-run --unit=btop-console --collect /usr/local/bin/btop-console.sh
