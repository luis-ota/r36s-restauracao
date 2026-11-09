# R36S / ArkOS — restauração, ajustes e aprendizado

Documentação de uma restauração real de um **R36S** (RK3326, 1 GB de RAM, tela 640×480) com **ArkOS 2.0 (build 04232022, Ubuntu 19.10, kernel 4.4)**, desde o cartão original morto até o aparelho jogável, com PortMaster, monitor de sistema e tema próprio.

Tudo aqui foi testado no aparelho. O que não foi medido está marcado como **não medido**. O que não funcionou está documentado do mesmo jeito — inclusive os becos sem saída, porque foram eles que custaram mais tempo.

> **Aviso:** este repositório é documentação técnica. Não contém ROMs, BIOS, imagens de disco, backups pessoais, credenciais de rede ou dados de conta. Nada aqui incentiva pirataria.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 — Hardware e diagnóstico](docs/01-hardware-e-diagnostico.md) | Modelo, painel, DTB, por que tela preta é o erro mais fácil de cometer |
| [02 — Recuperação do cartão](docs/02-recuperacao-do-cartao.md) | Como ler as partições, testar cartão e montar uma imagem enxuta que dá boot |
| [03 — Primeiro boot, rede e SSH](docs/03-primeiro-boot-e-rede.md) | Sequência de boot que funciona neste aparelho, Wi-Fi, acesso remoto |
| [04 — Performance](docs/04-performance.md) | O que rende FPS, o que não rende e o que pode quebrar o aparelho |
| [05 — btop no controle](docs/05-btop-no-controle.md) | Console no framebuffer, fonte, `openvt` e saída pelo gamepad |
| [06 — PortMaster](docs/06-portmaster.md) | Instalação, armadilhas do `/roms2`, permissões, EGL e launcher |
| [07 — EmulationStation e SDL](docs/07-emulationstation-e-sdl.md) | O caso do SDL2 com udev quebrado e o tema que não existia |
| [08 — Captura de tela](docs/08-captura-de-tela.md) | Como tirar print real da tela via DRM, sem X11 e sem compositor |
| [09 — Cartão TF2](docs/09-cartao-tf2.md) | Preparar o segundo cartão e o que o script do ArkOS realmente faz |
| [10 — Tema Lain](docs/10-tema-lain.md) | Estrutura do tema e como instalar |
| [11 — Lições aprendidas](docs/11-licoes-aprendidas.md) | Lista curta do que economiza horas |

## Scripts

Em [`scripts/`](scripts/):

- `drmcap.py` — captura a tela pelo framebuffer do DRM (funciona sem X11).
- `btop-console.sh` — abre o btop no console e fecha com START/SELECT/L+R.
- `btop-launcher.sh` — atalho do menu Ports para o btop.
- `portmaster-console.sh` — roda o PortMaster com o EmulationStation parado.
- `portmaster-launcher.sh` — atalho do menu Ports para o PortMaster.
- `perfmax` / `perfnorm` — versões que não derrubam o governor.
- `uinput-f12.py` — experimento de teclado virtual via `uinput`.

## Contexto do aparelho

- **Modelo:** R36S (clone RK3326), painel **V5**, 640×480, DTB de fábrica `elida,kd35t133`.
- **Sistema:** ArkOS 2.0, build 04232022 — Ubuntu 19.10, glibc 2.30, kernel 4.4, GPU Mali-G31 (Bifrost).
- **Armazenamento interno:** partição `root` de 2,5 GB e partição `roms` de 960 MB (exFAT) no mesmo cartão.
- **Controle:** gamepad identificado como `GO-Super Gamepad` em `/dev/input/event1`. **Não tem códigos clássicos de START/SELECT.**

## O que este repositório NÃO é

- Não é imagem pronta para gravar. Não há `.img` aqui.
- Não é lista de links de ROM.
- Não é receita genérica de "overclock". O aparelho tem limite físico e térmico.

## Licença

Código e textos: MIT (veja [LICENSE](LICENSE)).
Tema: projeto de fã não comercial, inspirado em *Serial Experiments Lain*, sem imagens da série. Fontes IBM Plex sob a SIL OFL 1.1. Créditos no [documento do tema](docs/10-tema-lain.md).
