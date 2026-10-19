#!/bin/bash
# Récupère les cotes Betclic (compare-bet.fr), les stats et résultats (soccerstats.com),
# puis écrit data.json et met les données dans la page.
set -e
cd "$(dirname "$0")/.."
T=$(mktemp -d); UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36"
get(){ for i in 1 2 3 4; do curl -sL -A "$UA" "$1" -o "$2"; grep -q "$3" "$2" && return 0; sleep 8; done; return 1; }
args=()
for p in "ligue1:Ligue 1" "ligue2:Ligue 2" "premier-league:Premier League" "liga:Liga" "serie-a:Serie A" "bundesliga:Bundesliga" "champions-league:Ligue des champions"; do
  f=${p%%:*}; get "https://www.compare-bet.fr/cotes/$f.html" "$T/$f.html" comparateur_H && args+=("$T/$f.html" "${p#*:}") || echo "cotes indisponibles : $f"
done
python3 -I outils/parse_cb.py "${args[@]}" > "$T/odds.json"
ha=(); rs=()
for l in france france2 england spain italy germany; do
  get "https://www.soccerstats.com/homeaway.asp?league=$l" "$T/$l.html" '>PPG<' && ha+=("$T/$l.html") || echo "stats indisponibles : $l"
  get "https://www.soccerstats.com/results.asp?league=$l&pmtype=bydate" "$T/res-$l.html" '<tr' && rs+=("$T/res-$l.html") || echo "résultats indisponibles : $l"
done
python3 -I outils/parse_ss.py "${ha[@]}" > "$T/stats.json"
python3 -I outils/parse_res.py "${rs[@]}" > "$T/results.json"
python3 -I outils/build_data.py "$T/odds.json" "$T/stats.json" "$T/results.json" data.json "$T/data.json"
python3 -I outils/inject.py "$T/data.json" analyse-paris.html
cp "$T/data.json" data.json
cp analyse-paris.html index.html
rm -rf "$T"
