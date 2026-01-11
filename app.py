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

@st.cache_data(ttl=5)
def load_data():
    url = get_csv_url(SHEET_URL)
    try:
        df_temp = pd.read_csv(url)
        # Pulizia intestazioni (rimuove spazi invisibili)
        df_temp.columns = [c.strip() for c in df_temp.columns]
        for col in df_temp.columns:
            df_temp[col] = df_temp[col].fillna("").astype(str).str.strip()
        return df_temp
    except: return pd.DataFrame()

def load_hotels():
    return ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR: RICERCA E TRASPORTI ---
with st.sidebar:
    st.header("📋 Pannello Controllo")
    st.markdown(f"[📂 Vai al Foglio Google]({SHEET_URL})")
    st.divider()
    
    if not df.empty:
        st.subheader("🔍 Ricerca Rapida")
        cerca = st.text_input("Nome dipendente:")
        if cerca:
            res = df[df['Nome'].str.contains(cerca, case=False)]
            if not res.empty:
                p = res.iloc[0]
                st.write(f"**Ruolo:** {p.get('Ruolo', 'N/D')}")
                st.write(f"**Zone:** {p.get('Zone_Padronanza', 'N/D')}")
                if 'Auto' in df.columns:
                    st.warning(f"🚗 Viaggia con: {p.get('Auto', 'Non specificato')}")
            else:
                st.error("Nessun risultato")
        
        st.divider()
        st.info("💡 L'app legge tutte le nuove colonne (Pendolare, Turno Spezzato, ecc.) ma usa solo quelle necessarie per il planning.")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Operativo"])

# TAB 1: DASHBOARD
with t1:
    if df.empty:
        st.error("Dati non trovati. Controlla il link Google Sheets.")
    else:
        st.subheader("Database Completo Staff")
        # Visualizziamo tutto il database per controllo
        st.dataframe(df, use_container_width=True, hide_index=True)

# TAB 2: CONFIGURAZIONE (Tempi)
with t2:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])
    new_config = []
    h_c = st.columns([2, 1, 1, 1, 1])
    for i, t in enumerate(["ZONA", "Arr. I", "Fer. I", "Arr. G", "Fer. G"]): h_c[i].caption(t)
    for h in lista_hotel:
        r = c_df[c_df['Hotel'] == h] if not c_df.empty and 'Hotel' in c_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty else d for k, d in zip(['Arr_Ind','Fer_Ind','Arr_Gru','Fer_Gru'], [60,30,45,20])]
        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].markdown(f"**{h}**")
        ai = cols[1].number_input("", 5, 240, vs[0], key=f"c_ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("", 5, 240, vs[1], key=f"c_fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("", 5, 240, vs[2], key=f"c_ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("", 5, 240, vs[3], key=f"c_fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 SALVA TEMPI"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Configurazione salvata!")

# TAB 3: PLANNING (Con Logica Auto)
with t3:
    st.header("🚀 Generazione Piano Giornaliero")
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    
    nomi_staff = sorted(df['Nome'].tolist()) if not df.empty else []
    assenti = st.multiselect("🏖️ Personale Assente/Riposo:", nomi_staff)
    
    # ALERT LOGISTICA AUTO
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_info = df[df['Nome'] == a]['Auto'].values[0]
            if auto_info and auto_info != "":
                compagni = df[(df['Auto'] == auto_info) & (~df['Nome'].isin(assenti))]
                if not compagni.empty:
                    st.warning(f"⚠️ **Trasporto:** {a} è assente. Compagni di auto da ricollocare o avvisare: **{', '.join(compagni['Nome'].tolist())}**")

    st.divider()
    
    current_in = []
    h_p = st.columns([2, 1, 1, 1, 1, 1, 1])
    for i, t in enumerate(["ZONA", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]): h_p[i].caption(t)
    for h in lista_hotel:
        r = lp_df[lp_df['Hotel'] == h] if not lp_df.empty and 'Hotel' in lp_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty else 0 for k in ["AI","FI","VI","AG","FG","VG"]]
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        vi = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{k}_{h}", label_visibility="collapsed") for i, k in enumerate(["ai","fi","vi","ag","fg","vg"])]
        current_in.append({"Hotel": h, "AI": vi[0], "FI": vi[1], "VI": vi[2], "AG": vi[3], "FG": vi[4], "VG": vi[5]})

    if st.button("🚀 ELABORA SCHIERAMENTO"):
        pd.DataFrame(current_in).to_csv(FILE_LAST_PLAN, index=False)
        conf_df = pd.read_csv(FILE_CONFIG)
        ris, attive, assegnate = [], df[~df['Nome'].isin(assenti)].copy(), []
        
        # Calcolo Ore
        for row in current_in:
            h_m = conf_df[conf_df['Hotel'] == row['Hotel']]
            if not h_m.empty:
                hc = h_m.iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * hc['Arr_Ind'] + (row['FI'] * hc['Fer_Ind']) + (row['AG'] + row['VG']) * hc['Arr_Gru'] + (row['FG'] * hc['Fer_Gru'])) / 60
            else: row['ore'] = 0

        # Assegnazione
        for row in sorted(current_in, key=lambda x: x['ore'], reverse=True):
            if row['ore'] > 0:
                gov = attive[(attive['Ruolo'].str.contains('overnante', case=False, na=False)) & (attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                resp = ", ".join(gov['Nome'].tolist()) if not gov.empty else "🚨 Jolly"
                
                n_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                cam = attive[(attive['Ruolo'].str.contains('ameriera', case=False, na=False)) & (attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~attive['Nome'].isin(assegnate))]
                
                if len(cam) < n_nec:
                    jolly = attive[(attive['Ruolo'].str.contains('ameriera', case=False, na=False)) & (~attive['Nome'].isin(assegnate)) & (~attive['Nome'].isin(cam['Nome']))].sort_values('Professionalita', ascending=False)
                    cam = pd.concat([cam, jolly]).head(n_nec)
                else: cam = cam.head(n_nec)
                
                s_icon = [f"{('📌' if len(str(c['Zone_Padronanza']).split(', ')) == 1 else '🔄')} {c['Nome']}" for _, c in cam.iterrows()]
                assegnate.extend(cam['Nome'].tolist())
                ris.append({"Zona": row['Hotel'], "Ore": round(row['ore'], 1), "Responsabile": resp, "Squadra": ", ".join(s_icon)})
        
        if ris:
            st.table(pd.DataFrame(ris))
