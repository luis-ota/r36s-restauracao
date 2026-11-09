# 12 — Descanso de tela e economia de bateria

Dois assuntos que o mesmo problema juntou: o screensaver que abria sozinho e a vontade de escurecer a tela para gastar menos.

## O tempo do descanso é em segundos

No EmulationStation do ArkOS, `ScreenSaverTime` é lido em **segundos**, e o comportamento vem de `ScreenSaverBehavior`.

Valores que funcionam:

```xml
<int name="ScreenSaverTime" value="90" />
<string name="ScreenSaverBehavior" value="slideshow" />
```

Com 90, o descanso entrou em ~95 s (o atraso é o tempo de subir o menu). Testado com print real da tela.

## Por que "10 minutos" virava 10 segundos

O menu **regrava** `es_settings.cfg` ao sair. Se você edita o arquivo com o EmulationStation rodando, a alteração pode ser sobrescrita quando ele fecha, e o valor antigo volta — inclusive um valor curto usado em teste.

Receita que não falha:

```bash
sudo systemctl stop emulationstation
python3 settings.py ScreenSaverTime=90 ScreenSaverBehavior=slideshow
sudo systemctl start emulationstation
```

Sempre pare o serviço antes de editar, e reinicie depois.

## O brilho não caía

O descanso do EmulationStation só cobre a tela com uma camada preta. O painel continua aceso no mesmo brilho, então **não economiza bateria**.

Solução: um daemon pequeno que escuta os controles e baixa o brilho de verdade em `/sys/class/backlight/backlight/brightness` depois de um tempo parado, devolvendo ao primeiro toque.

- Script: [`scripts/r36s-idle.py`](../scripts/r36s-idle.py)
- Serviço: `r36s-idle.service`, com `IDLE_SECONDS=60` e `DIM_PERCENT=45`
- Escuta todos os `/dev/input/event*` e reexamina a lista a cada 5 s, para pegar controle conectado depois
- `ExecStopPost` devolve o brilho ao normal se o serviço parar

Medido no aparelho: brilho 88 → 72 (45% de 160) após 70 s parado, e 88 de volta assim que chega um evento.

## Ordem prática

1. Aos 60 s parado, o brilho cai para 45% — economia real.
2. Aos 90 s, o slideshow do EmulationStation começa, mostrando as imagens. Elas aparecem já com o brilho reduzido.
3. Qualquer toque: o slideshow fecha e o brilho volta.

Se quiser só a economia, sem imagens: `ScreenSaverBehavior=dim` ou `black`.
Se quiser só as imagens: desative o `r36s-idle.service`.

## Ajustes

```bash
# tempo e intensidade
sudo systemctl edit r36s-idle
#   Environment=IDLE_SECONDS=120
#   Environment=DIM_PERCENT=30

# desligar
sudo systemctl disable --now r36s-idle
echo 88 | sudo tee /sys/class/backlight/backlight/brightness
```

## Cuidado

Brilho muito baixo em ambiente claro deixa a tela ilegível. 45% é o mínimo confortável testado aqui; abaixo disso só em ambiente escuro.
