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
        if "/d/" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return None
    except: return None

# --- FUNZIONI GRAFICHE E CALCOLO ---
def get_rating_icons(val):
    if val <= 0: return "⚪⚪⚪⚪⚪"
    full = int(val)
    half = 1 if (val - full) >= 0.5 else 0
    return "🟢" * full + "🌗" * half + "⚪" * (5 - full - half)

def calcola_rating(row):
    try:
        p = pd.to_numeric(row.get('Professionalita', 0), errors='coerce') or 0
        e = pd.to_numeric(row.get('Esperienza', 0), errors='coerce') or 0
        t = pd.to_numeric(row.get('Tenuta_Fisica', 0), errors='coerce') or 0
        d = pd.to_numeric(row.get('Disponibilita', 0), errors='coerce') or 0
        em = pd.to_numeric(row.get('Empatia', 0), errors='coerce') or 0
        g = pd.to_numeric(row.get('Capacita_Guida', 0), errors='coerce') or 0
        voto_5 = (p*0.25 + e*0.20 + t*0.20 + d*0.15 + em*0.10 + g*0.10) / 2
        return round(voto_5 * 2) / 2
    except: return 0.0

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    if not url: return pd.DataFrame()
    try:
        df_temp = pd.read_csv(url)
        df_temp.columns = [c.strip() for c in df_temp.columns]
        return df_temp
    except: return pd.DataFrame()

# Caricamento sicuro
df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# Inizializzazione colonne per evitare KeyError
if not df.empty:
    df = df.fillna("")
    df['Rating_Num'] = df.apply(lambda x: calcola_rating(x) if 'ameriera' in str(x.get('Ruolo', '')).lower() else 0.0, axis=1)
    df['Valutazione'] = df['Rating_Num'].apply(get_rating_icons)
else:
    st.error("⚠️ Il foglio Google non risponde o è vuoto. Controlla i permessi di condivisione!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Gestionale Live")
    st.markdown(f"[📂 Apri Google Sheets]({SHEET_URL})")
    st.divider()
    cerca = st.selectbox("Cerca dipendente:", [""] + sorted(df['Nome'].tolist()))
    if cerca:
        p = df[df['Nome'] == cerca].iloc[0]
        st.write(f"**Ruolo:** {p.get('Ruolo', 'N/D')}")
        if 'ameriera' in str(p.get('Ruolo')).lower():
            st.write(f"**Performance:** {p['Valutazione']}")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.subheader("Performance Staff")
    view_cols = ['Nome', 'Ruolo', 'Valutazione', 'Zone_Padronanza', 'Auto']
    presenti = [c for c in view_cols if c in df.columns]
    # Controllo extra prima del sort
    if 'Rating_Num' in df.columns:
        st.dataframe(df[presenti].sort_values('Rating_Num', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df[presenti], use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_config = []
    for h in lista_hotel:
        if not c_df.empty and 'Hotel' in c_df.columns and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        else: vs = [60, 30, 45, 20]
        col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
        col1.write(f"**{h}**")
        ai = col2.number_input("AI", 5, 200, vs[0], key=f"ai_{h}", label_visibility="collapsed")
        fi = col3.number_input("FI", 5, 200, vs[1], key=f"fi_{h}", label_visibility="collapsed")
        ag = col4.number_input("AG", 5, 200, vs[2], key=f"ag_{h}", label_visibility="collapsed")
        fg = col5.number_input("FG", 5, 200, vs[3], key=f"fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Configurazione"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Salvato!")

with t3:
    st.header("🚀 Planning")
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    assenti = st.multiselect("🏖️ Seleziona Assenti:", sorted(df['Nome'].tolist()))
    
    # Reset button (Novità)
    if st.button("🧹 Reset Campi"):
        pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"]).to_csv(FILE_LAST_PLAN, index=False)
        st.rerun()

    st.divider()
    # Logica planning... (uguale alla precedente)
