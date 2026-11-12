# 17 — Música de fundo no menu

O EmulationStation deste ArkOS toca uma música de fundo enquanto o menu está na tela. Este documento registra como a faixa foi feita, onde ela fica, o que já foi medido, o que ainda depende de você ouvir e olhar a tela, e como remover.

## Estado atual

| Item | Situação |
|---|---|
| Faixa instalada (`/roms/bgmusic/lain_menu_chill.ogg`) | Feito. md5 `25b0ac04…`, 684.715 bytes, igual ao gerado no PC |
| Nível de volume da faixa | Medido: RMS -18,6 dBFS, pico -6,9 dBFS |
| Música no slideshow e desligar no descanso | Medido com um ciclo de tempos reduzidos (ver [12](12-descanso-e-bateria.md)) |
| Pop-up com o nome da faixa | **Ainda aparece.** Ver [o pop-up](#o-pop-up-com-o-nome-da-faixa) |
| Música recomeçando ao entrar numa pasta | Configurado (`audio.persystem=false`), **não verificado** |
| Piano ainda alto? | Reduzido, **você precisa ouvir** para confirmar |

## Onde fica e como o ES encontra

- A pasta de música de fundo é `/roms/bgmusic/` (o atalho `/home/ark/.emulationstation/music` aponta para ela).
- O arquivo instalado é `/roms/bgmusic/lain_menu_chill.ogg`.
- Os arquivos `*.ogg.old` ficam na mesma pasta como backup. O ES os ignora.
- Durante o slideshow, a faixa **não** vem dessa pasta: o daemon toca o PCM bruto em `/home/ark/.r36s-idle/musica/lain_menu_chill.raw`, fora de `/roms/bgmusic`, para o ES não listar.

## Formato

| Campo | Valor |
|---|---|
| Arquivo | `lain_menu_chill.ogg` |
| Tamanho | 684.715 bytes |
| md5 (12 primeiros caracteres) | `25b0ac041873` |
| Codec | Ogg Vorbis, mono, 44,1 kHz |
| Duração | 106,67 s |
| Loop | a síntese dá a volta no fim, sem salto na emenda |

PCM bruto usado pelo slideshow: `s16le`, mono, 44,1 kHz, 9.408.000 bytes. Foi gerado a partir do WAV da mesma síntese. O RMS dele (-18,6 dBFS) bate com o do OGG decodificado (-18,61 dBFS).

## Como foi feita

A música é **gerada por código**, sem nenhum arquivo de áudio ou MIDI de terceiros. O script está em [`experimentos/musica-menu/synth.py`](../experimentos/musica-menu/synth.py).

- **Andamento:** 72 BPM, 32 compassos em 4/4 (cerca de 106,7 s).
- **Harmonia:** oito acordes de sétima em tom maior com uma cor de menor (Fmaj7, Dm7, Bbmaj7, Am7, Gm7, C7sus4, Fmaj7, Cadd9).
- **Camadas:**
  - *pad*: dois osciladores quase afinados (senoide + triângulo), com ataque de 0,9 s e release de 1,6 s;
  - *baixo*: triângulo em colcheias sobre a raiz de cada acorde;
  - *bells*: plinks de caixinha de música, com parciais que decaem depressa (senoide com 2× e 3,01× da frequência), e pizzicatos curtos em triângulo. **Esta é a camada que soa como piano.** Ver o histórico;
  - *melodia*: uma frase de 32 tempos, com vibrato suave de 5 Hz, tocada quatro vezes com variações.
- **Ruído:** existe um gerador de ruído rosa no script (`rain`), mas **não entra na mistura**.
- **Loop:** cada camada é somada com `% N`, então o que passa do fim volta para o começo. Isso dá a emenda sem crossfade.
- **Mistura atual:** pad ×1,0, baixo ×0,9, **bells ×0,15**, melodia ×0,85. Normalizada para o RMS alvo e limitada por uma curva suave perto do teto.

O encode para OGG foi feito com ffmpeg no PC. O comando exato não ficou registrado no repositório; o resultado é Vorbis mono, ~52 kbps.

## Histórico

1. **8 bits agitado:** arpejos de onda quadrada a ~120 BPM. O usuário não gostou. Guardado como `lain_menu_8bit.ogg.old`.
2. **Chill, primeira versão:** `lain_menu_chill_prev-20261111-2251.ogg.old`.
3. **Chill, segunda versão** (`…v2-20261111-2310.ogg.old`): a camada de caixinha de música foi reduzida cerca de 4 dB, porque ainda soava como piano.
4. **Chill, terceira versão** (`…v3-20261111-2311.ogg.old`, bells ×0,45): o usuário disse que o piano ainda estava muito alto.
5. **Versão atual** (bells ×0,15, cerca de -9,5 dB em relação à v3). Medição antes do peso da mistura: a média dos plinks não é maior que a do pad ou da melodia. O que faz soar como piano é o **ataque curto**, com crista de 16,6 dB. Se ainda parecer piano, o próximo suspeito é o baixo com notas curtas na oitava de cima, que tem timbre de pizzicato e não foi mexido.

## O pop-up com o nome da faixa

Quando a faixa começa, o ES mostra uma pílula branca no topo da tela com o nome da música (`lain_menu_chill`), por cerca de 7 segundos.

Prova em gravação do menu com o ES reiniciado (quadros capturados a cada ~0,6 s):

- [quadro com o pop-up](img/menu-popup-musica.png) (quadro 08 da gravação);
- [recorte do pop-up](img/menu-popup-recorte.png);
- [vídeo da gravação](img/gravacao-popup-musica.mp4).

Nos quadros, só a região do pop-up (x 254–385, y 10–47) muda; o resto da tela não muda. Ele fica visível do quadro 08 ao 19 (12 quadros) e some nos quadros 20–21.

**O que foi tentado:**

- `audio.display_titles_time` em `0` no `es_settings.cfg`. **Não funcionou**: o pop-up apareceu com o ES reiniciado depois da mudança. O valor `0` não desliga.
- A opção de interface "DISPLAY SONG TITLES" existe neste ES (está nas strings do binário). O valor que ela grava para "desligado" ainda não foi lido. **Próximo passo:** desligar essa opção na tela do ES (Sound Settings / Frontend Music) e ler `audio.display_titles_time` no `es_settings.cfg`.

## Música recomeçando ao entrar numa pasta

O ES monta uma playlist por sistema quando você entra numa pasta (`audio.persystem`). Como `/roms/bgmusic` não tem subpastas, a playlist cai no mesmo arquivo e recomeça do zero.

- Configurado: `audio.persystem` = `false` (backup em `/home/ark/.emulationstation/es_settings.cfg.bak-musica-20261111`).
- **Não verificado:** só dá para confirmar navegando no menu de verdade. Vale a partir do próximo início do ES.

## Música no slideshow

Ver [12 — Música no slideshow](12-descanso-e-bateria.md#música-no-slideshow). Resumo: a faixa toca em loop com `aplay` enquanto o slideshow está na tela, com volume acompanhando o brilho (piso de 20% do uso). No descanso profundo, ela para.

## Como trocar ou remover

Remover a música:

```bash
sudo rm /roms/bgmusic/lain_menu_chill.ogg
```

Voltar para uma versão anterior: renomeie o `.old` correspondente para `.ogg`, depois apague o atual.

Gerar outra versão: rode o `synth.py` no PC com `uv run --with numpy synth.py`, ajuste o caminho de saída (`OUT`) e faça o encode para OGG com ffmpeg. Copie para `/roms/bgmusic/`, confira o md5, e gere o PCM do slideshow com `ffmpeg -i faixa.ogg -f s16le -ac 1 -ar 44100 lain_menu_chill.raw`.

## O que falta confirmar (depende de você)

1. **Piano:** ouvir a faixa no menu e dizer se ainda está alto.
2. **Pop-up:** desligar "DISPLAY SONG TITLES" na tela do ES. Depois eu leio o valor gravado e confirmo pela gravação que o pop-up sumiu.
3. **Pasta:** entrar numa pasta de sistema e confirmar que a música não recomeça.
4. **Screensaver:** deixar o aparelho parar. A música deve tocar baixa no slideshow e desligar no descanso profundo. O ciclo rápido já foi medido, mas o tempo real (30 min até o descanso) não.
