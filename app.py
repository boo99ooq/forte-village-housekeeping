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

# --- NUOVA GRAFICA A BARRE ---
def get_rating_icons(val):
    if val <= 0: return "⬜⬜⬜⬜⬜"
    full = int(val)
    half = 1 if (val - full) >= 0.5 else 0
    empty = 5 - full - half
    return "🟩" * full + "🟨" * half + "⬜" * empty

def calcola_rating(row):
    try:
        # Pesi: Pro 25%, Esp 20%, Tenuta 20%, Disp 15%, Emp 10%, Guida 10%
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

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

if not df.empty:
    df = df.fillna("")
    df['Rating_Num'] = df.apply(lambda x: calcola_rating(x) if 'ameriera' in str(x.get('Ruolo', '')).lower() else 0.0, axis=1)
    df['Valutazione'] = df['Rating_Num'].apply(get_rating_icons)
else:
    st.error("⚠️ Impossibile caricare i dati.")
    st.stop()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard Performance", "⚙️ Configurazione Tempi", "🚀 Planning Operativo"])

with t1:
    st.subheader("Performance Staff (Barra di Qualità)")
    cols_to_show = ['Nome', 'Ruolo', 'Valutazione', 'Zone_Padronanza', 'Auto', 'Rating_Num']
    presenti = [c for c in cols_to_show if c in df.columns]
    
    st.dataframe(
        df[presenti].sort_values('Rating_Num', ascending=False),
        column_config={"Rating_Num": None}, # Nasconde la colonna tecnica
        use_container_width=True,
        hide_index=True
    )

with t3:
    st.header("🚀 Planning")
    # ... (Il resto del codice planning rimane identico)
