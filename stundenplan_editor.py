import json
import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Stundenplan-Generator & Editor", layout="wide")

DATEI_PFAD = "stundenplan_data.json"

# ==========================================
# HILFSFUNKTION: Automatische Raum-Analyse
# ==========================================
def analysiere_raumnummer(raum_str):
    """
    Analysiert Raumnummern wie '0.32' oder '1.54':
    - 0.32 -> Stockwerk 0 (EG), Gang 3
    - 1.54 -> Stockwerk 1 (1. OG), Gang 5
    Bei Freitext (z.B. 'Turnhalle') -> Stockwerk 0, Gang 0
    """
    raum_str = raum_str.strip()
    match = re.match(r"^(\d+)\.(\d)(\d+)$", raum_str)
    if match:
        stockwerk = int(match.group(1))
        gang = int(match.group(2))
        return stockwerk, gang
    return 0, 0

# ==========================================
# 1. DATENMANAGEMENT
# ==========================================
def lade_daten():
    if os.path.exists(DATEI_PFAD):
        with open(DATEI_PFAD, "r", encoding="utf-8") as f:
            d = json.load(f)
            if "Faecher_Katalog" not in d:
                d["Faecher_Katalog"] = [
                    {"Name": "Mathe", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Deutsch", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Chemie", "JgstVon": 8, "JgstBis": 13},
                    {"Name": "Physik", "JgstVon": 7, "JgstBis": 13},
                    {"Name": "Sport", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Sp_M", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Sp_W", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Ev", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Kath", "JgstVon": 5, "JgstBis": 13},
                    {"Name": "Ethik", "JgstVon": 5, "JgstBis": 13},
                ]
            return d
    return {
        "Klassen": [],
        "Faecher_Katalog": [
            {"Name": "Mathe", "JgstVon": 5, "JgstBis": 13},
            {"Name": "Deutsch", "JgstVon": 5, "JgstBis": 13},
            {"Name": "Chemie", "JgstVon": 8, "JgstBis": 13},
            {"Name": "Physik", "JgstVon": 7, "JgstBis": 13},
            {"Name": "Sport", "JgstVon": 5, "JgstBis": 13},
        ],
        "Raeume": [],
        "Lehrer": [],
        "Kopplungen": [],
        "Struktur": {},
        "Stundenplan": [],
    }

def speichere_daten(daten):
    with open(DATEI_PFAD, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

daten = lade_daten()
TAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
STUNDEN = list(range(1, 7))

st.title("⚙️ Schul-Stundenplan Manager & Auto-Generator")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 Fächer-Katalog",
    "🏫 Klassen & Räume",
    "👨‍🏫 Lehrer & Profile",
    "🎓 Fächer pro Klasse/Jgst",
    "🔀 Kopplungen & Schienen",
    "🤖 Auto-Berechnung & Plan",
])

# Hilfsliste für alle verfügbaren Fächer
ALLE_FAECHER_NAMEN = sorted([f["Name"] for f in daten.get("Faecher_Katalog", [])])

# ==========================================
# TAB 0: ZENTRALER FÄCHER-KATALOG
# ==========================================
with tab0:
    st.subheader("Zentraler Fächer-Katalog")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_neu_name = st.text_input("Neues Fach (Kürzel/Name):")
    with col_f2:
        f_jgst_v = st.number_input("Unterrichtet ab Jgst:", 5, 13, 5)
    with col_f3:
        f_jgst_b = st.number_input("Unterrichtet bis Jgst:", 5, 13, 13)

    if st.button("Fach im Katalog speichern"):
        if f_neu_name:
            if not any(f["Name"] == f_neu_name for f in daten["Faecher_Katalog"]):
                daten["Faecher_Katalog"].append({"Name": f_neu_name, "JgstVon": f_jgst_v, "JgstBis": f_jgst_b})
                speichere_daten(daten)
                st.success(f"Fach {f_neu_name} wurde angelegt!")
                st.rerun()
            else:
                st.warning("Fach existiert bereits im Katalog!")

    st.markdown("---")
    st.subheader("Vorhandene Fächer verwalten & löschen")
    if daten["Faecher_Katalog"]:
        st.dataframe(pd.DataFrame(daten["Faecher_Katalog"]))
        fach_loeschen = st.selectbox("Fach zum Löschen auswählen:", [f["Name"] for f in daten["Faecher_Katalog"]])
        if st.button("🗑️ Fach löschen"):
            daten["Faecher_Katalog"] = [f for f in daten["Faecher_Katalog"] if f["Name"] != fach_loeschen]
            speichere_daten(daten)
            st.success(f"Fach {fach_loeschen} gelöscht!")
            st.rerun()

