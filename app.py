import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

st.title("🏨 Dashboard Executive Housekeeping")
st.subheader("Forte Village Resort - Gestione e Modifica Squadra")

FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'

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

# --- LOGICA DI SELEZIONE PER MODIFICA ---
with st.sidebar:
    st.header("⚙️ Gestione Schede")
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    
    nome_da_modificare = None
    dati_precompilati = {}

    if modo == "Modifica Esistente" and not df.empty:
        nome_da_modificare = st.selectbox("Seleziona chi vuoi aggiornare:", df['Nome'].tolist())
        dati_precompilati = df[df['Nome'] == nome_da_modificare].iloc[0].to_dict()
    
    st.divider()
    
    with st.form("form_housekeeping", clear_on_submit=(modo == "Inserisci Nuova")):
        if modo == "Modifica Esistente":
            st.info(f"Aggiornamento: **{nome_da_modificare}**")
            nome = nome_da_modificare
        else:
            nome = st.text_input("Nome e Cognome")

        st.write("**Valutazione Strategica**")
        prof = st.slider("Professionalità", 1, 10, int(dati_precompilati.get('Professionalita', 5)))
        esp = st.slider("Esperienza", 1, 10, int(dati_precompilati.get('Esperienza', 5)))
        guida = st.slider("Capacità Guida", 1, 10, int(dati_precompilati.get('Capacita_Guida', 5)))
        tenuta = st.slider("Tenuta Fisica", 1, 10, int(dati_precompilati.get('Tenuta_Fisica', 5)))
        disp = st.slider("Disponibilità", 1, 10, int(dati_precompilati.get('Disponibilita', 5)))
        emp = st.slider("Empatia", 1, 10, int(dati_precompilati.get('Empatia', 5)))
        
        st.divider()
        st.write("**Relazioni e Preferenze**")
        lista_nomi = ["Nessuna"] + [n for n in df['Nome'].tolist() if n != nome] if not df.empty else ["Nessuna"]
        
        lavora_con = st.selectbox("Lavora bene con (Affinità):", lista_nomi, 
                                 index=lista_nomi.index(dati_precompilati.get('Lavora_Bene_Con', "Nessuna")) if dati_precompilati.get('Lavora_Bene_Con') in lista_nomi else 0)
        
        non_lavora_con = st.selectbox("NON assegnare a (Incompatibilità):", lista_nomi, 
                                     index=lista_nomi.index(dati_precompilati.get('Non_Assegnare_A', "Nessuna")) if dati_precompilati.get('Non_Assegnare_A') in lista_nomi else 0)
        
        st.divider()
        st.write("**Logistica e Vincoli**")
        pendolare = st.checkbox("Pendolare", value=bool(dati_precompilati.get('Pendolare', False)))
        spezzato = st.checkbox("Disponibile Spezzato", value=bool(dati_precompilati.get('Turno_Spezzato', False)))
        jolly = st.checkbox("Jolly", value=bool(dati_precompilati.get('Jolly', False)))
        
        opzioni_riposo = ["Nessuna", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        pref_riposo = st.selectbox("Preferenze Riposo:", opzioni_riposo, 
                                   index=opzioni_riposo.index(dati_precompilati.get('Riposo_Preferenziale', "Nessuna")))

        st.write("**Zone di Padronanza**")
        zone_attuali = str(dati_precompilati.get('Zone_Padronanza', "")).split(", ")
        zone_scelte = []
        for h in lista_hotel:
            if st.checkbox(h, key=f"ch_{h}", value=(h in zone_attuali)):
                zone_scelte.append(h)
        
        testo_bottone = "AGGIORNA SCHEDA" if modo == "Modifica Esistente" else "SALVA NUOVA SCHEDA"
        submit = st.form_submit_button(testo_bottone)

if submit and nome:
    nuovi_dati = {
        "Nome": nome.strip(), "Professionalita": prof, "Esperienza": esp, 
        "Capacita_Guida": guida, "Tenuta_Fisica": tenuta, 
        "Disponibilita": disp, "Empatia": emp, 
        "Pendolare": 1 if pendolare else 0,
        "Turno_Spezzato": 1 if spezzato else 0,
        "Jolly": 1 if jolly else 0,
        "Riposo_Preferenziale": pref_riposo,
        "Zone_Padronanza": ", ".join(zone_scelte),
        "Lavora_Bene_Con": lavora_con,
        "Non_Assegnare_A": non_lavora_con
    }
    
    if modo == "Modifica Esistente":
        df.loc[df['Nome'] == nome_da_modificare] = nuovi_dati
        st.success(f"Scheda di {nome} aggiornata!")
    else:
        if not df.empty and nome.strip().lower() in df['Nome'].str.lower().values:
            st.error("Errore: Nome già presente.")
        else:
            df = pd.concat([df, pd.DataFrame([nuovi_dati])], ignore_index=True)
            st.success(f"Scheda di {nome} creata!")
    
    df.to_csv(FILE_DATA, index=False)
    st.rerun()

# --- VISUALIZZAZIONE ---
if not df.empty:
    df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + \
                     (df['Capacita_Guida']*4) + (df['Tenuta_Fisica']*3) + \
                     (df['Disponibilita']*2) + (df['Empatia']*1)
    
    df_display = df.sort_values(by='Ranking', ascending=False)

    tab1, tab2 = st.tabs(["🏆 Classifica Generale", "🔍 Ricerca per Hotel"])
    with tab1:
        st.dataframe(df_display[['Nome', 'Ranking', 'Lavora_Bene_Con', 'Non_Assegnare_A', 'Riposo_Preferenziale', 'Zone_Padronanza']], use_container_width=True)
    with tab2:
        hotel_sel = st.selectbox("Hotel:", lista_hotel)
        st.table(df_display[df_display['Zone_Padronanza'].str.contains(hotel_sel, na=False)][['Nome', 'Ranking', 'Lavora_Bene_Con', 'Non_Assegnare_A']])
else:
    st.info("Database vuoto.")
