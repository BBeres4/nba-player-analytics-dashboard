# 🏀 NBA Player Analytics (Streamlit)

A Streamlit dashboard for exploring NBA player performance: custom rankings,
player "archetypes" via clustering, head-to-head comparisons, and simple
statistical patterns — built with Python, pandas, scikit-learn, and Altair.

---

## Project structure

```
app.py                    # entry point — sidebar, header, tabs
src/
  config.py                # paths, feature lists, brand color palette
  data.py                   # load / clean / cache / filter player data
  theme.py                  # CSS injection + small UI helpers (cards, eyebrow text)
  charts.py                 # reusable Altair chart builders
  archetypes.py             # KMeans clustering + role labeling (cached)
  scoring.py                # user-weighted custom ranking
  views.py                  # one render_*() function per tab
.streamlit/config.toml     # dark theme matching the portfolio's ink/gold/teal palette
data/
  player_stats.csv          # raw per-game player stats by season
  nba_stats.sqlite          # generated cache (built automatically on first run)
scripts/
  fetch_nba_data.py         # pulls fresh data from the NBA stats API
```

Splitting the app this way means each tab's logic is testable and readable
on its own, chart styling stays consistent everywhere it's used, and the
expensive clustering step is cached instead of recomputing on every sidebar
interaction.

---

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

If `data/player_stats.csv` is missing, fetch fresh data first:

```bash
python scripts/fetch_nba_data.py
```

---

## What this app does

- Who are the top performers, by a demo "overall impact" score?
- How efficient is a player at scoring?
- Which players are similar "types" (creators, playmakers, finishers)?
- How do any two players stack up against each other?
- If you change what you care about (impact vs. efficiency vs. points), who ranks highest?
- Which stats tend to move together (patterns, not cause-and-effect)?

## Tabs

### 📊 Overview
Top players by a demo "overall impact" score, a distribution chart to see
what's normal vs. rare, and a CSV download of the current top-20 table.

### 🧑 Player
Pick a player to see their latest season snapshot, a trend chart across
seasons, and their **closest statistical peers** — the players with the
most similar overall stat profile.

### ⚔️ Compare
Pick any two players and see a standardized, side-by-side bar comparison
across every stat, plus their raw career averages.

### 🏟 Team Hub
Pick a team to see roster size, average impact score, and a per-player
roster table.

### 🏁 Rankings
Build a custom "best player" definition by weighting PER, TS%, and PTS —
updates instantly, with a CSV download of your ranked list.

### 🧩 Archetypes
Groups players into 10 player types using KMeans clustering:

Primary Creator · Playmaker · Shot Creator · Off-Ball Scorer ·
Efficient Finisher · Rebounder / Hustle Big · Defensive Anchor (best-effort) ·
3&D Wing (best-effort) · Two-Way Wing · Energy / Bench Role

Includes a 2D "style map" (PCA) where closer players = more similar,
archetype profile averages, and a list of players inside each archetype.

### 🧠 Insights
A correlation heatmap, a "key takeaways" list of the strongest
relationships, and an interactive scatter plot to explore any two stats.

---

## Stats explained (for non-basketball watchers)

- **PTS (Points):** how many points a player scores per game
- **REB (Rebounds):** how many missed shots a player grabs (possession control)
- **AST (Assists):** passes that directly lead to a made shot
- **TS% (True Shooting %):** scoring efficiency (includes free throws)
- **Usage:** how involved a player is in the offense (more shots/turnovers = more usage)
- **PER (demo):** a custom "overall impact" score built from box score stats
  - ⚠️ This is **not the official NBA PER formula** — it's a demo metric for this project.

---

## Data source

This app expects a CSV file at `data/player_stats.csv` (see
`scripts/fetch_nba_data.py` to regenerate it from the NBA stats API). A
SQLite cache is built automatically on first run for faster reruns.