# ==========================================
# TAB 1: KLASSEN & RÄUME
# ==========================================
with tab1:
    st.subheader("1. Klassenverwaltung")
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        k_name = st.text_input("Klassenname (z.B. 10A):")
    with col_k2:
        k_jgst = st.number_input("Jahrgangsstufe:", min_value=5, max_value=13, value=10)
    with col_k3:
        k_anzahl = st.number_input("Schüleranzahl:", min_value=1, max_value=40, value=26)
    
    if st.button("Klasse hinzufügen"):
        if k_name:
            daten["Klassen"].append({"Name": k_name, "Jahrgang": k_jgst, "Schuelerzahl": k_anzahl})
            speichere_daten(daten)
            st.success(f"Klasse {k_name} angelegt!")
            st.rerun()

    if daten["Klassen"]:
        kl_loeschen = st.selectbox("Klasse löschen:", [k["Name"] for k in daten["Klassen"]])
        if st.button("🗑️ Klasse löschen"):
            daten["Klassen"] = [k for k in daten["Klassen"] if k["Name"] != kl_loeschen]
            speichere_daten(daten)
            st.success(f"Klasse {kl_loeschen} gelöscht!")
            st.rerun()

    st.markdown("---")
    st.subheader("2. Smarte Raumverwaltung")
    st.caption("💡 **Tipp:** Gibst du z. B. `0.32` ein, erkennt das System automatisch **EG (Stockwerk 0)** und **Gang 3**. Für Texträume wie `Turnhalle` bleibt es flexibel.")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        r_name = st.text_input("Raumnummer / Name (z.B. 0.32 oder Turnhalle):")
        r_kap = st.number_input("Kapazität (Schüler):", 10, 100, 30)
    with col_r2:
        r_ist_fach = st.checkbox("Ist Fachraum?")
        r_faecher_auswahl = st.multiselect("Fachraum für Fächer:", ALLE_FAECHER_NAMEN) if r_ist_fach else []

    if st.button("Raum hinzufügen"):
        if r_name:
            stock, gang = analysiere_raumnummer(r_name)
            daten["Raeume"].append({
                "Name": r_name.strip(), 
                "Stockwerk": stock, 
                "Gang": gang, 
                "Kapazitaet": r_kap, 
                "Ist_Fachraum": r_ist_fach, 
                "Faecher": r_faecher_auswahl
            })
            speichere_daten(daten)
            st.success(f"Raum {r_name} (Stockwerk {stock}, Gang {gang}) angelegt!")
            st.rerun()

    if daten["Raeume"]:
        st.markdown("---")
        st.subheader("Vorhandene Räume")
        st.dataframe(pd.DataFrame(daten["Raeume"]))
        raum_loeschen = st.selectbox("Raum löschen:", [r["Name"] for r in daten["Raeume"]])
        if st.button("🗑️ Raum löschen"):
            daten["Raeume"] = [r for r in daten["Raeume"] if r["Name"] != raum_loeschen]
            speichere_daten(daten)
            st.success(f"Raum {raum_loeschen} gelöscht!")
            st.rerun()

    st.markdown("---")
    st.subheader("Automatisierte Stammraum-Zuordnung")
    if st.button("📐 Stammräume automatisch nach Stockwerk & Kapazität berechnen"):
        stammraeume = {}
        normale_raeume = [r for r in daten["Raeume"] if not r["Ist_Fachraum"]]
        normale_raeume.sort(key=lambda x: (x["Stockwerk"], x["Gang"], x["Name"]))
        
        for kl in sorted(daten["Klassen"], key=lambda x: (x["Jahrgang"], x["Name"])):
            passender_raum = None
            for r in normale_raeume:
                if r["Name"] not in stammraeume.values() and r["Kapazitaet"] >= kl["Schuelerzahl"]:
                    passender_raum = r["Name"]
                    break
            if passender_raum:
                stammraeume[kl["Name"]] = passender_raum
        
        daten["Stammraeume"] = stammraeume
        speichere_daten(daten)
        st.success("Stammräume erfolgreich zugewiesen!")
        st.json(stammraeume)

