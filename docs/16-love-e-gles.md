# 16 — LÖVE no R36S: por que o jogo não abre

**Status: não resolvido.** O runtime do LÖVE do PortMaster não consegue criar o contexto OpenGL ES neste ArkOS. Este documento registra tudo que foi medido, tudo que foi tentado (inclusive o que não deu certo) e onde a investigação parou. Os arquivos de teste estão em [`experimentos/love-gles/`](../experimentos/love-gles/).

## Resumo

- **Runtime:** `love_11.5` do PortMaster, em `/opt/system/Tools/PortMaster/runtimes/love_11.5/`. Binário `love.aarch64`, bibliotecas em `libs.aarch64/` (`liblove-11.5.so`, `libluajit-5.1.so.2`, `libmodplug.so.1`, `libogg.so.0`). O runtime **não traz SDL nem EGL**: usa as bibliotecas do sistema.
- **Erro que impede a janela:**

  ```
  file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)
  Failed creating base context during opening of kernel driver.
  Kernel module may not have been loaded
  ```

- **Sintoma visual relacionado:** o splash em LÖVE do PortMaster pisca entre a própria interface e o menu do EmulationStation. É a mesma raiz (ver [06, armadilha 4](06-portmaster.md)).
- **Não é** falta de biblioteca. O loader encontra tudo; o erro acontece depois, na inicialização da GPU.

## O que o aparelho tem (medido)

### Bibliotecas gráficas

Há dois blobs Mali na imagem, e os nomes de `libEGL`, `libGLESv2` e `libgbm` são symlinks para eles:

| Caminho do symlink | Aponta para |
|---|---|
| `/usr/local/lib/aarch64-linux-gnu/libEGL.so.1`, `libGLESv2.so.2`, `libgbm.so.1` | `libmali-bifrost-g31-rxp0-gbm.so` (GBM, 40.867.064 bytes) |
| `/usr/lib/aarch64-linux-gnu/...` e `/lib/aarch64-linux-gnu/...` (mesmos nomes) | `libmali-bifrost-g31-rxp0-wayland-gbm.so` (wayland, 38.921.168 bytes) |

`ldconfig -p` lista `/usr/local` primeiro para `libEGL.so`, `libGLESv2.so` e `libgbm.so`. Assim, quem resolve pelo cache recebe o blob GBM.

### Como o EmulationStation funciona

O EmulationStation é o caso de referência, porque **funciona**:

- Seu binário tem `NEEDED` para `libEGL.so`, `libGLESv1_CM.so`, `libSDL2-2.0.so.0`, `libgo2.so` (a biblioteca de display do próprio ArkOS) e outras.
- Em `/proc/<pid>/maps`, com o menu aberto, aparecem **os dois blobs** mapeados (wayland primeiro, GBM depois), além de `/dev/mali0` aberto.
- O `emulationstation.sh` não define nenhuma variável de vídeo, de biblioteca ou de driver. Ele roda o binário direto.
- O processo roda como usuário **`ark`** (uid 1002), não como root.

### Blobs (análise no PC)

Os dois blobs foram copiados para o PC para análise, porque o `readelf` e o `objdump` do próprio aparelho emitem avisos ("local symbol ... at index >= .dynsym's sh_info") e contagens que não batem. Com `pyelftools` no PC:

- Nenhum dos quatro objetos envolvidos (`love.so`, `sdl2.so`, `gbm.so`, `wayland.so`) lista como indefinido os símbolos `glTextureStorage2DEXT` e `glMultiDrawElementsBaseVertexOES` na tabela dinâmica.
- Isso não explica o erro `symbol lookup error` que o `LD_DEBUG` mostrou para `libGLESv2.so.2`. A origem desses símbolos não foi encontrada.

## A ordem de carga (medida com `LD_DEBUG=files`)

Rodando o LÖVE como `ark`, com as bibliotecas do runtime e o SDL do sistema, sem definir driver de vídeo:

1. `liblove-11.5.so` pede `libSDL2-2.0.so.0`, que resolve para `/lib/aarch64-linux-gnu/libSDL2-2.0.so.0` (o do sistema).
2. O SDL, ao escolher o driver de vídeo, **carrega `libwayland-client` e depois `libmali-bifrost-g31-rxp0-wayland-gbm.so` por nome** (dynamically loaded). Esse blob puxa `libdrm` e `libwayland-server`.
3. Em seguida o SDL carrega `libEGL.so.1` (resolvido para o GBM em `/usr/local`), que abre `libGLESv2.so.2` (também GBM). Aparecem repetidos erros de lookup: `undefined symbol: eglGetPlatformDisplayEXT`.
4. Logo depois sai o erro `file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)`, duas vezes, e o contexto falha.

**O que a sequência prova:** o erro de versão aparece depois que o SDL carrega o blob wayland, e o EGL que chega ao GLES não tem `eglGetPlatformDisplayEXT` no escopo global.

**O que ela não prova:** que o blob wayland é o responsável pela versão `10.6`. Essa ligação continua sendo inferência.

