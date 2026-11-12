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

## Sobre arquivos, serviços e manutenção

29. **Dump de cartão morrendo também tem arquivo corrompido.** Uma cópia do blob Mali tirada do dump do cartão original tinha **o mesmo tamanho** do arquivo bom (40.867.064 bytes) e o cabeçalho de versão destruído; `readelf -V` acusava `Version: 545`. Validar com `sha256sum` **e** `readelf -V` antes de instalar qualquer arquivo vindo de dump.
30. **Não rode `apt upgrade` nesta base.** Ubuntu 19.10 sem suporte, kernel em `hold`, pouco espaço livre e nenhum rollback. Ver [15 — Atualizações](15-atualizacoes-e-limites-da-base.md).
31. **O `systemd-journald` deste aparelho está mascarado**, então o `journalctl` só mostra registros antigos. Para serviço próprio, `StandardOutput=append:` num arquivo é mais confiável que `journalctl`.
32. **`/proc/<pid>/comm` pode ter byte inválido.** Ler em texto quebra o serviço com `UnicodeDecodeError`; abra em binário e compare com `b"nome"`.
33. **O teclado virtual que funcionou registra as teclas 1 a 248 e espera 2,5 s** depois do `UI_DEV_CREATE`. O teste mudou a tecla e a quantidade ao mesmo tempo, então não dá para dizer qual detalhe foi decisivo.
34. **Joystick virtual não fez o DraStic salvar; teclado virtual fez.** O motivo não foi isolado. Salvar só passou a funcionar quando a tecla veio de um teclado `uinput`, não de um gamepad `uinput`.
35. **Reiniciar um serviço próprio no meio do jogo é seguro; parar o EmulationStation não é.** Derrubar o menu mata o DraStic junto.

## Sobre diagnóstico de GPU e bibliotecas (LÖVE)

36. **`readelf` e `objdump` do próprio aparelho não são confiáveis para blob Mali.** Emitem avisos de símbolo fora do `sh_info` e contagens que não batem. Copie o blob para o PC e leia com `pyelftools`.
37. **Leia a ordem de carga antes de chutar causa.** `LD_DEBUG=files` mostrou em uma rodada o que seis rodadas de tentativa (`LD_LIBRARY_PATH`, `RPATH`, driver do SDL) não tinham mostrado. Ver [16](16-love-e-gles.md).
38. **Teste como o mesmo usuário do serviço que funciona.** O EmulationStation roda como `ark`, não como root. Um teste como root pode dar um resultado que não vale para o menu.
39. **"O EmulationStation funciona" não prova que a biblioteca é boa para outro programa.** O ES liga `libEGL.so` e `libgo2.so` de forma diferente do LÖVE. Compare o que cada um carrega antes de concluir.
40. **Mudança que não altera o erro é hipótese descartada, não solução.** Registre a tentativa com o resultado do log, para ninguém repetir a mesma coisa. Nesta investigação, o erro de versão ficou idêntico em todas as dez tentativas.

## O que ainda não sabemos

- A causa exata da corrupção no reboot. O cartão já era suspeito, mas não dá para descartar outra causa.

- O motivo exato do erro de símbolo `udev` intermitente no SDL2 2.0.18.2. A hipótese mais forte é concorrência de display com processo órfão, mas não foi provado.
- ~~O blob Mali correto para casar userspace (`10.6`) com kernel (`11.7`) nesta imagem.~~

  **Revisado:** o blob nunca faltou. A imagem enxuta já tinha o arquivo certo, de 40.867.064 bytes. A causa do erro `10.6` contra `11.7` continua sem prova. A sequência medida aponta para o blob wayland (em `/usr/lib`), carregado pelo SDL na escolha do driver. Ver [06 — PortMaster](06-portmaster.md) e [16 — LÖVE e GLES](16-love-e-gles.md).

- Por que o LÖVE do PortMaster não abre janela neste ArkOS, mesmo com o runtime instalado. Ver [16](16-love-e-gles.md).
- Se o ES guarda algum estado de GPU que o LÖVE não tem (o `libgo2.so`, o momento de inicialização do `/dev/mali0`). Não testado.

- O comportamento do DraStic no boot: por que o load automático às vezes abre na tela inferior do DS. Ver [13 — Autosave](13-autosave-e-load-automatico.md).
- Quanto de ganho real o governor `performance` dá em cada jogo. Só sabemos que a frequência para de oscilar.
