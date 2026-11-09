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

## Ajustes aplicados depois (medidos no aparelho)

- `vm.swappiness=10`, `vm.dirty_writeback_centisecs=3000` e `dirty_ratio=15` em `/etc/sysctl.d/99-r36s.conf`: menos gravação no cartão, menos travadas e menos desgaste.
- `ModemManager` e `cups` desligados: nenhum uso neste aparelho.
- RetroArch: `menu_driver=rgui` (mais leve que o ozone), `audio_resampler_quality=0`, shaders e rewind desligados.
- Governadores no máximo no boot via `r36s-perf.service`.

## O que o EmulationStation custa

Medido com `/proc/<pid>/stat`: **cerca de 27% de um núcleo parado no menu** (~82 ticks a cada 3 s), com 99 MB residentes. O tema não muda isso: o tema padrão deu 80 ticks e o tema Lain 82.

Ou seja, o menu custa cerca de um quarto de um núcleo enquanto está aberto. **Durante o jogo, não custa nada:** o binário chama o emulador por `system()`, que bloqueia em `waitpid()` até o jogo terminar. Medição no menu: 571 ticks em 20 s (28,5% de um núcleo); com o jogo aberto, essa thread fica bloqueada.

Isso derruba a ideia de que o menu "rouba" CPU do emulador. Também derruba a ideia de reescrever o EmulationStation em Rust para ganhar FPS: o custo dele não está no caminho do jogo.

Conclusão honesta: o ganho de desempenho em jogos vem de governador, GPU no máximo, frameskip e menos serviços. Reescrever componentes em Rust não muda o teto dos emuladores neste hardware.

## Reescrita em Rust: o que a investigação mostrou

Um estudo separado (benchmarks em Rust, bash e Python, mais análise do binário) concluiu que **não há ganho de FPS** em reescrever componentes deste sistema em Rust:

- O gargalo é CPU/GPU do RK3326, e um quadro a 60 fps dura 16,7 ms. Nenhuma das economias medidas é por quadro: são por lançamento de jogo, a cada 30 s ou a cada 5 min.
- O EmulationStation fica **bloqueado** durante o jogo, então não disputa CPU.
- `btop` já é Rust. Os daemons do ArkOS dormem em `poll` e não estão no caminho do quadro.
- O único ruído periódico é o backup automático a cada 5 minutos, que mexe no cartão — e a solução é agendamento, não reescrita.

Resultado negativo, mas com prova: os números não sustentam a troca. Se um dia aparecer um front-end em Rust que aceite os temas e gamelists deste EmulationStation, a conversa muda.

## Autosave e o slot 9 do DraStic

O autosave espelha o último savestate bom no **slot 9**. Assim, para recuperar, basta abrir o menu do DraStic e escolher **Load state → slot 9**, sem mexer em arquivos.

- O slot 9 é reservado para isso: não use para savestate manual.
- Atualiza a cada 2 minutos (só quando o state muda) e ao fechar o jogo.
- Continua existindo o histórico numerado em `/home/ark/pokemon-backups`, com o atalho **Ports → Restaurar backup do Pokemon** para versões mais antigas.

### Slots do DraStic neste aparelho

- **Slot 1** — slot ativo (L1 carrega, R1 salva). O launcher grava `savestate_number = 1` no `drastic.cfg` antes de abrir o jogo, porque o DraStic regrava a configuração ao sair.
- **Slot 0** — reservado para save manual antes de algo arriscado.
- **Slot 9** — espelho automático do backup mais recente, para recuperar pelo menu (Load state → 9).

O autosave escolhe o backup mais novo entre todos os slots e copia para o 9, então funciona venha o save do slot 0 ou do 1.
