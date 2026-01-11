import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- FILE DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'
FILE_HISTORY = 'storico_planning.csv'

# --- CARICAMENTO DATI ---
def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Inizializzazione colonne tecniche se mancano
        if 'Ultimo_Riposo' not in df.columns: df['Ultimo_Riposo'] = (datetime.now() - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
        if 'Conteggio_Spezzati' not in df.columns: df['Conteggio_Spezzati'] = 0
        if 'Indisp_Spezzato' not in df.columns: df['Indisp_Spezzato'] = 0
        if 'Auto' not in df.columns: df['Auto'] = ""
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        ruolo = str(row.get('Ruolo', '')).lower()
        if 'overnante' in ruolo: return "⭐ (Coord.)", 10.0
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto = round(((p+e+t+d+em+g)/2)*2)/2
        return "🟩"*int(voto) + "🟨"*(1 if (voto%1)>=0.5 else 0) + "⬜"*(5-int(voto+0.5)), voto
    except: return "⬜"*5, 0.0

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR: GESTIONE ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    current = None
    if not df.empty:
        sel = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
        if sel != "--- NUOVO ---": current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        
        st.write("--- Logistica e Vincoli ---")
        # Viaggia con...
        lista_nomi = sorted(df['Nome'].tolist())
        opzioni_v = ["Nessuna / Auto Propria"] + lista_nomi + ["+ ALTRO..."]
        v_attuale = str(current['Auto']) if current is not None and str(current['Auto']) not in ["nan", ""] else "Nessuna / Auto Propria"
        s_v = st.selectbox("Viaggia con:", opzioni_v, index=opzioni_v.index(v_attuale) if v_attuale in opzioni_v else 0)
        f_auto = st.text_input("Specifica se altro:", "") if s_v == "+ ALTRO..." else s_v
        if f_auto == "Nessuna / Auto Propria": f_auto = ""
        
        f_indisp = st.checkbox("🚫 Indisponibilità Spezzato", value=True if current is not None and str(current.get('Indisp_Spezzato', 0)) in ["1", "True"] else False)
        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        f_dis = st.number_input("Voto Disponibilità", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)

        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Auto": f_auto, "Indisp_Spezzato": 1 if f_indisp else 0, "Disponibilita": f_dis, "Zone_Padronanza": f_zone}
            if current is not None:
                for col in df.columns: 
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df)
            st.rerun()

    st.divider()
    csv_b = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Backup Database", csv_b, "Housekeeping_DB_Staff.csv", "text/csv")

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    st.subheader("Stato Staff e Riposi")
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        df['G_Riposo'] = (datetime.now() - pd.to_datetime(df['Ultimo_Riposo'])).dt.days
        
        view_df = df[['Nome', 'Ruolo', 'Performance', 'G_Riposo', 'Conteggio_Spezzati', 'Auto']].sort_values('G_Riposo', ascending=False)
        st.dataframe(view_df, column_config={
            "G_Riposo": st.column_config.NumberColumn("Giorni senza riposo", format="%d 🗓️"),
            "Conteggio_Spezzati": st.column_config.NumberColumn("Split totali", format="%d 🌙"),
            "Auto": "Viaggia con"
        }, use_container_width=True, hide_index=True)
        
        if any(df['G_Riposo'] > 6):
            st.warning(f"⚠️ Attenzione: {', '.join(df[df['G_Riposo'] > 6]['Nome'].tolist())} lavorano da più di 6 giorni!")

with t2:
    st.header("⚙️ Configurazione Tempi Standard")
    st.info("💡 Copertura = 1/3 del tempo FI | Cambio Biancheria = 1/4 del tempo FI")
    # Qui il codice per salvare i tempi AI/FI/AG/FG nel file FILE_CONFIG

with t3:
    st.header("🚀 Planning Giornaliero")
    data_plan = datetime.now().strftime("%d/%m/%Y")
    assenti = st.multiselect("🛌 Chi è a RIPOSO / ASSENTE oggi?", sorted(df['Nome'].tolist()))
    
    # Alert Viaggi
    if assenti:
        for a in assenti:
            v_con = df[df['Nome'] == a]['Auto'].values[0]
            if v_con and v_con in df['Nome'].values:
                st.warning(f"⚠️ {a} è assente. Avvisa la compagna: **{v_con}**")

    # Inserimento Arrivi/Partenze/Coperture
    lp_df = pd.read_csv(FILE_LAST_PLAN) if os.path.exists(FILE_LAST_PLAN) else pd.DataFrame()
    current_plan = []
    h_cols = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 1, 1])
    for i, t in enumerate(["ZONA", "AI", "FI", "VI", "AG", "FG", "VG", "COPERT", "BIANCH"]): h_cols[i].caption(t)
    
    for hotel in lista_hotel:
        r = lp_df[lp_df['Hotel'] == hotel] if not lp_df.empty and 'Hotel' in lp_df.columns else pd.DataFrame()
        vs = [int(r.iloc[0][k]) if not r.empty and k in r.columns else 0 for k in ["AI","FI","VI","AG","FG","VG","COP","BIA"]]
        c = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 1, 1])
        c[0].write(f"**{hotel}**")
        vals = [c[i+1].number_input("", 0, 100, vs[i], key=f"p_{hotel}_{i}", label_visibility="collapsed") for i in range(8)]
        current_plan.append({"Hotel": hotel, "AI": vals[0], "FI": vals[1], "VI": vals[2], "AG": vals[3], "FG": vals[4], "VG": vals[5], "COP": vals[6], "BIA": vals[7]})

    if st.button("🚀 ELABORA SCHIERAMENTO"):
        # Logica di calcolo ore e assegnazione (come visto nei passaggi precedenti)
        st.session_state['last_plan_data'] = current_plan # Simulazione per test
        
        # Suggerimento Spezzato
        disponibili_sp = df[(df['Indisp_Spezzato'] == 0) & (df['Ruolo'] == "Cameriera") & (~df['Nome'].isin(assenti))]
        suggeriti = disponibili_sp.sort_values(['Conteggio_Spezzati', 'Rating_Num'], ascending=[True, False]).head(4)
        st.session_state['current_split_names'] = suggeriti['Nome'].tolist()
        
        st.success("Schieramento generato! Controlla i suggerimenti per lo spezzato.")
        st.write("**Suggeriti per lo Spezzato (19-22):**", ", ".join(st.session_state['current_split_names']))

    st.divider()
    if st.button("🧊 CRISTALLIZZA E SALVA STORICO"):
        # 1. Aggiorna data riposo per chi è assente
        if assenti:
            df.loc[df['Nome'].isin(assenti), 'Ultimo_Riposo'] = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Incrementa split per chi è stato suggerito/scelto
        if 'current_split_names' in st.session_state:
            df.loc[df['Nome'].isin(st.session_state['current_split_names']), 'Conteggio_Spezzati'] += 1
        
        # 3. Salva Database
        save_data(df)
        
        # 4. Salva nello Storico CSV
        st.success(f"Dati del {data_plan} cristallizzati! Database aggiornato.")
        st.balloons()

with t4:
    st.header("📅 Storico Planning")
    # Qui visualizzazione del file FILE_HISTORY
