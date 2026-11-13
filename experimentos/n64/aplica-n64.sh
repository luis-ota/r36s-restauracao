#!/bin/bash
# Aplica a configuração de N64 medida no aparelho:
# - Glide64mk2 sem vsync e com filtros leves (foi o que ficou em ~100% no OoT)
# - Rice em resolução nativa do N64, caso o usuário escolha Rice
# - entrada do Ocarina no gamelist, apontando para o Glide
set -e
CFG=/home/ark/.config/mupen64plus/mupen64plus.cfg
GL=/mnt/jogos/n64/gamelist.xml
ROM="./Legend of Zelda, The - Ocarina of Time (USA) (Rev 2).z64"

cp "$CFG" "/tmp/mupen64plus.cfg.antes-$(date +%s)"
cp "$GL" "/tmp/gamelist.antes-$(date +%s)"

# Glide
sed -i 's/^vsync = True/vsync = False/' "$CFG"
sed -i 's/^show_fps = .*/show_fps = 0/' "$CFG"
sed -i 's/^wrpResolution = .*/wrpResolution = 0/' "$CFG"
sed -i 's/^ghq_fltr = .*/ghq_fltr = 1/' "$CFG"
sed -i 's/^ghq_enht = .*/ghq_enht = 0/' "$CFG"
sed -i 's/^ghq_hirs = .*/ghq_hirs = 0/' "$CFG"
sed -i 's/^ghq_cmpr = .*/ghq_cmpr = 0/' "$CFG"
sed -i 's/^wrpAntiAliasing = .*/wrpAntiAliasing = 0/' "$CFG"

# Rice (alternativa)
sed -i 's/^InN64Resolution = .*/InN64Resolution = True/' "$CFG"
sed -i 's/^TextureEnhancement = .*/TextureEnhancement = 0/' "$CFG"
sed -i 's/^ForceTextureFilter = .*/ForceTextureFilter = 0/' "$CFG"
sed -i 's/^Mipmapping = .*/Mipmapping = 0/' "$CFG"
sed -i 's/^AnisotropicFiltering = .*/AnisotropicFiltering = 0/' "$CFG"

# Gamelist: adiciona o Ocarina com o Glide, sem duplicar
python3 - "$GL" "$ROM" <<'PY'
import sys, xml.etree.ElementTree as ET
caminho, rom = sys.argv[1], sys.argv[2]
arvore = ET.parse(caminho)
raiz = arvore.getroot()
for g in raiz.findall("game"):
    p = g.findtext("path")
    if p == rom:
        print("ja existia")
        break
else:
    g = ET.SubElement(raiz, "game")
    ET.SubElement(g, "path").text = rom
    ET.SubElement(g, "name").text = "The Legend of Zelda: Ocarina of Time"
    ET.SubElement(g, "emulator").text = "standalone-Glide64mk2"
    arvore.write(caminho, encoding="UTF-8", xml_declaration=True)
    print("entrada criada")
PY

chown ark:ark "$GL"
python3 -c "import xml.etree.ElementTree as ET; ET.parse('$GL'); print('gamelist ok')"

systemctl restart emulationstation
sleep 5
echo "es=$(systemctl is-active emulationstation)"
grep -E "^(vsync|show_fps|wrpResolution|ghq_fltr|ghq_hirs) =" "$CFG"
grep -E "^(InN64Resolution|TextureEnhancement|Mipmapping) =" "$CFG"
