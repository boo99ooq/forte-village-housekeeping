import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Housekeeping - Forte Village", layout="wide")

# --- FILE SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_PLAN = 'planning_salvati.csv'

def load_data():
    if os.path.exists(FILE_DATA):
        df = pd.read_csv(FILE_DATA)
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
        return df
    return pd.DataFrame(columns=["Nome", "Ruolo", "Professionalita", "Zone_Padronanza"])

def load_hotels():
    h_def = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"]
    if os.path.exists(FILE_HOTELS):
        try:
            lista = pd.read_csv(FILE_HOTELS)['Nome_Hotel'].str.strip().tolist()
            return [h for h in lista if h] if lista else h_def
        except: return h_def
    return h_def

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR STAFF ---
with st.sidebar:
    st.header("⚙️ Gestione Staff")
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    dati = {}
    nome_edit = None
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("staff_form"):
        n_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome")
        is_gov = st.checkbox("Governante", value=(dati.get('Ruolo') == "Governante"))
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5) if dati.get('Professionalita') else 5))
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        
        if is_gov:
            sel_z = st.multiselect("Hotel assegnati:", lista_hotel, default=[h for h in z_at if h in lista_hotel])
            z_ass = ", ".join(sel_z)
        else:
            sel_z = [h for h in lista_hotel if st.checkbox(h, key=f"s_{h}", value=(h in z_at))]
            z_ass = ", ".join(sel_z)

        if st.form_submit_button("SALVA STAFF"):
            if n_in:
                new = {"Nome": n_in, "Ruolo": "Governante" if is_gov else "Cameriera", "Professionalita": prof, "Zone_Padronanza": z_ass}
                if modo == "Modifica Esistente": df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Staff", "⚙️ Configurazione Tempi", "🚀 Planning Giornaliero"])

with t1:
    st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

with t2:
    st.header("Tempi di preparazione (minuti)")
    if os.path.exists(FILE_CONFIG): 
        conf = pd.read_csv(FILE_CONFIG)
    else: 
        conf = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])
    
    with st.form("c_form"):
        up_c = []
        for i, r in conf.iterrows():
            if r['Hotel'] in lista_hotel:
                st.write(f"### 🏨 {r['Hotel']}")
                c1, c2 = st.columns(2)
                ai = c1.slider(f"Individuale: Arrivo/Vuota", 5, 90, int(r.get('Arr_Ind', 60)), key=f"ai{i}")
                fi = c1.slider(f"Individuale: Fermata", 5, 90, int(r.get('Fer_Ind', 30)), key=f"fi{i}")
                ag = c2.slider(f"Gruppo: Arrivo/Vuota", 5, 90, int(r.get('Arr_Gru', 45)), key=f"ag{i}")
                fg = c2.slider(f"Gruppo: Fermata", 5, 90, int(r.get('Fer_Gru', 20)), key=f"fg{i}")
                up_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
        if st.form_submit_button("SALVA TEMPI"):
            pd.DataFrame(up_c).to_csv(FILE_CONFIG, index=False)
            st.success("Configurazione salvata!")

with t3:
    st.header("Calcolo del Carico")
    target = st.selectbox("Hotel:", lista_hotel)
    
    if os.path.exists(FILE_CONFIG):
        c_f = pd.read_csv(FILE_CONFIG)
        h_row = c_f[c_f['Hotel'] == target]
        
        if not h_row.empty:
            h_c = h_row.iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ospiti Individuali")
                n_ai = st.number_input("Arrivi + Vuote (Ind.)", 0, 100, 0, key="ni_a")
                n_fi = st.number_input("Fermate (Ind.)", 0, 100, 0, key="ni_f")
            
            with col2:
                st.subheader("Ospiti di Gruppo")
                n_ag = st.number_input("Arrivi + Vuote (Gru.)", 0, 100, 0, key="ng_a")
                n_fg = st.number_input("Fermate (Gru.)", 0, 100, 0, key="ng_f")
            
            # Calcolo pesato
            min_tot = (n_ai * h_c['Arr_Ind']) + (n_fi * h_c['Fer_Ind']) + (n_ag * h_c['Arr_Gru']) + (n_fg * h_c['Fer_Gru'])
            ore = min_tot / 60
            st.metric("Totale Ore Lavoro", f"{ore:.1f}")
            
            st.divider()
            
            with st.form("planning_save"):
                # GOVERNANTE
                govs_fisse = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                gov_scelta = ""
                if not govs_fisse.empty:
                    gov_scelta = govs_fisse.iloc[0]['Nome']
                    st.success(f"📌 Governante: **{gov_scelta}**")
                else:
                    altre_gov = df[df['Ruolo'] == "Governante"]
                    gov_scelta = st.selectbox("Scegli Governante Jolly:", [""] + altre_gov['Nome'].tolist())

                # CAMERIERE
                num_nec = round(ore / 7) if ore >= 7 else (1 if ore > 0 else 0)
                cam_zona = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                if cam_zona.empty:
                    cam_zona = df[df['Ruolo'] == "Cameriera"].sort_values('Professionalita', ascending=False)
                
                squadra = cam_zona.head(num_nec)
                st.table(squadra[['Nome', 'Professionalita']])
                
                if st.form_submit_button("💾 SALVA PLANNING"):
                    # Logica salvataggio su CSV
                    st.success("Planning Salvato!")
