import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- CONFIGURAZIONE PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    PDF_OK = True
except ImportError:
    PDF_OK = False

st.set_page_config(page_title="Forte Village Housekeeping", layout="wide")

# --- DATABASE ---
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
        cols_default = {
            'Part_Time': 0, 'Jolly': 0, 'Pendolare': 0, 'Riposo_Pref': '',
            'Viaggia_Con': '', 'Lavora_Bene_Con': 'Nessuna', 'Zone_Padronanza': '',
            'Professionalita': 5, 'Esperienza': 5, 'Tenuta_Fisica': 5, 
            'Disponibilita': 5, 'Empatia': 5, 'Capacita_Guida': 5
        }
        for col, val in cols_default.items():
            if col not in df.columns: df[col] = val
        df['Nome'] = df['Nome'].astype(str).str.strip()
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        if 'overnante' in str(row.get('Ruolo', '')).lower(): return "⭐ (Coord.)"
        v = (pd.to_numeric(row.get('Professionalita', 5))*0.25 + pd.to_numeric(row.get('Esperienza', 5))*0.20 + 
             pd.to_numeric(row.get('Tenuta_Fisica', 5))*0.20 + pd.to_numeric(row.get('Disponibilita', 5))*0.15)
        voto = round((v/2)*2)/2
        return "🟩"*int(voto) + ("🟨" if (voto%1)>=0.5 else "")
    except: return "⬜"*5

def pdf_scheda_staff(row):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 20); p.drawString(50, h-50, f"SCHEDA COLLABORATRICE: {row['Nome']}")
    p.line(50, h-60, 540, h-60)
    
    y = h-90
    p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"RUOLO: {row['Ruolo']}")
    y -= 20; p.setFont("Helvetica", 11); p.drawString(50, y, f"Zone Padronanza: {row['Zone_Padronanza']}")
    y -= 30
    
    p.setFont("Helvetica-Bold", 12); p.drawString(50, y, "DETTAGLI OPERATIVI:")
    y -= 20; p.setFont("Helvetica", 11)
    p.drawString(60, y, f"- Part-Time: {'SI' if row['Part_Time'] else 'NO'}")
    p.drawString(200, y, f"- Jolly: {'SI' if row['Jolly'] else 'NO'}")
    y -= 20
    p.drawString(60, y, f"- Pendolare: {'SI' if row['Pendolare'] else 'NO'}")
    p.drawString(200, y, f"- Viaggia con: {row['Viaggia_Con']}")
    y -= 20
    p.drawString(60, y, f"- Partner Preferito: {row['Lavora_Bene_Con']}")
    p.drawString(200, y, f"- Riposo Pref: {row['Riposo_Pref']}")
    
    y -= 40
    p.setFont("Helvetica-Bold", 12); p.drawString(50, y, "VALUTAZIONI (1-10):")
    y -= 20; p.setFont("Helvetica", 11)
    voci = [("Professionalità", 'Professionalita'), ("Esperienza", 'Esperienza'), ("Tenuta Fisica", 'Tenuta_Fisica'), 
            ("Disponibilità", 'Disponibilita'), ("Empatia", 'Empatia'), ("Capacità Guida", 'Capacita_Guida')]
    for label, col in voci:
        p.drawString(60, y, f"{label}: {row[col]}/10")
        y -= 15
        
    p.save(); buffer.seek(0)
    return buffer

def genera_pdf_planning(data_str, schieramento, split_list, lista_assenti):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 18); p.drawString(50, h-50, f"PLANNING - {data_str}")
    p.line(50, h-60, 540, h-60); y = h-85
    if lista_assenti:
        p.setFont("Helvetica-Bold", 10); p.setFillColorRGB(0.7, 0, 0)
        p.drawString(50, y, f"🛌 ASSENTI: {', '.join(lista_assenti)}")
        y -= 25; p.setFillColorRGB(0,0,0)
    for res in schieramento:
        if y < 100: p.showPage(); y = h-70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    p.save(); buffer.seek(0)
    return buffer

df = load_data()
nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []

# --- TABS ---
t_dash, t_staff, t_tempi, t_plan = st.tabs(["🏆 Dashboard", "👥 Anagrafica Staff", "⚙️ Tempi", "🚀 Planning"])

