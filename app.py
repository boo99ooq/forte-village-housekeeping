import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Executive Housekeeping - Master", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HOTELS = 'hotel_list.csv'

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
    if os.path.exists(FILE_HOTELS):
        try:
            lista = pd.read_csv(FILE_HOTELS)['Nome_Hotel'].str.strip().tolist()
            return [h for h in lista if h] if lista else h_def
        except: return h_def
    return h_def

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR (Gestione Staff) ---
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
        is_gov = st.checkbox("Governante", value=(str(dati.get('Ruolo','')).lower() == "governante"))
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5)))
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        
        if is_gov:
            sel_z = st.multiselect("Hotel assegnati:", lista_hotel, default=[h for h in z_at if h in lista_hotel])
            z_ass = ", ".join(sel_z)
        else:
            sel_z = [h for h in lista_hotel if st.checkbox(h, key=f"s_{h}", value=(h in z_at))]
            z_ass = ", ".join(sel_z)

        if st.form_submit_button("SALVA SCHEDA"):
            if n_in:
                new = {"Nome": n_in.strip(), "Ruolo": "Governante" if is_gov else "Cameriera", "Professionalita": prof, "Zone_Padronanza": z_ass}
                if modo == "Modifica Esistente": df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Configurazione Tempi", "🚀 Planning Resort"])

with t1:
    if not df.empty:
        st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

# --- TAB 2: CONFIGURAZIONE TEMPI (NUOVA GRIGLIA) ---
with t2:
    st.header("⚙️ Griglia Tempi per Camera")
    st.write("Imposta i minuti necessari per ogni tipologia di camera:")

    if os.path.exists(FILE_CONFIG):
        c_df = pd.read_csv(FILE_CONFIG)
    else:
        c_df = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])

    new_config = []
    
    # Intestazione
    h_c = st.columns([2, 1, 1, 1, 1])
    headers = ["HOTEL", "Arr. Indiv.", "Fer. Indiv.", "Arr. Gruppo", "Fer. Gruppo"]
    for i, txt in enumerate(headers): h_c[i].caption(txt)

    for h in lista_hotel:
        # Recupera valori esistenti o usa default
        row_exist = c_df[c_df['Hotel'] == h]
        val_ai = int(row_exist.iloc[0]['Arr_Ind']) if not row_exist.empty else 60
        val_fi = int(row_exist.iloc[0]['Fer_Ind']) if not row_exist.empty else 30
        val_ag = int(row_exist.iloc[0]['Arr_Gru']) if not row_exist.empty else 45
        val_fg = int(row_exist.iloc[0]['Fer_Gru']) if not row_exist.empty else 20

        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].markdown(f"**{h}**")
        ai = cols[1].number_input("", 5, 120, val_ai, key=f"conf_ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("", 5, 120, val_fi, key=f"conf_fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("", 5, 120, val_ag, key=f"conf_ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("", 5, 120, val_fg, key=f"conf_fg_{h}", label_visibility="collapsed")
        
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})

    if st.button("💾 SALVA TUTTI I TEMPI"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Tutti i tempi sono stati aggiornati con successo!")

# --- TAB 3: PLANNING (MATRICE) ---
with t3:
    st.header("🚀 Piano Operativo Resort")
    nomi_per_riposo = sorted(df['Nome'].tolist()) if not df.empty else []
    personale_assente = st.multiselect("🏖️ Seleziona chi è assente oggi:", nomi_per_riposo)
    
    st.divider()
    
    input_data = []
    h_col = st.columns([2, 1, 1, 1, 1, 1, 1])
    headers_p = ["HOTEL", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]
    for i, col in enumerate(h_col): col.caption(headers_p[i])

    for h in lista_hotel:
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        ai = c[1].number_input("", 0, 100, 0, key=f"p_ai_{h}", label_visibility="collapsed")
        fi = c[2].number_input("", 0, 100, 0, key=f"p_fi_{h}", label_visibility="collapsed")
        vi = c[3].number_input("", 0, 100, 0, key=f"p_vi_{h}", label_visibility="collapsed")
        ag = c[4].number_input("", 0, 100, 0, key=f"p_ag_{h}", label_visibility="collapsed")
        fg = c[5].number_input("", 0, 100, 0, key=f"p_fg_{h}", label_visibility="collapsed")
        vg = c[6].number_input("", 0, 100, 0, key=f"p_vg_{h}", label_visibility="collapsed")
        input_data.append({"Hotel": h, "AI": ai, "FI": fi, "VI": vi, "AG": ag, "FG": fg, "VG": vg})

    if st.button("🚀 GENERA PIANO RESORT"):
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            df_attive = df[~df['Nome'].isin(personale_assente)].copy()
            già_assegnate = []

            for row in input_data:
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind']) + 
                              (row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
            
            input_data = sorted(input_data, key=lambda x: x['ore'], reverse=True)

            for row in input_data:
                if row['ore'] > 0:
                    gov = df_attive[(df_attive['Ruolo'].str.lower() == "governante") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "🚨 Jolly"
                    num_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                    cam = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~df_attive['Nome'].isin(già_assegnate))]
                    if len(cam) < num_nec:
                        jolly = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (~df_attive['Nome'].isin(già_assegnate)) & (~df_attive['Nome'].isin(cam['Nome']))].sort_values('Professionalita', ascending=False)
                        cam = pd.concat([cam, jolly]).head(num_nec)
                    else: cam = cam.head(num_nec)
                    
                    s_list = []
                    for _, c in cam.iterrows():
                        già_assegnate.append(c['Nome'])
                        icon = "📌" if len(str(c['Zone_Padronanza']).split(", ")) == 1 else "🔄"
                        s_list.append(f"{icon} {c['Nome']}")
                    
                    risultati.append({"Hotel": row['Hotel'], "Ore": round(row['ore'], 1), "Resp": nomi_gov, "Squadra": ", ".join(s_list)})
            
            if risultati:
                st.write("### 📋 Schieramento Resort")
                st.table(pd.DataFrame(risultati))
