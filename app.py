import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'
FILE_HISTORY = 'storico_planning.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Assicuriamoci che la colonna Indisponibilità Spezzato esista
        if 'Indisp_Spezzato' not in df.columns: df['Indisp_Spezzato'] = 0
        return df.fillna("")
    return pd.DataFrame()

df = load_data()

# --- SIDEBAR (CON ENTRAMBI I CAMPI) ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    current = None
    if not df.empty:
        sel = st.selectbox("Seleziona:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
        if sel != "--- NUOVO ---": current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        
        # CAMPO 1: Indisponibilità (Vincolo)
        indisp_val = True if current is not None and str(current.get('Indisp_Spezzato', 0)) in ["1", "1.0", "True"] else False
        f_indisp = st.checkbox("🚫 Indisponibilità allo Spezzato", value=indisp_val)
        
        # CAMPO 2: Disponibilità (Voto 1-10)
        f_dis = st.number_input("Disponibilità (Voto 1-10)", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
        
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        
        if st.form_submit_button("💾 Salva Scheda"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Indisp_Spezzato": 1 if f_indisp else 0, "Disponibilita": f_dis, "Auto": f_auto}
            if current is not None:
                for col in df.columns:
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            df.to_csv(FILE_STAFF, index=False)
            st.success("Dati aggiornati!")
            st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t3:
    st.header("🚀 Planning & Turndown")
    # Caricamento e Visualizzazione Planning con Copertura e Biancheria
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    current_plan = []
    
    h_cols = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 1, 1])
    headers = ["ZONA", "AI", "FI", "VI", "AG", "FG", "VG", "COPERT.", "BIANCH."]
    for i, txt in enumerate(headers): h_cols[i].caption(txt)

    for h in ["Hotel Castello", "Le Dune", "Villa del Parco", "Bouganville"]: # Esempio
        r = lp_df[lp_df['Hotel'] == h] if not lp_df.empty and 'Hotel' in lp_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty and k in r.columns else 0 for k in ["AI","FI","VI","AG","FG","VG","COP","BIA"]]
        c = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 1, 1])
        c[0].write(f"**{h}**")
        vals = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{h}_{i}", label_visibility="collapsed") for i in range(8)]
        current_plan.append({"Hotel": h, "AI": vals[0], "FI": vals[1], "VI": vals[2], "AG": vals[3], "FG": vals[4], "VG": vals[5], "COP": vals[6], "BIA": vals[7]})

    if st.button("🚀 GENERA SCHIERAMENTO COMPLETO"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        risultati = []
        
        for row in current_plan:
            # Recupero tempi standard
            h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30, "Arr_Gru":45, "Fer_Gru":20}
            
            # Calcolo Tempi Speciali
            t_cop = h_c['Fer_Ind'] / 3
            t_bia = h_c['Fer_Ind'] / 4
            
            ore_diurne = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind']) + (row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
            ore_serali = (row['COP'] * t_cop + row['BIA'] * t_bia) / 60
            
            risultati.append({
                "Zona": row['Hotel'],
                "Ore Giorno": int(ore_diurne),
                "Ore Spezzato": round(ore_serali, 1),
                "Cameriere Split": max(1, round(ore_serali / 2)) if ore_serali > 0 else 0
            })
        
        st.subheader("Sintesi Carico Lavoro")
        st.table(pd.DataFrame(risultati))
        
        # Filtro Spezzato
        disponibili_split = df[(df['Indisp_Spezzato'] == 0) & (df['Ruolo'] == "Cameriera") & (~df['Nome'].isin(st.session_state.get('assenti', [])))]
        st.info(f"💡 Cameriere suggerite per lo split stasera: {', '.join(disponibili_split['Nome'].head(6).tolist())}")
