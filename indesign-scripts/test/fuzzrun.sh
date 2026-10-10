#!/bin/bash
# Dayanıklılık testi: fuzz.py varyasyonlarını script'le çalıştırıp her biri için tek satır yazar.
# Kullanım: python3 -I indesign-scripts/test/fuzz.py <klasör> <model.json>...
#           indesign-scripts/test/fuzzrun.sh indesign-scripts/kitapcik-b-olusturucu.jsx <klasör>
#           (MODE=rnd SEED=5 gibi ortam değişkenleri idmlrun.js'e geçer)
S=$1; D=$2; H=$(dirname "$0")/idmlrun.js
for f in "$D"/*.json; do
  r=$(node "$H" "$S" "$f" --quiet 2>&1)
  n=$(echo "$r" | grep -o 'YER DEĞİŞTİREN SORU: [0-9]* / [0-9]*' | sed 's/YER DEĞİŞTİREN SORU: //')
  dn=$(echo "$r" | grep -o 'Denetim: [^(]*')
  same=$(echo "$r" | grep -o 'numarası aynı kalan [0-9]*' | grep -o '[0-9]*$')
  iss=$(echo "$r" | grep -E '✘|Error|HATA|TypeError' | head -4 | tr '\n' ' ')
  echo "$(basename "$f" .json) | $n | aynı:$same | $dn $iss"
done
