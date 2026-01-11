import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Executive Housekeeping - Master", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv' # File per congelare i dati

# --- CARICAMENTO DATI ---
def load_data():
    cols = ["Nome", "Ruolo", "Professionalita", "Zone_Padronanza"]
    if os.path.exists(FILE_DATA):
        try:
            df_temp = pd.read_csv(FILE_DATA)
            if df_temp.empty or 'Nome' not in df_temp.columns:
                return pd.DataFrame(columns=cols)
            for col in df_temp.columns:
                df_temp[col] = df_temp[col].fillna("").astype(str).str.strip()
            return df_temp
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def load_hotels():
    h_def = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"]
    return h_def # Semplificato per stabilità

df = load_data()
lista_hotel = load_hotels()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Resort"])

# --- TAB 1: STAFF (Invariato) ---
with t1:
    st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

# --- TAB 2: TEMPI (Congelati nel file config_tempi.csv) ---
with t2:
    st.header("⚙️ Griglia Tempi Standard")
    if os.path.exists(FILE_CONFIG):
        c_df = pd.read_csv(FILE_CONFIG)
    else:
        c_df = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])

    new_config = []
    h_c = st.columns([2, 1, 1, 1, 1])
    headers = ["HOTEL", "Arr. Indiv.", "Fer. Indiv.", "Arr. Gruppo", "Fer. Gruppo"]
    for i, txt in enumerate(headers): h_c[i].caption(txt)

    for h in lista_hotel:
        row_exist = c_df[c_df['Hotel'] == h]
        val_ai = int(row_exist.iloc[0]['Arr_Ind']) if not row_exist.empty else 60
        val_fi = int(row_exist.iloc[0]['Fer_Ind']) if not row_exist.empty else 30
        val_ag = int(row_exist.iloc[0]['Arr_Gru']) if not row_exist.empty else 45
        val_fg = int(row_exist.iloc[0]['Fer_Gru']) if not row_exist.empty else 20

        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].markdown(f"**{h}**")
        ai = cols[1].number_input("", 5, 120, val_ai, key=f"c_ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("", 5, 120, val_fi, key=f"c_fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("", 5, 120, val_ag, key=f"c_ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("", 5, 120, val_fg, key=f"c_fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})

    if st.button("💾 CONGELA TEMPI"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Tempi congelati con successo!")

# --- TAB 3: PLANNING (CON SALVATAGGIO STATO) ---
with t3:
    st.header("🚀 Piano Operativo Resort")
    
    # Caricamento dell'ultimo stato salvato per il planning
    if os.path.exists(FILE_LAST_PLAN):
        last_plan_df = pd.read_csv(FILE_LAST_PLAN)
    else:
        last_plan_df = pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"])

    nomi_per_riposo = sorted(df['Nome'].tolist()) if not df.empty else []
    personale_assente = st.multiselect("🏖️ Seleziona chi è assente oggi:", nomi_per_riposo)
    
    st.divider()
    
    current_input = []
    h_col = st.columns([2, 1, 1, 1, 1, 1, 1])
    headers_p = ["HOTEL", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]
    for i, col in enumerate(h_col): col.caption(headers_p[i])

    for h in lista_hotel:
        # Recupero i valori congelati per questo hotel
        p_row = last_plan_df[last_plan_df['Hotel'] == h]
        v_ai = int(p_row.iloc[0]['AI']) if not p_row.empty else 0
        v_fi = int(p_row.iloc[0]['FI']) if not p_row.empty else 0
        v_vi = int(p_row.iloc[0]['VI']) if not p_row.empty else 0
        v_ag = int(p_row.iloc[0]['AG']) if not p_row.empty else 0
        v_fg = int(p_row.iloc[0]['FG']) if not p_row.empty else 0
        v_vg = int(p_row.iloc[0]['VG']) if not p_row.empty else 0

        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        ai = c[1].number_input("", 0, 100, v_ai, key=f"p_ai_{h}", label_visibility="collapsed")
        fi = c[2].number_input("", 0, 100, v_fi, key=f"p_fi_{h}", label_visibility="collapsed")
        vi = c[3].number_input("", 0, 100, v_vi, key=f"p_vi_{h}", label_visibility="collapsed")
        ag = c[4].number_input("", 0, 100, v_ag, key=f"p_ag_{h}", label_visibility="collapsed")
        fg = c[5].number_input("", 0, 100, v_fg, key=f"p_fg_{h}", label_visibility="collapsed")
        vg = c[6].number_input("", 0, 100, v_vg, key=f"p_vg_{h}", label_visibility="collapsed")
        current_input.append({"Hotel": h, "AI": ai, "FI": fi, "VI": vi, "AG": ag, "FG": fg, "VG": vg})

    c1, c2 = st.columns(2)
    
    if c1.button("🚀 GENERA E CONGELA DATI"):
        # Salviamo lo stato attuale nel file CSV
        pd.DataFrame(current_input).to_csv(FILE_LAST_PLAN, index=False)
        
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            df_attive = df[~df['Nome'].isin(personale_assente)].copy()
            già_assegnate = []

            for row in current_input:
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind']) + 
                              (row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
            
            input_sorted = sorted(current_input, key=lambda x: x['ore'], reverse=True)

            for row in input_sorted:
                if row['ore'] > 0:
                    gov = df_attive[(df_attive['Ruolo'].str.lower() == "governante") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "🚨 Jolly"
                    num_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                    cam = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~df_attive['Nome'].isin(già_assegnate))]
                    if len(cam) < num_nec:
                        jolly = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (~df_attive['Nome'].isin(già_assegnate)) & (~df_attive['Nome'].isin(cam['Nome']))].sort_values('Professionalita', ascending=False)
                        cam = pd.concat([cam, jolly]).head(num_nec)
                    else: cam = cam.head(num_nec)
                    
                    s_list = [f"{('📌' if len(str(c['Zone_Padronanza']).split(', ')) == 1 else '🔄')} {c['Nome']}" for _, c in cam.iterrows()]
                    for _, c in cam.iterrows(): già_assegnate.append(c['Nome'])
                    
                    risultati.append({"Hotel": row['Hotel'], "Ore": round(row['ore'], 1), "Resp": nomi_gov, "Squadra": ", ".join(s_list)})
            
            if risultati:
                st.write("### 📋 Schieramento Resort")
                st.table(pd.DataFrame(risultati))

    if c2.button("🧹 RESETTA MATRICE"):
        if os.path.exists(FILE_LAST_PLAN):
            os.remove(FILE_LAST_PLAN)
            st.rerun()
