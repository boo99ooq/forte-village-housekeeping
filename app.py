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

# --- GRAFICA E CALCOLO ---
def get_rating_bar(val):
    if val <= 0: return "⬜⬜⬜⬜⬜"
    full = int(val)
    half = 1 if (val - full) >= 0.5 else 0
    return "🟩" * full + "🟨" * half + "⬜" * (5 - full - half)

def calcola_rating(row):
    try:
        # Pesi: Professionalità 25%, Esperienza 20%, Tenuta 20%, Disp 15%, Empatia 10%, Guida 10%
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
    df['Performance'] = df['Rating_Num'].apply(get_rating_bar)
else:
    st.error("⚠️ Caricamento Foglio Google fallito.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Menu")
    st.markdown(f"[📂 Apri Foglio Google]({SHEET_URL})")
    st.divider()
    cerca = st.selectbox("Cerca:", [""] + sorted(df['Nome'].tolist()))
    if cerca:
        p = df[df['Nome'] == cerca].iloc[0]
        st.write(f"**Ruolo:** {p.get('Ruolo')}")
        if p['Rating_Num'] > 0: st.write(f"**Qualità:** {p['Performance']}")
        if 'Auto' in df.columns: st.info(f"🚗 Auto: {p.get('Auto', 'N/D')}")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.subheader("Performance Staff")
    cols = ['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto', 'Rating_Num']
    presenti = [c for c in cols if c in df.columns]
    st.dataframe(df[presenti].sort_values('Rating_Num', ascending=False), 
                 column_config={"Rating_Num": None}, use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_config = []
    for h in lista_hotel:
        vs = [60, 30, 45, 20]
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI", 5, 200, vs[0], key=f"ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("FI", 5, 200, vs[1], key=f"fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("AG", 5, 200, vs[2], key=f"ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("FG", 5, 200, vs[3], key=f"fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Configurazione salvata!")

with t3:
    st.header("🚀 Planning")
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    assenti = st.multiselect("🏖️ Assenti:", sorted(df['Nome'].tolist()))
    if st.button("🧹 Reset Planning"):
        pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"]).to_csv(FILE_LAST_PLAN, index=False)
        st.rerun()
    
    st.divider()
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_v = df[df['Nome'] == a]['Auto'].values[0]
            if auto_v:
                comp = df[(df['Auto'] == auto_v) & (~df['Nome'].isin(assenti))]
                if not comp.empty: st.warning(f"⚠️ {a} assente. Controlla: {', '.join(comp['Nome'].tolist())}")

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

    if st.button("🚀 GENERA E CONGELA"):
        pd.DataFrame(current_in).to_csv(FILE_LAST_PLAN, index=False)
        conf_df = pd.read_csv(FILE_CONFIG)
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
