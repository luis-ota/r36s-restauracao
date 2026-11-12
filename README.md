# R36S / ArkOS — restauração, ajustes e aprendizado

Documentação de uma restauração real de um **R36S** (RK3326, 1 GB de RAM, tela 640×480) com **ArkOS 2.0 (build 04232022, Ubuntu 19.10, kernel 4.4)**, desde o cartão original morto até o aparelho jogável, com PortMaster, monitor de sistema, tema próprio e **autosave real** no DraStic.

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
| [12 — Descanso e bateria](docs/12-descanso-e-bateria.md) | Screensaver, slideshow e escurecimento real do painel |
| [13 — Autosave e load automático](docs/13-autosave-e-load-automatico.md) | Teclado virtual, `F5`/`F7`, o serviço que salva sozinho e o atalho SELECT + START |
| [14 — Hardware real e identificação](docs/14-hardware-real-e-identificacao.md) | Placa da família "soy sauce", inventário medido e opções de firmware |
| [15 — Atualizações e limites da base](docs/15-atualizacoes-e-limites-da-base.md) | Por que `apt upgrade` aqui é má ideia, com os números na mão |
| [16 — LÖVE e GLES](docs/16-love-e-gles.md) | O LÖVE 11.5 do PortMaster roda neste ArkOS, com prova em gravação; o erro de `/dev/mali0` no log não impede nada |
| [17 — Música de fundo do menu](docs/17-musica-de-fundo-do-menu.md) | A faixa chill do menu: como foi gerada, onde fica, como trocar ou remover |

## Posts no blog

Dois textos em inglês contam a história por fora da documentação:

- [rebuilding a dead r36s, one lying card at a time](https://blog.wired.rs/posts/r36s-restoration) — a jornada completa: o boot que travou, os cartões que mentiam sobre o tamanho, a imagem mínima e a placa que não é a da etiqueta.
- [teaching a ds emulator to save itself](https://blog.wired.rs/posts/drastic-autosave-uinput) — o autosave do DraStic por teclado virtual, em detalhe.

## Scripts

Em [`scripts/`](scripts/):

- `drmcap.py` — captura a tela pelo framebuffer do DRM (funciona sem X11).
- `btop-console.sh` — abre o btop no console e fecha com START/SELECT/L+R.
- `btop-launcher.sh` — atalho do menu Ports para o btop.
- `portmaster-console.sh` — roda o PortMaster com o EmulationStation parado.
- `portmaster-launcher.sh` — atalho do menu Ports para o PortMaster.
- `perfmax` / `perfnorm` — versões que não derrubam o governor.
- `r36s-perf.sh` — aplica os ajustes de desempenho de forma idempotente.
- `uinput-f12.py` — experimento de teclado virtual via `uinput`.
- `r36s-autosave.py` — load automático e autosave do DraStic por teclado virtual.
- `backup_pokemon.sh` — backup versionado dos saves, com espelho no slot 9.
- `restaurar-save.sh` — atalho do menu Ports para restaurar uma versão antiga.
- `r36s-usbnet.sh` — rede por USB (gadget Ethernet).
- `r36s-idle.py` — escurece a luz de fundo por inatividade, faz slideshow com música de fundo em volume baixo e, depois de 30 min, entra em descanso profundo (menu fora, brilho e música desligados). Ver [12](docs/12-descanso-e-bateria.md).

## Experimentos

Arquivos que **não** fazem parte do sistema instalado. Estão aqui para reproduzir o que foi testado:

- [`experimentos/love-gles/`](experimentos/love-gles/) — teste do LÖVE no aparelho (`main.lua`), o shim de `dlopen` que não foi necessário (`dlshim.c`) e o script de ciclo completo com gravação da tela (`teste-love.sh`). Ver [16](docs/16-love-e-gles.md).
- [`experimentos/musica-menu/`](experimentos/musica-menu/) — `synth.py`, que gera a faixa chill do menu por síntese. O arquivo de áudio não é versionado; ele sai do script. Ver [17](docs/17-musica-de-fundo-do-menu.md).

## Contexto do aparelho

- **Modelo:** vendido como R36S, placa da família **"soy sauce"**: `Y3506_V03_20241210`. Tela 640×480, DTB `rk3326-r35s-linux.dtb` com painel `elida,kd35t133`. Detalhes e medições em [14](docs/14-hardware-real-e-identificacao.md).
- **Sistema:** ArkOS 2.0, build 04232022 — Ubuntu 19.10, glibc 2.30, kernel 4.4, GPU Mali-G31 (Bifrost).
- **Armazenamento:** sistema no cartão TF1; jogos em um segundo cartão (TF2), montado em `/mnt/jogos` e apontado pelo `es_systems.cfg`.
- **Controle:** gamepad `GO-Super Gamepad` em `/dev/input/event1`. SELECT = 704, START = 705; **SELECT + START por 1 s fecha o jogo**.

## O que este repositório NÃO é

- Não é imagem pronta para gravar. Não há `.img` aqui.
- Não é lista de links de ROM.
- Não é receita genérica de "overclock". O aparelho tem limite físico e térmico.

## Licença

Código e textos: MIT (veja [LICENSE](LICENSE)).
Tema: projeto de fã não comercial, inspirado em *Serial Experiments Lain*, sem imagens da série. Fontes IBM Plex sob a SIL OFL 1.1. Créditos no [documento do tema](docs/10-tema-lain.md).
