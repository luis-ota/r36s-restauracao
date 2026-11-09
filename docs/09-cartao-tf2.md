# 09 — Cartão TF2 (segundo cartão de ROMs)

O R36S tem duas portas de cartão: a interna (sistema) e a TF2. O ArkOS suporta mover as ROMs para a TF2, mas o script que faz isso tem particularidades que quebram o fluxo se você não souber.

## Preparar o cartão

Requisitos:

- **FAT32** (o kernel 4.4 monta `vfat`). Não use exFAT.
- Uma partição primária cobrindo o disco.
- Setor inicial **2048** (alinhamento moderno). Layout antigo começando no setor 63 funciona, mas é desnecessário.
- Rótulo livre (ex.: `ROMS`).

```bash
sudo sfdisk /dev/sdX <<'EOF'
label: dos
start=2048, type=c
EOF
sudo mkfs.vfat -F 32 -n ROMS /dev/sdX1
```

As pastas de ROM ficam na **raiz** do cartão, com os nomes que o ArkOS espera:

```
nds/ gba/ snes/ sfc/ n64/ gbc/ nes/ megadrive/
```

## O que o script "Switch to SD2 for Roms" faz

Ele está em `/opt/system/Advanced/Switch to SD2 for Roms.sh`. Em resumo:

1. Cria `/roms2` se não existir.
2. Descobre o dispositivo (`/dev/mmcblk1p1` ou `/dev/mmcblk1`) e o filesystem.
3. Desmonta o bind de `/opt/system/Tools`.
4. Monta o cartão em `/roms2`.
5. **Cria um swapfile de 256 MB**, ativa e — no fim do script — desativa e apaga. É temporário, mas é escrita no cartão.
6. Monta `/roms2/tools` em `/opt/system/Tools` (bind).
7. Reescreve `/etc/emulationstation/es_systems.cfg` trocando `/roms/` por `/roms2/`.
8. Adiciona a linha do cartão no `/etc/fstab`.
9. Ajusta dezenas de scripts (`drastic.sh`, `ppsspp.sh`, retroarch.cfg, etc.).
10. Extrai `/roms.tar` no cartão, move `/roms2/roms/*` para a raiz, copia `ports`.
11. Ajusta symlinks de saves do DraStic para `/roms2/nds/...`.

Existe o inverso em `/usr/local/bin/Switch to main SD for Roms.sh`.

## A pegadinha do `tools`

No passo 6, o script monta `/roms2/tools` em `/opt/system/Tools`. Se essa pasta **não existir no cartão**, o mount falha e `/opt/system/Tools` fica vazio — o menu Options perde PortMaster e todos os utilitários.

O script extrai `/roms.tar` no cartão só **depois** desse mount, então em cartão novo a ordem é frágil.

Solução prática: **crie `tools/` na raiz do cartão antes de rodar o script**, com o PortMaster dentro, ou rode o script duas vezes (a primeira popula o cartão, a segunda acerta o bind). Verifique depois:

```bash
mount | grep -E "roms2|system/Tools"
ls /opt/system/Tools
```

Se `/opt/system/Tools` estiver vazio, o PortMaster "sumiu" — não foi apagado, está escondido pelo mount.

## Depois da troca

- O EmulationStation passa a ler `/roms2`.
- O swapfile de 256 MB é criado e removido no mesmo script; não deixe swap permanente em cartão.
- Para voltar: **Switch to main SD for Roms**.

## Alternativa: não usar o script

Você pode manter as ROMs na TF2 montando manualmente e apontando só as pastas que quiser — menos mágico, menos risco de perder `/opt/system/Tools`. A desvantagem é que o EmulationStation precisa de `es_systems.cfg` coerente com os caminhos.

## Regra de ouro

Antes de rodar qualquer script que reescreve `es_systems.cfg` e `fstab`:

```bash
sudo cp /etc/emulationstation/es_systems.cfg /etc/emulationstation/es_systems.cfg.bak
sudo cp /etc/fstab /etc/fstab.bak
```

Se algo der errado, você volta em dois comandos em vez de reinstalar.
