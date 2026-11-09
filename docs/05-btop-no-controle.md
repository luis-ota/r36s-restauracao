# 05 — btop no controle

O objetivo era abrir o `btop` pelo menu do aparelho e **fechar com o gamepad**, sem teclado.

Parece simples. Não é.

## Problema 1: o btop não abre em terminal redirecionado

A primeira tentativa foi:

```bash
btop < /dev/tty1 > /tmp/btop.out 2>&1
```

Resultado:

```
ERROR: Failed to get size of terminal!
```

O `btop` precisa de um **terminal de verdade** (um TTY com `ioctl` de tamanho), não de redirecionamento. A solução é `openvt`, que abre o programa no console virtual:

```bash
openvt -c 1 -f -s -- btop
```

## Problema 2: fonte ilegível

A tela é 640×480. O `btop` exige no mínimo 80 colunas.

- Fonte de 6 px de largura: cabe 80 colunas, mas é ilegível.
- Fonte **Terminus Bold 16** (`Lat15-TerminusBold16.psf.gz`): 8 px de largura × 80 = 640. Cabe exatamente, e é legível.
- Linhas: 30 (480 / 16).

```bash
setfont /usr/share/consolefonts/Lat15-TerminusBold16.psf.gz < /dev/tty1
stty -F /dev/tty1 cols 80 rows 30
```

Ao sair, volte para a fonte que o EmulationStation usa (`Lat7-Terminus20x10.psf.gz`), senão o menu fica com letra enorme.

## Problema 3: o gamepad não tem START/SELECT

O controle deste aparelho (`GO-Super Gamepad`) **não envia os códigos clássicos** `BTN_START`/`BTN_SELECT`. Os botões extras aparecem como códigos altos.

Códigos reais lidos do dispositivo:

| Código evdev | Botão |
|---|---|
| 304 | A (south) |
| 305, 307, 308 | B, X, Y |
| 310, 311 | L, R |
| 312, 313 | L2, R2 |
| 544–547 | direcionais (hat) |
| **704–708** | **botões extras (start, select, fn)** |

Para consultar a máscara de teclas de um dispositivo:

```python
import fcntl, os
def eviocgbit(ev, n):
    return (2 << 30) | (n << 16) | (0x45 << 8) | (0x20 + ev)
fd = os.open("/dev/input/event1", os.O_RDONLY)
buf = bytearray(96)
fcntl.ioctl(fd, eviocgbit(1, 96), buf)
print([i*8+b for i, byte in enumerate(buf) for b in range(8) if byte & (1 << b)])
```

Foi assim que descobrimos que `315` (START) e `314` (SELECT) **não existem** neste controle — e por isso o script "não fechava": ele esperava botões que nunca chegavam.

## Problema 4: o script achava que o btop tinha morrido

Rodar `openvt ... &` e checar `$!` não funciona: o `openvt` sai e o `btop` continua em outro processo. O script então chamava o menu de volta e o btop ficava órfão desenhando na tela — exatamente o tipo de "tela maluca" que aparece depois.

Solução: localizar o PID real do `btop` e esperar por ele.

## Problema 5: o menu segurava a tela

O EmulationStation continua dono do display. Para o console aparecer, o serviço precisa parar — e o script precisa rodar fora do cgroup dele, senão morre junto.

`systemd-run` resolve:

```bash
sudo systemd-run --unit=btop-console --collect /usr/local/bin/btop-console.sh
```

## Script final

[`scripts/btop-console.sh`](../scripts/btop-console.sh):

```bash
#!/bin/bash
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty1 /dev/tty0 /dev/input/event1
setfont /usr/share/consolefonts/Lat15-TerminusBold16.psf.gz < /dev/tty1
stty -F /dev/tty1 cols 80 rows 30
printf "\033c" > /dev/tty1
printf "START, SELECT ou L+R fecha\n" > /dev/tty1
openvt -c 1 -f -s -- btop
sleep 0.6
BPID=$(pgrep -n -x btop)
sleep 1.2   # ignora o botão que abriu o menu
while [ -n "$BPID" ] && kill -0 "$BPID" 2>/dev/null; do
  hit=0
  for k in 704 705 706 707 708; do
    evtest --query /dev/input/event1 EV_KEY "$k"
    [ "$?" -eq 10 ] && hit=1
  done
  evtest --query /dev/input/event1 EV_KEY 310; l=$?
  evtest --query /dev/input/event1 EV_KEY 311; r=$?
  if [ "$hit" -eq 1 ] || { [ "$l" -eq 10 ] && [ "$r" -eq 10 ]; }; then
    kill "$BPID" 2>/dev/null
    break
  fi
  sleep 0.12
done
wait "$BPID" 2>/dev/null
setfont /usr/share/consolefonts/Lat7-Terminus20x10.psf.gz < /dev/tty1
printf "\033c" > /dev/tty1
systemctl start emulationstation
```

Atalho no menu Ports ([`scripts/btop-launcher.sh`](../scripts/btop-launcher.sh)):

```bash
#!/bin/bash
sudo systemd-run --unit=btop-console --collect /usr/local/bin/btop-console.sh
```

## Como instalar

```bash
sudo cp btop-console.sh /usr/local/bin/
sudo chmod 755 /usr/local/bin/btop-console.sh
sudo cp btop-launcher.sh /roms/ports/btop.sh
sudo chmod 755 /roms/ports/btop.sh
```

## Detalhe que confunde

`pgrep -a btop` às vezes não lista o processo, porque o nome do executável pode ser `python3`/outro. Use `pgrep -x btop` para nome exato ou `ps -ef | grep btop` quando estiver em dúvida.

Outra: se você matar o `btop` pelo SSH, deixe o script terminar. Ele reinicia o EmulationStation no fim. Matar o script no meio deixa o menu parado.
