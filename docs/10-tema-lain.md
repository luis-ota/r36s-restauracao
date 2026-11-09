# 10 — Tema LAIN // nEther

Tema para EmulationStation em 640×480, no clima de *Serial Experiments Lain*: preto e grafite, vermelho-sangue, texto creme, grão e scanlines.

**Este repositório não distribui imagens da série.** O tema já vem com fundos abstratos gerados por código. Para usar frames ou arte próprios, gere os fundos com as suas imagens (abaixo).

## O que foi verificado

- O layout, a seleção vermelha e o rodapé foram conferidos com print real da tela no aparelho, em uma versão com imagens de fundo próprias.
- Os fundos abstratos deste repositório foram renderizados só no PC. O XML é o mesmo, mas essa combinação exata não foi vista no aparelho.
- A tela de sistemas usa carrossel, porque esta versão do EmulationStation não aceita `<textlist>` nela. Ali a seleção é negrito e escala, não barra vermelha.
- A view `detailed` existe, mas não foi validada na tela.

## Usar imagens próprias

```bash
uv run --with pillow themes/lain/tools/build_backgrounds.py \
  --list minha-imagem-1.jpg \
  --systems minha-imagem-2.jpg
```

O script recorta para 640×480, aplica a paleta, escurece a área do texto e grava em `themes/lain/art/`. Sem argumentos, ele refaz os fundos abstratos. Cada argumento é opcional.

## Instalar

No ArkOS, `/etc/emulationstation/themes` é um symlink para `/roms/themes/`. Instalar ali deixa o tema dependente da partição de ROMs, que é a parte mais fácil de perder. Prefira a partição do sistema:

```bash
scp -r themes/lain ark@IP-DO-APARELHO:/tmp/lain
ssh ark@IP-DO-APARELHO '
  mkdir -p ~/.emulationstation/themes
  rm -rf ~/.emulationstation/themes/lain
  mv /tmp/lain ~/.emulationstation/themes/lain
  rm -rf ~/.emulationstation/themes/lain/tools
  sudo ln -sfn /home/ark/.emulationstation/themes /etc/emulationstation/themes
  cp -n ~/.emulationstation/es_settings.cfg ~/.emulationstation/es_settings.cfg.bak-lain
  sed -i "s|<string name=\"ThemeSet\" value=\"[^\"]*\" />|<string name=\"ThemeSet\" value=\"lain\" />|" \
    ~/.emulationstation/es_settings.cfg
  sudo systemctl restart emulationstation
'
```

Trocar o symlink esconde qualquer outro tema que esteja em `/roms/themes`. Para voltar, restaure `es_settings.cfg.bak-lain` e reinicie o serviço.

## Estrutura

```
themes/lain/
├── theme.xml              # views system, basic e detailed
├── art/                   # fundos, wordmark, selo e fontes
├── tools/                 # gerador dos fundos (não precisa ir para o aparelho)
└── <sistema>/theme.xml    # 102 sistemas, todos incluem ../theme.xml
```

O sistema `ports` usa `<theme>ports</theme>` no `es_systems.cfg`, então a pasta `ports/` precisa existir.

## Requisitos que guiaram o tema

- Seleção óbvia: barra vermelha com texto preto na lista de jogos.
- Rodapé inteiro em 640×480, sem atalho cortado.
- Sem vídeo e com pouco peso: cerca de 1,5 MB.

## Créditos

Tema de fã, não comercial e não afiliado à produção. *Serial Experiments Lain* e seus personagens pertencem aos detentores dos direitos.

As fontes IBM Plex Mono são distribuídas sob a SIL Open Font License 1.1 (`art/OFL-IBM-Plex.txt`).

Para conferir o resultado, tire print real da tela: veja [08 — Captura de tela](08-captura-de-tela.md).
