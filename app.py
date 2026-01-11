import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- CONFIGURAZIONE PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    PDF_OK = True
except ImportError:
    PDF_OK = False

st.set_page_config(page_title="Forte Village Housekeeping", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        # Assicuriamoci che tutte le colonne esistano
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
        v = (pd.to_numeric(row.get('Professionalita', 5))*0.25 + pd.to_numeric(row.get('Esperienza', 5))*0.20 + 
             pd.to_numeric(row.get('Tenuta_Fisica', 5))*0.20 + pd.to_numeric(row.get('Disponibilita', 5))*0.15 + 
             pd.to_numeric(row.get('Empatia', 5))*0.10 + pd.to_numeric(row.get('Capacita_Guida', 5))*0.10)
        voto = round((v/2)*2)/2
        return "🟩"*int(voto) + "🟨"*(1 if (voto%1)>=0.5 else 0) + "⬜"*(5-int(voto+0.5)), voto
    except: return "⬜"*5, 0.0

def genera_pdf(data_str, schieramento, split_list, lista_assenti):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h-50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h-60, 540, h-60)
    y = h-85
    if lista_assenti:
        p.setFont("Helvetica-Bold", 10); p.setFillColorRGB(0.7, 0, 0)
        p.drawString(50, y, f"🛌 ASSENTI/RIPOSI: {', '.join(lista_assenti)}")
        y -= 25; p.setFillColorRGB(0,0,0)
    for res in schieramento:
        if y < 100: p.showPage(); y = h-70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    y -= 20; p.line(50, y, 540, y); p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y-30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11); p.drawString(60, y-50, f"Personale: {', '.join(split_list)}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_nome = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + nomi_db)
    
    # Reset variabili per evitare ValueError
    curr = None
    if sel_nome != "--- NUOVO ---":
        match = df[df['Nome'] == sel_nome]
        if not match.empty:
            curr = match.iloc[0]

    with st.form("form_sidebar_fixed"):
        f_n = st.text_input("Nome", value=str(curr['Nome']) if curr is not None else "")
        # Correzione Index: usiamo una variabile sicura
        idx_r = 1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0
        f_r = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=idx_r)
        
        c1, c2 = st.columns(2)
        f_pt = c1.checkbox("🕒 Part-Time", value=bool(curr['Part_Time']) if curr is not None else False)
        f_is = c2.checkbox("🚫 No Spezzato", value=bool(curr['Indisp_Spezzato']) if curr is not None else False)
        
        f_au = st.selectbox("Viaggia con...", ["Nessuno"] + [n for n in nomi_db if n != f_n])
        
        idx_z = 0
        if curr is not None and str(curr['Zone_Padronanza']) in lista_hotel:
            idx_z = lista_hotel.index(str(curr['Zone_Padronanza']))
        f_zn = st.selectbox("Zona Padronanza", lista_hotel, index=idx_z)
        
        if st.form_submit_button("💾 SALVA"):
            nuova = {"Nome": f_n, "Ruolo": f_r, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_is else 0, 
                     "Auto": f_au, "Zone_Padronanza": f_zn, "Conteggio_Spezzati": curr['Conteggio_Spezzati'] if curr is not None else 0}
            if curr is not None: df = df[df['Nome'] != sel_nome]
            df = pd.concat([df, pd.DataFrame([nuova])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'Conteggio_Spezzati', 'Auto', 'Zone_Padronanza']], use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        cols = st.columns([2,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI (min)", 5, 120, 60, key=f"t_ai_{h}")
        fi = cols[2].number_input("FI (min)", 5, 120, 30, key=f"t_fi_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Salvati!")

with t3:
    st.header("🚀 Planning")
    data_p = st.date_input("Data:", datetime.now(), key="d_p_final")
    assenti = st.multiselect("🛌 Assenti/Riposi:", nomi_db, key="ass_final")
    
    cur_inp = {}
    st.columns([2,1,1,1,1])[0].write("**Hotel**")
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        p_ai = r[1].number_input("AI", 0, 100, 0, key=f"z_ai_{h}", label_visibility="collapsed")
        p_fi = r[2].number_input("FI", 0, 100, 0, key=f"z_fi_{h}", label_visibility="collapsed")
        p_co = r[3].number_input("COP", 0, 100, 0, key=f"z_co_{h}", label_visibility="collapsed")
        p_bi = r[4].number_input("BIA", 0, 100, 0, key=f"z_bi_{h}", label_visibility="collapsed")
        cur_inp[h] = {"AI": p_ai, "FI": p_fi, "COP": p_co, "BIA": p_bi}

    if st.button("🚀 GENERA SCHIERAMENTO"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # 1. Spezzati
        pool_spl = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0) & (attive['Ruolo'] == 'Cameriera')].sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        # 2. Logica Zone
        fabb = {}
        for h in lista_hotel:
            t = conf_df[conf_df['Hotel'] == h].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30}
            fabb[h] = (cur_inp[h]["AI"]*t["Arr_Ind"] + cur_inp[h]["FI"]*t["Fer_Ind"] + cur_inp[h]["COP"]*(t["Fer_Ind"]/3) + cur_inp[h]["BIA"]*(t["Fer_Ind"]/4)) / 60
        
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        zone_p = [h for h in lista_hotel if h not in ["Le Palme", "Hotel Castello Garden"]] + ["MACRO: PALME & GARDEN"]
        
        gia_a, ris = [], []
        for zona in zone_p:
            o_n = fabb.get(zona, 0)
            t_h, o_f = [], 0
            
            # Gov flessibile
            gov = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_a)) & 
                         (attive['Zone_Padronanza'].apply(lambda x: str(x).lower() in zona.lower() or zona.lower() in str(x).lower()))]
            for _, g in gov.iterrows():
                t_h.append(f"⭐ {g['Nome']} (Gov.)"); gia_a.append(g['Nome'])

            # Cameriere
            if o_n > 0:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                cand['Pr'] = cand['Zone_Padronanza'].apply(lambda x: 0 if (str(x).lower() in zona.lower() or zona.lower() in str(x).lower()) else 1)
                cand = cand.sort_values(['Pr', 'Rating_Num'], ascending=[True, False])
                for _, p in cand.iterrows():
                    if o_f < o_n:
                        t_h.append(p['Nome']); gia_a.append(p['Nome'])
                        o_f += 5.0 if (p['Part_Time'] == 1 or p['Nome'] in pool_spl) else 7.5
                    else: break
            if t_h: ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Ore": round(o_n, 1)})
        
        st.session_state['r_f'] = ris; st.session_state['s_f'] = pool_spl; st.session_state['l_f'] = list(set(attive[attive['Ruolo']=='Cameriera']['Nome']) - set(gia_a))

    if 'r_f' in st.session_state:
        st.divider()
        final_l = []
        for i, r in enumerate(st.session_state['r_f']):
            with st.expander(f"📍 {r['Hotel']} ({r['Ore']}h)"):
                cur_t = [n.strip() for n in r['Team'].split(",")]
                opts = sorted(list(set(cur_t) | set(st.session_state['l_f'])))
                edt = st.multiselect(f"Team {r['Hotel']}", opts, default=cur_t, key=f"f_ed_{i}")
                final_l.append({"Hotel": r['Hotel'], "Team": ", ".join(edt)})
        
        if st.button("🧊 SALVA E SCARICA PDF"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_l, st.session_state['s_f'], assenti)
            st.download_button("📥 DOWNLOAD", pdf, "Planning.pdf", "application/pdf")