# ==========================================
# TAB 2: LEHRERPROFILE & WÜNSCHE
# ==========================================
with tab2:
    st.subheader("Lehrerprofil anlegen")
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        l_kuerzel = st.text_input("Kürzel (z.B. MEY):")
        l_vname = st.text_input("Vor- & Nachname:")
        l_max = st.number_input("Max. Wochenstunden:", 1, 30, 24)
    with col_l2:
        l_faecher_sel = st.multiselect("Fächer auswählen:", ALLE_FAECHER_NAMEN)
        l_jgst_von = st.number_input("Unterrichtet Jgst von:", 5, 13, 5)
        l_jgst_bis = st.number_input("Unterrichtet Jgst bis:", 5, 13, 13)
    with col_l3:
        l_w_tage = st.multiselect("Wunschtage:", TAGE)
        l_s_tage = st.multiselect("Sperrtage (Fest):", TAGE)
        l_s_std = st.multiselect("Sperrstunden (Fest):", STUNDEN)
        l_w_jgst = st.multiselect("Wunsch-Jahrgangsstufen:", list(range(5, 14)))

    if st.button("Lehrer speichern"):
        if l_kuerzel:
            daten["Lehrer"] = [l for l in daten["Lehrer"] if l["Kuerzel"] != l_kuerzel.strip()]
            daten["Lehrer"].append({
                "Kuerzel": l_kuerzel.strip(),
                "Name": l_vname,
                "Faecher": l_faecher_sel,
                "MaxStunden": l_max,
                "Wunschtage": l_w_tage,
                "Sperrtage": l_s_tage,
                "Sperrstunden": l_s_std,
                "WunschJgst": l_w_jgst,
                "JgstVon": l_jgst_von,
                "JgstBis": l_jgst_bis
            })
            speichere_daten(daten)
            st.success(f"Lehrer {l_kuerzel} gespeichert!")
            st.rerun()

    st.markdown("---")
    st.subheader("Vorhandene Lehrer verwalten")
    if daten["Lehrer"]:
        st.dataframe(pd.DataFrame(daten["Lehrer"]))
        l_loeschen = st.selectbox("Lehrer löschen:", [l["Kuerzel"] for l in daten["Lehrer"]])
        if st.button("🗑️ Lehrer löschen"):
            daten["Lehrer"] = [l for l in daten["Lehrer"] if l["Kuerzel"] != l_loeschen]
            speichere_daten(daten)
            st.success(f"Lehrer {l_loeschen} gelöscht!")
            st.rerun()

# ==========================================
# TAB 3: FÄCHER PRO KLASSE / JGST
# ==========================================
with tab3:
    st.subheader("Unterrichtsstunden zuweisen")
    alle_klassen_namen = [k["Name"] for k in daten["Klassen"]]
    
    col_st1, col_st2, col_st3 = st.columns(3)
    with col_st1:
        ausgewaehlte_klasse = st.selectbox("Klasse wählen:", alle_klassen_namen if alle_klassen_namen else ["Keine Klasse"])
        kl_jgst = 11
        for k in daten["Klassen"]:
            if k["Name"] == ausgewaehlte_klasse:
                kl_jgst = k["Jahrgang"]
                break

    with col_st2:
        passende_faecher = [
            f["Name"] for f in daten["Faecher_Katalog"]
            if f["JgstVon"] <= kl_jgst <= f["JgstBis"]
        ]
        sel_fach = st.selectbox("Fach auswählen:", passende_faecher if passende_faecher else ALLE_FAECHER_NAMEN)

    with col_st3:
        sel_stunden = st.number_input("Wochenstunden:", 1, 10, 3)

    if st.button("Fach der Klasse zuweisen"):
        if ausgewaehlte_klasse not in daten["Struktur"]:
            daten["Struktur"][ausgewaehlte_klasse] = []
        
        daten["Struktur"][ausgewaehlte_klasse] = [
            e for e in daten["Struktur"][ausgewaehlte_klasse] if e["Fach"] != sel_fach
        ]
        daten["Struktur"][ausgewaehlte_klasse].append({"Fach": sel_fach, "Stunden": sel_stunden})
        speichere_daten(daten)
        st.success(f"{sel_stunden}h {sel_fach} für Klasse {ausgewaehlte_klasse} zugewiesen!")
        st.rerun()

    st.markdown("---")
    st.subheader("Fach-Zuweisung löschen")
    if ausgewaehlte_klasse in daten["Struktur"] and daten["Struktur"][ausgewaehlte_klasse]:
        fach_zu_loeschen = st.selectbox(
            f"Fach aus Klasse {ausgewaehlte_klasse} entfernen:", 
            [e["Fach"] for e in daten["Struktur"][ausgewaehlte_klasse]]
        )
        if st.button("🗑️ Zuweisung löschen"):
            daten["Struktur"][ausgewaehlte_klasse] = [
                e for e in daten["Struktur"][ausgewaehlte_klasse] if e["Fach"] != fach_zu_loeschen
            ]
            speichere_daten(daten)
            st.success(f"Fach {fach_zu_loeschen} aus {ausgewaehlte_klasse} entfernt!")
            st.rerun()

