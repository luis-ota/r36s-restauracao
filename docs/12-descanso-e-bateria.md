# 12 — Descanso de tela e economia de bateria

O descanso do EmulationStation, nesta versão, tem dois problemas: volta menos de 2 segundos depois de você sair e não baixa o brilho do painel (só cobre a tela com preto). Por isso o descanso aqui **não usa o do EmulationStation**.

## Como funciona agora

Um daemon próprio ([`scripts/r36s-idle.py`](../scripts/r36s-idle.py)) cuida de tudo:

| Tempo parado | O que acontece |
|---|---|
| 60 s | brilho do painel cai para 45% — economia real de bateria |
| 90 s | EmulationStation para e as imagens do slideshow começam, trocando a cada 8 s |
| qualquer toque | fecha as imagens, restaura o brilho e sobe o EmulationStation de volta |

Com um jogo rodando, ele não age: nem escurece, nem abre imagens.

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
Environment=DIM_SECONDS=60
Environment=SLIDE_SECONDS=90
Environment=DIM_PERCENT=45
Environment=SLIDE_SECONDS_EACH=8
```

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

Brilho em 45% é o mínimo confortável com luz ambiente. Abaixo disso, só no escuro. O daemon nunca escurece com jogo rodando.
