# 13 — Autosave real e load automático no DraStic

O DraStic **não tem autosave**. Não existe opção no binário, no `drastic.cfg` nem no menu. Este documento descreve a solução que funciona neste aparelho: um teclado virtual via `uinput` que aperta as teclas de save e load do próprio emulador, comandado por um serviço que só age depois de um load.

## Resumo do que ficou funcionando

| Recurso | Como |
|---|---|
| Salvar sozinho | A cada **3 minutos**, se algum botão foi apertado desde o último save |
| Carregar sozinho ao abrir | `F7` nos primeiros segundos, até 3 tentativas |
| Fechar o jogo | Segurar **SELECT + START** por 1 segundo |
| Só age depois de um load | Detecta a leitura de um `.dss` logo depois do `F7` ou do `L1` |
| Segurança | Sem botão apertado, não salva; jogo aberto do zero, não salva |

O serviço é o `r36s-autosave.service`, com o script [`scripts/r36s-autosave.py`](../scripts/r36s-autosave.py).

## O problema que impede o óbvio

O jogo **sempre abre do zero**. Se um autosave apertar "salvar" nos primeiros segundos, ele grava um jogo vazio por cima do seu progresso. Foi exatamente o aviso do dono do aparelho: *"antes tem que dar um load"*.

Por isso a regra do serviço é: **só liga depois de confirmar que um state foi carregado**, e desliga quando o jogo fecha.

## O que NÃO funcionou

Tudo abaixo foi testado e descartado com medição, não por suposição:

| Tentativa | Resultado |
|---|---|
| Criar um controle virtual com `uinput` no boot | O DraStic ignorou |
| Joystick virtual completo, com eixos e `/dev/input/js1` | O kernel criou o `js1`, o DraStic ignorou |
| Apertar a tecla mapeada no save via joystick virtual | Log do serviço registrou o aperto, o arquivo não mudou |
| Apertar `KEY_S` (`keycode 31`) | Nenhum efeito |
| Serviço periódico apertando o botão R1 | Nenhum efeito |

**O que foi medido:** joysticks virtuais não fizeram o DraStic salvar, e um teclado virtual apertando F5 fez. O motivo de o joystick não funcionar não foi isolado.

## A solução: teclado virtual

O DraStic usa SDL2 (`libSDL2-2.0.so.0.18.2`) e abre os dispositivos de entrada por evdev. Um teclado virtual criado em `/dev/uinput` **é lido**.

O que o script faz. O teste que funcionou mudou a tecla e a quantidade de teclas ao mesmo tempo, então não dá para dizer qual detalhe foi decisivo:

1. **Registra as teclas `1..248`**, não só uma.
2. **Esperar 2,5 s depois de criar o aparelho.** O SDL precisa enxergar o dispositivo novo antes do primeiro evento.
3. **Destruir o dispositivo depois do aperto.** Não fica nada pendurado entre um save e outro.

### As teclas do DraStic

O README do emulador lista atalhos de teclado. Cruzando com o `drastic.cfg` deste aparelho:

```ini
controls_a[CONTROL_INDEX_SAVE_STATE] = 318
controls_a[CONTROL_INDEX_LOAD_STATE] = 320
```

O DraStic mapeia scancode do SDL + 256:

| Scancode SDL | Código na config | Tecla |
|---|---|---|
| 62 | 318 | **F5** — salvar state |
| 64 | 320 | **F7** — carregar state |

Confirmado no aparelho: um `F5` injetado com o jogo aberto gravou o slot 1 às 21:54:32, e o jogo continuou rodando.

> A documentação do DraStic fala em `S`/`L` para os slots. Neste aparelho vale o que está no `drastic.cfg`: `F5` salva e `F7` carrega.

## Como o serviço decide

Máquina de estados simples, rodando a cada 2 segundos:

```
jogo abre
  └─ processo com menos de 30 s de vida?
       ├─ sim → tenta F7 (até 3 vezes, 6 s de intervalo)
       └─ não → espera L1 manual
                    │
                    ▼
     DraStic leu um .dss em até 3 s do F7/L1?
       ├─ sim → ARMA o autosave, próximo save em 180 s
       └─ não → tenta de novo (F7) ou espera L1
                    │
                    ▼
     a cada 180 s: houve botão apertado desde o último save?
       ├─ sim → aperta F5
       └─ não → pula (evita gravar state repetido à toa)
                    │
jogo fecha → desarma, zera contadores
```

### As travas que evitam estrago

| Trava | Por quê |
|---|---|
| `JOGO_NOVO = 30 s` | Só faz load automático em processo recém-aberto. Serviço reiniciado no meio da partida **não** recarrega nada. |
| Detecção por leitura de arquivo | Não basta ver o botão: o DraStic tem que ter **lido** o `.dss`. `inotify` com `IN_OPEN`/`IN_ACCESS` no diretório de savestates. |
| `JANELA_LOAD = 3 s` | A leitura tem que ser logo depois do `F7`/`L1`, senão é outra coisa lendo o arquivo. |
| `flock` no lock do backup | O backup roda a cada 2 min e **também lê** os `.dss`. Sem isso, uma leitura do backup que coincidisse com um L1 ou F7 sem efeito poderia ligar o autosave. |
| Sem atividade, sem save | Se você parou de jogar, não faz sentido gastar escrita no cartão. |
| `SIGTERM`, não `SIGKILL` | O atalho de fechar pede para o DraStic sair, em vez de matar o processo à força. Não foi testado se isso grava o `.dsv`, então salve dentro do jogo antes de fechar. |

