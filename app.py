import streamlit as st
import pandas as pd
import os

# Configurazione Pagina
st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

st.title("🏨 Dashboard Executive Housekeeping")
st.subheader("Forte Village Resort - Gestione Squadra Piani")

FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'

# Funzioni di caricamento
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame()

def load_hotels():
    if os.path.exists(FILE_HOTELS):
        return pd.read_csv(FILE_HOTELS)['Nome_Hotel'].tolist()
    return ["Generico"]

df = load_data()
lista_hotel = load_hotels()

# --- BARRA LATERALE: INSERIMENTO ---
with st.sidebar:
    st.header("📝 Nuova Scheda")
    with st.form("form_inserimento", clear_on_submit=True):
        nome = st.text_input("Nome e Cognome (evitare duplicati)")
        
        st.write("**Valutazione Strategica (1-10)**")
        col_voti1, col_voti2 = st.columns(2)
        with col_voti1:
            prof = st.slider("Professionalità", 1, 10, 5)
            esp = st.slider("Esperienza", 1, 10, 5)
            guida = st.slider("Capacità Guida (Leader)", 1, 10, 5)
        with col_voti2:
            tenuta = st.slider("Tenuta Fisica", 1, 10, 5)
            disp = st.slider("Disponibilità", 1, 10, 5)
            emp = st.slider("Empatia", 1, 10, 5)
        
        st.divider()
        st.write("**Relazioni e Preferenze**")
        # Elenco nomi per affinità (se il DB non è vuoto)
        lista_nomi = ["Nessuna"] + df['Nome'].tolist() if not df.empty else ["Nessuna"]
        lavora_con = st.selectbox("Lavora bene con (Affinità):", lista_nomi)
        
        st.divider()
        st.write("**Logistica e Vincoli**")
        pendolare = st.checkbox("Pendolare")
        spezzato = st.checkbox("Disponibile Spezzato")
        jolly = st.checkbox("Jolly (Cambio Hotel)")
        
        riposo = st.selectbox("Riposo Preferenziale", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"])
        
        st.write("**Zone di Padronanza**")
        zone_scelte = []
        for h in lista_hotel:
            if st.checkbox(h, key=f"check_{h}"):
                zone_scelte.append(h)
        
        submit = st.form_submit_button("SALVA SCHEDA")

# --- LOGICA DI SALVATAGGIO (CON CONTROLLO DUPLICATI) ---
if submit and nome:
    nome_pulito = nome.strip()
    
    # Controllo duplicato
    if not df.empty and nome_pulito.lower() in df['Nome'].str.lower().str.strip().values:
        st.error(f"Attenzione: {nome_pulito} è già presente nel database! Modifica il nome o usa la gestione esistente.")
    else:
        nuova_riga = {
            "Nome": nome_pulito, "Professionalita": prof, "Esperienza": esp, 
            "Capacita_Guida": guida, "Tenuta_Fisica": tenuta, 
            "Disponibilita": disp, "Empatia": emp, 
            "Pendolare": 1 if pendolare else 0,
            "Turno_Spezzato": 1 if spezzato else 0,
            "Jolly": 1 if jolly else 0,
            "Riposo_Preferenziale": riposo,
            "Zone_Padronanza": ", ".join(zone_scelte),
            "Lavora_Bene_Con": lavora_con
        }
        df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
        df.to_csv(FILE_DATA, index=False)
        st.success(f"Scheda di {nome_pulito} salvata con successo!")
        st.rerun()

# --- DASHBOARD PRINCIPALE ---
if not df.empty:
    # Calcolo Ranking Executive
    df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + \
                     (df['Capacita_Guida']*4) + (df['Tenuta_Fisica']*3) + \
                     (df['Disponibilita']*2) + (df['Empatia']*1)
    
    df_display = df.sort_values(by='Ranking', ascending=False)

    tab1, tab2, tab3 = st.tabs(["🏆 Classifica Generale", "🔍 Ricerca per Hotel", "📁 Database Completo"])

    with tab1:
        st.write("### Ranking Squadra")
        # Visualizziamo anche l'affinità nella tabella principale
        st.dataframe(df_display[['Nome', 'Ranking', 'Professionalita', 'Esperienza', 'Lavora_Bene_Con', 'Zone_Padronanza', 'Jolly']], use_container_width=True)

    with tab2:
        hotel_sel = st.selectbox("Scegli un Hotel per vedere lo staff esperto:", lista_hotel)
        risultato = df_display[df_display['Zone_Padronanza'].str.contains(hotel_sel, na=False)]
        st.table(risultato[['Nome', 'Ranking', 'Tenuta_Fisica', 'Lavora_Bene_Con']])

    with tab3:
        st.write("Dati grezzi archiviati:")
        st.dataframe(df)
else:
    st.info("Benvenuta Executive. Inizia inserendo la prima risorsa nella barra laterale.")
