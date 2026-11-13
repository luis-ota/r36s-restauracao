# 08 — Captura de tela sem X11

Precisávamos ver o que estava na tela para diagnosticar temas e sobreposição. O aparelho não tem X11, não tem compositor, e `/dev/fb0` **não mostra o que o EmulationStation desenha**.

## Por que `/dev/fb0` não serve

Ler `/dev/fb0` devolveu 640×480 de branco, mesmo com o menu visível na tela. Motivo: o console (fbcon) e o EmulationStation usam caminhos diferentes. O EmulationStation pega o display via **DRM/KMS** e desenha no framebuffer do CRTC; o `/dev/fb0` é a emulação de framebuffer do console.

Consequência prática: `ffmpeg -f fbdev`, `dd if=/dev/fb0` e similares capturam o console — não o jogo nem o menu.

## A solução: ler o framebuffer do CRTC via DRM

A receita:

1. Abrir `/dev/dri/card0`.
2. `DRM_IOCTL_MODE_GETRESOURCES` → lista de CRTCs.
3. `DRM_IOCTL_MODE_GETCRTC` → qual framebuffer (`fb_id`) está ativo.
4. `DRM_IOCTL_MODE_GETFB` → largura, altura, pitch, bpp, handle.
5. `DRM_IOCTL_MODE_MAP_DUMB` → offset para mapear a memória.
6. `mmap` e ler `pitch * height` bytes.
7. Converter de `BGRA` (little-endian, XRGB8888) para PNG.

Tudo com `ctypes`, sem instalar nada. Script completo: [`scripts/drmcap.py`](../scripts/drmcap.py).

### Instale de forma permanente (não em `/tmp`)

`/tmp` some no reboot, e uma captura que falha em silêncio já nos fez concluir
coisa errada (ver [16](16-love-e-gles.md)). Instale os dois arquivos no rootfs:

```bash
sudo install -m 755 scripts/drmcap.py /usr/local/bin/drmcap.py
sudo install -m 755 scripts/drmcap /usr/local/bin/drmcap
```

O `/usr/local/bin/drmcap` roda o `.py`, confere que o arquivo saiu com
1.228.800 bytes (640×480×4) e só então move para o destino. Se a captura
falhar, ele sai com erro e uma mensagem — não deixa ninguém achando que gravou.

```bash
sudo drmcap /tmp/shot.raw
# drmcap: ok /tmp/shot.raw (1228800 bytes)

ffmpeg -y -v error -f rawvideo -pix_fmt bgra -s 640x480 -i shot.raw shot.png
```

O `/tmp/shot.txt` (largura, altura, pitch e bpp) continua sendo gerado.

### Detalhes que dão erro

- **Structs**: `drm_mode_crtc` tem 100 bytes, `drm_mode_card_res` 64, `drm_mode_fb_cmd` 28, `drm_mode_map_dumb` 16. Se o tamanho do `ioctl` não bater, vem `EINVAL`.
- **`GETRESOURCES` duas vezes**: a primeira chamada devolve as contagens; a segunda, preenchida com buffers válidos, devolve os IDs. Se você passar ponteiro nulo com contagem > 0, vem `EFAULT` ("Bad address").
- **Precisa de root** (ou grupo `video`) para abrir `/dev/dri/card0`.
- **Formato**: neste aparelho, `XRGB8888` little-endian → `bgra` no ffmpeg.

## Alternativa: teclado virtual via `uinput`

Tentamos também injetar `F12` (atalho de screenshot do EmulationStation em algumas builds) criando um teclado virtual:

```python
# /dev/uinput, UI_SET_EVBIT, UI_SET_KEYBIT, UI_DEV_CREATE
# struct uinput_user_dev (legado, 1116 bytes)
```

O dispositivo foi criado e a tecla enviada — mas o EmulationStation deste build **não tem** captura por F12 (`strings` mostra `SCREENSHOT` como nome de input, não atalho global). Script em [`scripts/uinput-f12.py`](../scripts/uinput-f12.py).

Curiosidade útil: no kernel 4.4 deste aparelho, `UI_DEV_SETUP` falha com `EINVAL`; é preciso usar a struct legada `uinput_user_dev`.

## Quando usar isso

- Verificar um tema sem pedir foto para outra pessoa.
- Confirmar que a GUI de um port abriu de verdade.
- Diagnosticar sobreposição de dois programas na mesma tela.
- Registrar antes/depois de um ajuste visual.

## Limitação

A captura pega o framebuffer do CRTC, então mostra o que está **sendo escaneado** naquele instante. Se o app troca de buffer no meio, você pode pegar um quadro parcial. Para um print de diagnóstico, basta repetir.
