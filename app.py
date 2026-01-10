import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_CONFIG = 'config_tempi.csv'

# --- FUNZIONI CARICAMENTO ---
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def load_hotels():
    if os.path.exists(FILE_HOTELS):
        return pd.read_csv(FILE_HOTELS)['Nome_Hotel'].tolist()
    return ["Hotel Castello", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"]

df = load_data(FILE_DATA, ["Nome", "Ruolo", "Professionalita", "Esperienza", "Capacita_Guida", "Tenuta_Fisica", "Disponibilita", "Empatia", "Pendolare", "Turno_Spezzato", "Jolly", "Riposo_Preferenziale", "Zone_Padronanza", "Lavora_Bene_Con", "Non_Assegnare_A"])
lista_hotel = load_hotels()

# --- TAB PRINCIPALI ---
tab_home, tab_config, tab_planning = st.tabs(["👥 Gestione Staff", "⚙️ Configurazione Tempi", "🚀 Planning Giornaliero"])

# --- TAB CONFIGURAZIONE (I TUOI SLIDER) ---
with tab_config:
    st.header("Parametri di Carico Lavoro (Minuti)")
    st.info("Imposta qui quanto tempo richiede ogni operazione per tipologia di ospite.")
    
    # Inizializziamo o carichiamo la config
    if os.path.exists(FILE_CONFIG):
        config_df = pd.read_csv(FILE_CONFIG)
    else:
        # Default se non esiste
        config_data = []
        for h in lista_hotel:
            config_data.append({"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Vuo_Ind": 45, "Arr_Gru": 45, "Fer_Gru": 20, "Vuo_Gru": 30})
        config_df = pd.DataFrame(config_data)

    with st.form("save_config"):
        new_config = []
        for index, row in config_df.iterrows():
            st.subheader(f"🏨 {row['Hotel']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                ai = st.slider(f"Arrivo Indiv.", 5, 90, int(row['Arr_Ind']), key=f"ai_{index}")
                ag = st.slider(f"Arrivo Gruppo", 5, 90, int(row['Arr_Gru']), key=f"ag_{index}")
            with c2:
                fi = st.slider(f"Fermata Indiv.", 5, 90, int(row['Fer_Ind']), key=f"fi_{index}")
                fg = st.slider(f"Fermata Gruppo", 5, 90, int(row['Fer_Gru']), key=f"fg_{index}")
            with c3:
                vi = st.slider(f"Vuota Indiv.", 5, 90, int(row['Vuo_Ind']), key=f"vi_{index}")
                vg = st.slider(f"Vuota Gruppo", 5, 90, int(row['Vuo_Gru']), key=f"vg_{index}")
            
            new_config.append({"Hotel": row['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Vuo_Ind": vi, "Arr_Gru": ag, "Fer_Gru": fg, "Vuo_Gru": vg})
            st.divider()
        
        if st.form_submit_button("SALVA CONFIGURAZIONE TEMPI"):
            pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
            st.success("Configurazione salvata correttamente!")

# --- TAB PLANNING (L'INTELLIGENZA) ---
with tab_planning:
    st.header("Pianificazione Giornaliera")
    if not os.path.exists(FILE_CONFIG):
        st.warning("Configura prima i tempi nel Tab apposito.")
    else:
        target_hotel = st.selectbox("Seleziona Hotel da pianificare:", lista_hotel)
        conf = pd.read_csv(FILE_CONFIG)
        h_conf = conf[conf['Hotel'] == target_hotel].iloc[0]
        
        st.write(f"### Inserimento Camere - {target_hotel}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ospiti Individuali**")
            n_ai = st.number_input("Arrivi Individuali", 0, 100, 0)
            n_fi = st.number_input("Fermate Individuali", 0, 100, 0)
            n_vi = st.number_input("Vuote Individuali", 0, 100, 0)
        with col2:
            st.markdown("**Ospiti di Gruppo**")
            n_ag = st.number_input("Arrivi Gruppo", 0, 100, 0)
            n_fg = st.number_input("Fermate Gruppo", 0, 100, 0)
            n_vg = st.number_input("Vuote Gruppo", 0, 100, 0)
        
        # CALCOLO CARICO
        minuti_totali = (n_ai * h_conf['Arr_Ind']) + (n_fi * h_conf['Fer_Ind']) + (n_vi * h_conf['Vuo_Ind']) + \
                        (n_ag * h_conf['Arr_Gru']) + (n_fg * h_conf['Fer_Gru']) + (n_vg * h_conf['Vuo_Gru'])
        ore_totali = minuti_totali / 60
        
        st.metric("Carico di Lavoro Stimato", f"{ore_totali:.1f} Ore")
        
        if st.button("GENERA PROPOSTA SQUADRA"):
            # Logica di proposta basata su Ranking e Padronanza
            disponibili = df[df['Zone_Padronanza'].str.contains(target_hotel, na=False)].copy()
            disponibili['Ranking'] = (disponibili['Professionalita']*5) + (disponibili['Esperienza']*5)
            squadra = disponibili.sort_values('Ranking', ascending=False)
            
            st.write("### 📋 Squadra Suggerita per questo carico:")
            # Semplice calcolo: una persona = 7 ore di lavoro
            num_persone_nec = round(ore_totali / 7) if ore_totali > 0 else 0
            st.success(f"Suggerimento: Impiegare almeno {num_persone_nec} persone per questo carico.")
            st.table(squadra.head(max(2, num_persone_nec))[['Nome', 'Ruolo', 'Lavora_Bene_Con']])

# --- TAB HOME (TUA GESTIONE ATTUALE) ---
with tab_home:
    # (Qui rimane il codice precedente per Inserimento/Modifica staff)
    st.info("Usa la barra laterale per gestire il personale come al solito.")
    # ... (Il resto del codice di gestione staff) ...
