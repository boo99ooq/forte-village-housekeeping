wimport streamlit as st
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

# --- SIDEBAR: GESTIONE STAFF ---
with st.sidebar:
    st.header("⚙️ Gestione Personale")
    if not df.empty:
        st.download_button("📥 Backup Database", data=df.to_csv(index=False).encode('utf-8'), file_name='backup_staff.csv')
    
    st.divider()
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    dati = {}
    nome_edit = None
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("staff_form"):
        n_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome e Cognome")
        is_gov = st.checkbox("Governante", value=(dati.get('Ruolo') == "Governante"))
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5) if dati.get('Professionalita') else 5))
        
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        if is_gov:
            st.info("Assegnazione Fissa (Max 2)")
            sel_z = st.multiselect("Hotel di riferimento:", lista_hotel, default=[h for h in z_at if h in lista_hotel], max_selections=2)
            z_ass = ", ".join(sel_z)
        else:
            st.write("**Zone di Padronanza**")
            sel_z = [h for h in lista_hotel if st.checkbox(h, key=f"s_{h}", value=(h in z_at))]
            z_ass = ", ".join(sel_z)

        if st.form_submit_button("SALVA SCHEDA"):
            if n_in:
                new = {"Nome": n_in.strip(), "Ruolo": "Governante" if is_gov else "Cameriera", "Professionalita": prof, "Zone_Padronanza": z_ass}
                if modo == "Modifica Esistente": df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.rerun()

# --- TABS PRINCIPALI ---
t1, t2, t3 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Resort"])

# --- TAB 1: STAFF ---
with t1:
    if not df.empty:
        st.write("### Situazione Squadra")
        st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)
    else:
        st.info("Nessun dato presente. Inserisci lo staff dalla barra laterale.")

# --- TAB 2: TEMPI ---
with t2:
    st.header("Configurazione Minuti per Camera")
    if os.path.exists(FILE_CONFIG): 
        conf = pd.read_csv(FILE_CONFIG)
    else: 
        conf = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])
    
    # Sincronizzazione automatica per nuovi hotel
    presenti = conf['Hotel'].tolist()
    mancanti = [h for h in lista_hotel if h not in presenti]
    if mancanti:
        new_c = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in mancanti])
        conf = pd.concat([conf, new_c], ignore_index=True)

    with st.form("c_form"):
        up_c = []
        for i, r in conf.iterrows():
            if r['Hotel'] in lista_hotel:
                st.write(f"#### 🏨 {r['Hotel']}")
                c1, c2 = st.columns(2)
                with c1:
                    ai = st.slider(f"Indiv: Arrivo/Vuota", 5, 90, int(r.get('Arr_Ind', 60)), key=f"ai{i}")
                    fi = st.slider(f"Indiv: Fermata", 5, 90, int(r.get('Fer_Ind', 30)), key=f"fi{i}")
                with c2:
                    ag = st.slider(f"Gruppo: Arrivo/Vuota", 5, 90, int(r.get('Arr_Gru', 45)), key=f"ag{i}")
                    fg = st.slider(f"Gruppo: Fermata", 5, 90, int(r.get('Fer_Gru', 20)), key=f"fg{i}")
                up_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
        if st.form_submit_button("SALVA CONFIGURAZIONE TEMPI"):
            pd.DataFrame(up_c).to_csv(FILE_CONFIG, index=False)
            st.success("Configurazione salvata per tutto il resort!")

# --- TAB 3: PLANNING (MATRICE) ---
with t3:
    st.header("🚀 Piano Operativo Resort")
    st.write("Inserisci i carichi di lavoro giornalieri per ogni hotel:")

    # MATRICE DI INPUT
    input_data = []
    
    # Intestazione Colonne
    h_col = st.columns([2, 1, 1, 1, 1, 1, 1])
    h_col[0].caption("HOTEL")
    h_col[1].caption("Arr. Ind")
    h_col[2].caption("Fer. Ind")
    h_col[3].caption("Vuo. Ind")
    h_col[4].caption("Arr. Gru")
    h_col[5].caption("Fer. Gru")
    h_col[6].caption("Vuo. Gru")

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

    st.divider()
    
    if st.button("🚀 CALCOLA PIANO DI LAVORO GLOBALE"):
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            
            for row in input_data:
                # Trova i tempi per l'hotel corrente
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                
                # Calcolo ore pesate
                ore_ind = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind'])) / 60
                ore_gru = ((row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
                ore_tot = ore_ind + ore_gru
                
                if ore_tot > 0:
                    # Governante Fissa
                    gov = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "Governante Jolly"
                    
                    # Calcolo numero cameriere (base 7 ore)
                    num_nec = round(ore_tot / 7) if ore_tot >= 7 else 1
                    
                    # Cameriere per zona
                    cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    if cam.empty:
                        cam = df[df['Ruolo'] == "Cameriera"].sort_values('Professionalita', ascending=False)
                    
                    nomi_cam = ", ".join(cam.head(num_nec)['Nome'].tolist())
                    
                    risultati.append({
                        "Hotel": row['Hotel'],
                        "Ore Totali": round(ore_tot, 1),
                        "Responsabile": nomi_gov,
                        "Cameriere Suggerite": nomi_cam
                    })
            
            if risultati:
                st.write("### 📋 Proposta di Schieramento")
                st.table(pd.DataFrame(risultati))
            else:
                st.warning("Inserire dei carichi di lavoro (Arrivi/Fermate) per generare il piano.")ith t3:
    st.header("🚀 Piano Operativo Globale Resort")
    st.write("Inserisci i carichi di lavoro per tutti gli hotel:")

    # Creiamo una struttura dati per l'input
    input_data = []
    
    # Intestazione colonne per chiarezza
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
    h_col2.caption("Arr. Ind.")
    h_col3.caption("Fer. Ind.")
    h_col4.caption("Vuo. Ind.")
    h_col5.caption("Arr. Gru.")
    h_col6.caption("Fer. Gru.")
    h_col7.caption("Vuo. Gru.")

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

    st.divider()
    
    if st.button("🚀 GENERA PIANO DI LAVORO RESORT"):
        if os.path.exists(FILE_CONFIG):
            conf = pd.read_csv(FILE_CONFIG)
            risultati = []
            
            for row in input_data:
                h_c = conf[conf['Hotel'] == row['Hotel']].iloc[0]
                
                # Calcolo ore (usando i tempi salvati nel Tab 2)
                min_tot = ((row['AI'] + row['VI']) * h_c['Arr_Ind']) + (row['FI'] * h_c['Fer_Ind']) + \
                          ((row['AG'] + row['VG']) * h_c['Arr_Gru']) + (row['FG'] * h_c['Fer_Gru'])
                ore = min_tot / 60
                
                if ore > 0:
                    # Identifica Governante
                    gov = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "DA ASSEGNARE"
                    
                    # Suggerimento cameriere
                    num_nec = round(ore / 7) if ore >= 7 else 1
                    cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    if cam.empty: 
                        cam = df[df['Ruolo'] == "Cameriera"].sort_values('Professionalita', ascending=False)
                    
                    nomi_cam = ", ".join(cam.head(num_nec)['Nome'].tolist())
                    
                    risultati.append({
                        "Hotel": row['Hotel'],
                        "Ore Fabbisogno": round(ore, 1),
                        "Governante": nomi_gov,
                        "Cameriere Suggerite": nomi_cam
                    })
            
            if risultati:
                st.write("### 📋 Proposta di Schieramento")
                st.table(pd.DataFrame(risultati))
            else:
                st.warning("Nessun carico di lavoro inserito.")
