import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- FILE DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'
FILE_HISTORY = 'storico_planning.csv'

# --- FUNZIONI DI SUPPORTO ---
def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        for col in ['Part_Time', 'Indisp_Spezzato', 'Conteggio_Spezzati', 'Ultimo_Riposo', 'Auto']:
            if col not in df.columns: df[col] = 0
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

# --- SIDEBAR: RIPRISTINATA ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    current = None
    if not df.empty:
        sel = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()))
        if sel != "--- NUOVO ---": current = df[df['Nome'] == sel].iloc[0]

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        
        c_opt = st.columns(2)
        f_pt = c_opt[0].checkbox("🕒 Part-Time", value=True if current is not None and str(current.get('Part_Time', 0)) in ["1", "True"] else False)
        f_indisp = c_opt[1].checkbox("🚫 No Spezzato", value=True if current is not None and str(current.get('Indisp_Spezzato', 0)) in ["1", "True"] else False)
        
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        
        st.write("--- Valutazioni (1-10) ---")
        col1, col2 = st.columns(2)
        f_pro = col1.number_input("Prof.", 0, 10, int(pd.to_numeric(current['Professionalita'], 5)) if current is not None else 5)
        f_esp = col2.number_input("Esp.", 0, 10, int(pd.to_numeric(current['Esperienza'], 5)) if current is not None else 5)
        f_dis = col1.number_input("Disp.", 0, 10, int(pd.to_numeric(current['Disponibilita'], 5)) if current is not None else 5)
        
        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_indisp else 0, "Auto": f_auto, "Zone_Padronanza": f_zone, "Professionalita": f_pro, "Esperienza": f_esp, "Disponibilita": f_dis}
            if current is not None:
                for col in df.columns: 
                    if col not in nuova_d: nuova_d[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df)
            st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    st.subheader("Performance e Stato Staff")
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        df['G_Riposo'] = (datetime.now() - pd.to_datetime(df['Ultimo_Riposo'])).dt.days
        df['Tipo'] = df['Part_Time'].apply(lambda x: "🕒 PT" if str(x) in ["1", "True"] else "FULL")
        
        view_df = df[['Nome', 'Ruolo', 'Tipo', 'Performance', 'G_Riposo', 'Conteggio_Spezzati', 'Auto']].sort_values('G_Riposo', ascending=False)
        st.dataframe(view_df, use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        vs = [60, 30, 45, 20]
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI", 5, 200, vs[0], key=f"ai_{h}")
        fi = cols[2].number_input("FI", 5, 200, vs[1], key=f"fi_{h}")
        ag = cols[3].number_input("AG", 5, 200, vs[2], key=f"ag_{h}")
        fg = cols[4].number_input("FG", 5, 200, vs[3], key=f"fg_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False)
        st.success("Tempi Salvati!")

# ... (Tab 3 Planning e Tab 4 Storico seguono la logica precedente) ...
