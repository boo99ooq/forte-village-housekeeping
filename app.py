import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

st.title("🏨 Dashboard Executive Housekeeping")
st.subheader("Gestione Team Piani - Forte Village Resort")

FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'

# Caricamento Dati
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame(columns=["Nome", "Ruolo", "Professionalita", "Esperienza", "Capacita_Guida", "Tenuta_Fisica", "Disponibilita", "Empatia", "Pendolare", "Turno_Spezzato", "Jolly", "Riposo_Preferenziale", "Zone_Padronanza", "Lavora_Bene_Con", "Non_Assegnare_A"])

def load_hotels():
    if os.path.exists(FILE_HOTELS):
        return pd.read_csv(FILE_HOTELS)['Nome_Hotel'].tolist()
    return ["Hotel Castello", "Le Dune", "Villa del Parco"]

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR: AZIONI E BACKUP ---
with st.sidebar:
    st.header("⚙️ Pannello di Controllo")
    
    # Sistema di Backup (Fondamentale per non perdere dati online)
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 SCARICA BACKUP DATI",
            data=csv,
            file_name='housekeeping_database.csv',
            mime='text/csv',
            help="Scarica questo file regolarmente e caricalo su GitHub per 'congelare' i tuoi inserimenti."
        )
    
    st.divider()
    modo = st.radio("Cosa vuoi fare?", ["Inserisci Nuova", "Modifica/Aggiorna"])
    
    nome_edit = None
    dati = {}
    if modo == "Modifica/Aggiorna" and not df.empty:
        nome_edit = st.selectbox("Seleziona la risorsa:", df['Nome'].tolist())
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    st.divider()
    
    with st.form("form_lavoro", clear_on_submit=(modo == "Inserisci Nuova")):
        if modo == "Modifica/Aggiorna":
            st.info(f"Stai modificando: **{nome_edit}**")
            nome_input = nome_edit
        else:
            nome_input = st.text_input("Nome e Cognome")
        
        # --- L'OPZIONE SPUNTABILE PER GOVERNANTE ---
        is_gov = st.checkbox("È una GOVERNANTE?", value=(dati.get('Ruolo') == "Governante"))
        ruolo = "Governante" if is_gov else "Cameriera"
        
        st.write("**Valutazioni (1-10)**")
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5)))
        esp = st.slider("Esperienza", 1, 10, int(dati.get('Esperienza', 5)))
        guida = st.slider("Leadership (Capacità Guida)", 1, 10, int(dati.get('Capacita_Guida', 10 if is_gov else 5)))
        tenuta = st.slider("Tenuta Fisica", 1, 10, int(dati.get('Tenuta_Fisica', 5)))
        disp = st.slider("Disponibilità", 1, 10, int(dati.get('Disponibilita', 5)))
        emp = st.slider("Empatia", 1, 10, int(dati.get('Empatia', 5)))
        
        st.divider()
        nomi_per_relazioni = ["Nessuna"] + [n for n in df['Nome'].tolist() if n != nome_input] if not df.empty else ["Nessuna"]
        lavora_con = st.selectbox("Lavora bene con:", nomi_per_relazioni, index=0 if modo == "Inserisci Nuova" or dati.get('Lavora_Bene_Con') not in nomi_per_relazioni else nomi_per_relazioni.index(dati.get('Lavora_Bene_Con')))
        non_lavora = st.selectbox("Non assegnare a:", nomi_per_relazioni, index=0 if modo == "Inserisci Nuova" or dati.get('Non_Assegnare_A') not in nomi_per_relazioni else nomi_per_relazioni.index(dati.get('Non_Assegnare_A')))
        
        st.divider()
        pend = st.checkbox("Pendolare", value=bool(dati.get('Pendolare', False)))
        spec = st.checkbox("Disponibile Spezzato", value=bool(dati.get('Turno_Spezzato', False)))
        jol = st.checkbox("Jolly (Cambio Hotel)", value=bool(dati.get('Jolly', False)))
        
        opzioni_rip = ["Nessuna", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        rip = st.selectbox("Preferenze Riposo:", opzioni_rip, index=opzioni_rip.index(dati.get('Riposo_Preferenziale', "Nessuna")))
        
        st.write("**Zone di Padronanza**")
        zone_attuali = str(dati.get('Zone_Padronanza', "")).split(", ")
        scelte = []
        for h in lista_hotel:
            if st.checkbox(h, key=f"h_{h}", value=(h in zone_attuali)):
                scelte.append(h)
        
        testo_btn = "AGGIORNA DATI" if modo == "Modifica/Aggiorna" else "SALVA SCHEDA"
        submit = st.form_submit_button(testo_btn)

# --- SALVATAGGIO ---
if submit and nome_input:
    row = {
        "Nome": nome_input.strip(), "Ruolo": ruolo, "Professionalita": prof, "Esperienza": esp, 
        "Capacita_Guida": guida, "Tenuta_Fisica": tenuta, "Disponibilita": disp, "Empatia": emp, 
        "Pendolare": 1 if pend else 0, "Turno_Spezzato": 1 if spec else 0, "Jolly": 1 if jol else 0,
        "Riposo_Preferenziale": rip, "Zone_Padronanza": ", ".join(scelte), 
        "Lavora_Bene_Con": lavora_con, "Non_Assegnare_A": non_lavora
    }
    
    if modo == "Modifica/Aggiorna":
        df.loc[df['Nome'] == nome_input] = row
    else:
        if nome_input.strip() in df['Nome'].values:
            st.error("Errore: Nome già esistente. Usa 'Modifica' per cambiare i dati.")
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    
    df.to_csv(FILE_DATA, index=False)
    st.success("Dati salvati!")
    st.rerun()

# --- VISUALIZZAZIONE ---
if not df.empty:
    # Calcolo Ranking
    df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + (df['Capacita_Guida']*4) + (df['Tenuta_Fisica']*3) + (df['Disponibilita']*2) + (df['Empatia']*1)
    
    df_sort = df.sort_values(by=['Ruolo', 'Ranking'], ascending=[False, False])
    
    t1, t2 = st.tabs(["🏆 Classifica Generale", "🔍 Cerca Staff per Hotel"])
    
    with t1:
        st.write("### Riepilogo Team (Governanti in evidenza)")
        # Applichiamo uno stile: le governanti in grassetto
        st.dataframe(df_sort[['Nome', 'Ruolo', 'Ranking', 'Professionalita', 'Lavora_Bene_Con', 'Non_Assegnare_A', 'Zone_Padronanza']], use_container_width=True)

    with t2:
        hotel = st.selectbox("Seleziona Hotel:", lista_hotel)
        res = df_sort[df_sort['Zone_Padronanza'].str.contains(hotel, na=False)]
        st.table(res[['Nome', 'Ruolo', 'Ranking', 'Turno_Spezzato', 'Riposo_Preferenziale']])
else:
    st.info("Benvenuta. Inserisci le prime risorse per attivare la Dashboard.")
