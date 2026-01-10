import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_CONFIG = 'config_tempi.csv'

def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame(columns=["Nome", "Ruolo", "Professionalita", "Esperienza", "Capacita_Guida", "Tenuta_Fisica", "Disponibilita", "Empatia", "Pendolare", "Turno_Spezzato", "Jolly", "Riposo_Preferenziale", "Zone_Padronanza", "Lavora_Bene_Con", "Non_Assegnare_A"])

def load_hotels():
    if os.path.exists(FILE_HOTELS):
        return pd.read_csv(FILE_HOTELS)['Nome_Hotel'].tolist()
    return ["Hotel Castello", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"]

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR: GESTIONE PERSONALE ---
with st.sidebar:
    st.header("⚙️ Gestione Personale")
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
        
        # --- LOGICA ASSEGNAZIONE FISSA GOVERNANTE ---
        if is_gov:
            st.warning("Assegnazione Fissa Stagionale")
            # Per le governanti usiamo un menu a tendina singolo
            zona_assegnata = st.selectbox("Hotel di Riferimento:", lista_hotel, 
                                          index=lista_hotel.index(dati.get('Zone_Padronanza')) if dati.get('Zone_Padronanza') in lista_hotel else 0)
        else:
            st.write("**Zone di Padronanza (Cameriera)**")
            zone_at = str(dati.get('Zone_Padronanza', "")).split(", ")
            scelte_cam = [h for h in lista_hotel if st.checkbox(h, key=f"side_{h}", value=(h in zone_at))]
            zona_assegnata = ", ".join(scelte_cam)

        lavora_con = st.selectbox("Lavora bene con:", ["Nessuna"] + df['Nome'].tolist())
        
        if st.form_submit_button("SALVA/AGGIORNA"):
            new_row = {
                "Nome": nome_in.strip(), "Ruolo": ruolo, 
                "Professionalita": st.slider("Prof.", 1, 10, 5), 
                "Capacita_Guida": 10 if is_gov else 5,
                "Zone_Padronanza": zona_assegnata, 
                "Lavora_Bene_Con": lavora_con
            }
            if modo == "Modifica Esistente":
                df = df[df['Nome'] != nome_edit]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(FILE_DATA, index=False)
            st.rerun()

# --- TAB PLANNING ---
with tab_planning:
    st.header("🚀 Pianificazione Strategica")
    target = st.selectbox("Seleziona Hotel:", lista_hotel)
    
    # 1. Identifica la Governante Fissa dell'hotel
    gov_fissa = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'] == target)]
    
    if not gov_fissa.empty:
        st.success(f"📌 Governante Responsabile per la stagione: **{gov_fissa.iloc[0]['Nome']}**")
    else:
        st.error("⚠️ Nessuna Governante assegnata stabilmente a questo hotel!")

    # ... (Resto del codice per il calcolo delle ore e suggerimento cameriere) ...
