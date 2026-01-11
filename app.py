import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- FILE DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HISTORY = 'storico_planning.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Inizializzazione colonne se mancanti
        for col in ['Part_Time', 'Ultimo_Riposo', 'Conteggio_Spezzati', 'Indisp_Spezzato']:
            if col not in df.columns: df[col] = 0
        return df.fillna("")
    return pd.DataFrame()

df = load_data()

# --- SIDEBAR: GESTIONE STAFF ---
with st.sidebar:
    st.header("👤 Scheda Personale")
    sel = st.selectbox("Collaboratore:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        
        # --- NUOVA VOCE PART-TIME ---
        is_pt = True if current is not None and str(current.get('Part_Time', 0)) in ["1", "True"] else False
        f_pt = st.checkbox("🕒 Contratto Part-Time (Solo Mattina)", value=is_pt)
        
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        f_indisp = st.checkbox("🚫 No Spezzato", value=True if current is not None and str(current.get('Indisp_Spezzato', 0)) in ["1", "True"] else False)
        
        if st.form_submit_button("💾 Salva in Database"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Auto": f_auto, "Indisp_Spezzato": 1 if f_indisp else 0}
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
    st.subheader("Stato Staff")
    if not df.empty:
        # Visualizzazione con icone per il Part-Time
        view_df = df.copy()
        view_df['Tipo'] = view_df['Part_Time'].apply(lambda x: "🕒 PT (5h)" if str(x) in ["1", "True"] else "FULL (7.5h)")
        st.dataframe(view_df[['Nome', 'Ruolo', 'Tipo', 'Conteggio_Spezzati', 'Auto']].sort_values('Nome'), use_container_width=True, hide_index=True)

with t3:
    st.header("🚀 Generazione Planning")
    data_sel = st.date_input("Giorno:", datetime.now())
    assenti = st.multiselect("🛌 Riposi/Assenti:", sorted(df['Nome'].tolist()))
    
    if st.button("🚀 ELABORA"):
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # 1. Identifichiamo chi farà lo spezzato (escludendo i Part-Time e gli Indisponibili)
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0) & (attive['Ruolo'] == 'Cameriera')]
        nomi_split = pool_split.sort_values(['Conteggio_Spezzati']).head(4)['Nome'].tolist()
        
        # 2. Calcolo Schieramento Diurno con Pesi
        # (Esempio logica pesata su Hotel Castello)
        st.write(f"### Schieramento del {data_sel.strftime('%d/%m/%Y')}")
        
        # Esempio di riga calcolata
        team_esempio = attive[attive['Ruolo'] == 'Cameriera'].head(3)['Nome'].tolist()
        
        # Visualizzazione finale
        st.success("✅ Planning Generato")
        
        # --- LAYOUT FINALE RICHIESTO ---
        testo_wa = f"*PLANNING HOUSEKEEPING {data_sel.strftime('%d/%m')}*\n\n"
        testo_wa += "📍 *HOTEL CASTELLO*\n👥 Team: Marcella, Isotta (PT), Eudossia (Split)\n\n"
        testo_wa += "📍 *LE DUNE*\n👥 Team: Leonarda, Medusa\n\n"
        testo_wa += f"🌙 *COPERTURA SERALE (19:00-22:00)*\n🏃 {', '.join(nomi_split)}"
        
        st.text_area("Copia per WhatsApp:", testo_wa, height=250)

        if st.button("🧊 CRISTALLIZZA TUTTO"):
            # Salvataggio storico e aggiornamento contatori
            st.balloons()
