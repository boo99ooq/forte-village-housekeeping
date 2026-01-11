import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Import di sicurezza per ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    PDF_OK = True
except ImportError:
    PDF_OK = False

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HISTORY = 'storico_planning.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Inizializzazione colonne mancanti
        cols = ['Nome', 'Ruolo', 'Part_Time', 'Indisp_Spezzato', 'Conteggio_Spezzati', 
                'Ultimo_Riposo', 'Zone_Padronanza', 'Auto', 'Professionalita', 
                'Esperienza', 'Tenuta_Fisica', 'Disponibilita', 'Empatia', 'Capacita_Guida']
        for c in cols:
            if c not in df.columns: df[c] = 5
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        ruolo = str(row.get('Ruolo', '')).lower()
        if 'overnante' in ruolo: return "⭐ (Coord.)", 10.0
        p = pd.to_numeric(row.get('Professionalita', 5)) * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5)) * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5)) * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5)) * 0.15
        em = pd.to_numeric(row.get('Empatia', 5)) * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5)) * 0.10
        voto = round(((p+e+t+d+em+g)/2)*2)/2
        return "🟩"*int(voto) + "🟨"*(1 if (voto%1)>=0.5 else 0) + "⬜"*(5-int(voto+0.5)), voto
    except: return "⬜"*5, 0.0

