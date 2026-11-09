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

Foi assim que descobrimos o problema de SDL2 documentado em [07](07-emulationstation-e-sdl.md).
