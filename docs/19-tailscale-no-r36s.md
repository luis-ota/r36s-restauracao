# 19 — Tailscale no R36S

O aparelho agora entra na tailnet e responde por SSH de **qualquer rede Wi-Fi**, sem depender do IP da rede local nem de abrir porta no roteador.

## Por que isso resolve

Antes, o acesso era por `192.168.1.18` (Wi-Fi de casa) ou `192.168.7.2` (cabo USB). Fora de casa, ou em outra rede, não havia acesso. Com o Tailscale, o aparelho mantém uma conexão de saída para o plano de controle e fica alcançável pelo IP da tailnet em qualquer lugar com internet.

## O que o aparelho tinha

- Kernel 4.4.189, aarch64, glibc 2.30 (Ubuntu 19.10).
- `/dev/net/tun` presente e módulo `tun.ko` na imagem.
- ~304 MB livres no rootfs antes da instalação.

Isso é suficiente: o pacote estático não usa a glibc do sistema e o `tailscaled` usa o TUN do kernel.

## Instalação

Baixe o pacote estático arm64 no PC e leve os dois binários:

```bash
curl -O https://pkgs.tailscale.com/stable/tailscale_<versao>_arm64.tgz
tar xzf tailscale_<versao>_arm64.tgz
```

Opcional, mas economiza espaço no cartão: `llvm-strip tailscale tailscaled` (de 31+40 MB para 21+27 MB).

No aparelho:

```bash
sudo install -m 755 tailscale  /usr/local/bin/tailscale
sudo install -m 755 tailscaled /usr/local/bin/tailscaled
sudo install -m 644 tailscaled.service /etc/systemd/system/tailscaled.service
sudo systemctl daemon-reload
sudo systemctl enable --now tailscaled
```

## O serviço

`/etc/systemd/system/tailscaled.service`:

```ini
[Unit]
Description=Tailscale node agent (R36S)
After=network-pre.target NetworkManager.service
Wants=network-pre.target

[Service]
Type=notify
ExecStartPre=/usr/local/bin/tailscaled --cleanup
ExecStart=/usr/local/bin/tailscaled --state=/var/lib/tailscale/tailscaled.state --port=41641
Restart=on-failure
RestartSec=5
RuntimeDirectory=tailscale
StateDirectory=tailscale
CacheDirectory=tailscale

[Install]
WantedBy=multi-user.target
```

`RuntimeDirectory` e `StateDirectory` criam `/run/tailscale` e `/var/lib/tailscale` com a permissão certa. O estado fica no cartão e o nó não precisa ser autorizado de novo a cada boot.

### Armadilha: o caminho do socket

O `tailscaled` aceita `--socket=...`, mas o CLI procura o padrão `tailscaled.sock`. Na primeira tentativa usei `--socket=/run/tailscale/tailscaled.socket` (nome diferente) e o resultado foi:

```
failed to connect to local tailscaled ... dial unix /var/run/tailscale/...
```

Solução: **não** passe `--socket`; deixe o padrão. E rode o CLI com `sudo` (o socket é `0700` do root).

## Login

```bash
sudo tailscale up --hostname=r36s --accept-dns=false
```

O comando imprime um link (`https://login.tailscale.com/a/...`) e fica esperando. Rode-o de um jeito que sobreviva ao fim da sessão SSH, senão o link pode expirar:

```bash
sudo systemd-run --unit=tsup --collect \
  --property=StandardOutput=append:/tmp/tsup.log \
  --property=StandardError=append:/tmp/tsup.log \
  /usr/local/bin/tailscale up --hostname=r36s --accept-dns=false
```

Depois é só abrir o link e aprovar na conta.

**`--accept-dns=false` é de propósito**: não quero que o Tailscale mexa no DNS deste ArkOS antigo nem quebre a resolução local.

## Verificação feita

- `tailscale status` no PC lista o nó **r36s** com um IP da faixa `100.x` da tailnet.
- `tailscale ping r36s`: resposta direta pela rede local (poucos ms).
- HTTP de teste (`python3 -m http.server`) respondeu **200** tanto pelo IP da LAN quanto pelo IP da tailnet, provando que TCP passa.
- SSH pelo IP da tailnet: conecta e roda comando.
- `tailscaled`: `enabled` e `active`; volta sozinho no boot.

### Detalhe do primeiro SSH

Na primeira conexão o `ssh` ficou parado esperando a confirmação da host key nova. Com `StrictHostKeyChecking accept-new` (ou respondendo `yes` uma vez) passa direto. Não era problema de MTU nem de rede: ICMP e HTTP já funcionavam.

## Uso

No PC, um alias em `~/.ssh/config`:

```
Host r36s-ts
    HostName <ip-da-tailnet>
    User ark
    StrictHostKeyChecking accept-new
```

Aí é `ssh r36s-ts` de qualquer lugar. O acesso continua por senha do usuário `ark`; se quiser acesso sem senha, o caminho é instalar a chave pública do PC em `~/.ssh/authorized_keys` do aparelho (não feito).

## Limites

- Precisa de internet no aparelho. Sem rede, nada de tailnet.
- O nó aparece na tailnet mesmo dormindo, mas só responde quando o Wi-Fi conecta.
- Se o roteador bloquear UDP, o Tailscale cai para relay (DERP): funciona, só mais lento.
- Não foi testado em outra rede Wi-Fi de verdade; a verificação foi na rede de casa, com conexão direta.
