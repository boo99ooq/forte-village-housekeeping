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

def get_rating_icons(val):
    if val <= 0: return "⚪⚪⚪⚪⚪"
    full = int(val)
    half = 1 if (val - full) >= 0.5 else 0
    return "🟢" * full + "🌗" * half + "⚪" * (5 - full - half)

def calcola_rating(row):
    try:
        # Recupero sicuro dei valori numerici
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
    # Creazione colonne calcolate
    df['Rating_Num'] = df.apply(lambda x: calcola_rating(x) if 'ameriera' in str(x.get('Ruolo', '')).lower() else 0.0, axis=1)
    df['Valutazione'] = df['Rating_Num'].apply(get_rating_icons)
else:
    st.error("⚠️ Impossibile caricare i dati. Verifica il link Google Sheets.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Menu")
    st.markdown(f"[📂 Foglio Google]({SHEET_URL})")
    cerca = st.selectbox("Cerca:", [""] + sorted(df['Nome'].tolist()))
    if cerca:
        p = df[df['Nome'] == cerca].iloc[0]
        st.write(f"**Ruolo:** {p.get('Ruolo')}")
        if 'Rating_Num' in df.columns and p['Rating_Num'] > 0:
            st.write(f"**Voto:** {p['Valutazione']}")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.subheader("Performance Staff")
    # Definiamo le colonne da visualizzare (Rating_Num serve per ordinare, quindi lo includiamo)
    cols_to_show = ['Nome', 'Ruolo', 'Valutazione', 'Zone_Padronanza', 'Auto', 'Rating_Num']
    presenti = [c for c in cols_to_show if c in df.columns]
    
    # Ordiniamo e poi nascondiamo la colonna tecnica Rating_Num
    st.dataframe(
        df[presenti].sort_values('Rating_Num', ascending=False),
        column_config={"Rating_Num": None}, # Questa riga nasconde la colonna numerica
        use_container_width=True,
        hide_index=True
    )

with t2:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_config = []
    for h in lista_hotel:
        if not c_df.empty and 'Hotel' in c_df.columns and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        else: vs = [60, 30, 45, 20]
        c = st.columns([2,1,1,1,1])
        c[0].write(f"**{h}**")
        ai = c[1].number_input("AI", 5, 200, vs[0], key=f"ai_{h}", label_visibility="collapsed")
        fi = c[2].number_input("FI", 5, 200, vs[1], key=f"fi_{h}", label_visibility="collapsed")
        ag = c[3].number_input("AG", 5, 200, vs[2], key=f"ag_{h}", label_visibility="collapsed")
        fg = c[4].number_input("FG", 5, 200, vs[3], key=f"fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Salvato!")

with t3:
    st.header("🚀 Planning")
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    assenti = st.multiselect("🏖️ Assenti:", sorted(df['Nome'].tolist()))
    
    if st.button("🧹 Reset Planning"):
        pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"]).to_csv(FILE_LAST_PLAN, index=False)
        st.rerun()

    st.divider()
    # Logica di inserimento numeri e calcolo schieramento...
    # (Codice identico a quello funzionante in precedenza)
