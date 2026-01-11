import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'
FILE_HISTORY = 'storico_planning.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Inizializzazione colonne mancanti
        if 'Ultimo_Riposo' not in df.columns: df['Ultimo_Riposo'] = (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        if 'Conteggio_Spezzati' not in df.columns: df['Conteggio_Spezzati'] = 0
        if 'Indisponibilita_Spezzato' not in df.columns: df['Indisponibilita_Spezzato'] = 0
        return df.fillna("")
    return pd.DataFrame()

df = load_data()

# --- SIDEBAR (Pulita) ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    current = None
    if not df.empty:
        sel = st.selectbox("Seleziona:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
        if sel != "--- NUOVO ---": current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        f_indisp = st.checkbox("🚫 Indisponibilità Spezzato", value=True if current is not None and str(current.get('Indisponibilita_Spezzato', 0)) in ["1", "True"] else False)
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        f_dis = st.number_input("Voto Disponibilità", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
        
        if st.form_submit_button("💾 Salva Scheda"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Auto": f_auto, "Disponibilita": f_dis, "Indisponibilita_Spezzato": 1 if f_indisp else 0}
            if current is not None:
                for col in df.columns: 
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            df.to_csv(FILE_STAFF, index=False)
            st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    # Segnale riposi (Chi non riposa da > 6 giorni)
    df['G_Riposo'] = (datetime.now() - pd.to_datetime(df['Ultimo_Riposo'])).dt.days
    st.subheader("Stato Personale")
    st.dataframe(df[['Nome', 'Ruolo', 'G_Riposo', 'Conteggio_Spezzati', 'Auto']].sort_values('G_Riposo', ascending=False),
                 column_config={"G_Riposo": st.column_config.NumberColumn("Giorni senza riposo", format="%d 🗓️")},
                 use_container_width=True, hide_index=True)

with t3:
    st.header("🚀 Planning Giornaliero")
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    assenti = st.multiselect("🛌 Chi è a RIPOSO oggi?", sorted(df['Nome'].tolist()))
    
    # ... (Qui inserimento Arrivi/Partenze) ...
    
    if st.button("🚀 GENERA E MOSTRA SUGGERIMENTI"):
        # Logica per suggerire lo split (chi ne ha fatti meno)
        split_pool = df[(df['Indisponibilita_Spezzato'] == 0) & (df['Ruolo'] == "Cameriera") & (~df['Nome'].isin(assenti))]
        suggeriti_sp = split_pool.sort_values(['Conteggio_Spezzati', 'Disponibilita'], ascending=[True, False]).head(4)
        st.session_state['last_split'] = suggeriti_sp['Nome'].tolist()
        st.write("✨ **Suggeriti per lo Spezzato stasera:**", ", ".join(st.session_state['last_split']))

    if st.button("🧊 CRISTALLIZZA DATI E AGGIORNA STORICO"):
        # 1. Aggiorna Riposi
        df.loc[df['Nome'].isin(assenti), 'Ultimo_Riposo'] = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Aggiorna Conteggio Spezzati (quelli suggeriti o selezionati)
        if 'last_split' in st.session_state:
            df.loc[df['Nome'].isin(st.session_state['last_split']), 'Conteggio_Spezzati'] += 1
        
        # 3. Salva su CSV
        df.to_csv(FILE_STAFF, index=False)
        
        # 4. Salva nello storico (simulato)
        st.success(f"Dati del {data_oggi} salvati! Riposi resettati per gli assenti e split conteggiati.")
        st.balloons()
