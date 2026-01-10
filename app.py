import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_CONFIG = 'config_tempi.csv'

# --- CARICAMENTO DATI ---
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame(columns=["Nome", "Ruolo", "Professionalita", "Esperienza", "Capacita_Guida", "Tenuta_Fisica", "Disponibilita", "Empatia", "Pendolare", "Turno_Spezzato", "Jolly", "Riposo_Preferenziale", "Zone_Padronanza", "Lavora_Bene_Con", "Non_Assegnare_A"])

def load_hotels():
    # Lista predefinita con Hotel Castello Garden incluso
    hotel_default = [
        "Hotel Castello", "Hotel Castello Garden", "Le Dune", 
        "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"
    ]
    if os.path.exists(FILE_HOTELS):
        try:
            lista = pd.read_csv(FILE_HOTELS)['Nome_Hotel'].str.strip().tolist()
            return lista if (lista and len(lista) > 0) else hotel_default
        except:
            return hotel_default
    return hotel_default

df = load_data()
lista_hotel = load_hotels()

# --- BARRA LATERALE: GESTIONE STAFF ---
with st.sidebar:
    st.header("⚙️ Gestione Personale")
    if not df.empty:
        csv_back = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Backup Database (Eseguire sempre!)", data=csv_back, file_name='housekeeping_database.csv', mime='text/csv')
    
    st.divider()
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    
    nome_edit = None
    dati = {}
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", df['Nome'].tolist())
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("form_staff", clear_on_submit=(modo == "Inserisci Nuova")):
        nome_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome e Cognome")
        is_gov = st.checkbox("È una GOVERNANTE?", value=(dati.get('Ruolo') == "Governante"))
        ruolo = "Governante" if is_gov else "Cameriera"
        
        st.write("**Valutazione**")
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5)))
        esp = st.slider("Esperienza", 1, 10, int(dati.get('Esperienza', 5)))
        guida = st.slider("Capacità Guida", 1, 10, int(dati.get('Capacita_Guida', 10 if is_gov else 5)))
        
        st.divider()
        if is_gov:
            st.info("Assegnazione Fissa (Max 2 Hotel)")
            zone_attuali = str(dati.get('Zone_Padronanza', "")).split(", ")
            scelte_gov = st.multiselect("Alberghi di riferimento:", 
                                        lista_hotel, 
                                        default=[h for h in zone_attuali if h in lista_hotel],
                                        max_selections=2)
            zona_assegnata = ", ".join(scelte_gov)
        else:
            st.write("**Zone di Padronanza (Cameriera)**")
            zone_at = str(dati.get('Zone_Padronanza', "")).split(", ")
            scelte_cam = [h for h in lista_hotel if st.checkbox(h, key=f"side_{h}", value=(h in zone_at))]
            zona_assegnata = ", ".join(scelte_cam)

        relazioni = ["Nessuna"] + (df['Nome'].tolist() if not df.empty else [])
        lavora_con = st.selectbox("Lavora bene con:", relazioni, 
                                  index=relazioni.index(dati.get('Lavora_Bene_Con', "Nessuna")) if dati.get('Lavora_Bene_Con') in relazioni else 0)
        
        if st.form_submit_button("SALVA / AGGIORNA"):
            new_row = {
                "Nome": nome_in.strip(), "Ruolo": ruolo, "Professionalita": prof, 
                "Esperienza": esp, "Capacita_Guida": guida, 
                "Zone_Padronanza": zona_assegnata, "Lavora_Bene_Con": lavora_con
            }
            if modo == "Modifica Esistente":
                df = df[df['Nome'] != nome_edit]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(FILE_DATA, index=False)
            st.rerun()

# --- TABS ---
tab_home, tab_config, tab_planning = st.tabs(["🏆 Dashboard Staff", "⚙️ Tempi per Hotel", "🚀 Planning Giornaliero"])

with tab_home:
    if not df.empty:
        df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + (df['Capacita_Guida']*4)
        st.dataframe(df.sort_values(['Ruolo', 'Ranking'], ascending=[False, False])[['Nome', 'Ruolo', 'Zone_Padronanza', 'Ranking', 'Lavora_Bene_Con']], use_container_width=True)
    else:
        st.info("Usa la barra laterale per inserire staff.")

