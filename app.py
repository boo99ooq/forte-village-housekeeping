import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Executive Housekeeping - Master", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

# --- CARICAMENTO DATI ---
def load_data():
    cols = ["Nome", "Ruolo", "Professionalita", "Zone_Padronanza"]
    if os.path.exists(FILE_DATA):
        try:
            df_temp = pd.read_csv(FILE_DATA)
            if df_temp.empty or 'Nome' not in df_temp.columns:
                return pd.DataFrame(columns=cols)
            for col in df_temp.columns:
                df_temp[col] = df_temp[col].fillna("").astype(str).str.strip()
            return df_temp
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def load_hotels():
    # Aggiunto "Cala del Forte" e "Spazi Comuni"
    return ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Gestione Staff")
    if not df.empty:
        st.download_button("📥 Backup Staff", data=df.to_csv(index=False).encode('utf-8'), file_name='backup_staff.csv')
    
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    dati = {}
    nome_edit = None
    
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("staff_form"):
        n_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome e Cognome")
        is_gov = st.checkbox("Governante", value=(str(dati.get('Ruolo','')).lower() == "governante"))
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5)))
        z_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        
        if is_gov:
            st.info("Assegnazione Fissa")
            sel_z = st.multiselect("Destinazione:", lista_hotel, default=[h for h in z_at if h in lista_hotel])
            z_ass = ", ".join(sel_z)
        else:
            st.write("**Zone Padronanza**")
            sel_z = [h for h in lista_hotel if st.checkbox(h, key=f"s_{h}", value=(h in z_at))]
            z_ass = ", ".join(sel_z)

        if st.form_submit_button("SALVA SCHEDA"):
            if n_in:
                new = {"Nome": n_in.strip(), "Ruolo": "Governante" if is_gov else "Cameriera", "Professionalita": prof, "Zone_Padronanza": z_ass}
                if modo == "Modifica Esistente": df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Resort"])

with t1:
    if not df.empty:
        st.dataframe(df[['Nome', 'Ruolo', 'Zone_Padronanza', 'Professionalita']], use_container_width=True)

with t2:
    st.header("⚙️ Griglia Tempi Standard")
    if os.path.exists(FILE_CONFIG):
        c_df = pd.read_csv(FILE_CONFIG)
    else:
        c_df = pd.DataFrame([{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in lista_hotel])

    new_config = []
    h_c = st.columns([2, 1, 1, 1, 1])
    for i, txt in enumerate(["DESTINAZIONE", "Arr. I", "Fer. I", "Arr. G", "Fer. G"]): h_c[i].caption(txt)

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
        st.success("Configurazione aggiornata!")

with t3:
    st.header("🚀 Piano Operativo Resort")
    if os.path.exists(FILE_LAST_PLAN):
        lp_df = pd.read_csv(FILE_LAST_PLAN)
    else:
        lp_df = pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"])

    personale_assente = st.multiselect("🏖️ Assenze oggi:", sorted(df['Nome'].tolist()))
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

    c1, c2 = st.columns(2)
    if c1.button("🚀 GENERA E CONGELA"):
        pd.DataFrame(current_input).to_csv(FILE_LAST_PLAN, index=False)
        if os.path.exists(FILE_CONFIG):
            conf_df = pd.read_csv(FILE_CONFIG)
            risultati = []
            df_attive = df[~df['Nome'].isin(personale_assente)].copy()
            già_assegnate = []
            
            for row in current_input:
                h_c = conf_df[conf_df['Hotel'] == row['Hotel']].iloc[0]
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

    if c2.button("🧹 RESET"):
        if os.path.exists(FILE_LAST_PLAN): os.remove(FILE_LAST_PLAN)
        st.rerun()
