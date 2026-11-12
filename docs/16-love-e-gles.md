# 16 — LÖVE no R36S: funciona, com um erro de log que não impede nada

**Status: o LÖVE 11.5 do PortMaster abre janela e roda neste ArkOS.** Os erros de `/dev/mali0` aparecem no log, mas não impedem o jogo de desenhar.

Prova (gravação da tela, quadros reais): [quadro inicial](img/love-quadro-inicio.png), [quadro no meio da execução](img/love-quadro-meio.png) e [o vídeo da execução](img/gravacao-love.mp4).

## Correção desta versão do documento

Uma versão anterior deste texto dizia que o LÖVE **não abria janela** e que a causa era o blob Mali. **Isso estava errado.** O erro foi confiar nos logs sem olhar a tela: o `drmcap.py` não estava no aparelho, então as capturas falhavam sem aviso, e eu não tinha nenhuma imagem para checar. Quando a captura foi feita de verdade, o jogo apareceu.

Os experimentos com shim de `dlopen`, pré-carga de blobs e driver `kmsdrm` estão descritos abaixo como histórico. Eles foram feitos a partir de uma premissa falsa e não fazem parte da solução.

## Como rodar que funciona

Como o usuário `ark` (o mesmo que roda o EmulationStation), com as bibliotecas do próprio runtime e o SDL do sistema, sem definir driver de vídeo:

```bash
L=/opt/system/Tools/PortMaster/runtimes/love_11.5
sudo -u ark env LD_LIBRARY_PATH=$L/libs.aarch64 XDG_RUNTIME_DIR=/run/user/1002 SDL_AUDIODRIVER=alsa \
  $L/love.aarch64 /mnt/jogos/love-test
```

- `XDG_RUNTIME_DIR` precisa existir e pertencer a `ark` (`/run/user/1002`). Sem isso, o SDL reclama, mas o teste de tela foi feito com ele criado.
- O teste de tela da pasta `experimentos/love-gles/` sai com SELECT ou START, ou depois de 25 s.
- O EmulationStation deve estar **parado** enquanto o LÖVE roda. Com o menu na tela, os dois disputam o display (ver [06, armadilha 4](06-portmaster.md)).

## O erro que aparece no log (e não impede nada)

```
file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)
Failed creating base context during opening of kernel driver.
```

Pela trilha de carga (`LD_DEBUG=files`), o SDL, ao escolher o driver de vídeo, carrega primeiro o blob de **wayland** (`libmali-bifrost-g31-rxp0-wayland-gbm.so`). É ele que imprime essa mensagem. Depois disso o SDL segue e o LÖVE renderiza normalmente.

**Não está provado** que o blob wayland seja a causa da versão `10.6`. O que está medido é a sequência: a mensagem sai quando esse blob é carregado, e o jogo continua. Ninguém precisa consertar isso para o LÖVE funcionar.

## Medido na gravação

- Quadro 02: `t = 0.2`, `fps: 4` (início, o SDL ainda está inicializando).
- Quadro 20: `t = 12.2`, `fps: 77`, quadrado vermelho se movendo.
- O quadrado vermelho que você viu na tela era **este teste**, rodando, e não um erro visual.
- Os 40 quadros cobrem cerca de 35 s. A execução termina pelo `love.event.quit` do teste (25 s), e o aparelho volta para a tela preta antes do EmulationStation subir de novo.

Não foi testado ainda: o botão SELECT/START de saída pelo controle (o `joystickpressed` do teste), o áudio pelo ALSA durante o jogo e um jogo de PortMaster de verdade.

## Histórico (tentativas da versão anterior)

Essas tentativas foram avaliadas só pelo log de erro. Como o resultado real era outro, nenhuma delas tem valor como solução, mas ficam registradas para não serem repetidas por engano:

| Tentativa | Observação |
|---|---|
| `LD_LIBRARY_PATH` com as libs do runtime, como root | Log com erro de versão, mas o jogo rodava |
| Pasta curada `/tmp/lovelibs` sem EGL/GLES/SDL do runtime | Idem |
| Symlinks de EGL/GLES/gbm apontando para o GBM | Idem |
| `SDL_VIDEODRIVER=kmsdrm` | Idem |
| `LD_PRELOAD` com GBM e wayland | Idem |
| Shim `dlopen` (`RTLD_NOW` → `RTLD_LAZY`), código em [`experimentos/love-gles/dlshim.c`](../experimentos/love-gles/dlshim.c) | Idem |
| Como `ark`, com `LD_PRELOAD` do GBM | Idem |

## Ponte com o bug visual do PortMaster

O splash do PortMaster também roda em LÖVE e pisca junto com o menu do EmulationStation, porque os dois disputam o display. A solução é a mesma do [doc 06](06-portmaster.md): rodar com o EmulationStation parado. Esse ponto **não foi retestado** com o LÖVE correto nesta versão do documento.

## Reproduzir a gravação

O script [`experimentos/love-gles/teste-love.sh`](../experimentos/love-gles/teste-love.sh) para o EmulationStation, roda o teste, grava os quadros com `drmcap` e devolve o menu. Ele exige que o `drmcap.py` esteja em `/tmp` do aparelho, que o `main.lua` esteja em `/mnt/jogos/love-test/`, e que nenhum jogo esteja aberto. Confira que o arquivo de captura foi criado: uma captura que falha sem aviso foi justamente o que nos enganou aqui.
