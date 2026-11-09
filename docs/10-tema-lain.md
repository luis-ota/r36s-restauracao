# 10 — Tema Lain

O aparelho vinha sem nenhum tema instalado: o EmulationStation caía no tema interno (fundo branco, texto azul, seleção praticamente invisível). Este repositório inclui um tema próprio, no clima de *Serial Experiments Lain*.

## Instalar

```bash
sudo cp -r themes/lain /etc/emulationstation/themes/lain
```

Ative no EmulationStation: **Start → UI Settings → Theme Set → Lain**.

Ou por arquivo:

```bash
sudo cp /home/ark/.emulationstation/es_settings.cfg /home/ark/.emulationstation/es_settings.cfg.bak
# troque o valor de ThemeSet
sed -i 's|<string name="ThemeSet" value="[^"]*" />|<string name="ThemeSet" value="lain" />|' \
  /home/ark/.emulationstation/es_settings.cfg
sudo systemctl restart emulationstation
```

## Estrutura

```
themes/lain/
├── theme.xml          # formato v3 do EmulationStation
├── art/               # fundos e elementos
└── <sistema>/theme.xml  # views específicas, quando necessário
```

O sistema `ports` merece atenção: o `es_systems.cfg` aponta `<theme>ports</theme>`, então uma view `ports` precisa existir (ou a view padrão precisa funcionar para ele), senão PortMaster e btop ficam ilegíveis.

## Requisitos que o tema cumpre

- **640×480**. Nada de layout pensado para 1080p.
- **Seleção óbvia**: alto contraste entre item selecionado e não selecionado. O tema padrão falhava nisso.
- **Rodapé inteiro**: os atalhos (OPTIONS, MENU, FAVORITE, RANDOM, BACK, LAUNCH) não podem ser cortados nas laterais.
- **Sem vídeos**: só imagens estáticas, para não gastar CPU/RAM do aparelho.
- **Tamanho pequeno**: a partição do sistema tem pouco espaço livre.

## Créditos e uso

Fan art não comercial inspirada em *Serial Experiments Lain*. A obra original e seus personagens pertencem aos detentores dos direitos. Este tema é para uso pessoal, sem fins comerciais, e não é afiliado à produção.

Se você for redistribuir, mantenha os créditos e não cobre por ele.

## Como conferir o resultado

Não confie no "parece que está bom" olhando o XML. Tire print real da tela — veja [08 — Captura de tela](08-captura-de-tela.md) — e olhe: lista de sistemas, lista de jogos com dois itens, item selecionado e rodapé.
