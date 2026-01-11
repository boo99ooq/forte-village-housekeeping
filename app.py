import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
        # Calcolo pesato basato sulle tue colonne
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        full, half = int(voto_5), (1 if (voto_5 % 1) >= 0.5 else 0)
        return "🟩" * full + "🟨" * half + "⬜" * (5 - full - half), voto_5
    except: return "⬜⬜⬜⬜⬜", 0.0

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR: GESTIONE SCHEDE ---
with st.sidebar:
    st.header("👤 Schede Personale")
    nomi_staff = ["--- NUOVO ---"] + sorted(df['Nome'].tolist()) if not df.empty else ["--- NUOVO ---"]
    sel = st.selectbox("Seleziona per modificare:", nomi_staff)
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=current['Nome'] if current else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if not current or "Cameriera" in current['Ruolo'] else 1)
        
        c1, c2 = st.columns(2)
        f_pro = c1.number_input("Prof.", 0, 10, int(pd.to_numeric(current['Professionalita'], errors='coerce') or 5) if current else 5)
        f_esp = c2.number_input("Esp.", 0, 10, int(pd.to_numeric(current['Esperienza'], errors='coerce') or 5) if current else 5)
        f_ten = c1.number_input("Fisico", 0, 10, int(pd.to_numeric(current['Tenuta_Fisica'], errors='coerce') or 5) if current else 5)
        f_dis = c2.number_input("Disp.", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current else 5)
        
        f_zone = st.text_input("Zone Padronanza", value=current['Zone_Padronanza'] if current else "")
        f_auto = st.text_input("Auto (es: Agave)", value=current['Auto'] if current else "")

        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova_data = {"Nome": f_nome, "Ruolo": f_ruolo, "Professionalita": f_pro, "Esperienza": f_esp, 
                          "Tenuta_Fisica": f_ten, "Disponibilita": f_dis, "Zone_Padronanza": f_zone, "Auto": f_auto}
            # Integriamo con le altre colonne esistenti nel CSV per non perderle
            if current is not None:
                for col in df.columns:
                    if col not in nuova_data: nuova_data[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_data])], ignore_index=True)
            save_data(df)
            st.success("Salvato!")
            st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.subheader("Performance e Logistica")
        st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto']].sort_values('Rating_Num', ascending=False), 
                     use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi")
    # ... (Logica tempi già vista, salvataggio su FILE_CONFIG)

with t3:
    st.header("🚀 Planning Operativo")
    assenti = st.multiselect("🏖️ Assenti:", sorted(df['Nome'].tolist()) if not df.empty else [])
    # Alert Auto
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_v = df[df['Nome'] == a]['Auto'].values[0]
            if auto_v:
                comp = df[(df['Auto'] == auto_v) & (~df['Nome'].isin(assenti))]
                if not comp.empty: st.warning(f"⚠️ {a} (Auto: {auto_v}) è assente. Avvisa: {', '.join(comp['Nome'].tolist())}")
    # ... (Logica generazione schieramento)