with t_dash:
    st.header("🏆 Performance Staff")
    if not df.empty:
        df_v = df.copy()
        df_v['Rating'] = df_v.apply(get_rating_bar, axis=1)
        df_v['Status'] = df_v.apply(lambda r: ("🃏 " if r['Jolly'] else "") + ("🚌 " if r['Pendolare'] else ""), axis=1)
        st.dataframe(df_v[['Status', 'Nome', 'Ruolo', 'Rating', 'Zone_Padronanza', 'Lavora_Bene_Con']], use_container_width=True, hide_index=True)

with t_staff:
    st.header("📝 Scheda Personale Collaboratrici")
    sel_n = st.selectbox("Seleziona collaboratrice per modificare:", ["--- NUOVA ---"] + nomi_db)
    curr = None
    if sel_n != "--- NUOVA ---":
        match = df[df['Nome'] == sel_n]
        if not match.empty: curr = match.iloc[0]
    
    with st.form("form_staff_definitivo"):
        c1, c2, c3 = st.columns(3)
        f_nome = c1.text_input("Nome e Cognome", value=str(curr['Nome']) if curr is not None else "")
        f_ruolo = c2.selectbox("Ruolo", ["Cameriera", "Governante"], index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        def_padro = [z.strip() for z in str(curr['Zone_Padronanza']).split(",") if z.strip() in lista_hotel] if curr is not None else []
        f_padro = c3.multiselect("Zone di Padronanza", lista_hotel, default=def_padro)
        
        st.divider()
        c4, c5, c6 = st.columns(3)
        with c4:
            f_pt = st.checkbox("🕒 Part-Time", value=bool(curr['Part_Time']) if curr is not None else False)
            f_jol = st.checkbox("🃏 Jolly", value=bool(curr['Jolly']) if curr is not None else False)
            f_pen = st.checkbox("🚌 Pendolare", value=bool(curr['Pendolare']) if curr is not None else False)
        with c5:
            idx_v = nomi_db.index(curr['Viaggia_Con'])+1 if curr is not None and curr['Viaggia_Con'] in nomi_db else 0
            f_via = st.selectbox("🚗 Viaggia con...", ["Nessuna"] + nomi_db, index=idx_v)
            idx_l = nomi_db.index(curr['Lavora_Bene_Con'])+1 if curr is not None and curr['Lavora_Bene_Con'] in nomi_db else 0
            f_lbc = st.selectbox("🤝 Lavora bene con...", ["Nessuna"] + nomi_db, index=idx_l)
        with c6:
            opzioni_r = ["Nessuno", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica", "DATA SPECIFICA"]
            val_rip = str(curr['Riposo_Pref']) if curr is not None else "Nessuno"
            idx_r = opzioni_r.index(val_rip) if val_rip in opzioni_r else (8 if "/" in val_rip else 0)
            f_rip_tipo = st.selectbox("Tipo Riposo", opzioni_r, index=idx_r)
            f_data_s = st.date_input("Calendario", datetime.now(), format="DD/MM/YYYY")
            f_rip_final = f_data_s.strftime("%d/%m/%Y") if f_rip_tipo == "DATA SPECIFICA" else f_rip_tipo

        st.divider()
        v1, v2, v3 = st.columns(3)
        f_prof = v1.slider("Professionalità", 1, 10, int(curr['Professionalita']) if curr is not None else 5)
        f_esp = v2.slider("Esperienza", 1, 10, int(curr['Esperienza']) if curr is not None else 5)
        f_ten = v3.slider("Tenuta Fisica", 1, 10, int(curr['Tenuta_Fisica']) if curr is not None else 5)
        f_dis = v1.slider("Disponibilità", 1, 10, int(curr.get('Disponibilita', 5)) if curr is not None else 5)
        f_emp = v2.slider("Empatia", 1, 10, int(curr.get('Empatia', 5)) if curr is not None else 5)
        f_gui = v3.slider("Capacità Guida", 1, 10, int(curr.get('Capacita_Guida', 5)) if curr is not None else 5)

        if st.form_submit_button("💾 SALVA SCHEDA"):
            if f_nome:
                nuova_r = {
                    "Nome": f_nome.strip(), "Ruolo": f_ruolo, "Zone_Padronanza": ", ".join(f_padro),
                    "Part_Time": 1 if f_pt else 0, "Jolly": 1 if f_jol else 0, "Pendolare": 1 if f_pen else 0,
                    "Riposo_Pref": f_rip_final, "Viaggia_Con": f_via, "Lavora_Bene_Con": f_lbc,
                    "Professionalita": f_prof, "Esperienza": f_esp, "Tenuta_Fisica": f_ten,
                    "Disponibilita": f_dis, "Empatia": f_emp, "Capacita_Guida": f_gui
                }
                df = pd.concat([df[df['Nome'] != (curr['Nome'] if curr is not None else "---")], pd.DataFrame([nuova_r])], ignore_index=True)
                save_data(df); st.success(f"Dati salvati!"); st.rerun()

    if curr is not None:
        if st.button("📄 GENERA PDF SCHEDA"):
            pdf_s = pdf_scheda_staff(curr)
            st.download_button(f"📥 Scarica {curr['Nome']}", pdf_s, f"Scheda_{curr['Nome']}.pdf")

with t_tempi:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        m_ai, m_fi, m_ag, m_fg = 60, 30, 45, 25
        if not c_df.empty:
            tr = c_df[c_df['Hotel'] == h]
            if not tr.empty: m_ai, m_fi, m_ag, m_fg = tr.iloc[0].get('AI', 60), tr.iloc[0].get('FI', 30), tr.iloc[0].get('AG', 45), tr.iloc[0].get('FG', 25)
        v_ai = r[1].number_input("AI", 5, 120, m_ai, key=f"t_ai_{h}", label_visibility="collapsed")
        v_fi = r[2].number_input("FI", 5, 120, m_fi, key=f"t_fi_{h}", label_visibility="collapsed")
        v_ag = r[3].number_input("AG", 5, 120, m_ag, key=f"t_ag_{h}", label_visibility="collapsed")
        v_fg = r[4].number_input("FG", 5, 120, m_fg, key=f"t_fg_{h}", label_visibility="collapsed")
        new_c.append({"Hotel": h, "AI": v_ai, "FI": v_fi, "AG": v_ag, "FG": v_fg})
    if st.button("💾 Salva Tempi"): pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Salvati!")

with t_plan:
    st.header("🚀 Generazione Planning")
    c_d, c_a = st.columns([1, 2])
    data_p = c_d.date_input("Data Planning:", datetime.now(), format="DD/MM/YYYY")
    data_p_str = data_p.strftime("%d/%m/%Y")
    giorno_sett_p = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][data_p.weekday()]
    
    suggeriti = [r['Nome'] for _, r in df.iterrows() if r.get('Riposo_Pref') in [giorno_sett_p, data_p_str]] if not df.empty else []
    assenti = c_a.multiselect("🛌 Assenti/Riposi:", nomi_db, default=suggeriti)
    
    cur_inp = {}
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        cur_inp[h] = {
            "AI": r[1].number_input("AI", 0, 100, 0, key=f"p_ai_{h}", label_visibility="collapsed"),
            "FI": r[2].number_input("FI", 0, 100, 0, key=f"p_fi_{h}", label_visibility="collapsed"),
            "AG": r[3].number_input("AG", 0, 100, 0, key=f"p_ag_{h}", label_visibility="collapsed"),
            "FG": r[4].number_input("FG", 0, 100, 0, key=f"p_fg_{h}", label_visibility="collapsed")
        }

    if st.button("🚀 GENERA SCHIERAMENTO", use_container_width=True):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # 1. Definiamo le liste base
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        st.session_state['spl_v_fin'] = pool_spl
        
        if not conf_df.empty:
            conf_df.columns = [str(c).strip().upper() for c in conf_df.columns]
            if 'HOTEL' not in conf_df.columns:
                conf_df.rename(columns={conf_df.columns[0]: 'HOTEL'}, inplace=True)
        
        # 2. Calcolo Fabbisogni
        fabb = {}
        for h in lista_hotel:
            m = conf_df[conf_df['HOTEL'] == h] if not conf_df.empty else pd.DataFrame()
            if not m.empty:
                m_ai = m.iloc[0].get('AI', m.iloc[0].get('ARR I', 60))
                m_fi = m.iloc[0].get('FI', m.iloc[0].get('FERM I', 30))
                m_ag = m.iloc[0].get('AG', m.iloc[0].get('ARR G', 45))
                m_fg = m.iloc[0].get('FG', m.iloc[0].get('FERM G', 25))
            else:
                m_ai, m_fi, m_ag, m_fg = 60, 30, 45, 25
            
            tot_f = cur_inp[h]["FI"] + cur_inp[h]["FG"]
            fabb[h] = (cur_inp[h]["AI"]*m_ai + cur_inp[h]["FI"]*m_fi + cur_inp[h]["AG"]*m_ag + cur_inp[h]["FG"]*m_fg + tot_f*15) / 60
        
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ord = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        # 3. Assegnazione con Icone
        gia_a, ris = set(), []
        for zona in z_ord:
            o_n, t_h, o_f = fabb.get(zona, 0), [], 0
            
            # --- Governanti ---
            gov = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_a))]
            mask_g = gov['Zone_Padronanza'].str.contains(zona.replace("Hotel ", ""), case=False, na=False)
            for _, g in gov[mask_g].iterrows():
                t_h.append(f"⭐ {g['Nome']} (Gov.)")
                gia_a.add(g['Nome'])
            
            # --- Cameriere ---
            if o_n > 0 or zona in ["Hotel Castello", "Hotel Castello 4 Piano"]:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                cand['Pr'] = cand['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                
                for _, p in cand.sort_values('Pr').iterrows():
                    if p['Nome'] in gia_a: continue
                    if o_f < (o_n if o_n > 0 else 7.5):
                        is_spl = p['Nome'] in pool_spl
                        is_pt = p['Part_Time'] == 1
                        ico = "🌙 " if is_spl else ("🕒 " if is_pt else "")
                        
                        t_h.append(f"{ico}{p['Nome']}")
                        gia_a.add(p['Nome'])
                        o_f += 5.0 if (is_pt or is_spl) else 7.5
                        
                        c_pre = str(p.get('Lavora_Bene_Con', '')).strip()
                        if c_pre in attive['Nome'].values and c_pre not in gia_a:
                            p_c = attive[attive['Nome'] == c_pre].iloc[0]
                            is_spl_c = c_pre in pool_spl
                            is_pt_c = p_c['Part_Time'] == 1
                            ico_c = "🌙 " if is_spl_c else ("🕒 " if is_pt_c else "")
                            t_h.append(f"{ico_c}{c_pre}")
                            gia_a.add(c_pre)
                            o_f += 5.0 if (is_pt_c or is_spl_c) else 7.5
                    else: break
            
            if t_h:
                if len([n for n in t_h if "Gov." not in n]) % 2 != 0:
                    rest = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))]
                    if not rest.empty:
                        r_p = rest.iloc[0]
                        ico_r = "🌙 " if r_p['Nome'] in pool_spl else ("🕒 " if r_p['Part_Time'] == 1 else "")
                        t_h.append(f"{ico_r}{r_p['Nome']}")
                        gia_a.add(r_p['Nome'])
                
                ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Req": round(o_n, 1)})
        
        st.session_state['res_v_fin'] = ris
        st.rerun()
    if 'res_v_fin' in st.session_state:
        st.divider()
        final_l = []
        spl = st.session_state.get('spl_v_fin', [])
        
        for i, r in enumerate(st.session_state['res_v_fin']):
            with st.expander(f"📍 {r['Hotel']} (Req: {r['Req']}h)"):
                # Puliamo i nomi dalle icone per farli combaciare con nomi_db
                default_puliti = [
                    n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🌙 ", "").replace("🕒 ", "").strip() 
                    for n in r['Team'].split(",")
                ]
                
                # Il multiselect ora troverà i nomi corretti in nomi_db
                s = st.multiselect(
                    f"Team {r['Hotel']}", 
                    nomi_db, 
                    default=default_puliti, 
                    key=f"e_{i}"
                )
                final_l.append({"Hotel": r['Hotel'], "Team": ", ".join(s)})
        
        if st.button("🧊 SCARICA PDF"):
            pdf = genera_pdf_planning(data_p_str, final_l, spl, assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
