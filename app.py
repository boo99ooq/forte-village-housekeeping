import streamlit as st
import pandas as pd
import os

# Configurazione Pagina
st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

st.title("🏨 Dashboard Executive Housekeeping")
st.subheader("Forte Village Resort - Gestione Squadra Piani")

FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'

# Funzione caricamento dati cameriere
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame()

# Funzione caricamento lista hotel
def load_hotels():
    if os.path.exists(FILE_HOTELS):
        return pd.read_csv(FILE_HOTELS)['Nome_Hotel'].tolist()
    return ["Generico"]

df = load_data()
lista_hotel = load_hotels()

# --- BARRA LATERALE: INSERIMENTO ---
with st.sidebar:
    st.header("📝 Nuova Scheda")
    with st.form("form_inserimento"):
        nome = st.text_input("Nome e Cognome")
        
        st.write("**Valutazione Strategica (1-10)**")
        prof = st.slider("Professionalità", 1, 10, 5)
        esp = st.slider("Esperienza", 1, 10, 5)
        guida = st.slider("Capacità Guida (Leader)", 1, 10, 5)
        tenuta = st.slider("Tenuta Fisica", 1, 10, 5)
        disp = st.slider("Disponibilità", 1, 10, 5)
        emp = st.slider("Empatia", 1, 10, 5)
        
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

if submit and nome:
    nuova_riga = {
        "Nome": nome, "Professionalita": prof, "Esperienza": esp, 
        "Capacita_Guida": guida, "Tenuta_Fisica": tenuta, 
        "Disponibilita": disp, "Empatia": emp, 
        "Pendolare": 1 if pendolare else 0,
        "Turno_Spezzato": 1 if spezzato else 0,
        "Jolly": 1 if jolly else 0,
        "Riposo_Preferenziale": riposo,
        "Zone_Padronanza": ", ".join(zone_scelte)
    }
    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
    df.to_csv(FILE_DATA, index=False)
    st.success(f"Scheda di {nome} salvata!")
    st.rerun()

# --- DASHBOARD PRINCIPALE ---
if not df.empty:
    # Calcolo Ranking Executive (Pesi: Prof 5, Esp 5, Guida 4, Tenuta 3, Disp 2, Emp 1)
    df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + \
                     (df['Capacita_Guida']*4) + (df['Tenuta_Fisica']*3) + \
                     (df['Disponibilita']*2) + (df['Empatia']*1)
    
    df_display = df.sort_values(by='Ranking', ascending=False)

    tab1, tab2 = st.tabs(["🏆 Classifica Generale", "🔍 Ricerca per Hotel"])

    with tab1:
        st.write("### Ranking Squadra (Top in alto)")
        st.dataframe(df_display[['Nome', 'Ranking', 'Professionalita', 'Esperienza', 'Zone_Padronanza', 'Jolly']], use_container_width=True)

    with tab2:
        hotel_sel = st.selectbox("Scegli un Hotel per vedere chi lo conosce:", lista_hotel)
        risultato = df_display[df_display['Zone_Padronanza'].str.contains(hotel_sel, na=False)]
        st.table(risultato[['Nome', 'Ranking', 'Tenuta_Fisica', 'Turno_Spezzato']])
else:
    st.info("Benvenuta. Inizia inserendo una scheda nella barra a sinistra.")
