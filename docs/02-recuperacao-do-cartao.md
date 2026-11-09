# 02 — Recuperação do cartão

## Primeiro: descobrir se o cartão é confiável

Antes de gravar qualquer coisa, teste. Cartão falso ou desgastado aceita gravação e devolve lixo na leitura — e isso se manifesta como "o sistema corrompeu sozinho", o que faz você perder horas.

### Teste de capacidade real (escrita + leitura)

Grave blocos em pontos distribuídos ao longo do disco, leia de volta e compare. Pontos testados aqui: 32 MiB, 500 MiB, 1500 MiB, 2500 MiB e 3200 MiB.

Se qualquer ponto falhar ou devolver conteúdo diferente, **descarte o cartão**. Não existe ajuste de software que resolva.

### Sinais de cartão morto

- O disco muda de tamanho entre conexões (ex.: dezenas de GB → 512 KB).
- `lsblk` mostra tamanho, mas `dd` corrompe.
- Erros de I/O no `dmesg` durante escrita.

Um cartão que se identifica como 512 KB não tem partição recuperável: o controlador está em modo de emergência.

## Ler as regiões do cartão original

Se o cartão ainda responde, copie as regiões antes de qualquer coisa:

```bash
# bootloader (início do disco)
sudo dd if=/dev/sdX of=head.img bs=1M count=16 status=progress

# tabela de partições + partições
sudo sfdisk -d /dev/sdX > layout.txt
sudo dd if=/dev/sdX1 of=boot.img bs=1M status=progress
sudo dd if=/dev/sdX2 of=root.img bs=1M status=progress
```

Guarde `layout.txt` junto: ele descreve os setores iniciais de cada partição.

## Montar um cartão que dá boot

A combinação que funcionou neste aparelho foi **bootloader + BOOT + root originais**, com o DTB de fábrica. Outras distros (ROCKNIX, AmberELEC) subiram mas ficaram com tela preta — mesmo problema de DTB/painel descrito em [01](01-hardware-e-diagnostico.md).

Passos:

1. Recrie a tabela com o mesmo layout do `layout.txt` (setor inicial e tipo de cada partição).
2. Grave `head.img` no início do disco.
3. Grave `boot.img` na partição BOOT (vfat).
4. Grave `root.img` na partição root (ext4).
5. Crie a partição `roms` (exFAT) e monte em `/roms`.

## Deixar a imagem enxuta

A imagem original tem 7 GB, mas boa parte é conteúdo opcional (temas, emuladores, ports). Para caber em cartões pequenos, dá para:

- remover pacotes não usados;
- apagar caches (`/var/cache/apt`, `/root/.cache`);
- esvaziar `/roms` e deixar só as pastas base;
- manter o kernel, o DTB e os serviços essenciais.

O que **não** pode ser removido sem quebrar o boot:

- `rk817-calibrationd` (calibração do PMIC/bateria)
- `351mp.service` (brilho/volume no boot)
- `batteryplus` (daemon de bateria)
- `mali-select` (quando existir — symlinks do driver Mali)

## Backup: o que vale guardar

- `head.img`, `boot.img`, `root.img`
- DTB de fábrica (`rk3326-r35s-linux.dtb` ou equivalente)
- `layout.txt`
- `/etc/emulationstation/es_systems.cfg` e `es_input.cfg`

Com isso você reconstrói o aparelho mesmo se a partição root for apagada.

> Backups pessoais não fazem parte deste repositório.
