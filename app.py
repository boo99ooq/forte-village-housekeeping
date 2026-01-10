import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Housekeeping - Forte Village", layout="wide")

# --- FILE SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HOTELS = 'hotel_list.csv'

def load_data():
    if os.path.exists(FILE_DATA):
        df = pd.read_csv(FILE_DATA)
        # Pulizia base per evitare errori di lettura
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

# --- SIDEBAR GESTIONE ---
with st.sidebar:
    st.header("⚙️ Gestione")
    if not df.empty:
        st.download_button("📥 Backup CSV", data=df.to_csv(index=False).encode('utf-8'), file_name='backup_staff.csv')
    
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    dati = {}
    nome_edit = None
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("staff_form"):
        n_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome")
        is_gov = st.checkbox("Governante", value=(dati.get('Ruolo') == "Governante"))
        prof = st.slider("Professionalità (1-10)", 1, 10, int(dati.get('Professionalita', 5) if dati.get('Professionalita') else 5))
        
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        if is_gov:
            st.info("Assegnazione Fissa")
            sel_z = st.multiselect("Hotel assegnati:", lista_hotel, default=[h for h in z_at if h in lista_hotel])
            z_ass = ", ".join(sel_z)
        else:
            st.write("**Zone Padronanza**")
            sel_z = [h for h in lista_hotel if st.checkbox(h, key=f"s_{h}", value=(h in z_at))]
            z_ass = ", ".join(sel_z)

        if st.form_submit_button("SALVA"):
            if n_in:
                new = {"Nome": n_in, "Ruolo": "Governante" if is_gov else "Cameriera", "Professionalita": prof, "Zone_Padronanza": z_ass}
                if modo == "Modifica Esistente": df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Staff", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        st.write("### Elenco Personale")
        st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

with t2:
    st.header("Configurazione Minuti")
    if os.path.exists(FILE_CONFIG): 
        conf = pd.read_csv(FILE_CONFIG)
    else: 
        conf = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30} for h in lista_hotel])
    
    # Sincronizza hotel mancanti
    mancanti = [h for h in lista_hotel if h not in conf['Hotel'].tolist()]
    if mancanti:
        new_c = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30} for h in mancanti])
        conf = pd.concat([conf, new_c], ignore_index=True)

    with st.form("c_form"):
        up_c = []
        for i, r in conf.iterrows():
            if r['Hotel'] in lista_hotel:
                st.write(f"**{r['Hotel']}**")
                c1, c2 = st.columns(2)
                ai = c1.slider(f"Arrivo/Vuota (min)", 5, 90, int(r['Arr_Ind']), key=f"ai{i}")
                fi = c2.slider(f"Fermata (min)", 5, 90, int(r['Fer_Ind']), key=f"fi{i}")
                up_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi})
        if st.form_submit_button("SALVA TEMPI"):
            pd.DataFrame(up_c).to_csv(FILE_CONFIG, index=False)
            st.success("Tempi salvati!")

with t3:
    st.header("Planning del Giorno")
    target = st.selectbox("Seleziona Hotel:", lista_hotel)
    
    if os.path.exists(FILE_CONFIG):
        c_f = pd.read_csv(FILE_CONFIG)
        h_row = c_f[c_f['Hotel'] == target]
        
        if not h_row.empty:
            h_c = h_row.iloc[0]
            col1, col2 = st.columns(2)
            n_ai = col1.number_input("N° Arrivi + Vuote", 0, 100, 0)
            n_fi = col2.number_input("N° Fermate", 0, 100, 0)
            
            ore = ((n_ai * h_c['Arr_Ind']) + (n_fi * h_c['Fer_Ind'])) / 60
            st.metric("Carico lavoro stimato", f"{ore:.1f} Ore")
            
            st.divider()
            
            # GESTIONE GOVERNANTE
            govs_fisse = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(target, na=False))]
            if not govs_fisse.empty:
                for _, g in govs_fisse.iterrows():
                    st.success(f"📌 Responsabile: **{g['Nome']}**")
            else:
                st.warning("⚠️ Nessuna Governante fissa per questo hotel.")
                altre_gov = df[df['Ruolo'] == "Governante"]
                if not altre_gov.empty:
                    st.selectbox("Scegli una Governante Jolly:", ["-- Seleziona --"] + altre_gov['Nome'].tolist())

            # GESTIONE CAMERIERE (Tabella Pulita)
            if ore > 0:
                num_nec = round(ore / 7) if ore >= 7 else 1
                cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                
                if cam.empty:
                    st.info("Nessuna cameriera specifica. Mostro le migliori disponibili:")
                    cam = df[df['Ruolo'] == "Cameriera"].sort_values('Professionalita', ascending=False)
                
                st.write(f"### Squadra suggerita ({num_nec} persone)")
                # Visualizziamo solo colonne utili per non creare confusione
                st.table(cam.head(num_nec)[['Nome', 'Professionalita']])
