# 12 — Descanso de tela e economia de bateria

O descanso do EmulationStation, nesta versão, tem dois problemas: volta menos de 2 segundos depois de você sair e não baixa o brilho do painel (só cobre a tela com preto). Por isso o descanso aqui **não usa o do EmulationStation**.

## Como funciona agora

Um daemon próprio ([`scripts/r36s-idle.py`](../scripts/r36s-idle.py)) cuida de tudo:

| Tempo parado | O que acontece |
|---|---|
| 45 s | brilho do painel cai para 18% (28 de 160) — economia agressiva |
| 90 s | EmulationStation para e as imagens começam, trocando a cada 8 s, com brilho em 8% (12 de 160) |
| 30 min de slideshow sem toque | **descanso profundo**: as imagens param, o brilho cai para 1 (de 160) e o EmulationStation fica fora |
| qualquer toque | fecha as imagens, restaura o brilho e sobe o EmulationStation de volta, se ele não estiver rodando |

## Descanso profundo

Antes, o slideshow terminava, o menu voltava por alguns segundos e entrava de novo no slideshow. No aparelho, isso rodou por dois dias seguidos com o menu subindo e descendo, com CPU e calor constantes (a placa chegou a 50,8 °C nesse período).

Agora, quando o slideshow chega ao limite de `MAX_SLIDE_MIN` (30 min) sem nenhum toque, o daemon **para de ciclar**:

- não sobe mais o menu;
- deixa o brilho no mínimo (`RESTING_PERCENT=1`, ou seja, 1 de 160);
- registra `descanso profundo: menu fora, aguardando toque` no log.

Qualquer toque sai do descanso: o brilho volta ao normal e, se o EmulationStation não estiver rodando e nenhum jogo ou app de console estiver aberto, o menu é iniciado de novo.

Se um jogo começar durante o slideshow, o daemon não faz nada com o menu, para não derrubar o jogo.

### O que foi medido e o que não foi

- **Medido no aparelho:** a versão nova instalada, a sintaxe, e a estabilidade de descritores de arquivo do daemon depois de reinício (5 descritores, 0 reinícios em 32 s).
- **Diferença conhecida:** depois dessa medição, removi do repositório uma variável sem efeito (`RESTING_MIN`). O aparelho ainda roda a versão anterior, que só carrega essa variável sem usar. O arquivo instalado vai ser atualizado no próximo reinício do daemon, para não interromper o slideshow agora.
- **Não medido:** o caminho completo de 30 minutos de slideshow até o descanso profundo, e o retorno pelo toque depois dele. Não foi cronometrado no aparelho. Para testar sem esperar, use `MAX_SLIDE_MIN=1` e `SLIDE_SECONDS=10` no serviço e observe o log.

Com um jogo rodando, ele não age: nem escurece, nem abre imagens. Se o menu tiver aberto qualquer outro programa, como um port, ele também não para o menu, porque isso mataria o programa.

## Por que parar o EmulationStation

O `image-viewer` só consegue desenhar na tela quando o EmulationStation solta o display. Parar o serviço é o jeito confiável; não há API para pedir isso ao menu.

O custo é que a volta leva alguns segundos, porque o menu é reiniciado. Em troca, as imagens aparecem de verdade e o botão funciona.

## O detalhe do toque

Com o visualizador na frente, o EmulationStation (e nós) não recebem os eventos do controle: o `image-viewer` toma o dispositivo só para ele.

A saída é ler a interface **legada** do joystick, `/dev/input/js*`, que continua funcionando mesmo com o `evdev` tomado. Foi medido no aparelho: o `js0` entrega eventos normalmente enquanto o `image-viewer` está na frente.

Duas armadilhas resolvidas no caminho:

- Abrir `/dev/input/js0` dispara um lote com o estado inicial (eixos e botões). Sem descartar esse lote, o slideshow fecharia sozinho no primeiro instante.
- Controle conectado depois precisa ser descoberto: a lista de `js*` é reexaminada a cada 2 s durante o slideshow.

## Configuração

`/etc/systemd/system/r36s-idle.service`:

```
Environment=DIM_SECONDS=45
Environment=SLIDE_SECONDS=90
Environment=DIM_PERCENT=18
Environment=SLIDE_PERCENT=8
Environment=SLIDE_SECONDS_EACH=8
Environment=MAX_SLIDE_MIN=30
Environment=RESTING_PERCENT=1
```

`MAX_SLIDE_MIN` define quando o slideshow termina e o descanso profundo entra. `RESTING_PERCENT` é o brilho do descanso profundo, em porcentagem do máximo.

O brilho normal fica gravado em `/etc/r36s-idle.normal`, para o serviço não confundir "brilho de uso" com "brilho escurecido" quando reinicia no meio do descanso.

Se as imagens não existirem, o daemon só escurece.

## Desligar ou ajustar

```bash
# desligar
sudo systemctl disable --now r36s-idle
cat /etc/r36s-idle.normal | sudo tee /sys/class/backlight/backlight/brightness

# mudar tempos
sudo systemctl edit r36s-idle
```

## O screensaver do EmulationStation

As chaves `ScreenSaverTime` e `ScreenSaverBehavior` ficam **fora** de `es_settings.cfg`. Com elas, o menu volta ao descanso imediatamente após o toque, e o valor de tempo é sobrescrito quando o serviço fecha.

Se quiser usar o do sistema mesmo assim: pare o serviço antes de editar o arquivo, e saiba que o defeito de reentrada continua.

## Cuidado

Brilho em 18% (28 de 160) é bem baixo: no escuro fica confortável, com luz do dia quase ilegível — mas qualquer toque devolve na hora. Para 10%, troque `DIM_PERCENT=10`. O daemon nunca escurece com jogo rodando.
