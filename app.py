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

# --- SIDEBAR (Rimane invariata per la gestione staff) ---
with st.sidebar:
    st.header("⚙️ Gestione Personale")
    if not df.empty:
        st.download_button("📥 Backup Staff", data=df.to_csv(index=False).encode('utf-8'), file_name='backup_staff.csv')
    
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    dati = {}
    nome_edit = None
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("staff_form"):
        n_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome")
        is_gov = st.checkbox("Governante", value=(dati.get('Ruolo') == "Governante"))
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5) if dati.get('Professionalita') else 5))
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        
        if is_gov:
            sel_z = st.multiselect("Hotel (Max 2):", lista_hotel, default=[h for h in z_at if h in lista_hotel], max_selections=2)
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
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning Resort"])

with t1:
    if not df.empty:
        st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

with t2:
    st.header("Configurazione Minuti")
    if os.path.exists(FILE_CONFIG): conf = pd.read_csv(FILE_CONFIG)
    else: conf = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])
    
    with st.form("c_form"):
        up_c = []
        for i, r in conf.iterrows():
            if r['Hotel'] in lista_hotel:
                st.write(f"#### 🏨 {r['Hotel']}")
                c1, c2 = st.columns(2)
                ai = c1.slider(f"Ind. Arrivo", 5, 90, int(r.get('Arr_Ind', 60)), key=f"ai{i}")
                fi = c1.slider(f"Ind. Fermata", 5, 90, int(r.get('Fer_Ind', 30)), key=f"fi{i}")
                ag = c2.slider(f"Gru. Arrivo", 5, 90, int(r.get('Arr_Gru', 45)), key=f"ag{i}")
                fg = c2.slider(f"Gru. Fermata", 5, 90, int(r.get('Fer_Gru', 20)), key=f"fg{i}")
                up_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
        if st.form_submit_button("SALVA TEMPI"):
            pd.DataFrame(up_c).to_csv(FILE_CONFIG, index=False)
            st.success("Salvato!")

with t3:
    st.header("🚀 Piano Operativo Globale")
    
    # --- BOX RIPOSI ---
    st.subheader("🏖️ Gestione Assenze")
    tutte_cameriere = sorted(df[df['Ruolo'] == "Cameriera"]['Nome'].tolist())
    cameriere_riposo = st.multiselect("Seleziona le cameriere a riposo oggi:", tutte_cameriere)
    
    st.divider()
    
    # --- MATRICE CARICHI ---
    st.subheader("📊 Inserimento Carichi di Lavoro")
    input_data = []
    h_col = st.columns([2, 1, 1, 1, 1, 1, 1])
    headers = ["HOTEL", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]
    for i, col in enumerate(h_col): col.caption(headers[i])

    for h in lista_hotel:
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        ai = c[1].number_input("", 0, 100, 0, key=f"ai_{h}", label_visibility="collapsed")
        fi = c[2].number_input("", 0, 100, 0, key=f"fi_{h}", label_visibility="collapsed")
        vi = c[3].number_input("", 0, 100, 0, key=f"vi_{h}", label_visibility="collapsed")
        ag = c[4].number_input("", 0, 100, 0, key=f"ag_{h}", label_visibility="collapsed")
        fg = c[5].number_input("", 0, 100, 0, key=f"fg_{h}", label_visibility="collapsed")
        vg = c[6].number_input("", 0, 100, 0, key=f"vg_{h}", label_visibility="collapsed")
        input_data.append({"Hotel": h, "AI": ai, "FI": fi, "VI": vi, "AG": ag, "FG": fg, "VG": vg})

    if st.button("🚀 GENERA PIANO RESORT"):
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            
            # Filtriamo subito chi è a riposo dal calcolo
            df_attive = df[~df['Nome'].isin(cameriere_riposo)].copy()
            già_assegnate = [] 

            # Calcolo ore preventivo per ogni hotel
            for row in input_data:
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind']) + (row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
            
            # Ordiniamo per carico di lavoro
            input_data = sorted(input_data, key=lambda x: x['ore'], reverse=True)

            for row in input_data:
                if row['ore'] > 0:
                    gov = df_attive[(df_attive['Ruolo'] == "Governante") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "Jolly"
                    
                    num_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                    
                    # Filtro cameriere attive e di zona non ancora assegnate
                    cam = df_attive[(df_attive['Ruolo'] == "Cameriera") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~df_attive['Nome'].isin(già_assegnate))]
                    
                    # Se non bastano quelle di zona, prendiamo le altre attive (Jolly)
                    if len(cam) < num_nec:
                        jolly = df_attive[(df_attive['Ruolo'] == "Cameriera") & (~df_attive['Nome'].isin(già_assegnate)) & (~df_attive['Nome'].isin(cam['Nome']))].sort_values('Professionalita', ascending=False)
                        cam = pd.concat([cam, jolly]).head(num_nec)
                    else:
                        cam = cam.head(num_nec)

                    nomi_con_icona = []
                    for _, c in cam.iterrows():
                        già_assegnate.append(c['Nome'])
                        n_zone = len(str(c['Zone_Padronanza']).split(", "))
                        icona = "📌" if n_zone == 1 else "🔄"
                        nomi_con_icona.append(f"{icona} {c['Nome']}")
                    
                    risultati.append({"Hotel": row['Hotel'], "Ore": round(row['ore'], 1), "Responsabile": nomi_gov, "Squadra": ", ".join(nomi_con_icona)})
            
            if risultati:
                st.write("### 📋 Proposta di Schieramento")
                st.caption(f"Cameriere totali a riposo: {len(cameriere_riposo)} | Disponibili: {len(df_attive[df_attive['Ruolo']=='Cameriera'])}")
                st.table(pd.DataFrame(risultati))
