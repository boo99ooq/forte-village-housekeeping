import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        if 'ameriera' not in str(row.get('Ruolo', '')).lower(): return "N/A", 0.0
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        return "🟩" * int(voto_5) + "🟨" * (1 if (voto_5 % 1) >= 0.5 else 0) + "⬜" * (5 - int(voto_5 + 0.5)), voto_5
    except: return "⬜⬜⬜⬜⬜", 0.0

# Inizializzazione dati
df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR: GESTIONE ---
with st.sidebar:
    st.header("👤 Pannello Staff")
    
    # Inizializziamo current come None all'inizio della sidebar
    current = None
    
    if not df.empty:
        nomi_staff = ["--- NUOVO ---"] + sorted(df['Nome'].tolist())
        sel = st.selectbox("Seleziona dipendente:", nomi_staff)
        
        if sel != "--- NUOVO ---":
            current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        # Se current è None, i campi saranno vuoti (nuovo inserimento)
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], 
                               index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        f_auto = st.text_input("Auto (es: Agave)", value=str(current['Auto']) if current is not None else "")
        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        
        st.write("--- Valutazioni (1-10) ---")
        c1, c2 = st.columns(2)
        f_pro = c1.number_input("Professionalità", 0, 10, int(pd.to_numeric(current['Professionalita'], errors='coerce') or 5) if current is not None else 5)
        f_esp = c2.number_input("Esperienza", 0, 10, int(pd.to_numeric(current['Esperienza'], errors='coerce') or 5) if current is not None else 5)
        f_ten = c1.number_input("Tenuta Fisica", 0, 10, int(pd.to_numeric(current['Tenuta_Fisica'], errors='coerce') or 5) if current is not None else 5)
        f_dis = c2.number_input("Disponibilità", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
        f_emp = c1.number_input("Empatia", 0, 10, int(pd.to_numeric(current['Empatia'], errors='coerce') or 5) if current is not None else 5)
        f_gui = c2.number_input("Capacità Guida", 0, 10, int(pd.to_numeric(current['Capacita_Guida'], errors='coerce') or 5) if current is not None else 5)
        
        submitted = st.form_submit_button("💾 SALVA SCHEDA")
        
        if submitted:
            nuova_data = {
                "Nome": f_nome, "Ruolo": f_ruolo, "Auto": f_auto, "Zone_Padronanza": f_zone,
                "Professionalita": f_pro, "Esperienza": f_esp, "Tenuta_Fisica": f_ten,
                "Disponibilita": f_dis, "Empatia": f_emp, "Capacita_Guida": f_gui
            }
            # Mantieni colonne extra se presenti
            if current is not None:
                for col in df.columns:
                    if col not in nuova_data: nuova_data[col] = current[col]
                df = df[df['Nome'] != sel]
            
            df = pd.concat([df, pd.DataFrame([nuova_data])], ignore_index=True)
            save_data(df)
            st.success("Salvato con successo!")
            st.rerun()

    st.divider()
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Backup CSV", csv_data, "Housekeeping_DB_Staff.csv", "text/csv")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.subheader("Performance Staff")
        view_cols = ['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto', 'Rating_Num']
        presenti = [c for c in view_cols if c in df.columns]
        st.dataframe(df[presenti].sort_values('Rating_Num', ascending=False), 
                     column_config={"Rating_Num": None}, use_container_width=True, hide_index=True)

# (Tab 2 e 3 seguono la stessa logica di caricamento/salvataggio dei file locali)
