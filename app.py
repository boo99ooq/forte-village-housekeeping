import streamlit as st
import pandas as pd
import os

# Configurazione Pagina
st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

st.title("🏨 Dashboard Executive Housekeeping")
st.subheader("Gestione e Ranking Squadra Piani")

FILE_DATA = 'housekeeping_database.csv'

# Funzione per caricare i dati
def load_data():
    if os.path.exists(FILE_DATA):
        return pd.read_csv(FILE_DATA)
    return pd.DataFrame()

# Caricamento database
df = load_data()

# --- SEZIONE INSERIMENTO NUOVA SCHEDA ---
with st.sidebar:
    st.header("📝 Nuova Scheda Cameriera")
    with st.form("form_inserimento"):
        nome = st.text_input("Nome e Cognome")
        
        col1, col2 = st.columns(2)
        with col1:
            prof = st.slider("Professionalità", 1, 10, 5)
            esp = st.slider("Esperienza", 1, 10, 5)
            guida = st.slider("Capacità Guida", 1, 10, 5)
        with col2:
            tenuta = st.slider("Tenuta Fisica", 1, 10, 5)
            disp = st.slider("Disponibilità", 1, 10, 5)
            emp = st.slider("Empatia", 1, 10, 5)
        
        st.divider()
        
        pendolare = st.checkbox("Pendolare")
        spezzato = st.checkbox("Disponibile Spezzato")
        jolly = st.checkbox("Jolly (Cambio Last Minute)")
        
        riposo = st.selectbox("Giorno di Riposo", ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"])
        zone = st.text_input("Zone di Padronanza (es: Castello, Dune)")
        
        submit = st.form_submit_button("SALVA SCHEDA")

if submit:
    if nome:
        nuova_riga = {
            "Nome": nome, "Professionalita": prof, "Esperienza": esp, 
            "Capacita_Guida": guida, "Tenuta_Fisica": tenuta, 
            "Disponibilita": disp, "Empatia": emp, 
            "Pendolare": 1 if pendolare else 0,
            "Turno_Spezzato": 1 if spezzato else 0,
            "Jolly": 1 if jolly else 0,
            "Riposo_Preferenziale": riposo,
            "Zone_Padronanza": zone
        }
        df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
        df.to_csv(FILE_DATA, index=False)
        st.success(f"Scheda di {nome} salvata correttamente!")
    else:
        st.error("Inserisci il nome prima di salvare.")

# --- VISUALIZZAZIONE E RANKING ---
if not df.empty:
    # Calcolo Ranking Ponderato
    df['Ranking'] = (df['Professionalita'] * 5) + (df['Esperienza'] * 5) + \
                     (df['Capacita_Guida'] * 4) + (df['Tenuta_Fisica'] * 3) + \
                     (df['Disponibilita'] * 2) + (df['Empatia'] * 1)
    
    # Ordina per Ranking
    df_display = df.sort_values(by='Ranking', ascending=False)
    
    st.write("### 🏆 Ranking Personale (Pesi Executive)")
    st.dataframe(df_display[['Nome', 'Ranking', 'Professionalita', 'Esperienza', 'Zone_Padronanza', 'Jolly']], use_container_width=True)
    
    # Filtri Rapidi
    st.write("### 🔍 Filtri Rapidi Ufficio")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Mostra solo chi fa lo Spezzato"):
            st.table(df[df['Turno_Spezzato'] == 1][['Nome', 'Ranking']])
    with c2:
        if st.button("Mostra i Jolly"):
            st.table(df[df['Jolly'] == 1][['Nome', 'Ranking']])
else:
    st.info("Il database è vuoto. Usa la barra laterale per inserire la prima cameriera.")
