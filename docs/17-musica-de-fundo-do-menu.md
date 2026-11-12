# 17 — Música de fundo no menu

O EmulationStation deste ArkOS toca uma música de fundo enquanto o menu está na tela. Este documento registra como a faixa foi feita, onde ela fica, como remover e o que ainda não foi verificado.

**Status:** o arquivo está instalado no aparelho, com o md5 conferido. **Ainda não foi ouvido no aparelho** e o ALSA ainda não foi checado com o menu aberto, porque o aparelho estava no slideshow do descanso. Ver [o que falta verificar](#o-que-falta-verificar).

## Onde fica e como o ES encontra

- A pasta de música de fundo é `/roms/bgmusic/` (o atalho `/home/ark/.emulationstation/music` aponta para ela).
- O arquivo instalado é `/roms/bgmusic/lain_menu_chill.ogg`.
- O ES toca os arquivos dessa pasta. Os arquivos `*.ogg.old` ficam ali como backup e o ES os ignora.

## Formato

| Campo | Valor |
|---|---|
| Arquivo | `lain_menu_chill.ogg` |
| Tamanho | 691.245 bytes |
| md5 (12 primeiros caracteres) | `c7924fe6764e` |
| Codec | Ogg Vorbis, mono, 44,1 kHz |
| Bitrate | ~52 kbps |
| Duração | 106,67 s |
| Loop | a síntese dá a volta no fim (ver abaixo), sem salto na emenda |

Níveis, medidos pelo script de síntese antes do encode: RMS **-18,6 dBFS**, pico no teto de **-6,5 dBFS**, com compressão suave acima de -9 dBFS. O agente que instalou relatou pico de -6,7 dBFS no OGG final.

## Como foi feita

A música é **gerada por código**, sem nenhum arquivo de áudio ou MIDI de terceiros. O script está em [`experimentos/musica-menu/synth.py`](../experimentos/musica-menu/synth.py).

- **Andamento:** 72 BPM, 32 compassos em 4/4 (cerca de 106,7 s).
- **Harmonia:** oito acordes de sétima em tom maior com uma cor de menor (Fmaj7, Dm7, Bbmaj7, Am7, Gm7, C7sus4, Fmaj7, Cadd9).
- **Camadas:**
  - *pad*: dois osciladores quase afinados (senoide + triângulo), com ataque de 0,9 s e release de 1,6 s;
  - *baixo*: triângulo em um padrão de colcheias sobre a raiz de cada acorde;
  - *bells*: plinks de caixinha de música, com parciais que decaem depressa (senoide com 2× e 3,01× da frequência), e pizzicatos curtos em triângulo;
  - *melodia*: uma frase de 32 tempos, com vibrato suave de 5 Hz, tocada quatro vezes com variações.
- **Ruído:** um gerador de ruído rosa existe no script (`rain`), mas **não entra na mistura final**.
- **Loop:** cada camada é somada com `% N`, então o que passa do fim volta para o começo. Isso dá a emenda sem crossfade; o script imprime a diferença entre a primeira e a última amostra para conferir.
- **Mistura:** pad ×1,0, baixo ×0,9, bells ×0,45, melodia ×0,85, normalizada para o RMS alvo e limitada por uma curva suave perto do teto.

O WAV de saída é mono, 16 bits, 44.100 Hz. O encode para OGG foi feito com ffmpeg no PC; **o comando exato não ficou registrado no repositório**, só o resultado (Vorbis, mono, ~52 kbps).

## Histórico

1. **8 bits agitado:** arpejos de onda quadrada a ~120 BPM. O usuário não gostou. O arquivo foi guardado como `lain_menu_8bit.ogg.old`.
2. **Chill, primeira versão:** `lain_menu_chill_prev-20261111-2251.ogg.old`.
3. **Chill, segunda versão:** `lain_menu_chill_v2-20261111-2310.ogg.old`. O agente reduziu a camada de caixinha de música (*bells*) cerca de 4 dB, porque ela tinha o timbre mais parecido com piano. Baixo, pad e melodia ficaram iguais.
4. **Versão atual:** a que está instalada, gerada pelo `synth.py` acima.

As versões antigas ficam na mesma pasta com o sufixo `.old` e podem ser apagadas.

## Como trocar ou remover

Remover a música: apague o arquivo da pasta, sem reiniciar nada.

```bash
sudo rm /roms/bgmusic/lain_menu_chill.ogg
```

Voltar para uma versão anterior: renomeie o `.old` correspondente para `.ogg`, depois apague o atual.

Gerar outra versão: rode o `synth.py` no PC com `uv run --with numpy synth.py`, ajuste o caminho de saída (`OUT`) e faça o encode para OGG com ffmpeg. Copie o resultado para `/roms/bgmusic/` e confira o md5.

## Ajuste de volume

O canal `Playback` do sistema estava em 85% (cerca de -20 dB), segundo o agente. Se o conjunto ainda estiver alto, dá para baixar isso no sistema (`amixer`) sem mexer no arquivo. O volume medido no arquivo não é o volume que sai do alto-falante.

## O que falta verificar

1. **Ouvir no aparelho.** Acordar o aparelho e ouvir a faixa no menu. Esta é a verificação que importa e ainda não foi feita por ninguém.
2. **Prova pelo ALSA.** Com o menu na tela: `cat /proc/asound/card*/pcm*/sub*/status` deve mostrar `state: RUNNING`. Ainda não foi confirmado com a faixa nova.
3. **Reinício do ES.** O ES estava rodando com a versão anterior. A faixa nova vale na próxima vez que o ES iniciar ou trocar de faixa.

Não ouvi a faixa e não rodei o teste do ALSA. Os itens acima ficam em aberto até alguém confirmar.
