# 07 — EmulationStation e SDL

Dois problemas que parecem "o sistema quebrou" e na verdade são detalhes de biblioteca.

## Caso 1: SDL2 e o símbolo `udev` que não existe

### Sintoma

O EmulationStation para de subir:

```
ERROR  Error initializing SDL!
  Failed loading udev_device_get_action: /lib/aarch64-linux-gnu/libSDL2-2.0.so.0:
  undefined symbol: _udev_device_get_action
ERROR  Renderer failed to initialize!
ERROR  Window failed to initialize!
```

O serviço fica em `failed` e a tela volta para o console (ou fica preta).

### O que existe na imagem

O sistema traz **quatro** builds de SDL2 lado a lado:

| Arquivo | Tamanho | Comportamento |
|---|---|---|
| `libSDL2-2.0.so.0.10.0` | 940 KB | build de distro |
| `libSDL2-2.0.so.0.14.1` | 8,8 MB | build do ArkOS (compatível com udev daqui) |
| `libSDL2-2.0.so.0.16.0` | 1,3 MB | falha no udev |
| `libSDL2-2.0.so.0.18.2` | 2,3 MB | é o alvo normal do symlink; funciona com rotação correta |

O symlink manda:

```
/lib/aarch64-linux-gnu/libSDL2-2.0.so.0 -> /usr/lib/aarch64-linux-gnu/libSDL2.so
/usr/lib/aarch64-linux-gnu/libSDL2.so  -> libSDL2-2.0.so.0.18.2
```

### Diagnóstico rápido

```bash
python3 -c "
import ctypes
s = ctypes.CDLL('libSDL2-2.0.so.0')
print(s.SDL_Init(0x20), ctypes.string_at(s.SDL_GetError()))
"
```

- Retorno `0` → SDL sobe.
- Retorno `-1` com erro de udev → a build carregada não conversa com o `libudev` do sistema.

Teste versão por versão:

```bash
for v in 0.14.1 0.16.0 0.18.2; do
  python3 -c "
import ctypes
s=ctypes.CDLL('/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.$v')
print('$v', s.SDL_Init(0x20), ctypes.string_at(s.SDL_GetError())[:70])
"
done
```

Resultado observado aqui: `0.14.1` sobe; `0.16.0` e `0.18.2` falham com o erro de udev — mas de forma **intermitente** no caso do `0.18.2`, que é o que o aparelho usa normalmente.

### A armadilha da "solução"

Trocar o symlink para `0.14.1` faz o SDL subir... e a tela fica **girada 90°**, porque essa build não aplica a rotação que o painel exige.

Ou seja: a correção "óbvia" troca um problema por outro. O que resolveu de fato foi:

1. manter `0.18.2` (rotação correta);
2. reiniciar o serviço (`reset-failed` + `start`);
3. eliminar o processo concorrente que estava segurando o display (outro `pugwash` antigo). O erro de udev desapareceu junto.

Lição: antes de trocar biblioteca, verifique **quem mais está usando a tela**. Um processo órfão de outra sessão pode ser a causa real.

### Se precisar reverter

```bash
sudo cp -a /usr/lib/aarch64-linux-gnu/libSDL2.so /usr/lib/aarch64-linux-gnu/libSDL2.so.bak
sudo ln -sfn /usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.18.2 /usr/lib/aarch64-linux-gnu/libSDL2.so
sudo systemctl restart emulationstation
```

## Caso 2: `ParseGamelistsOnly` esconde tudo

O ArkOS permite ligar *Parse Gamelists Only* (Start → Advanced), que faz o EmulationStation ler **apenas** `gamelist.xml` em vez de varrer as pastas.

Efeito colateral: sistemas sem `gamelist.xml` aparecem com **0 jogos**, mesmo tendo arquivos. No menu Ports, isso deixou a lista vazia — "0 GAMES AVAILABLE".

Se você ligou essa opção e algo sumiu:

```bash
grep ParseGamelistsOnly /home/ark/.emulationstation/es_settings.cfg
```

Remova a linha (ou desligue no menu) e reinicie o EmulationStation. Alternativa: criar `gamelist.xml` para o sistema.

## Caso 3: tema apontando para pasta inexistente

`ThemeSet = pixel` sem `/etc/emulationstation/themes/pixel` faz o EmulationStation cair no tema padrão interno: fundo branco, texto azul, e **a seleção é só uma faixa preta** — praticamente invisível.

Verificar:

```bash
grep ThemeSet /home/ark/.emulationstation/es_settings.cfg
ls /etc/emulationstation/themes
```

`/etc/emulationstation/themes` é um symlink para `/roms/themes/`. Se a partição de ROMs estiver vazia ou corrompida, todos os temas somem junto.

Se a pasta não existe, instale um tema ou aponte para um que exista. O tema deste repositório está em [`themes/lain`](../themes/lain) e é descrito em [10 — Tema Lain](10-tema-lain.md).

## Ordem de diagnóstico que funciona

1. `systemctl status emulationstation` — está `failed`?
2. `journalctl -u emulationstation -n 40` — qual erro?
3. `ps -ef | grep -E "pugwash|love|btop"` — tem outro processo na tela?
4. Teste `SDL_Init` (acima) — a biblioteca sobe?
5. Só então mexa em symlink/tema.

Pular direto para o passo 5 é como trocar o motor porque o pneu furou.
