import datetime
import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Schul-Vertretungsplan", layout="wide")

DATEI_PFAD = "stundenplan_data.json"


# ==========================================
# 1. DATENBASIS (Holt sich alles vom Master-Plan)
# ==========================================
def lade_daten():
  if os.path.exists(DATEI_PFAD):
    with open(DATEI_PFAD, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"Stundenplan": [], "Stammraeume": {}, "Lehrer": [], "Klassen": []}


daten = lade_daten()

STAMMRÄUME = daten.get("Stammraeume", {})
TAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
STUNDEN = list(range(1, 7))

# Echter Stundenplan direkt aus der gemeinsamen JSON-Datei
STUNDENPLAN = daten.get("Stundenplan", [])

# Dynamische Klassen- und Lehrerlisten aus dem Master-Plan ermitteln
ALLE_KLASSEN = sorted(list(set(e["Klasse"] for e in STUNDENPLAN)))
if not ALLE_KLASSEN:
  ALLE_KLASSEN = ["11A", "11B", "12A", "13A"]  # Fallback

ALLE_LEHRER = sorted(list(set(e["Lehrer"] for e in STUNDENPLAN)))
if not ALLE_LEHRER:
  ALLE_LEHRER = ["SCH", "MEY", "FIS"]  # Fallback

# ==========================================
# 2. SEITENLEISTE
# ==========================================

st.sidebar.header("Ansicht & Ausfälle")

ansicht_modus = st.sidebar.radio(
    "Ansicht wählen:", ["Klassenansicht", "Gesamtansicht (Nur Vertretungen)"]
)

if ansicht_modus == "Klassenansicht":
  ausgewaehlte_klasse = st.sidebar.selectbox(
      "Klasse auswählen:", ALLE_KLASSEN, index=0
  )
else:
  ausgewaehlte_klasse = "Gesamtansicht"

st.sidebar.subheader("Abwesenheit")

kranke_lehrer = st.sidebar.multiselect(
    "Abwesende(r) Lehrer:",
    options=ALLE_LEHRER,
    default=[ALLE_LEHRER[0]] if ALLE_LEHRER else [],
)

st.sidebar.write("Zeitraum / Tage auswählen:")
heute = datetime.date.today()
datums_bereich = st.sidebar.date_input(
    "Datum von - bis:",
    value=(heute, heute + datetime.timedelta(days=4)),
    format="DD.MM.YYYY",
)

betroffene_tage = []
if isinstance(datums_bereich, tuple) and len(datums_bereich) == 2:
  start_d, end_d = datums_bereich
  cur = start_d
  wochenschluessel = {
      0: "Montag",
      1: "Dienstag",
      2: "Mittwoch",
      3: "Donnerstag",
      4: "Freitag",
  }
  while cur <= end_d:
    if cur.weekday() in wochenschluessel:
      betroffene_tage.append(wochenschluessel[cur.weekday()])
    cur += datetime.timedelta(days=1)
else:
  betroffene_tage = TAGE

ganztagig = st.sidebar.checkbox("Ganztägig", value=True)

if ganztagig:
  start_std, end_std = 1, 6
else:
  col_from, col_to = st.sidebar.columns(2)
  with col_from:
    start_std = st.number_input("Stunde von:", min_value=1, max_value=6, value=1)
  with col_to:
    end_std = st.number_input("Stunde bis:", min_value=1, max_value=6, value=6)

# ==========================================
# 3. TITEL
# ==========================================

if ansicht_modus == "Klassenansicht":
  st.title(f"Vertretungsplan Klasse {ausgewaehlte_klasse}")
  st.subheader(f"Wochenplan für Klasse {ausgewaehlte_klasse}")
else:
  st.title("Vertretungsplan Gesamtansicht")
  st.subheader("Übersicht aller Vertretungen & Raumverlegungen")

if not STUNDENPLAN:
  st.warning(
      "⚠ Noch kein Stundenplan im Editor berechnet! Bitte erstelle zuerst"
      " den Master-Plan."
  )

# ==========================================
# 4. TABELLEN-AUFBAU
# ==========================================

grid = {tag: {std: "" for std in STUNDEN} for tag in TAGE}

if ansicht_modus == "Klassenansicht":
  gefilterter_plan = [e for e in STUNDENPLAN if e["Klasse"] == ausgewaehlte_klasse]