## O atalho para fechar: SELECT + START

O DraStic não tinha atalho de saída (`CONTROL_INDEX_QUIT = 65535`, ou seja, nenhum). O serviço assumiu isso: **segurar SELECT + START por 1 segundo**.

Comportamento:

1. Se o autosave está armado, aperta `F5` e espera **3 s** (o DraStic grava em segundo plano).
2. Manda `SIGTERM` no processo do DraStic.
3. O `drastic.sh` termina, roda o backup e o EmulationStation volta.

Se o autosave **não** está armado, fecha sem salvar. É proposital: melhor perder o state do que gravar um jogo vazio por cima.

Os códigos dos botões vieram das capabilities do `event1`: `SELECT = 704` e `START = 705` (índices 12 e 13 do joydev).

## Instalação

```bash
sudo install -m 755 r36s-autosave.py /usr/local/bin/r36s-autosave.py
```

`/etc/systemd/system/r36s-autosave.service`:

```ini
[Unit]
Description=Autosave do DraStic depois de um load
After=local-fs.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/r36s-autosave.py
Restart=always
RestartSec=5
StandardOutput=append:/home/ark/pokemon-backups/autosave.log
StandardError=append:/home/ark/pokemon-backups/autosave.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now r36s-autosave
```

O Python do sistema é 3.7.5. O script não usa nada além da biblioteca padrão.

## Operação

```bash
# estado e log
systemctl is-active r36s-autosave
sudo tail -f /home/ark/pokemon-backups/autosave.log

# reiniciar depois de mudar o script
sudo systemctl restart r36s-autosave
```

Log típico de uma sessão saudável:

```
servico iniciado: a cada 180 s, depois de um load
jogo aberto, vou carregar o state
F7 enviado, tentativa 1 de 3
load detectado, autosave ligado
state salvo automaticamente
```

Se aparecer `jogo aberto, aguardando L1`, é o serviço esperando você carregar o state: aperte **L1** e ele arma.

### Ajustes

Variáveis de ambiente no `Environment=` da unit:

| Variável | Padrão | Efeito |
|---|---|---|
| `AUTOSAVE_SEG` | `180` | Intervalo entre saves |
| `AUTOSAVE_DIR` | `/mnt/jogos/nds/savestates` | Onde ficam os `.dss` |

Constantes no topo do script: `JOGO_NOVO`, `ESPERA_LOAD`, `MAX_TENTATIVAS`, `SEGURAR_FECHAR`, `ESPERA_SAVE`, `JANELA_LOAD`.

### Desligar

```bash
sudo systemctl disable --now r36s-autosave
```

Não mexe em arquivo nenhum do DraStic: é só o serviço parando de apertar teclas.

## Onde ele grava, e o que protege

- O autosave grava no **slot ativo** (hoje o **slot 1**, o mesmo do `R1`).
- O backup a cada 2 minutos copia o state para `/home/ark/pokemon-backups` e espelha o mais recente no **slot 9**.
- São guardadas **12 versões recentes + 6 marcos antigos** de cada state. Com autosave a cada 3 minutos, as recentes cobrem cerca de 36 minutos de jogo, e os marcos guardam pontos mais antigos.
- Para voltar atrás: **Ports → Restaurar backup do Pokemon**, ou copiar a versão desejada de `~/pokemon-backups/"Pokemon - Black Version_1.dss"/000123.dss` para o slot, com o jogo fechado.

## Linha do tempo dos testes (o que foi medido)

| Hora | O que aconteceu |
|---|---|
| 21:54:32 | `F5` manual com o jogo aberto: slot 1 mudou de tamanho e hash. Prova de que a tecla funciona. |
| 22:01:25 | Primeiro save **automático** do serviço (3 min depois do L1). |
| 22:04:26 | Segundo save automático. |
| 22:08 | Backup copiou e atualizou o slot 9. |
| 22:08:33 | Serviço reiniciado com o jogo aberto: **não** recarregou nada (trava `JOGO_NOVO`). |
| 22:09 | `SELECT + START` fechou o jogo pelo log. |
| 22:09:30 | Jogo aberto de novo: `F7` na primeira tentativa, load detectado, autosave armado. |
| Depois | Aparelho reiniciado: o serviço subiu sozinho e o autosave funcionou nessa sessão. |
| 06:18:43 | `SELECT + START` com o autosave ligado: log "salvo antes de fechar" e slot 1 gravado. |

## O que ainda não foi confirmado

- **Tela de baixo ao carregar.** Às vezes o load abre na tela inferior do DS e é preciso trocar de tela. A causa não foi confirmada; a suspeita é que o state guarda a tela em que foi salvo. Não foi colocado nenhum "swap" automático para não inverter quando já abre certo.
- **Outros jogos de DS.** Tudo foi validado com um jogo só. A lógica é do emulador, não do jogo, então deve valer para todos, mas não foi medido.

## Cuidado com uma coisa

Não pare o EmulationStation para "testar" com um jogo aberto: **derrubar o menu mata o DraStic**. Para mexer no serviço, reinicie só ele (`systemctl restart r36s-autosave`), que o script tolera ser reiniciado em qualquer momento.
