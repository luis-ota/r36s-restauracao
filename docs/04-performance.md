# 04 — Performance

Resumo do que foi aplicado, do que foi descartado e por quê. A regra: **nada que possa apagar a tela ou corromper o cartão entra**. Ganho de FPS não paga um aparelho brickado.

## O que foi aplicado

### 1. Impedir que o EmulationStation derrube o governor

O ArkOS chama `perfmax` antes de cada jogo e `perfnorm` depois. A implementação original **redefine o governor** com base no que o menu manda — ou seja, todo travamento manual em `performance` é desfeito no primeiro jogo.

Solução: substituir `perfmax` e `perfnorm` por versões que apenas reaplicam o perfil de máximo, sem escolher governor por conta própria. Scripts em [`scripts/perfmax`](../scripts/perfmax) e [`scripts/perfnorm`](../scripts/perfnorm).

Resultado: CPU fica em 1.296 MHz durante o jogo e continua depois, em vez de voltar para `ondemand`.

### 2. Drastic (NDS)

No `drastic.cfg`:

```
frameskip_type = 2
frameskip_value = 2
safe_frameskip = 1
threaded_3d = 1
hires_3d = 0
```

`threaded_3d` e `hires_3d` já eram o padrão correto. O que muda é o frameskip automático com proteção: evita queda quando a cena 3D aperta, ao custo de imagem mais "picotada". Não sobe o teto — gerencia a queda.

### 3. RetroArch (quando presente)

```
audio_resampler_quality = "0"
rewind_enable = "false"
run_ahead_enabled = "false"
video_shader_enable = "false"
video_smooth = "false"
video_scale_integer = "true"
savestate_thumbnail_enable = "false"
```

Nenhum desses muda a imagem de forma perceptível. Todos removem trabalho que este chip não tem de sobra.

### 4. Serviços que só atrasam o boot

Desativados: `apt-daily.timer`, `apt-daily-upgrade.timer`, `NetworkManager-wait-online.service`.

Nunca desative: `rk817-calibrationd`, `351mp.service`, `batteryplus`, `mali-select`.

## O que NÃO foi aplicado (e por quê)

| Ideia | Por que ficou de fora |
|---|---|
| Subir CPU acima de 1.296 MHz por sysfs | O kernel deste ArkOS não tem OPP acima disso. `scaling_max_freq` engana; não há frequência real disponível. |
| `echo 1 > .../cpufreq/boost` | Só existe em kernels BSP com OPP turbo. Aqui o arquivo normalmente não existe. |
| Ajustar DMC/RAM | O nó `dmc/devfreq` não existe neste aparelho. O `perfmax` tenta e falha em silêncio. |
| Undervolt em runtime | O framework de OPP reverte na primeira transição. Só funcionaria com patch de DTB. |
| zram / swap | Emulação aqui é limitada por CPU. Comprimir memória disputa exatamente os ciclos que faltam. O mantenedor do ArkOS diz que nenhum emulador suportado se beneficia de mais de 1 GB. |
| Panfrost | Não há caminho Panfrost nesta imagem/kernel; o blob proprietário é o usado. |
| Trocar DTB para 60 Hz | Risco alto de tela preta. Não aumenta FPS. Ver [01](01-hardware-e-diagnostico.md). |
| Overclock por kernel alternativo | Exige kernel `Image.oc` + DTB + resfriamento; neste aparelho, com cartão não confiável, é convite a brick. |

## Sobre "ganho de FPS"

Nenhuma fonte pública mede FPS de jogo (Drastic, GBA, SNES, N64) neste aparelho. Os números que existem são de benchmark sintético (glmark2, memset) e não se traduzem em FPS. Trate qualquer promessa de "10–30% mais FPS" como não verificada.

O que se pode afirmar com os testes feitos aqui:

- O governor importa: sem `performance`, a frequência oscila e o jogo engasga.
- O frameskip do Drastic importa nas cenas 3D: sem ele, a queda é maior.
- O resto é ajuste fino de boot, memória e ruído — não de teto de desempenho.

## Medindo de verdade

```bash
# frequência atual (repita durante o jogo)
watch -n 0.5 cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq

# governor
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor

# GPU
cat /sys/devices/platform/ff400000.gpu/devfreq/ff400000.gpu/governor

# temperatura
cat /sys/class/thermal/thermal_zone0/temp
```

Se `scaling_cur_freq` oscilar durante o jogo, o `perfmax`/`perfnorm` ainda está derrubando o perfil — volte ao item 1.