with tab_config:
    st.header("Configurazione Minuti")
    # Caricamento o creazione config
    if os.path.exists(FILE_CONFIG):
        config_df = pd.read_csv(FILE_CONFIG)
        # Aggiungiamo hotel mancanti (come il Castello Garden appena inserito)
        presenti = config_df['Hotel'].tolist()
        per_aggiungere = [h for h in lista_hotel if h not in presenti]
        if per_aggiungere:
            new_rows = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Vuo_Ind": 45, "Arr_Gru": 45, "Fer_Gru": 20, "Vuo_Gru": 30} for h in per_aggiungere])
            config_df = pd.concat([config_df, new_rows], ignore_index=True)
    else:
        config_df = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Vuo_Ind": 45, "Arr_Gru": 45, "Fer_Gru": 20, "Vuo_Gru": 30} for h in lista_hotel])

    with st.form("config_form"):
        updated_c = []
        for i, r in config_df.iterrows():
            st.subheader(f"🏨 {r['Hotel']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                ai = st.slider(f"Arrivo Ind.", 5, 90, int(r['Arr_Ind']), key=f"ai_{i}")
                ag = st.slider(f"Arrivo Gru.", 5, 90, int(r['Arr_Gru']), key=f"ag_{i}")
            with c2:
                fi = st.slider(f"Fermata Ind.", 5, 90, int(r['Fer_Ind']), key=f"fi_{i}")
                fg = st.slider(f"Fermata Gru.", 5, 90, int(r['Fer_Gru']), key=f"fg_{i}")
            with c3:
                vi = st.slider(f"Vuota Ind.", 5, 90, int(r['Vuo_Ind']), key=f"vi_{i}")
                vg = st.slider(f"Vuota Gru.", 5, 90, int(r['Vuo_Gru']), key=f"vg_{i}")
            updated_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Vuo_Ind": vi, "Arr_Gru": ag, "Fer_Gru": fg, "Vuo_Gru": vg})
        if st.form_submit_button("SALVA CONFIGURAZIONE"):
            pd.DataFrame(updated_c).to_csv(FILE_CONFIG, index=False)
            st.success("Configurazione Tempi salvata!")

with tab_planning:
    st.header("Pianificazione Giornaliera")
    target = st.selectbox("Seleziona Hotel:", lista_hotel)
    if os.path.exists(FILE_CONFIG):
        c_f = pd.read_csv(FILE_CONFIG)
        if target in c_f['Hotel'].values:
            h_c = c_f[c_f['Hotel'] == target].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                n_ai = st.number_input("Arrivi Ind.", 0, 100, 0, key="p_ai")
                n_fi = st.number_input("Fermate Ind.", 0, 100, 0, key="p_fi")
                n_vi = st.number_input("Vuote Ind.", 0, 100, 0, key="p_vi")
            with col2:
                n_ag = st.number_input("Arrivi Gru.", 0, 100, 0, key="p_ag")
                n_fg = st.number_input("Fermate Gru.", 0, 100, 0, key="p_fg")
                n_vg = st.number_input("Vuote Gru.", 0, 100, 0, key="p_vg")
            
            ore_tot = ((n_ai*h_c['Arr_Ind']) + (n_fi*h_c['Fer_Ind']) + (n_vi*h_c['Vuo_Ind']) + (n_ag*h_c['Arr_Gru']) + (n_fg*h_c['Fer_Gru']) + (n_vg*h_c['Vuo_Gru'])) / 60
            st.metric("Carico stimato (Ore)", f"{ore_tot:.1f}")
            
            if st.button("CALCOLA SQUADRA"):
                # Mostra governante fissa
                govs = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                for _, g in govs.iterrows():
                    st.success(f"📌 Responsabile: **{g['Nome']}**")
                
                # Suggerimento cameriere
                num_c = round(ore_tot / 7)
                cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                st.table(cam.head(num_c if num_c > 0 else 3)[['Nome', 'Lavora_Bene_Con']])
