import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Housekeeping Resort - Live Sheets", layout="wide")

# --- CONFIGURAZIONE GOOGLE SHEETS ---
# Incolla qui l'URL del tuo foglio Google (quello che ottieni cliccando 'Condividi')
SHEET_URL = "https://docs.google.com/spreadsheets/d/1KRQ_jfd60uy80l7p44brg08MVfA93LScV2P3X9Mx8bY/edit?usp=sharing"
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

# Funzione per convertire l'URL di condivisione in URL di esportazione CSV
def get_csv_url(url):
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    except:
        return None

@st.cache_data(ttl=10) # Aggiorna i dati ogni 10 secondi se ricarichi
def load_data_from_gsheets():
    csv_url = get_csv_url(SHEET_URL)
    if not csv_url:
        st.error("URL di Google Sheets non valido.")
        return pd.DataFrame()
    try:
        df_temp = pd.read_csv(csv_url)
        # Pulizia dati
        for col in df_temp.columns:
            df_temp[col] = df_temp[col].fillna("").astype(str).str.strip()
        return df_temp
    except Exception as e:
        st.error(f"Impossibile leggere Google Sheets: {e}")
        return pd.DataFrame()

def load_hotels():
    return [
        "Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", 
        "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta",
        "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"
    ]

# Caricamento Staff Live
df = load_data_from_gsheets()
lista_hotel = load_hotels()

# --- INTERFACCIA ---
st.title("🚀 Sistema Housekeeping Live")
st.info("I dati dello staff vengono letti in tempo reale dal tuo Foglio Google.")

t1, t2, t3 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Resort"])

# --- TAB 1: STAFF ---
with t1:
    if not df.empty:
        c1, c2 = st.columns(2)
        n_gov = len(df[df['Ruolo'].str.lower() == "governante"])
        n_cam = len(df[df['Ruolo'].str.lower() == "cameriera"])
        c1.metric("Governanti", n_gov)
        c2.metric("Cameriere", n_cam)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Incolla l'URL del foglio Google nel codice per vedere lo staff.")

# --- TAB 2: CONFIGURAZIONE TEMPI ---
with t2:
    st.header("⚙️ Griglia Tempi Standard")
    if os.path.exists(FILE_CONFIG):
        c_df = pd.read_csv(FILE_CONFIG)
    else:
        c_df = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])

    new_config = []
    h_c = st.columns([2, 1, 1, 1, 1])
    for i, txt in enumerate(["ZONA", "Arr. I", "Fer. I", "Arr. G", "Fer. G"]): h_c[i].caption(txt)

    for h in lista_hotel:
        row_exist = c_df[c_df['Hotel'] == h]
        vals = [int(row_exist.iloc[0][k]) if not row_exist.empty else d for k, d in zip(['Arr_Ind','Fer_Ind','Arr_Gru','Fer_Gru'], [60,30,45,20])]
        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].markdown(f"**{h}**")
        ai = cols[1].number_input("", 5, 240, vals[0], key=f"c_ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("", 5, 240, vals[1], key=f"c_fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("", 5, 240, vals[2], key=f"c_ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("", 5, 240, vals[3], key=f"c_fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})

    if st.button("💾 CONGELA TEMPI"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Tempi salvati!")

# --- TAB 3: PLANNING ---
with t3:
    st.header("🚀 Planning Resort")
    if os.path.exists(FILE_LAST_PLAN):
        lp_df = pd.read_csv(FILE_LAST_PLAN)
    else:
        lp_df = pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"])

    # Gestione Assenze
    nomi_staff = sorted(df['Nome'].tolist()) if not df.empty else []
    personale_assente = st.multiselect("🏖️ Seleziona chi è assente oggi:", nomi_staff)
    
    st.divider()
    
    current_input = []
    h_p = st.columns([2, 1, 1, 1, 1, 1, 1])
    for i, t in enumerate(["ZONA", "Arr.I", "Fer.I", "Vuo.I", "Arr.G", "Fer.G", "Vuo.G"]): h_p[i].caption(t)

    for h in lista_hotel:
        r = lp_df[lp_df['Hotel'] == h]
        vs = [int(r.iloc[0][k]) if not r.empty else 0 for k in ["AI","FI","VI","AG","FG","VG"]]
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        vals_in = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{k}_{h}", label_visibility="collapsed") for i, k in enumerate(["ai","fi","vi","ag","fg","vg"])]
        current_input.append({"Hotel": h, "AI": vals_in[0], "FI": vals_in[1], "VI": vals_in[2], "AG": vals_in[3], "FG": vals_in[4], "VG": vals_in[5]})

    if st.button("🚀 GENERA E CONGELA"):
        pd.DataFrame(current_input).to_csv(FILE_LAST_PLAN, index=False)
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            df_attive = df[~df['Nome'].isin(personale_assente)].copy()
            già_assegnate = []
            
            for row in current_input:
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0] if row['Hotel'] in conf_df['Hotel'].values else conf_df.iloc[0]
                row['ore'] = ((row['AI'] + row['VI']) * h_c['Arr_Ind'] + (row['FI'] * h_c['Fer_Ind']) + (row['AG'] + row['VG']) * h_c['Arr_Gru'] + (row['FG'] * h_c['Fer_Gru'])) / 60
            
            for row in sorted(current_input, key=lambda x: x['ore'], reverse=True):
                if row['ore'] > 0:
                    gov = df_attive[(df_attive['Ruolo'].str.lower() == "governante") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    resp = ", ".join(gov['Nome'].tolist()) if not gov.empty else "🚨 Jolly"
                    n_nec = round(row['ore'] / 7) if row['ore'] >= 7 else 1
                    cam = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (df_attive['Zone_Padronanza'].str.contains(row['Hotel'], na=False)) & (~df_attive['Nome'].isin(già_assegnate))]
                    if len(cam) < n_nec:
                        jolly = df_attive[(df_attive['Ruolo'].str.lower() == "cameriera") & (~df_attive['Nome'].isin(già_assegnate)) & (~df_attive['Nome'].isin(cam['Nome']))].sort_values('Professionalita', ascending=False)
                        cam = pd.concat([cam, jolly]).head(n_nec)
                    else: cam = cam.head(n_nec)
                    
                    s_icon = [f"{('📌' if len(str(c['Zone_Padronanza']).split(', ')) == 1 else '🔄')} {c['Nome']}" for _, c in cam.iterrows()]
                    for _, c in cam.iterrows(): già_assegnate.append(c['Nome'])
                    risultati.append({"Zona": row['Hotel'], "Ore": round(row['ore'], 1), "Resp": resp, "Squadra": ", ".join(s_icon)})
            st.table(pd.DataFrame(risultati))