## Tentativas (em ordem)

Todas rodadas com o LÖVE de teste (`main.lua`, em `experimentos/love-gles/`), captura de tela pelo `drmcap` e restauração do EmulationStation no fim.

| # | Mudança | Resultado |
|---|---|---|
| 1 | `LD_LIBRARY_PATH` com as libs do runtime, como root | Erro de versão do mali |
| 2 | Pasta curada `/tmp/lovelibs` sem EGL/GLES/SDL do runtime, com GBM | Erro de versão do mali |
| 3 | Symlinks de `libEGL`, `libGLESv2`, `libgbm` em todas as versões de SONAME, apontando para o GBM | Erro de versão do mali |
| 4 | `LD_DEBUG=libs` e `files` | Revelou a ordem de carga acima; sem solução |
| 5 | `SDL_VIDEODRIVER=kmsdrm` | Erro de versão do mali. **Observação:** a trilha de carga não foi refeita com kmsdrm, então não está confirmado se o blob wayland deixa de ser carregado |
| 6 | `LD_PRELOAD` com GBM e wayland, `kmsdrm` | Erro de versão do mali |
| 7 | Shim `dlopen` que troca `RTLD_NOW` por `RTLD_LAZY` (ver código abaixo), como root | Erro de versão do mali |
| 8 | Shim + `LD_PRELOAD` do GBM, como `ark`, com `kmsdrm` | Erro de versão do mali |
| 9 | Rodar como `ark` com as libs do runtime e o sistema | Erro de versão do mali |
| 10 | Patch binário no `SDL_LoadObject` (troca `RTLD_NOW` por `RTLD_LAZY`) | **Não concluído.** O `.text` do SDL foi desmontado, mas o `dlopen` real não foi localizado |

### O shim (tentativa 7)

Compilado no PC com `zig cc -target aarch64-linux-gnu.2.28`, código em [`experimentos/love-gles/dlshim.c`](../experimentos/love-gles/dlshim.c):

```c
#define _GNU_SOURCE
#include <dlfcn.h>

void *dlopen(const char *file, int mode) {
    static void *(*real)(const char *, int);
    if (!real) real = (void *(*)(const char *, int))dlsym(RTLD_NEXT, "dlopen");
    return real(file, (mode & ~RTLD_NOW) | RTLD_LAZY);
}
```

Não resolveu. Como o ES sobrevive com lazy binding e o erro continuou igual, a hipótese de `RTLD_NOW` foi descartada pelo teste, não só pela leitura.

## Hipóteses descartadas

- **Biblioteca faltando ou caminho errado:** descartado. Com `LD_LIBRARY_PATH` correto, o loader resolve tudo.
- **`RPATH`/`RUNPATH` escondido no binário do LÖVE:** descartado. `readelf -d` não mostra nenhum.
- **Usuário root contra `ark`:** descartado. O erro é igual nos dois.
- **Driver de vídeo wayland por padrão:** a trilha mostra o blob wayland carregado, mas forçar `kmsdrm` não eliminou o erro. Não é a causa isolada.

## Hipóteses em aberto

- **O `libgo2.so` do ES.** O ES faz o display por essa biblioteca, e o LÖVE não passa por ela. Não foi testado se o ES inicializa o `/dev/mali0` antes do GL, o que faria diferença na negociação de versão.
- **A versão negociada pelo ES.** Um rastreio de `ioctl` do ES e do LÖVE, comparando a versão enviada ao `/dev/mali0`, mostraria se o problema é a versão ou só a ordem de carga. Não foi feito: o aparelho não tem `strace`.
- **O blob wayland como causa da versão `10.6`.** Só confirmável com o rastreio acima.

## Próximo passo, se alguém for continuar

1. Instalar ou compilar um `strace` para o aparelho (ou cruzar com o PC via `uv run --with`) e capturar o `ioctl` de versão do `/dev/mali0` nos dois casos.
2. Rodar o ES com `LD_DEBUG=files` (exige parar o menu e relançar; só sem jogo aberto) e comparar a ordem de carga com a do LÖVE.
3. Se nada disso fechar, tratar o LÖVE como **não suportado** neste ArkOS e usar outra estratégia para os ports que dependem dele.

## Como reproduzir o teste

Requer acesso SSH ao aparelho sem senha (chave), `drmcap.py` em `/tmp` no aparelho e o `main.lua` em `/mnt/jogos/love-test/`. O script [`experimentos/love-gles/teste-love.sh`](../experimentos/love-gles/teste-love.sh) faz o ciclo completo: confere se não há jogo aberto, para o EmulationStation, roda o LÖVE, captura a tela e restaura o menu.

Nunca pare o EmulationStation com jogo aberto. O script confere antes.

## Ponte com o bug visual

O splash do PortMaster em LÖVE pisca com o menu porque os dois disputam o display. A solução adotada para os ports é a mesma do [doc 06](06-portmaster.md): rodar com o EmulationStation parado. Isso resolve a sobreposição, mas **não resolve** o erro de GL, então o splash continua sem janela.
