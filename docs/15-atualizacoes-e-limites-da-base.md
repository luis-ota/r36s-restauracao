# 15 — Atualizações do sistema e os limites desta base

## Resposta curta

**Não rode `apt update && apt upgrade` neste aparelho.** Não é preguiça nem superstição: é o tipo de operação que transforma um console que funciona num console que não sobe, e não existe desfazer.

## O que foi medido na imagem

```
VERSION="19.10 (Eoan Ermine)"
PRETTY_NAME="Ubuntu 19.10"
VERSION_CODENAME=eoan
```

```bash
$ grep -hvE '^\s*#|^\s*$' /etc/apt/sources.list
deb http://old-releases.ubuntu.com/ubuntu eoan main universe
deb http://old-releases.ubuntu.com/ubuntu eoan-updates main universe
deb http://old-releases.ubuntu.com/ubuntu eoan-security main universe
deb http://deb.odroid.in/go2 bionic main

$ dpkg --get-selections | awk '$2=="hold"{print $1}'
linux-odroid-go2

$ df -h /   # raiz com cerca de 90% de uso
```

Quatro fatos, cada um já é motivo suficiente:

1. **A base está morta desde julho de 2020.** Ubuntu 19.10 saiu de suporte e os repositórios apontam para `old-releases.ubuntu.com`, que é um **arquivo congelado**. Não há correção nova ali: você traria pacotes de 2020 por cima de uma imagem montada à mão.
2. **O pacote do kernel está em `hold` de propósito.** Alguém travou `linux-odroid-go2` porque trocar o kernel neste aparelho quebra o boot. Um `upgrade` tenta resolver isso e pode destravar o que foi travado.
3. **A raiz estava com cerca de 90% de uso.** Um upgrade baixa e descompacta centenas de pacotes. Encher o disco no meio do processo deixa o sistema em estado inconsistente.
4. **Sem rollback.** Não há snapshot, não há `btrfs`, não há como voltar. O único desfazer é regravar o cartão a partir de uma imagem.

## Por que quebra: ABI, não "versão velha"

Esta imagem não é um Ubuntu de desktop com pacotes soltos. Ela carrega binários **compilados para esta base**:

- RetroArch 1.9.13 e os cores,
- EmulationStation e as bibliotecas de SDL2/udev,
- o blob proprietário do Mali (`libEGL`, `libGLESv2`, `libgbm` apontam todos para ele),
- os emuladores standalone e as ferramentas do ArkOS.

Um upgrade puxa glibc e bibliotecas mais novas. Os binários acima passam a pedir símbolos que não existem, ou pior, carregam uma biblioteca e falham no meio. O sintoma clássico aqui é:

```
error while loading shared libraries: ... unsupported version 545 of Verneed record
```

Isso já aconteceu de forma controlada: um único arquivo do Mali trocado por uma cópia corrompida derrubou o EmulationStation inteiro. Um upgrade faz esse tipo de troca em dezenas de arquivos de uma vez.

## O que é razoável fazer

| Ação | Veredito |
|---|---|
| `apt update && apt upgrade` | **Não** |
| `apt dist-upgrade` / `do-release-upgrade` | **Jamais** |
| Instalar **um** pacote específico, sabendo o que ele arrasta | Aceitável, com imagem de backup em mãos |
| Atualizar RetroArch/core por conta própria | Já foi feito aqui, com versão fixa e backup (`retroarch.1913.bak`) |
| Atualizar o sistema | Trocar de imagem em cartão novo, não atualizar no lugar |

Se precisar de um programa novo, instale só ele e confira o que veio junto:

```bash
apt-get install -s pacote     # simulação, não instala
```

## "E uma VM para testar?"

VM de PC não emula o Mali-G31 deste chip. O que quebra neste aparelho é driver gráfico proprietário casado com kernel 4.4 — uma VM mostraria outra GPU, outro driver e outro resultado. Testar em VM dá falsa confiança justamente no ponto que mais quebra.

O laboratório útil é outro: **uma cópia do cartão**. Imagem boa + cartão separado = teste real, com volta garantida.

## O caminho certo para "sistema mais novo"

Se um dia isso importar, é imagem nova num cartão novo:

1. Escolher firmware compatível com a **placa** (veja [14 — Hardware real](14-hardware-real-e-identificacao.md)).
2. Gravar num cartão diferente, nunca no que está funcionando.
3. Conferir painel e DTB no primeiro boot.
4. Migrar saves e ajustes depois que o sistema novo provar que sobe.

O cartão atual continua intocado como plano B.

## Recuperação, se algo der errado

- **Imagem completa com checksum** do sistema funcionando: é o desfazer real.
- **Backup dos saves** fora do cartão do sistema, com versões numeradas.
- **Acesso por SSH** funciona mesmo com a tela apagada, o que salva a paciência em caso de DTB errado.

## A lição de ouro desta base

Sistema congelado não é sistema quebrado. Um console offline, que roda os jogos que você quer, **não ganha nada** com pacotes de 2020 sendo atualizados. O risco é todo seu e o ganho é zero.
