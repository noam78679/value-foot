#!/bin/bash
# Récupère les cotes Betclic (compare-bet.fr) et les stats (soccerstats.com), puis met les données dans analyse-paris.html
set -e
cd "$(dirname "$0")/.."
T=$(mktemp -d); UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36"
args=()
for p in "ligue1:Ligue 1" "premier-league:Premier League" "liga:Liga" "serie-a:Serie A" "bundesliga:Bundesliga" "champions-league:Ligue des champions"; do
  f=${p%%:*}; for i in 1 2 3 4; do curl -sL -A "$UA" "https://www.compare-bet.fr/cotes/$f.html" -o "$T/$f.html"; grep -q comparateur_H "$T/$f.html" && break; sleep 10; done
  grep -q comparateur_H "$T/$f.html" && args+=("$T/$f.html" "${p#*:}")
done
python3 -I outils/parse_cb.py "${args[@]}" > "$T/odds.json"
for l in france england spain italy germany; do curl -sfL -A "$UA" "https://www.soccerstats.com/homeaway.asp?league=$l" -o "$T/$l.html"; done
python3 -I outils/parse_ss.py "$T"/{france,england,spain,italy,germany}.html > "$T/stats.json"
python3 -I outils/build_data.py "$T/odds.json" "$T/stats.json" "$T/data.json"
python3 -I outils/inject.py "$T/data.json" analyse-paris.html
cp "$T/data.json" data.json
cp analyse-paris.html index.html
rm -rf "$T"
