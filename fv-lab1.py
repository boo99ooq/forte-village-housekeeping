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

# --- DATABASE E CONFIG ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
lista_hotel = [
    "Hotel Castello", "Hotel Castello Garden", "Hotel Castello 4 Piano", 
    "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", 
    "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"
]

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        if 'overnante' in str(row.get('Ruolo', '')).lower(): return "⭐ (Coord.)", 10.0
        v = (pd.to_numeric(row.get('Professionalita', 5))*0.5 + pd.to_numeric(row.get('Esperienza', 5))*0.5)
        voto = round((v/2)*2)/2
        return "🟩"*int(voto) + "⬜"*(5-int(voto)), voto
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

    # --- ORDINAMENTO PERSONALIZZATO ---
    ordine_pref = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"]
    mappa_res = {r['Hotel']: r for r in schieramento}
    final_ordered = []
    for pref in ordine_pref:
        if pref in mappa_res: final_ordered.append(mappa_res[pref])
    for r in schieramento:
        if r['Hotel'] not in ordine_pref: final_ordered.append(r)

    for res in final_ordered:
        if y < 100: p.showPage(); y = h-70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    
    y -= 20; p.line(50, y, 540, y); p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y-30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11); p.drawString(60, y-50, f"Personale: {', '.join(split_list) if split_list else 'Nessuno'}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()

# --- SIDEBAR (MULTI-ZONA) ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_nome = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + nomi_db)
    curr = df[df['Nome'] == sel_nome].iloc[0] if sel_nome != "--- NUOVO ---" else None

    with st.form("form_v8"):
        f_n = st.text_input("Nome", value=str(curr['Nome']) if curr is not None else "")
        f_r = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        
        # Multi-selezione per le zone
        z_attuali = [z.strip() for z in str(curr['Zone_Padronanza']).split(",")] if curr is not None else []
        f_zn = st.multiselect("Zone di Padronanza", lista_hotel, default=[z for z in z_attuali if z in lista_hotel])
        
        f_pt = st.checkbox("🕒 Part-Time", value=bool(curr['Part_Time']) if curr is not None else False)
        
        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova = {"Nome": f_n, "Ruolo": f_r, "Zone_Padronanza": ", ".join(f_zn), "Part_Time": 1 if f_pt else 0, "Conteggio_Spezzati": 0}
            if curr is not None: df = df[df['Nome'] != sel_nome]
            df = pd.concat([df, pd.DataFrame([nuova])], ignore_index=True)
            save_data(df); st.rerun()

# --- TAB ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.header("🏆 Performance Staff")
    if not df.empty:
        filtro_z = st.selectbox("🔍 Filtra per Zona:", ["TUTTI"] + lista_hotel)
        df_d = df.copy()
        df_d[['Performance', 'Rating_Num']] = df_d.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        if filtro_z != "TUTTI":
            df_d = df_d[df_d['Zone_Padronanza'].str.contains(filtro_z, na=False)]
        st.dataframe(df_d[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza']], use_container_width=True, hide_index=True)

with t3:
    st.header("🚀 Elaborazione Planning")
    col_d, col_a = st.columns([1, 2])
    data_p = col_d.date_input("Data Planning:", datetime.now(), key="date_p_final_v10")
    assenti = col_a.multiselect("🛌 Assenti/Riposi:", nomi_db, key="ass_p_final_v10")
    
    st.write("### 📊 Inserimento Carico Lavoro")
    cur_inp = {}
    h_col = st.columns([2, 1, 1, 1, 1])
    h_col[0].write("**Hotel**"); h_col[1].write("AI"); h_col[2].write("FI"); h_col[3].write("COP"); h_col[4].write("BIA")
    
    for h in lista_hotel:
        row_c = st.columns([2, 1, 1, 1, 1])
        row_c[0].write(f"**{h}**")
        p_ai = row_c[1].number_input("", 0, 100, 0, key=f"v10_ai_{h}", label_visibility="collapsed")
        p_fi = row_c[2].number_input("", 0, 100, 0, key=f"v10_fi_{h}", label_visibility="collapsed")
        p_co = row_c[3].number_input("", 0, 100, 0, key=f"v10_co_{h}", label_visibility="collapsed")
        p_bi = row_c[4].number_input("", 0, 100, 0, key=f"v10_bi_{h}", label_visibility="collapsed")
        cur_inp[h] = {"AI": p_ai, "FI": p_fi, "COP": p_co, "BIA": p_bi}

    if st.button("🚀 GENERA SCHIERAMENTO", key="btn_v10_genera"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # 1. Identificazione 4 Spezzati (Cameriere FT che hanno dato disponibilità)
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        
        # 2. Calcolo Fabbisogni Orari
        fabb = {}
        for h in lista_hotel:
            t_row = conf_df[conf_df['Hotel'] == h] if not conf_df.empty else pd.DataFrame()
            m_ai, m_fi = (t_row.iloc[0]['Arr_Ind'], t_row.iloc[0]['Fer_Ind']) if not t_row.empty else (60, 30)
            # Calcolo ore: (AI*tempo + FI*tempo + Extra) / 60
            fabb[h] = (cur_inp[h]["AI"]*m_ai + cur_inp[h]["FI"]*m_fi + cur_inp[h]["COP"]*(m_fi/3) + cur_inp[h]["BIA"]*(m_fi/4)) / 60
        
        # Macro Zona
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        zone_ordine = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + \
                      [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_ass, ris = [], []
        
        for zona in zone_ordine:
            o_nec = fabb.get(zona, 0)
            team_h, o_fatti = [], 0
            
            # --- ASSEGNAZIONE GOVERNANTI (Sibilla, Lavinia, Febe, ecc.) ---
            govs = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_ass))]
            mask_g = govs['Zone_Padronanza'].str.contains(zona.replace("Hotel ", ""), case=False, na=False)
            for _, g in govs[mask_g].iterrows():
                team_h.append(f"⭐ {g['Nome']} (Gov.)")
                gia_ass.append(g['Nome'])

            # --- ASSEGNAZIONE CAMERIERE ---
            if o_nec > 0 or zona in ["Hotel Castello", "Hotel Castello 4 Piano"]:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_ass))].copy()
                # Priorità a chi ha la zona in padronanza
                cand['Prio'] = cand['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                cand = cand.sort_values(['Prio'], ascending=True)
                
                for _, p in cand.iterrows():
                    if o_fatti < (o_nec if o_nec > 0 else 7.5): # Garantisce almeno una persona se zona importante
                        team_h.append(p['Nome'])
                        gia_ass.append(p['Nome'])
                        o_fatti += 5.0 if (p['Part_Time'] == 1 or p['Nome'] in pool_spl) else 7.5
                    else:
                        break
            
            if team_h:
                ris.append({"Hotel": zona, "Team": ", ".join(team_h), "Ore": round(o_nec, 1)})
        
        st.session_state['v10_res'] = ris
        st.session_state['v10_spl'] = pool_spl
        st.session_state['v10_libere'] = list(set(attive[attive['Ruolo']=='Cameriera']['Nome']) - set(gia_ass))

    # --- MOSTRA RISULTATI ---
    if 'v10_res' in st.session_state:
        st.divider()
        final_list = []
        for i, r in enumerate(st.session_state['v10_res']):
            with st.expander(f"📍 {r['Hotel']} (Fabbisogno: {r['Ore']}h)"):
                current_team = [n.strip() for n in r['Team'].split(",")]
                opzioni = sorted(list(set(current_team) | set(st.session_state['v10_libere'])))
                edit_team = st.multiselect(f"Staff {r['Hotel']}", opzioni, default=current_team, key=f"edit_v10_{i}")
                final_list.append({"Hotel": r['Hotel'], "Team": ", ".join(edit_team)})
        
        if st.button("🧊 CONFERMA E SCARICA PDF", key="btn_v10_pdf"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, st.session_state['v10_spl'], assenti)
            st.download_button("📥 DOWNLOAD PDF", pdf, f"Planning_{data_p}.pdf", "application/pdf")
