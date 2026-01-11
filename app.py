import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- CONFIGURAZIONE ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KRQ_jfd60uy80l7p44brg08MVfA93LScV2P3X9Mx8bY/edit?usp=sharing"
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def get_csv_url(url):
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    except: return None

# --- FUNZIONI CALCOLO ---
def calcola_rating(row):
    try:
        # Pesi: Pro 25%, Esp 20%, Tenuta 20%, Disp 15%, Emp 10%, Guida 10%
        p = float(row.get('Professionalita', 5)) * 0.25
        e = float(row.get('Esperienza', 5)) * 0.20
        t = float(row.get('Tenuta_Fisica', 5)) * 0.20
        d = float(row.get('Disponibilita', 5)) * 0.15
        em = float(row.get('Empatia', 5)) * 0.10
        g = float(row.get('Capacita_Guida', 5)) * 0.10
        # Trasformazione in base 5 con mezze stelle
        return round(((p+e+t+d+em+g) / 2) * 2) / 2
    except: return 0.0

def get_stars(val):
    if val <= 0: return "N/D"
    f = int(val)
    h = 1 if (val - f) >= 0.5 else 0
    return "⭐" * f + "🌠" * h + "🌑" * (5 - f - h)

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    try:
        df_temp = pd.read_csv(url)
        df_temp.columns = [c.strip() for c in df_temp.columns]
        for col in df_temp.columns:
            df_temp[col] = df_temp[col].fillna("").astype(str).str.strip()
        return df_temp
    except: return pd.DataFrame()

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# Applichiamo il calcolo stelle immediato
if not df.empty:
    df['Rating_Num'] = df.apply(lambda x: calcola_rating(x) if 'ameriera' in str(x['Ruolo']).lower() else 0, axis=1)
    df['Stelle'] = df['Rating_Num'].apply(get_stars)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Gestionale Live")
    st.markdown(f"[📂 Apri Google Sheets]({SHEET_URL})")
    st.divider()
    if not df.empty:
        st.subheader("🔍 Cerca e Trasporti")
        cerca = st.selectbox("Seleziona dipendente:", [""] + sorted(df['Nome'].tolist()))
        if cerca:
            p = df[df['Nome'] == cerca].iloc[0]
            st.write(f"**Ruolo:** {p['Ruolo']}")
            if 'ameriera' in p['Ruolo'].lower(): st.write(f"**Valutazione:** {p['Stelle']}")
            if 'Auto' in df.columns: st.info(f"🚗 Auto: {p.get('Auto', 'Non impostata')}")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.subheader("Classifica Qualità Cameriere")
    view_cols = ['Nome', 'Ruolo', 'Stelle', 'Zone_Padronanza', 'Auto']
    presenti = [c for c in view_cols if c in df.columns]
    st.dataframe(df[presenti].sort_values('Rating_Num', ascending=False), use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])
    new_config = []
    for h in lista_hotel:
        r = c_df[c_df['Hotel'] == h] if not c_df.empty and 'Hotel' in c_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty else d for k, d in zip(['Arr_Ind','Fer_Ind','Arr_Gru','Fer_Gru'], [60,30,45,20])]
        col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
        col1.write(h)
        ai = col2.number_input("AI", 5, 200, vs[0], key=f"ai_{h}", label_visibility="collapsed")
        fi = col3.number_input("FI", 5, 200, vs[1], key=f"fi_{h}", label_visibility="collapsed")
        ag = col4.number_input("AG", 5, 200, vs[2], key=f"ag_{h}", label_visibility="collapsed")
        fg = col5.number_input("FG", 5, 200, vs[3], key=f"fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)

with t3:
    st.header("🚀 Generazione Planning")
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    assenti = st.multiselect("🏖️ Assenti oggi:", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_info = df[df['Nome'] == a]['Auto'].values[0]
            if auto_info:
                compagni = df[(df['Auto'] == auto_info) & (~df['Nome'].isin(assenti))]
                if not compagni.empty: st.warning(f"⚠️ {a} (Auto) è assente. Avvisa: {', '.join(compagni['Nome'].tolist())}")

    st.divider()
    # Inserimento dati planning e logica assegnazione (uguale alla precedente ma usa Rating_Num per ordinare)
    # ... (omesso per brevità, usa la logica di assegnazione dell'ultimo messaggio)
