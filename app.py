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

# --- FUNZIONI GRAFICHE E CALCOLO ---
def get_rating_icons(val):
    if val <= 0: return "⚪⚪⚪⚪⚪"
    full = int(val)
    half = 1 if (val - full) >= 0.5 else 0
    empty = 5 - full - half
    return "🟢" * full + "🌗" * half + "⚪" * empty

def calcola_rating(row):
    try:
        # Pesi stabiliti: Pro 25%, Esp 20%, Tenuta 20%, Disp 15%, Emp 10%, Guida 10%
        p = pd.to_numeric(row.get('Professionalita', 0), errors='coerce') or 0
        e = pd.to_numeric(row.get('Esperienza', 0), errors='coerce') or 0
        t = pd.to_numeric(row.get('Tenuta_Fisica', 0), errors='coerce') or 0
        d = pd.to_numeric(row.get('Disponibilita', 0), errors='coerce') or 0
        em = pd.to_numeric(row.get('Empatia', 0), errors='coerce') or 0
        g = pd.to_numeric(row.get('Capacita_Guida', 0), errors='coerce') or 0
        
        # Calcolo ponderato su base 10 -> trasformazione in base 5
        voto_5 = (p*0.25 + e*0.20 + t*0.20 + d*0.15 + em*0.10 + g*0.10) / 2
        return round(voto_5 * 2) / 2
    except: return 0.0

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    try:
        df_temp = pd.read_csv(url)
        df_temp.columns = [c.strip() for c in df_temp.columns]
        return df_temp
    except: return pd.DataFrame()

# Caricamento
df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

if not df.empty:
    for col in df.columns: df[col] = df[col].fillna("")
    # Creazione colonne Rating
    df['Rating_Num'] = df.apply(lambda x: calcola_rating(x) if 'ameriera' in str(x.get('Ruolo', '')).lower() else 0.0, axis=1)
    df['Valutazione'] = df['Rating_Num'].apply(get_rating_icons)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Gestionale Live")
    st.markdown(f"[📂 Apri Google Sheets]({SHEET_URL})")
    st.divider()
    if not df.empty:
        cerca = st.selectbox("Cerca dipendente:", [""] + sorted(df['Nome'].tolist()))
        if cerca:
            p = df[df['Nome'] == cerca].iloc[0]
            st.write(f"**Ruolo:** {p.get('Ruolo', 'N/D')}")
            if 'ameriera' in str(p.get('Ruolo')).lower():
                st.write(f"**Performance:** {p['Valutazione']}")
            if 'Auto' in df.columns:
                st.info(f"🚗 Auto: {p.get('Auto', 'Non impostata')}")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if df.empty:
        st.error("Dati non disponibili. Controlla il link Google Sheets.")
    else:
        st.subheader("Performance Staff (Media Ponderata)")
        view_cols = ['Nome', 'Ruolo', 'Valutazione', 'Zone_Padronanza', 'Auto']
        presenti = [c for c in view_cols if c in df.columns]
        st.dataframe(df[presenti].sort_values('Rating_Num', ascending=False), use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_config = []
    for h in lista_hotel:
        if not c_df.empty and h in c_df['Hotel'].values:
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
    assenti = st.multiselect("🏖️ Seleziona Assenti:", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_val = df[df['Nome'] == a]['Auto'].values[0]
            if auto_val:
                compagni = df[(df['Auto'] == auto_val) & (~df['Nome'].isin(assenti))]
                if not compagni.empty:
                    st.warning(f"⚠️ {a} (Auto) è assente. Controlla: {', '.join(compagni['Nome'].tolist())}")

    st.divider()
    current_in = []
    h_p = st.columns([2, 1, 1, 1, 1, 1, 1])
    for i, t in enumerate(["ZONA", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]): h_p[i].caption(t)
    for h in lista_hotel:
        r = lp_df[lp_df['Hotel'] == h] if not lp_df.empty and 'Hotel' in lp_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty else 0 for k in ["AI","FI","VI","AG","FG","VG"]]
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].write(f"**{h}**")
        vi = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{k}_{h}", label_visibility="collapsed") for i, k in enumerate(["ai","fi","vi","ag","fg","vg"])]
        current_in.append({"Hotel": h, "AI": vi[0], "FI": vi[1], "VI": vi[2], "AG": vi[3], "FG": vi[4], "VG": vi[5]})

    if st.button("🚀 ELABORA SCHIERAMENTO"):
        pd.DataFrame(current_in).to_csv(FILE_LAST_PLAN, index=False)
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        ris, attive, assegnate = [], df[~df['Nome'].isin(assenti)].copy(), []
        
        for row in current_in:
            if not conf_df.empty and row['Hotel'] in conf_df['Hotel'].values:
                hc = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * hc['Arr_Ind'] + (row['FI'] * hc['Fer_Ind']) + (row['AG'] + row['VG']) * hc['Arr_Gru'] + (row['FG'] * hc['Fer_Gru'])) / 60
            else: row['ore'] = 0

        for row in sorted(current_in, key=lambda x: x['ore'], reverse=True):
            if row['ore'] > 0:
                gov = attive[(attive['Ruolo'].str.contains('overnante', case=False, na=False)) & (attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                resp = ", ".join(gov['Nome'].tolist()) if not gov.empty else "🚨 Jolly"
                n_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                cam = attive[(attive['Ruolo'].str.contains('ameriera', case=False, na=False)) & (attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~attive['Nome'].isin(assegnate))]
                if len(cam) < n_nec:
                    jolly = attive[(attive['Ruolo'].str.contains('ameriera', case=False, na=False)) & (~attive['Nome'].isin(assegnate)) & (~attive['Nome'].isin(cam['Nome']))].sort_values('Rating_Num', ascending=False)
                    cam = pd.concat([cam, jolly]).head(n_nec)
                else: cam = cam.head(n_nec)
                s_icon = [f"{('📌' if len(str(c.get('Zone_Padronanza','')).split(', ')) == 1 else '🔄')} {c['Nome']}" for _, c in cam.iterrows()]
                assegnate.extend(cam['Nome'].tolist())
                ris.append({"Zona": row['Hotel'], "Ore": round(row['ore'], 1), "Resp": resp, "Team": ", ".join(s_icon)})
        if ris: st.table(pd.DataFrame(ris))