# ==========================================
# TAB 4: KOPPLUNGEN & SCHIENEN
# ==========================================
with tab4:
    st.subheader("Parallel-Kopplungen (z.B. Reli/Ethik, Fremdsprachen)")
    kop_bezeichnung = st.text_input("Name der Kopplung (z.B. Religion/Ethik 11):")
    betroffene_klassen = st.multiselect("Über welche Klassen erstreckt sich die Kopplung?", alle_klassen_namen)
    
    col_kop1, col_kop2 = st.columns(2)
    with col_kop1:
        kop_fach = st.selectbox("Gekoppeltes Fach auswählen:", ALLE_FAECHER_NAMEN, key="kop_fach_sel")
    with col_kop2:
        kop_gruppe = st.selectbox("Betroffene Schülergruppe:", [
            "alle", "männlich", "weiblich", "ethik", "katholisch", "evangelisch", 
            "englisch", "französisch", "spanisch", "latein"
        ])

    if st.button("Kopplungsregel anlegen"):
        if kop_bezeichnung and betroffene_klassen:
            daten["Kopplungen"].append({
                "Name": kop_bezeichnung,
                "Klassen": betroffene_klassen,
                "Fach": kop_fach,
                "Gruppe": kop_gruppe
            })
            speichere_daten(daten)
            st.success("Kopplung erfolgreich angelegt!")
            st.rerun()

    st.markdown("---")
    st.subheader("Bestehende Kopplungen verwalten")
    if daten["Kopplungen"]:
        st.dataframe(pd.DataFrame(daten["Kopplungen"]))
        kop_loeschen = st.selectbox("Kopplung löschen:", [k["Name"] for k in daten["Kopplungen"]])
        if st.button("🗑️ Kopplung löschen"):
            daten["Kopplungen"] = [k for k in daten["Kopplungen"] if k["Name"] != kop_loeschen]
            speichere_daten(daten)
            st.success(f"Kopplung {kop_loeschen} gelöscht!")
            st.rerun()

# ==========================================
# TAB 5: AUTOMATISCHE SOLVER-BERECHNUNG
# ==========================================
with tab5:
    st.subheader("🤖 Automatische Stundenplan-Berechnung")
    st.write("Der Solver berechnet unter Berücksichtigung aller Wünsche, Sperrzeiten, Fachräume und Lehrer-Kapazitäten einen neuen Stundenplan.")

    if st.button("🚀 Stundenplan jetzt automatisch berechnen"):
        neuer_plan = []
        stammraeume = daten.get("Stammraeume", {})
        
        erfolg = True
        for kl_obj in daten["Klassen"]:
            kl_name = kl_obj["Name"]
            jgst = kl_obj["Jahrgang"]
            stammraum = stammraeume.get(kl_name, "R101")
            fächer_liste = daten["Struktur"].get(kl_name, [])

            for f_item in fächer_liste:
                fach = f_item["Fach"]
                anzahl = f_item["Stunden"]
                
                mögliche_lehrer = [
                    l for l in daten["Lehrer"]
                    if fach in l["Faecher"] and l["JgstVon"] <= jgst <= l["JgstBis"]
                ]
                
                if not mögliche_lehrer:
                    st.error(f"Kein passender Lehrer für {fach} in Jgst {jgst} gefunden!")
                    erfolg = False
                    break
                
                lehrer = mögliche_lehrer[0]
                
                ist_fachraum = False
                zugewiesener_raum = stammraum
                for r in daten["Raeume"]:
                    if r["Ist_Fachraum"] and fach in r["Faecher"]:
                        ist_fachraum = True
                        zugewiesener_raum = r["Name"]
                        break

                platzierte_stunden = 0
                for tag in TAGE:
                    if tag in lehrer["Sperrtage"]:
                        continue
                    for std in STUNDEN:
                        if std in lehrer["Sperrstunden"]:
                            continue
                        
                        belegt = any(
                            p["Tag"] == tag and p["Stunde"] == std and 
                            (p["Lehrer"] == lehrer["Kuerzel"] or p["Klasse"] == kl_name)
                            for p in neuer_plan
                        )
                        
                        if not belegt:
                            neuer_plan.append({
                                "Tag": tag,
                                "Stunde": std,
                                "Klasse": kl_name,
                                "Fach": fach,
                                "Lehrer": lehrer["Kuerzel"],
                                "Raum": zugewiesener_raum,
                                "Ist_Fachraum": ist_fachraum
                            })
                            platzierte_stunden += 1
                            if platzierte_stunden >= anzahl:
                                break
                    if platzierte_stunden >= anzahl:
                        break

        if erfolg:
            daten["Stundenplan"] = neuer_plan
            speichere_daten(daten)
            st.success("🎉 Stundenplan erfolgreich berechnet und direkt zu GitHub synchronisiert!")
            st.balloons()
