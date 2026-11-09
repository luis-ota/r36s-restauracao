#!/bin/bash
# Restaura o backup mais recente do save do Pokemon.
# Pode ser chamado do menu (Ports) ou por SSH. Nunca roda com o jogo aberto.
set -u

CARD=/mnt/jogos/nds
BAK=/home/ark/pokemon-backups
JOGO="Pokemon - Black Version"
LOG=/home/ark/pokemon-backups/restauracao.log

log() { echo "$(date '+%F %T') $*" >>"$LOG"; }

if pgrep -x drastic >/dev/null; then
  log "RECUSADO: jogo aberto"
  echo "Feche o jogo antes de restaurar."
  sleep 4
  exit 1
fi

[ -d "$BAK/$JOGO.dsv" ] || { log "sem backups de .dsv"; echo "Sem backups do save."; sleep 4; exit 1; }

ultimo_dsv=$(ls -1 "$BAK/$JOGO.dsv" | grep -E '^[0-9]{6}\.dsv$' | sort | tail -n 1)
mkdir -p "$CARD/backup"
[ -f "$CARD/backup/$JOGO.dsv" ] && cp -f "$CARD/backup/$JOGO.dsv" "/tmp/save-antes-de-restaurar.dsv"
cp -f "$BAK/$JOGO.dsv/$ultimo_dsv" "$CARD/backup/$JOGO.dsv"
log "restaurado .dsv $ultimo_dsv (atual guardado em /tmp/save-antes-de-restaurar.dsv)"

# savestate mais recente do slot 0, se existir
dir_ss="$BAK/${JOGO}_0.dss"
if [ -d "$dir_ss" ]; then
  ultimo_dss=$(ls -1 "$dir_ss" | grep -E '^[0-9]{6}\.dss$' | sort | tail -n 1)
  if [ -n "${ultimo_dss:-}" ]; then
    mkdir -p "$CARD/savestates"
    [ -f "$CARD/savestates/${JOGO}_0.dss" ] && cp -f "$CARD/savestates/${JOGO}_0.dss" "/tmp/state-antes-de-restaurar.dss"
    cp -f "$dir_ss/$ultimo_dss" "$CARD/savestates/${JOGO}_0.dss"
    log "restaurado savestate $ultimo_dss (atual guardado em /tmp/state-antes-de-restaurar.dss)"
  fi
fi

sync
log "fim: $(ls -l "$CARD/backup/$JOGO.dsv" | awk '{print $5" bytes"}')"
echo "Restaurado. Abra o jogo e use Continuar (ou Load state 0)."
