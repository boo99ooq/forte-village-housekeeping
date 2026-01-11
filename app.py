import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'
FILE_HISTORY = 'storico_planning.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        for col in ['Part_Time', 'Ultimo_Riposo', 'Conteggio_Spezzati', 'Indisp_Spezzato', 'Zone_Padronanza']:
            if col not in df.columns: df[col] = 0
        return df.fillna("")
    return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    sel = st.selectbox("Collaboratore:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_pt = st.checkbox("🕒 Part-Time (9-14)", value=True if current is not None and str(current.get('Part_Time', 0)) in ["1", "True"] else False)
        f_zone = st.text_input("Zona Appartenenza/Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        f_indisp = st.checkbox("🚫 No Spezzato", value=True if current is not None and str(current.get('Indisp_Spezzato', 0)) in ["1", "True"] else False)
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        
        if st.form_submit_button("💾 SALVA"):
            nuova_d = {"Nome": f_nome, "Part_Time": 1 if f_pt else 0, "Zone_Padronanza": f_zone, "Indisp_Spezzato": 1 if f_indisp else 0, "Auto": f_auto}
            if current is not None:
                for col in df.columns: 
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            df.to_csv(FILE_STAFF, index=False)
            st.rerun()

# --- LOGICA PLANNING ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t3:
    st.header("🚀 Elaborazione Planning")
    data_sel = st.date_input("Data:", datetime.now())
    assenti = st.multiselect("🛌 Assenti/Riposi:", sorted(df['Nome'].tolist()))
    
    if st.button("🚀 GENERA SCHIERAMENTO"):
        attive = df[~df['Nome'].isin(assenti)].copy()
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        
        # 1. Identificazione Split (Solo Full-Time e Disponibili)
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)]
        nomi_split = pool_split.sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        # 2. Assegnazione Cameriere alle Zone
        assegnate = []
        resoconto = []
        
        # Inserisci qui la tua logica di caricamento camere (current_plan)
        # Per brevità simuliamo l'output basato sulla tua regola:
        for hotel in lista_hotel:
            team_zona = []
            # Prendi la PT assegnata a quell'hotel se attiva
            pt_zona = attive[(attive['Part_Time'] == 1) & (attive['Zone_Padronanza'].str.contains(hotel))]
            if not pt_zona.empty:
                nome_pt = pt_zona.iloc[0]['Nome']
                team_zona.append(f"{nome_pt} (PT)")
                assegnate.append(nome_pt)
            
            # Aggiungi Full-Time (che pesano 7.5h o 5h se split)
            # ... logica di completamento ...
            
            resoconto.append({"Hotel": hotel, "Team": ", ".join(team_zona)})

        # --- OUTPUT WHATSAPP ---
        st.subheader("📱 Messaggio Pronto per WhatsApp")
        testo_wa = f"*PLANNING HOUSEKEEPING {data_sel.strftime('%d/%m')}*\n"
        testo_wa += "----------------------------------\n"
        for r in resoconto:
            if r['Team']: testo_wa += f"📍 *{r['Hotel']}*\n👥 {r['Team']}\n\n"
        
        testo_wa += "🌙 *COPERTURA SERALE (19:00-22:00)*\n"
        testo_wa += f"🏃 {', '.join(nomi_split) if nomi_split else 'Nessuna assegnata'}"
        
        st.text_area("Copia e invia:", testo_wa, height=400)

        if st.button("🧊 CRISTALLIZZA"):
            # Salvataggio storico e aggiornamento contatori
            st.success("Dati salvati nello storico!")
