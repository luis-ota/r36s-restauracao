# 14 — Hardware real e identificação (clone "soy sauce")

Este aparelho foi vendido como R36S, mas **não é uma R36S original**: a placa é da família `Y3506`, conhecida na comunidade como "soy sauce". Este documento mostra como identificar, o que foi medido, o que muda na prática e qual firmware serve.

## Por que identificar antes de qualquer coisa

O nome "R36S" não diz nada sobre a placa. Existem pelo menos três famílias de placa com esse nome comercial, e **cada uma pede um DTB e um painel diferentes**. Instalar a imagem errada dá tela preta, sem mensagem de erro — o aparelho sobe, responde na rede e a tela fica apagada.

## Como identificar em três passos

1. **Placa.** Abra a tampa traseira (parafusos na traseira) e leia o texto impresso na PCB. É o identificador que vale, muito mais que a etiqueta.
2. **DTB em uso.** Na partição BOOT:

   ```bash
   ls /boot/*.dtb
   grep -i "load mmc.*dtb" /boot/boot.ini
   ```

3. **O que o kernel enxerga:**

   ```bash
   cat /sys/firmware/devicetree/base/model
   tr '\0' '\n' < /sys/firmware/devicetree/base/compatible | head -3
   ```

## O resultado deste aparelho

| Verificação | Valor encontrado |
|---|---|
| PCB | `Y3506_V03_20241210` (lote `2507` logo abaixo) |
| Etiqueta | "Game Console", `MODEL No: R36S`, sem marca |
| DTB carregado | `/boot/rk3326-r35s-linux.dtb` (md5 `9dd051f13539f98450d8b8b8d929b5c0`) |
| Nó de painel dentro do DTB | `panel@0`, compatível `elida,kd35t133`, `simple-panel-dsi`, timings de 60 Hz declarados |
| `model` em execução | `Rockchip RK3326` |
| `compatible` | `rockchip,rk3326-odroidgo3-linux` |

Na tabela de compatibilidade do dArkOSRE, a placa `Y3506_v03_20241210` aparece na seção **"Soy Sauce"**, com status **completed** e testador. Ou seja: é um clone conhecido, mapeado e já testado por outra pessoa.

> Correção de documentação anterior: este repositório dizia "painel V5" e "DTB `elida,kd35t133`". O `elida,kd35t133` é o **driver do painel dentro** do DTB, não o nome do DTB. E "V5" é outra revisão da placa (`Y3506_V05`), não esta. Esta é **V03**.

## Inventário medido

Tudo abaixo foi lido do próprio aparelho, não veio de ficha de loja:

| Item | Medição |
|---|---|
| SoC | Rockchip RK3326, 4× Cortex-A35 |
| Frequências disponíveis | 1008 / 1200 / 1248 / 1296 MHz |
| RAM | 919.104 kB visíveis (~1 GiB) |
| GPU | Mali-G31 (Bifrost), blob proprietário |
| Tela | DSI, `640x480p78`, framebuffer `640,480` |
| Áudio | codec `rk817` (alto-falante e fone) |
| Bateria | `rk817-battery`, carga completa **3.188 mAh**, saúde `Good` |
| Etiqueta da bateria | 3,8 V, 3500 mAh (o medidor registra 3.188 mAh) |
| Analógicos | analógicos reais: `ABS_X`, `ABS_Y`, `ABS_RX`, `ABS_RY` |
| Entradas | `event1` = `GO-Super Gamepad`; `event3` = `odroidgo3-keys`; `event0` = `rk8xx_pwrkey` |
| Botões extras | SELECT = 704, START = 705, mais 706–708 |
| Temperatura | ~47 °C em repouso |
| Armazenamento | dois cartões, sistema e jogos, ambos a 50 MHz |

## Original × clone: o que muda

| Aspecto | Muda? | Comentário |
|---|---|---|
| Desempenho | **Não** | Mesmo SoC, mesma GPU, mesma RAM, mesma tela. FPS é igual. |
| Tela | Depende | Mesma resolução; o lote do painel varia e exige DTB compatível. |
| Controles | Às vezes | Analógicos e borrachas variam por lote. Aqui os analógicos são de verdade. |
| Bateria | Às vezes | Capacidade e saúde variam. Aqui está saudável. |
| Suporte | **Sim** | Projetos "para R36 original" não cobrem clone. |
| Garantia | **Sim** | Sem suporte do fabricante original. |
| Valor de revenda | **Sim** | Não é o modelo "autêntico" que a comunidade referencia. |
| Facilidade de firmware | **Sim** | Precisa de imagem com DTB para a placa certa. |

Resumo honesto: **clone não é sinônimo de aparelho pior, é sinônimo de aparelho sem suporte oficial.** O que define a experiência é o SoC, e ele é o mesmo.

## A família de firmwares, sem confusão

Confusão comum no fórum: são ramos da mesma árvore, não sistemas independentes.

| Nome | O que é | Serve neste aparelho? |
|---|---|---|
| **ArkOS** | Sistema original desta imagem. Autor arquivou o projeto no fim de 2025. | É o que está rodando |
| **dArkOS** | Sucessor oficial do ArkOS, base Debian. Não tem imagem para R36S. | Não tem imagem |
| **dArkOSRE** | Fork do dArkOS adaptado **por placa**, cobre R36S e clones. | **Sim**, placa listada como testada |
| **dArkOSen** | "dArkOS Enhanced". Recursos extras, feito para **R36 originais**. | **Não** — autor não cobre clones |
| **ArkOS4Clone** | Imagem comunitária com seletor de DTB para clones | Sim, alternativa |
| **ROCKNIX** | Continuação do JELOS, tem imagem RK3326 e variante para clones | Sim, alternativa |

O ponto prático: **não instale dArkOSen neste aparelho**. Se um dia quiser trocar de sistema, o caminho documentado é o **dArkOSRE**, com a placa `Y3506_v03_20241210`.

## O ponto frágil não é o clone, são os cartões

O sistema e os jogos estão em cartões genéricos, sem marca, negociando a 50 MHz. Foi um cartão ruim que derrubou o aparelho na primeira vez. Antes de trocar de aparelho ou de sistema, **um cartão de marca muda mais a vida do que qualquer firmware**.

Regras que já valeram a pena:

- Testar o cartão com dados aleatórios e leitura `iflag=direct` antes de confiar.
- Guardar uma imagem completa do sistema que funciona, com checksum.
- Manter os saves fora do cartão do sistema.

## Se trocar de painel ou de placa

Refaça os três passos de identificação e **anote aqui**: placa, DTB e timings. O DTB é o item mais fácil de perder e o mais difícil de adivinhar.
