#!/bin/sh
CPU=/sys/devices/system/cpu/cpufreq/policy0
GPU=/sys/devices/platform/ff400000.gpu/devfreq/ff400000.gpu
chmod 666 "$CPU/scaling_governor" "$CPU/scaling_min_freq" "$GPU/governor" 2>/dev/null
echo performance > "$CPU/scaling_governor"
echo 1296000 > "$CPU/scaling_min_freq"
echo performance > "$GPU/governor"
# cartao de jogos: leitura da ROM nao fica atras de um save
[ -w /sys/block/mmcblk1/queue/scheduler ] && echo deadline > /sys/block/mmcblk1/queue/scheduler
