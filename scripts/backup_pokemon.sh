#!/bin/bash
# Backup versionado dos saves do Pokemon Black. Roda pelo cron a cada 5 minutos.
#
# Guarda uma versao nova so quando o arquivo muda, entao um save estragado nao
# empurra as copias boas para fora. Os backups ficam em outra particao, porque
# uma corrupcao em /roms costuma levar a pasta inteira junto.
#
# Para restaurar, com o jogo fechado, copie a versao desejada de volta:
#   cp ~/pokemon-backups/"Pokemon - Black Version.dsv"/000123.dsv \
#      /roms/nds/backup/"Pokemon - Black Version.dsv"

set -u

GAMES=("Pokemon - Black Version")

DEST="${DEST_DIR:-/home/ark/pokemon-backups}"
MIN_AGE="${MIN_AGE:-15}"              # segundos sem mudar antes de copiar
MIN_FREE_MB="${MIN_FREE_MB:-100}"     # nao ocupa o resto do disco do sistema
MIN_DSV_KB="${MIN_DSV_KB:-64}"        # .dsv menor que isso e save vazio do DraStic

# Quantas versoes manter: recentes, mais "marcos" (uma a cada 10) para ter
# algo antigo se o estrago so for percebido bem depois.
KEEP_DSV=12; MARKS_DSV=12
KEEP_DSS=12; MARKS_DSS=6

# Numera as versoes em vez de usar a data: o relogio deste aparelho volta para
# 2020 quando liga sem rede.

if [ -n "${ROMS_DIR:-}" ]; then
  ROMS="$ROMS_DIR"
elif mountpoint -q /mnt/jogos; then
  ROMS=/mnt/jogos
elif mountpoint -q /roms2; then
  ROMS=/roms2
else
  ROMS=/roms
fi

mkdir -p "$DEST" || exit 1
LOG="$DEST/backup.log"

log() {
  echo "$(date '+%F %T') $*" >> "$LOG"
  if [ "$(wc -l < "$LOG")" -gt 400 ]; then
    tail -n 200 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  fi
}

exec 9> "$DEST/.lock"
flock -n 9 || exit 0

is_blank() {
  [ ! -s "$1" ] || [ "$(tr -d '\0' < "$1" | head -c 1 | wc -c)" -eq 0 ]
}

versions() {
  find "$1" -maxdepth 1 -type f -regextype posix-extended \
    -regex '.*/[0-9]{6}\.(dsv|dss)' -printf '%f\n' | sort
}

prune() {
  local dir=$1 recent=$2 marks=$3 name num i
  local -a all
  local -A keep=()
  mapfile -t all < <(versions "$dir")

  for ((i = ${#all[@]} - 1; i >= 0; i--)); do
    name=${all[i]}
    num=$((10#${name%%.*}))
    if ((recent > 0)); then
      keep[$name]=1
      recent=$((recent - 1))
    elif ((marks > 0 && num % 10 == 0)); then
      keep[$name]=1
      marks=$((marks - 1))
    fi
  done

  for name in "${all[@]}"; do
    [ -n "${keep[$name]:-}" ] || rm -f -- "${dir:?}/$name"
  done
}

backup_file() {
  local src=$1 recent=$2 marks=$3
  local base ext dir newest next tmp target age free

  [ -f "$src" ] || return 0
  base=${src##*/}
  ext=${base##*.}
  dir="$DEST/$base"

  age=$(($(date +%s) - $(stat -c %Y "$src")))
  # Idade negativa significa relogio ajustado depois da gravacao: pode copiar.
  if ((age >= 0 && age < MIN_AGE)); then
    return 0
  fi

  if [ "$ext" = "dsv" ] && [ "$(stat -c %s "$src")" -lt $((MIN_DSV_KB * 1024)) ]; then
    log "IGNORADO, .dsv pequeno demais (save vazio): $base"
    return 0
  fi

  if is_blank "$src"; then
    log "IGNORADO, arquivo vazio ou zerado: $base"
    return 0
  fi

  mkdir -p "$dir" || return 1
  newest=$(versions "$dir" | tail -n 1)
  if [ -n "$newest" ] && cmp -s "$src" "$dir/$newest"; then
    return 0
  fi

  free=$(df -Pm "$DEST" | awk 'NR==2 {print $4}')
  if [ "$free" -lt "$MIN_FREE_MB" ]; then
    log "SEM ESPACO, ${free} MB livres, nao copiei: $base"
    return 1
  fi

  tmp="$dir/.tmp.$$"
  if ! cp -- "$src" "$tmp" || ! sync -- "$tmp" || ! cmp -s "$src" "$tmp"; then
    rm -f -- "$tmp"
    log "FALHA ao copiar: $base"
    return 1
  fi

  next=1
  [ -z "$newest" ] || next=$((10#${newest%%.*} + 1))
  printf -v target '%06d.%s' "$next" "$ext"
  mv -- "$tmp" "$dir/$target" || { rm -f -- "$tmp"; return 1; }
  sync -- "$dir"
  log "NOVA VERSAO $target: $base"

  prune "$dir" "$recent" "$marks"
}

# Espelha o ultimo state bom do slot principal no slot 9, para carregar pela
# interface do DraStic (Load state -> 9) sem mexer em arquivos.
espelhar_slot9() {
  local jogo=$1 dir_ss="$ROMS/nds/savestates" origem destino ultimo
  # pega o backup mais recente entre todos os slots (0 = manual, 1 = ativo)
  origem=$(ls -1t "$DEST/${jogo}"_*.dss/*.dss 2>/dev/null | head -n 1)
  [ -n "$origem" ] || return 0
  ultimo=${origem##*/}
  destino="$dir_ss/${jogo}_9.dss"
  cmp -s "$origem" "$destino" && return 0
  cp -f "$origem" "$destino.tmp" && sync -- "$destino.tmp" && mv -f "$destino.tmp" "$destino" || return 1
  log "SLOT 9 atualizado com ${origem#"$DEST"/}"
}

# Sem a pasta, a particao pode estar desmontada. Nada e apagado nesse caso.
[ -d "$ROMS/nds/backup" ] || exit 0

status=0
for game in "${GAMES[@]}"; do
  backup_file "$ROMS/nds/backup/$game.dsv" "$KEEP_DSV" "$MARKS_DSV" || status=1

  for state in "$ROMS/nds/savestates/$game"_*.dss; do
    [ "${state##*_}" = "9.dss" ] && continue
    backup_file "$state" "$KEEP_DSS" "$MARKS_DSS" || status=1
  done
  espelhar_slot9 "$game" || status=1
done

exit "$status"