# --- PDF GENERATOR ---
def genera_pdf(data_str, schieramento, split_list):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    y = h - 100
    for res in schieramento:
        if y < 120: p.showPage(); y = h - 70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    y -= 20; p.line(50, y, 540, y); p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y - 30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11); p.drawString(60, y - 50, f"Personale: {', '.join(split_list) if split_list else 'Nessuna'}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR COMPLETA ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    sel = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + sorted(df['Nome'].tolist()) if not df.empty else ["--- NUOVO ---"])
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if not current or "Cameriera" in str(current['Ruolo']) else 1)
        
        c_opt = st.columns(2)
        f_pt = c_opt[0].checkbox("🕒 Part-Time", value=bool(current['Part_Time']) if current is not None else False)
        f_indisp = c_opt[1].checkbox("🚫 No Spezzato", value=bool(current['Indisp_Spezzato']) if current is not None else False)
        
        f_auto = st.text_input("Viaggia con...", value=str(current['Auto']) if current is not None else "")
        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        
        st.write("**Valutazioni (1-10)**")
        col1, col2 = st.columns(2)
        v_pro = col1.number_input("Prof.", 1, 10, int(current['Professionalita']) if current is not None else 5)
        v_esp = col2.number_input("Esp.", 1, 10, int(current['Esperienza']) if current is not None else 5)
        v_ten = col1.number_input("Tenuta Fis.", 1, 10, int(current['Tenuta_Fisica']) if current is not None else 5)
        v_dis = col2.number_input("Disp.", 1, 10, int(current['Disponibilita']) if current is not None else 5)
        v_emp = col1.number_input("Empatia", 1, 10, int(current['Empatia']) if current is not None else 5)
        v_gui = col2.number_input("Guida", 1, 10, int(current['Capacita_Guida']) if current is not None else 5)

        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_indisp else 0, 
                       "Auto": f_auto, "Zone_Padronanza": f_zone, "Professionalita": v_pro, "Esperienza": v_esp, 
                       "Tenuta_Fisica": v_ten, "Disponibilita": v_dis, "Empatia": v_emp, "Capacita_Guida": v_gui}
            if current is not None: df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    st.subheader("Performance Staff")
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        df['G_Riposo'] = (datetime.now() - pd.to_datetime(df['Ultimo_Riposo'].replace(0, datetime.now()))).dt.days
        df['Tipo'] = df['Part_Time'].apply(lambda x: "🕒 PT" if x == 1 else "FULL")
        st.dataframe(df[['Nome', 'Ruolo', 'Tipo', 'Performance', 'G_Riposo', 'Conteggio_Spezzati', 'Auto']].sort_values('G_Riposo', ascending=False), use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    h_cols = st.columns([2, 1, 1, 1, 1])
    h_cols[0].write("**Hotel**"); h_cols[1].caption("AI (min)"); h_cols[2].caption("FI (min)"); h_cols[3].caption("AG (min)"); h_cols[4].caption("FG (min)")
    for h in lista_hotel:
        vs = [60, 30, 45, 20] 
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("", 5, 200, vs[0], key=f"t_ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("", 5, 200, vs[1], key=f"t_fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("", 5, 200, vs[2], key=f"t_ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("", 5, 200, vs[3], key=f"t_fg_{h}", label_visibility="collapsed")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 SALVA TEMPI"): pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Tempi Salvati!")

with t3:
    st.header("🚀 Elaborazione Planning")
    data_p = st.date_input("Planning per il giorno:", datetime.now())
    assenti = st.multiselect("🛌 Chi è in RIPOSO oggi?", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    st.write("### 📊 Inserimento Camere")
    cur_inp = []
    for h in lista_hotel:
        c = st.columns([2, 0.8, 0.8, 0.8, 0.8])
        c[0].write(f"**{h}**")
        ai = c[1].number_input("AI", 0, 100, 0, key=f"p_ai_{h}")
        fi = c[2].number_input("FI", 0, 100, 0, key=f"p_fi_{h}")
        cop = c[3].number_input("COP", 0, 100, 0, key=f"p_cop_{h}")
        bia = c[4].number_input("BIA", 0, 100, 0, key=f"p_bia_{h}")
        cur_inp.append({"Hotel": h, "AI": ai, "FI": fi, "COP": cop, "BIA": bia})

    if st.button("🚀 GENERA E VERIFICA"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)]
        nomi_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)].sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        risultati = []
        for inp in cur_inp:
            if (inp['AI'] + inp['FI'] + inp['COP'] + inp['BIA']) > 0:
                t = conf_df[conf_df['Hotel'] == inp['Hotel']].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30}
                ore_nec = (inp['AI']*t['Arr_Ind'] + inp['FI']*t['Fer_Ind'] + inp['COP']*(t['Fer_Ind']/3) + inp['BIA']*(t['Fer_Ind']/4)) / 60
                
                # Assegnazione automatica (basata su padronanza zona)
                team = attive[attive['Zone_Padronanza'].str.contains(inp['Hotel']) & (~attive['Nome'].isin(nomi_split))].head(2)['Nome'].tolist()
                
                ore_fornite = sum([5.0 if (attive[attive['Nome'] == n].iloc[0]['Part_Time'] == 1 or n in nomi_split) else 7.5 for n in team])
                diff = ore_fornite - ore_nec
                
                if diff < 0: st.error(f"⚠️ **{inp['Hotel']}**: Mancano {abs(round(diff,1))}h! (Servono {round(ore_nec,1)}h, team fornisce {ore_fornite}h)")
                else: st.success(f"✅ **{inp['Hotel']}**: Coperto ({ore_fornite}h fornite)")
                
                risultati.append({"Hotel": inp['Hotel'], "Team": ", ".join(team), "Responsabile": "Governante"})
        
        st.session_state['res'] = risultati
        st.session_state['spl'] = nomi_split

    if 'res' in st.session_state:
        st.divider()
        st.table(pd.DataFrame(st.session_state['res']))
        st.info(f"🌙 **Spezzato:** {', '.join(st.session_state['spl'])}")
        if PDF_OK:
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), st.session_state['res'], st.session_state['spl'])
            st.download_button("📥 SCARICA PDF", pdf, "Planning.pdf", "application/pdf")
        
        if st.button("🧊 CRISTALLIZZA E SALVA STORICO"):
            df.loc[df['Nome'].isin(assenti), 'Ultimo_Riposo'] = data_p.strftime("%Y-%m-%d")
            df.loc[df['Nome'].isin(st.session_state['spl']), 'Conteggio_Spezzati'] += 1
            save_data(df); st.success("Dati Cristallizzati!"); st.balloons()
