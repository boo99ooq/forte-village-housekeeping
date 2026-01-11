import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        ruolo = str(row.get('Ruolo', '')).lower()
        # Se è una governante, restituiamo la stella
        if 'overnante' in ruolo:
            return "⭐ (Coord.)", 10.0
        
        if 'ameriera' not in ruolo:
            return "⚪ Staff", 0.0

        # Calcolo mattoncini per cameriere
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        return "🟩" * int(voto_5) + "🟨" * (1 if (voto_5 % 1) >= 0.5 else 0) + "⬜" * (5 - int(voto_5 + 0.5)), voto_5
    except:
        return "⬜⬜⬜⬜⬜", 0.0

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR: GESTIONE ---
with st.sidebar:
    st.header("👤 Pannello Staff")
    current = None
    if not df.empty:
        nomi_staff = ["--- NUOVO ---"] + sorted(df['Nome'].tolist())
        sel = st.selectbox("Seleziona collaboratore:", nomi_staff)
        if sel != "--- NUOVO ---":
            current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], 
                               index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        
        # Logica "Viaggia con..."
        lista_nomi = sorted(df['Nome'].tolist())
        opzioni_v = ["Nessuna / Auto Propria"] + lista_nomi + ["+ AGGIUNGI ALTRO..."]
        v_attuale = str(current['Auto']) if current is not None and str(current['Auto']) != "nan" and str(current['Auto']) != "" else "Nessuna / Auto Propria"
        s_v = st.selectbox("Viaggia con:", opzioni_v, index=opzioni_v.index(v_attuale) if v_attuale in opzioni_v else 0)
        f_auto = st.text_input("Specifica se altro:", "") if s_v == "+ AGGIUNGI ALTRO..." else s_v
        if f_auto == "Nessuna / Auto Propria": f_auto = ""

        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        
        st.write("--- Valutazioni (1-10) ---")
        c1, c2 = st.columns(2)
        f_pro = c1.number_input("Prof.", 0, 10, int(pd.to_numeric(current['Professionalita'], errors='coerce') or 5) if current is not None else 5)
        f_esp = c2.number_input("Esp.", 0, 10, int(pd.to_numeric(current['Esperienza'], errors='coerce') or 5) if current is not None else 5)
        f_ten = c1.number_input("Fisico", 0, 10, int(pd.to_numeric(current['Tenuta_Fisica'], errors='coerce') or 5) if current is not None else 5)
        f_dis = c1.number_input("Disp.", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
        f_emp = c2.number_input("Empatia", 0, 10, int(pd.to_numeric(current['Empatia'], errors='coerce') or 5) if current is not None else 5)
        f_gui = c2.number_input("Guida", 0, 10, int(pd.to_numeric(current['Capacita_Guida'], errors='coerce') or 5) if current is not None else 5)
        
        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Auto": f_auto, "Zone_Padronanza": f_zone,
                       "Professionalita": f_pro, "Esperienza": f_esp, "Tenuta_Fisica": f_ten,
                       "Disponibilita": f_dis, "Empatia": f_emp, "Capacita_Guida": f_gui}
            if current is not None:
                for col in df.columns:
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df)
            st.rerun()

    st.divider()
    csv_b = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Backup CSV", csv_b, "Housekeeping_DB_Staff.csv", "text/csv")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.subheader("Performance e Ruoli")
        st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto', 'Rating_Num']].sort_values(['Ruolo', 'Rating_Num'], ascending=[True, False]), 
                     column_config={"Rating_Num": None}, use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi Standard (minuti)")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        vs = [60, 30, 45, 20]
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("A.Ind", 5, 200, vs[0], key=f"ai_{h}")
        fi = cols[2].number_input("F.Ind", 5, 200, vs[1], key=f"fi_{h}")
        ag = cols[3].number_input("A.Gru", 5, 200, vs[2], key=f"ag_{h}")
        fg = cols[4].number_input("F.Gru", 5, 200, vs[3], key=f"fg_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Configurazione Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False)
        st.success("Tempi salvati!")

with t3:
    st.header("🚀 Generazione Planning Giornaliero")
    assenti = st.multiselect("🏖️ Personale Assente:", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    # Alert Viaggi
    if assenti:
        for a in assenti:
            v_con = df[df['Nome'] == a]['Auto'].values[0]
            if v_con and v_con != "Nessuna / Auto Propria":
                st.warning(f"⚠️ **{a}** è assente. Avvisa la collega che viaggia con lei: **{v_con}**")

    st.divider()
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    current_plan = []
    header = st.columns([2, 1, 1, 1, 1, 1, 1])
    titles = ["ZONA", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]
    for i, t in enumerate(titles): header[i].caption(t)

    for h in lista_hotel:
        r = lp_df[lp_df['Hotel'] == h] if not lp_df.empty and 'Hotel' in lp_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty else 0 for k in ["AI","FI","VI","AG","FG","VG"]]
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].write(f"**{h}**")
        vals = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{h}_{i}", label_visibility="collapsed") for i in range(6)]
        current_plan.append({"Hotel": h, "AI": vals[0], "FI": vals[1], "VI": vals[2], "AG": vals[3], "FG": vals[4], "VG": vals[5]})

    if st.button("🚀 ELABORA SCHIERAMENTO"):
        pd.DataFrame(current_plan).to_csv(FILE_LAST_PLAN, index=False)
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        
        # Calcolo Ore
        for row in current_plan:
            if not conf_df.empty and row['Hotel'] in conf_df['Hotel'].values:
                hc = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * hc['Arr_Ind'] + (row['FI'] * hc['Fer_Ind']) + (row['AG'] + row['VG']) * hc['Arr_Gru'] + (row['FG'] * hc['Fer_Gru'])) / 60
            else: row['ore'] = 0

        ris, attive, assegnate = [], df[~df['Nome'].isin(assenti)].copy(), []
        # Ordinamento hotel per carico lavoro
        for row in sorted(current_plan, key=lambda x: x['ore'], reverse=True):
            if row['ore'] > 0:
                # Trova Governante della zona
                gov = attive[(attive['Ruolo'].str.contains('overnante', case=False)) & (attive['Zone_Padronanza'].str.contains(row['Hotel']))]
                resp = gov['Nome'].iloc[0] if not gov.empty else "🚨 Jolly"
                
                # Calcolo cameriere necessarie (1 ogni 7 ore di lavoro circa)
                n_cam = max(1, round(row['ore'] / 7))
                
                # Selezione Cameriere (Priorità a chi conosce la zona e ha rating alto)
                cam = attive[(attive['Ruolo'].str.contains('ameriera', case=False)) & 
                             (attive['Zone_Padronanza'].str.contains(row['Hotel'])) & 
                             (~attive['Nome'].isin(assegnate))].sort_values('Rating_Num', ascending=False)
                
                # Se non bastano, pesca dai Jolly (rating alto)
                if len(cam) < n_cam:
                    jolly = attive[(attive['Ruolo'].str.contains('ameriera', case=False)) & 
                                   (~attive['Nome'].isin(assegnate)) & 
                                   (~attive['Nome'].isin(cam['Nome']))].sort_values('Rating_Num', ascending=False)
                    cam = pd.concat([cam, jolly]).head(n_cam)
                else:
                    cam = cam.head(n_cam)
                
                assegnate.extend(cam['Nome'].tolist())
                ris.append({"Zona": row['Hotel'], "Ore Totali": round(row['ore'], 1), "Responsabile": resp, "Team Cameriere": ", ".join(cam['Nome'].tolist())})
        
        if ris:
            st.success("Schieramento Generato con successo!")
            st.table(pd.DataFrame(ris))
