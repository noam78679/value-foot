#!/bin/bash
# Récupère les matchs, résultats (avec xG) et cotes du marché de ~36 championnats (football-data.co.uk),
# les cotes Betclic (compare-bet.fr), les buteurs (soccerstats.com) et l'actu (Google Actualités),
# puis écrit data.json et met les données dans la page.
set -e
cd "$(dirname "$0")/.."
T=$(mktemp -d); UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36"
get(){ for i in 1 2 3 4; do curl -sL -A "$UA" "$1" -o "$2" 2>/dev/null; grep -q "$3" "$2" 2>/dev/null && return 0; sleep 4; done; return 1; }
mkdir -p "$T/fd/res"
FDU=https://www.football-data.co.uk
get "$FDU/fixtures.csv" "$T/fd/fixtures.csv" HomeTeam || { echo "matchs à venir indisponibles"; exit 1; }
get "$FDU/new_league_fixtures.csv" "$T/fd/new_league_fixtures.csv" Country || echo "Country" > "$T/fd/new_league_fixtures.csv"
for d in F1 F2 E0 SP1 I1 D1 E1 E2 E3 D2 I2 SP2 N1 B1 P1 T1 G1 SC0 SC1 SC2 SC3; do
  get "$FDU/mmz4281/2627/$d.csv" "$T/fd/res/$d.csv" FTHG || { rm -f "$T/fd/res/$d.csv"; echo "résultats indisponibles : $d"; }
done
for c in ARG AUT BRA CHN DNK FIN IRL JPN MEX NOR POL ROU SWZ SWE USA; do
  get "$FDU/new/$c.csv" "$T/fd/res/new-$c.csv" Country || { rm -f "$T/fd/res/new-$c.csv"; echo "résultats indisponibles : $c"; }
done
args=()
for p in "ligue1:Ligue 1" "ligue2:Ligue 2" "premier-league:Premier League" "liga:Liga" "serie-a:Serie A" "bundesliga:Bundesliga" "champions-league:Ligue des champions"; do
  f=${p%%:*}; get "https://www.compare-bet.fr/cotes/$f.html" "$T/$f.html" comparateur_H && args+=("$T/$f.html" "${p#*:}") || echo "cotes Betclic indisponibles : $f"
done
python3 -I outils/parse_cb.py "${args[@]}" > "$T/betclic.json"
sc=()
for l in france france2 england spain italy germany england2 germany2 italy2 spain2 netherlands portugal belgium turkey greece scotland; do
  get "https://www.soccerstats.com/scorers.asp?league=$l" "$T/sc-$l.html" 'player.asp' && sc+=("$T/sc-$l.html") || echo "buteurs indisponibles : $l"
done
python3 -I outils/parse_sc.py "${sc[@]}" > "$T/scorers.json"
rs=()
for l in france france2 england spain italy germany; do
  get "https://www.soccerstats.com/results.asp?league=$l&pmtype=bydate" "$T/res-$l.html" '<tr' && rs+=("$T/res-$l.html") || echo "résultats récents indisponibles : $l"
done
python3 -I outils/parse_res.py "${rs[@]}" > "$T/ssres.json"
python3 -I outils/build_data.py "$T/fd" "$T/betclic.json" "$T/scorers.json" data.json "$T/data.json" "$T/ssres.json"
python3 -I outils/news.py "$T/data.json" data.json
python3 -I outils/inject.py "$T/data.json" analyse-paris.html
cp "$T/data.json" data.json
cp analyse-paris.html index.html
rm -rf "$T"
