# 03 — Primeiro boot, rede e SSH

## Sequência de boot que funciona

1. Cartão com bootloader + BOOT + root + DTB de fábrica.
2. Ao ligar, o EmulationStation sobe e aparece o menu.
3. Se a tela ficar preta mas o aparelho responder na rede, o problema é DTB — veja [01](01-hardware-e-diagnostico.md).

## Wi-Fi

O ArkOS tem assistente de Wi-Fi no menu. Alternativa por linha de comando:

```bash
nmcli device wifi list
nmcli device wifi connect "SUA_REDE" password "SUA_SENHA"
```

Confira o IP:

```bash
ip -4 -br addr show
```

## SSH

O ArkOS aceita SSH com o usuário padrão:

```
usuário: ark
senha:   ark
```

**Troque a senha** em *Options → Change Password* antes de deixar o aparelho em rede. Este repositório não publica credenciais de ninguém.

Para facilitar, crie um host no `~/.ssh/config` da sua máquina:

```
Host r36s
    HostName 192.168.1.xxx
    User ark
```

Evite gravar a senha em texto no config. Use chave, ou deixe o `ssh` pedir.

## Ritmo da rede neste aparelho

Medido no próprio R36S, via Wi-Fi, contra a Cloudflare (não é a velocidade do PC):

| Métrica | Valor |
|---|---|
| Download | ~207 Mb/s |
| Upload | ~105 Mb/s |
| Latência (conexão) | ~21 ms |
| TTFB | ~95 ms |

Ou seja: o Wi-Fi **não** é o gargalo para baixar ports ou temas. Download grande pode ser feito direto no aparelho.

## Comandos úteis de diagnóstico

```bash
# estado do EmulationStation
systemctl status emulationstation --no-pager

# reiniciar o menu
sudo systemctl restart emulationstation

# se o serviço ficou em failed
sudo systemctl reset-failed emulationstation
sudo systemctl start emulationstation

# espaço nas duas partições
df -h / /roms

# o que está segurando a tela
ps -ef | grep -E "emulationstation|pugwash|love"
```

## Erro clássico: serviço em `failed`

Quando o EmulationStation cai, `systemctl start` não funciona até limpar o estado:

```bash
sudo systemctl reset-failed emulationstation
sudo systemctl start emulationstation
```

Isso não conserta a causa, mas devolve o menu. A causa precisa ser lida no log:

```bash
sudo journalctl -u emulationstation -n 40 --no-pager
```

Atenção: hoje o `systemd-journald` deste aparelho está mascarado, então o `journalctl` só mostra registros antigos. Confira com `systemctl is-enabled systemd-journald`. Se estiver `masked`, pare o serviço e rode `/usr/bin/emulationstation/emulationstation` pelo SSH para ver o erro.

Foi assim que descobrimos o problema de SDL2 documentado em [07](07-emulationstation-e-sdl.md).

## Rede pelo celular sem o dongle de Wi-Fi

Há dois jeitos de dar internet ao aparelho fora de casa, e eles são bem diferentes.

### 1. Hotspot do celular (o simples)

O R36S entra no **hotspot** do celular como cliente Wi-Fi, igual a qualquer rede:

```bash
nmcli device wifi list
nmcli device wifi connect "HOTSPOT" password "SENHA"
```

Detalhes que fazem diferença: o hotspot precisa estar em **2.4 GHz** (o Wi-Fi deste aparelho não vê 5 GHz) e em **WPA2** (WPA3 puro costuma falhar).

### 2. Celular no cabo (USB tethering)

A porta USB-C do R36S é compartilhada: normalmente ela roda em modo **gadget** (o PC vê o aparelho em `192.168.7.2`). Mas a mesma porta roda em modo **host** — é assim que o dongle de Wi-Fi funciona nela. Então, **sem o dongle**, dá para colocar o celular no cabo e usar o tethering dele.

Requisitos:

- Adaptador **OTG** (USB-C macho → USB-A fêmea) e o cabo do celular.
- Celular **Android** com "Tethering USB" ligado. **iPhone não funciona**: o kernel 4.4 deste aparelho não tem o módulo `ipheth`.
- O dongle de Wi-Fi tem que estar fora — a porta é uma só.

O script [`scripts/r36s-tether.sh`](../scripts/r36s-tether.sh) faz a troca:

```bash
sudo r36s-tether.sh        # tira o modo gadget, carrega rndis_host e pega DHCP
sudo r36s-tether.sh --off  # volta ao modo gadget (o PC vê o R36S de novo)
```

O que ele faz, em ordem:

1. para o `r36s-usbnet` e descarrega o `g_ether` (libera a porta);
2. carrega `usbnet`, `rndis_host` e `cdc_ether`;
3. espera aparecer `usb0`/`eth1` (a interface do celular);
4. `ip link set up` + `dhclient`;
5. testa `ping 1.1.1.1` e avisa se não houver internet.

Se nenhuma interface aparecer, ele **restaura o modo gadget** e sai com erro, em vez de deixar o aparelho sem rede nenhuma. Testado esse caminho no aparelho.

Limites medidos/sabidos:

- O kernel tem `rndis_host`, `cdc_ether` e `usbnet`, e o `dhclient` existe: a parte de software está pronta.
- **Não foi testado com um celular de verdade** — falta o aparelho na mão e o adaptador OTG.
- O R36S precisa alimentar o celular pela porta. Celular que se recusa a carregar por OTG pode não liberar o tethering.
- Enquanto o tethering está ligado, o cabo não serve para acessar o R36S pelo PC (a porta está em modo host).

Com o Tailscale ([19](19-tailscale-no-r36s.md)), qualquer um dos dois caminhos deixa o aparelho alcançável pelo mesmo IP da tailnet.