else:
  gefilterter_plan = STUNDENPLAN

eintraege_nach_slot = {tag: {std: [] for std in STUNDEN} for tag in TAGE}
for e in gefilterter_plan:
  eintraege_nach_slot[e["Tag"]][e["Stunde"]].append(e)

for tag in TAGE:
  for std in STUNDEN:
    eintraege = eintraege_nach_slot[tag][std]
    if not eintraege:
      grid[tag][std] = ""
      continue

    html_blocks = []
    for e in eintraege:
      klasse = e["Klasse"]
      fach = e["Fach"]
      lehrer = e["Lehrer"]
      raum = e["Raum"]
      ist_fachraum = e.get("Ist_Fachraum", False)

      ist_krank = (
          (lehrer in kranke_lehrer)
          and (tag in betroffene_tage)
          and (start_std <= std <= end_std)
      )

      if ansicht_modus != "Klassenansicht" and not ist_krank:
        continue

      klassen_prefix = (
          f"<b>[{klasse}]</b> " if ansicht_modus != "Klassenansicht" else ""
      )

      if ist_krank:
        is_stufe_12_13 = klasse.startswith("12") or klasse.startswith("13")
        is_stufe_11 = klasse.startswith("11")

        if is_stufe_12_13:
          lehrer_text = (
              "<span class='text-red'>Entfall (Klasse 12/13)</span>"
          )
        elif is_stufe_11:
          lehrer_text = "<span class='new-blue'>Plus (Eigenstudium)</span>"
        else:
          belegte_lehrer_in_stunde = [
              s["Lehrer"]
              for s in STUNDENPLAN
              if s["Tag"] == tag and s["Stunde"] == std
          ]
          verfuegbare_vertreter = [
              l
              for l in ALLE_LEHRER
              if (l not in belegte_lehrer_in_stunde) and (l not in kranke_lehrer)
          ]
          if verfuegbare_vertreter:
            vertretungs_lehrer = verfuegbare_vertreter[0]
            lehrer_text = (
                f"<span class='new-green'>{vertretungs_lehrer}"
                " (Vertretung)</span>"
            )
          else:
            lehrer_text = (
                "<span class='text-red'>Kein Lehrer frei (Entfall)</span>"
            )

        stammraum = STAMMRÄUME.get(klasse, "R101")
        if ist_fachraum:
          raum_text = (
              f"<span class='strike-red'>{raum}</span><br>"
              f"<span class='new-green'>{stammraum}</span>"
          )
        else:
          raum_text = f"<span class='room'>{raum}</span>"

        block = (
            f'<div class="cell-content">'
            f"{klassen_prefix}<b>{fach}</b> <span"
            f" class='strike-red'>{lehrer}</span><br>"
            f"{lehrer_text}<br>"
            f"{raum_text}"
            f"</div>"
        )
      else:
        block = (
            f'<div class="cell-content">'
            f"{klassen_prefix}<b>{fach}</b> &nbsp; <span"
            f" class='teacher'>{lehrer}</span><br>"
            f"<span class='room'>{raum}</span>"
            f"</div>"
        )
      html_blocks.append(block)

    grid[tag][std] = (
        "<hr style='margin: 4px 0; border: 0.5px solid #444;'>".join(
            html_blocks
        )
    )

df_grid = pd.DataFrame(grid)
df_grid.index.name = "Stunde"

st.markdown(
    """
<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        background-color: transparent;
    }
    th {
        background-color: #262730 !important;
        color: #ffffff !important;
        text-align: center;
        padding: 10px;
        border: 1px solid #444;
        font-size: 15px;
    }
    td {
        border: 1px solid #444;
        padding: 8px;
        vertical-align: middle;
        height: 70px;
        background-color: #1e1e1e;
    }
    .cell-content {
        text-align: center;
        font-size: 13px;
        color: #e0e0e0;
    }
    .teacher { color: #aaa; }
    .room { color: #4dabf7; font-weight: bold; }
    .strike-red { color: #ff6b6b; text-decoration: line-through; font-weight: bold; }
    .text-red { color: #ff6b6b; font-weight: bold; }
    .new-green { color: #51cf66; font-weight: bold; }
    .new-blue { color: #339af0; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

st.write(df_grid.to_html(escape=False), unsafe_allow_html=True)
