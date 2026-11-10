# 01 — Hardware e diagnóstico

## O aparelho

| Item | Valor |
|---|---|
| Modelo | R36S, placa "soy sauce" (RK3326) |
| SoC | Rockchip RK3326, 4× Cortex-A35 |
| RAM | 1 GB |
| GPU | Mali-G31 (Bifrost), driver blob proprietário |
| Tela | 640×480, DSI, painel `elida,kd35t133` |
| Sistema | ArkOS 2.0 build 04232022 (Ubuntu 19.10, glibc 2.30, kernel 4.4) |
| Controle | `GO-Super Gamepad` em `/dev/input/event1` |

## O ponto mais importante: a tela

O R36S existe em várias revisões de placa e painel, e **cada revisão pede um DTB diferente**. Neste aparelho:

| Item | Valor |
|---|---|
| Placa | `Y3506_V03_20241210` (família "soy sauce") |
| DTB carregado pelo `boot.ini` | `/boot/rk3326-r35s-linux.dtb` |
| md5 desse DTB | `9dd051f13539f98450d8b8b8d929b5c0` |
| Painel dentro do DTB | `panel@0`, compatível `elida,kd35t133`, `simple-panel-dsi` |
| `model` informado ao kernel | `Rockchip RK3326` |
| `compatible` | `rockchip,rk3326-odroidgo3-linux` |

O `elida,kd35t133` é o **driver do painel dentro** do DTB, não o nome do arquivo do DTB. Versões antigas deste documento chamavam isso de "painel V5". A placa impressa neste aparelho é V03, e a origem do rótulo "V5" não foi confirmada. Detalhes em [14 — Hardware real](14-hardware-real-e-identificacao.md).

Se você trocar o `.dtb` da partição BOOT por um de outro painel — inclusive os de 60 Hz que circulam em guias de "melhorar o pacing" — o sintoma é **tela preta**, sem mensagem nenhuma. O sistema sobe, o SSH responde, e a tela fica apagada. Não é placa queimada: é DTB errado.

Regras práticas:

1. **Sempre faça backup do `.dtb`** antes de qualquer teste.
2. Se a tela apagar depois de mexer no BOOT, volte o DTB anterior. Se não tiver backup, o aparelho ainda responde por SSH (quando a rede sobe), mas visualmente parece morto.
3. "Melhorar o pacing" trocando para 60 Hz é ajuste de **painel**, não de desempenho. Não aumenta FPS; muda o ritmo de quadros. O risco não compensa sem saber exatamente qual painel você tem.

## Como o sistema se organiza

O cartão de boot tem três partes relevantes:

| Região | O que é | Tamanho típico |
|---|---|---|
| Início bruto do cartão | bootloader (U-Boot/Rockchip) | 16 MiB |
| Partição BOOT | kernel (`Image`), DTB, `boot.ini` | ~112 MiB |
| Partição root | sistema de arquivos ext4 | ~6,5 GiB |
| Partição roms | exFAT, montada em `/roms` | ~960 MiB (imagem enxuta) |

A partição `roms` é pequena e enche rápido. Ela guarda os atalhos de ports, saves e o que você colocar de ROM. É o primeiro lugar onde falta espaço.

## Sintomas que levaram ao diagnóstico

- O cartão original parou de bootar.
- Um cartão de grande capacidade aceitava gravação mas corrompia arquivos: só uma fração da capacidade era gravável de verdade.
- Um cartão menor reportava capacidade cheia e armazenava menos de 10% disso.
- O cartão original passou a se identificar como **512 KB** — sinal clássico de controlador morto, não de sistema de arquivos corrompido.

Nenhum desses é problema de software. Cartão que reporta capacidade errada não se conserta com `fsck`. Veja o procedimento de teste em [02 — Recuperação do cartão](02-recuperacao-do-cartao.md).

## O que sobreviveu

As três regiões do cartão original foram copiadas para imagem antes de qualquer escrita:

- `head.img` — 16.777.216 bytes (bootloader)
- `boot.img` — 117.440.512 bytes (kernel + DTB + boot.ini)
- `root.img` — 7.025.459.200 bytes (root intacto)

Com essas três peças é possível reconstruir um cartão que dá boot **sem** depender de download de imagem de terceiros. Foi assim que o aparelho voltou.
