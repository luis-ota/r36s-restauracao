# 11 — Lições aprendidas

Lista curta, na ordem em que teriam economizado mais tempo.

## Sobre a tela

1. **DTB errado = tela preta, não aparelho morto.** Antes de abrir o aparelho, teste o DTB anterior.
2. **O `/dev/fb0` não é o que está na tela.** Para ver o EmulationStation, leia o framebuffer do CRTC via DRM ([08](08-captura-de-tela.md)).
3. **Dois programas desenhando na mesma tela = salada.** Antes de culpar o tema, procure processo órfão (`ps -ef | grep pugwash`).

## Sobre cartão

4. **Cartão que reporta tamanho errado está morto.** 512 KB não tem partição para recuperar.
5. **Teste de escrita/leitura em cinco pontos** antes de confiar em qualquer cartão.
6. **FAT32, não exFAT** para a TF2 — o kernel 4.4 monta `vfat`.

## Sobre performance

7. **O `perfmax` do ArkOS derruba seu governor** a cada jogo. Se você travou em `performance` e voltou para `ondemand`, é isso.
8. **Não existe ganho de FPS em frequência acima de 1.296 MHz** neste kernel por sysfs. O limite é o kernel, não a configuração.
9. **zram não ajuda emulação** aqui: a CPU já é o gargalo, e comprimir memória consome CPU.
10. **Nenhuma fonte pública mede FPS de jogo neste aparelho.** Desconfie de porcentagens redondas.

## Sobre PortMaster e EmulationStation

11. **`/roms2` fantasma** faz o PortMaster instalar ports invisíveis. Confira `HM_DEFAULT_PORTS_DIR` no log.
12. **`ParseGamelistsOnly` esconde sistemas sem `gamelist.xml`** — inclusive a pasta Ports inteira.
13. **SDL2 tem quatro builds na imagem** e nem todas conversam com o `libudev` daqui. A build antiga que "funciona" gira a tela 90°.
14. **`systemd-run` é o que salva** quando o script precisa parar o EmulationStation sem morrer junto.
15. **`systemctl start` não sobe serviço em `failed`** — precisa de `reset-failed` antes.

## Sobre o controle

16. **Este controle não tem START/SELECT clássicos.** Os botões extras são evdev 704–708; L/R são 310/311.
17. **Script que espera botão inexistente "não fecha"** e deixa processo órfão.

## Sobre processos

18. **`pkill -f NomeDoScript` pelo SSH mata a própria sessão** se o padrão casar com o comando remoto. Prefira PID exato.
19. **Sempre verifique se o processo anterior morreu** antes de abrir de novo.

## Sobre escrever documentação

20. **O que você descarta vale tanto quanto o que funciona.** Metade do tempo perdido foi em soluções plausíveis que não se aplicam a este hardware.

## Sobre confiar em cartão (a parte que doeu)

21. **Um sistema que funciona o dia inteiro pode não voltar do reboot.** Em um cartão que já tinha dado erro, o aparelho não ligou depois de um reboot: o ext4 perdeu diretórios inteiros (`/opt/system`, `/home/ark/...`) e o setor de boot do exFAT foi sobrescrito por dados de outro arquivo. O `e2fsck` deixou o root "limpo", mas sem esses diretórios.
22. **`fsck` limpo não quer dizer sistema inteiro.** Depois do reparo, confira se os diretórios importantes ainda existem.
23. **Teste com zeros e leitura pelo cache não prova nada.** Grave dados aleatórios, leia com `iflag=direct` e compare o hash. Sem isso, você mede a memória do PC, não o cartão.
24. **Não gaste um cartão suspeito em alta capacidade.** Se ele guarda só uma fração do que anuncia, crie uma partição menor que o trecho já testado.
25. **Guarde uma imagem boa com checksum.** Foi ela que trouxe o sistema de volta em minutos, em vez de refazer tudo. O que você alterou depois da imagem se perde, então leve scripts e temas para fora do cartão.
26. **Um cartão pode passar no PC e falhar no aparelho.** Um cartão aprovado no leitor USB apareceu na segunda porta com o tamanho errado e erros de I/O. Teste também no slot onde ele vai ficar.
27. **Tema em `/roms/themes` morre junto com a partição de ROMs.** Em `/etc/emulationstation/themes` há um symlink para lá.
28. **Um atalho chamado `PortMaster.sh` em `/roms/ports` some quando o PortMaster abre.** Com o nome `AbrirPortMaster.sh`, ele fica. Não localizei a linha exata que apaga o arquivo.

## O que ainda não sabemos

- A causa exata da corrupção no reboot. O cartão já era suspeito, mas não dá para descartar outra causa.

- O motivo exato do erro de símbolo `udev` intermitente no SDL2 2.0.18.2. A hipótese mais forte é concorrência de display com processo órfão, mas não foi provado.
- O blob Mali correto para casar userspace (`10.6`) com kernel (`11.7`) nesta imagem. Sem ele, qualquer app GLES cai para software.
- Quanto de ganho real o governor `performance` dá em cada jogo. Só sabemos que a frequência para de oscilar.
