# 06 — PortMaster

Instalar o PortMaster no ArkOS é "só rodar o script oficial". Na prática, neste aparelho, foram cinco armadilhas.

## Instalação

Baixe o `Install.PortMaster.sh` mais recente em [github.com/PortsMaster/PortMaster-GUI/releases](https://github.com/PortsMaster/PortMaster-GUI/releases) e rode no aparelho:

```bash
chmod +x Install.PortMaster.sh
bash Install.PortMaster.sh
```

Ele extrai para `/opt/system/Tools/PortMaster` e cria `/opt/system/Tools/PortMaster.sh`.

Existe também o `Install.Full.PortMaster.sh` (~664 MB) com todos os runtimes embutidos. **Não use** se a partição `/roms` é pequena: os runtimes podem ser baixados sob demanda depois.

## Armadilha 1: o instalador procura uma pasta que não existe

Durante a instalação aparece:

```
mv: cannot stat 'PortMaster/libs/*.squashfs': No such file or directory
```

É ruído: a pasta `libs/` vem vazia de propósito no pacote base, e os runtimes são baixados no primeiro uso. Não impede nada.

## Armadilha 2: `log.txt` sem permissão

O `PortMaster.sh` faz:

```bash
> "$controlfolder/log.txt" && exec > >(tee "$controlfolder/log.txt") 2>&1
```

Se a pasta é `root:root` e o script roda como `ark`, isso falha:

```
PortMaster.sh: line 29: /opt/system/Tools/PortMaster/log.txt: Permission denied
```

Solução:

```bash
sudo chmod 777 /opt/system/Tools/PortMaster
sudo touch /opt/system/Tools/PortMaster/log.txt
sudo chmod 666 /opt/system/Tools/PortMaster/log.txt
```

## Armadilha 3: `/roms2` fantasma

O `harbourmaster` decide onde instalar ports assim:

```
if Path("/roms2/tools").is_dir():
    HM_DEFAULT_TOOLS_DIR = /roms2/tools
    HM_DEFAULT_PORTS_DIR = /roms2/ports
else:
    ... /roms/tools e /roms/ports
```

Se existir **qualquer** diretório `/roms2` (mesmo vazio, mesmo criado por engano), o PortMaster passa a instalar em `/roms2/ports` — que não é lido pelo EmulationStation, que aponta para `/roms/ports`. Resultado: você instala ports e eles "desaparecem".

Conferir:

```bash
grep -E "HM_DEFAULT" /opt/system/Tools/PortMaster/log.txt | tail -n 3
```

Se aparecer `/roms2/...` e você não tem o segundo cartão montado, remova a pasta fantasma:

```bash
sudo rm -rf /roms2
```

Quando o segundo cartão está realmente montado em `/roms2`, o comportamento é intencional (veja [09 — Cartão TF2](09-cartao-tf2.md)).

## Armadilha 4: EGL/Mali quebrado e interface "transparente"

Sintomas:

```
file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)
Failed creating base context during opening of kernel driver.
```

Consequências:

- O splash (feito em LÖVE) não abre: `Could not create EGL window surface`.
- A GUI do PortMaster cai para renderização em software. Funciona, mas herda o framebuffer anterior — e o menu do EmulationStation aparece **por baixo** da interface, dando a impressão de tela sobreposta.

Causa provável: blob Mali de userspace incompatível com o driver de kernel desta imagem. Corrigir isso exige o blob certo para o kernel — não é ajuste de configuração.

Solução adotada: **não competir pela tela**. Rodar o PortMaster com o EmulationStation parado (veja abaixo). O fundo passa a ser o console limpo, e a sobreposição desaparece.

## Armadilha 5: instância antiga esquecida

Uma execução anterior do `pugwash` que não morreu continua desenhando. Junto com o EmulationStation, você fica com **três** programas disputando o display e o resultado é uma salada.

Antes de investigar qualquer coisa visual, verifique:

```bash
ps -ef | grep -E "pugwash|PortMaster" | grep -v grep
```

Se houver processo antigo, mate pelo PID (não use `pkill -f PortMaster.sh` pelo SSH: o padrão casa com o próprio comando remoto e derruba a sessão).

## Launcher correto

Rodar o PortMaster direto pelo menu deixa o EmulationStation vivo, disputando a tela. O launcher abaixo tira o PortMaster do cgroup do menu, para o menu, executa, e devolve o menu no fim.

`/usr/local/bin/portmaster-console.sh`:

```bash
#!/bin/bash
systemctl stop emulationstation
sleep 1
chmod 666 /dev/tty0 /dev/tty1 /dev/input/event1 2>/dev/null
printf "\033c" > /dev/tty1
/opt/system/Tools/PortMaster.sh
printf "\033c" > /dev/tty1
systemctl start emulationstation
```

`/roms/ports/PortMaster.sh`:

```bash
#!/bin/bash
sudo systemd-run --unit=portmaster --collect /usr/local/bin/portmaster-console.sh
```

Assim ele aparece na lista **Ports**, junto dos outros atalhos.

## Onde os ports vão parar

- Atalhos: `/roms/ports/*.sh`
- Dados de ports: `/roms/ports/<nome>/`
- Configuração do PortMaster: `/roms/tools/PortMaster/config`

A partição `/roms` da imagem enxuta tem ~960 MB. Dois ou três ports pequenos cabem; ports grandes não. Alternativa: usar o segundo cartão (veja [09](09-cartao-tf2.md)).

## Como sair da interface

No PortMaster, **START + SELECT** juntos encerram a GUI (o código verifica `buttons['START'] and buttons['BACK']`).

Neste controle, esses botões são os extras (códigos 704–708 no evdev). Se não responder, feche pelo SSH:

```bash
sudo systemctl stop portmaster
sudo systemctl start emulationstation
```

## Runtimes

No primeiro uso o PortMaster baixa `pylibs.zip` e cria `pylibs/`. Precisa de internet no aparelho — o Wi-Fi aqui dá conta (~200 Mb/s). Se a tela travar no primeiro download, espere: ele está extraindo.

Runtimes de ports específicos (Love, Mono, etc.) são baixados por port, quando necessários.
