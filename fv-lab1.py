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
    st.header("⚙️ Tempi Standard (Minuti)")
    st.info("**Legenda:** ARR I: Arrivi Ind. | FERM I: Fermate Ind. | ARR G: Arrivi Gruppo | FERM G: Fermate Gruppo")
    st.caption("Nota: Coperture (1/3 fermata) e Cambio Biancheria (1/4 fermata) sono calcolati automaticamente.")
    
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    
    # Intestazioni colonne
    h_cols = st.columns([2, 1, 1, 1, 1])
    h_cols[0].write("**ALBERGO**")
    h_cols[1].write("**ARR I**")
    h_cols[2].write("**FERM I**")
    h_cols[3].write("**ARR G**")
    h_cols[4].write("**FERM G**")

    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        m_ai, m_fi, m_ag, m_fg = 60, 30, 45, 25
        if not c_df.empty:
            tr = c_df[c_df['HOTEL'] == h.upper()] if 'HOTEL' in c_df.columns else c_df[c_df.iloc[:,0] == h]
            if not tr.empty:
                m_ai = tr.iloc[0].get('AI', 60); m_fi = tr.iloc[0].get('FI', 30)
                m_ag = tr.iloc[0].get('AG', 45); m_fg = tr.iloc[0].get('FG', 25)
        
        v_ai = r[1].number_input("AI", 5, 120, int(m_ai), key=f"t_ai_{h}", label_visibility="collapsed")
        v_fi = r[2].number_input("FI", 5, 120, int(m_fi), key=f"t_fi_{h}", label_visibility="collapsed")
        v_ag = r[3].number_input("AG", 5, 120, int(m_ag), key=f"t_ag_{h}", label_visibility="collapsed")
        v_fg = r[4].number_input("FG", 5, 120, int(m_fg), key=f"t_fg_{h}", label_visibility="collapsed")
        new_c.append({"HOTEL": h.upper(), "AI": v_ai, "FI": v_fi, "AG": v_ag, "FG": v_fg})
    
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False)
        st.success("Tempi salvati correttamente!")
    with t_plan:
       st.header("🚀 Generazione Planning")
    c_d, c_a = st.columns([1, 2])
    data_p = c_d.date_input("Data Planning:", datetime.now(), format="DD/MM/YYYY")
    data_p_str = data_p.strftime("%d/%m/%Y")
    
    assenti = c_a.multiselect("🛌 Assenti/Riposi:", nomi_db)
    
    # Intestazioni (Sigle corrette)
    hp = st.columns([2, 1, 1, 1, 1, 1, 1])
    hp[0].write("**ALBERGO**"); hp[1].write("**ARR I**"); hp[2].write("**FERM I**")
    hp[3].write("**ARR G**"); hp[4].write("**FERM G**"); hp[5].write("**COP**"); hp[6].write("**BIANC**")

    cur_inp = {}
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        cur_inp[h] = {
            "AI": r[1].number_input("AI", 0, 100, 0, key=f"p_ai_{h}", label_visibility="collapsed"),
            "FI": r[2].number_input("FI", 0, 100, 0, key=f"p_fi_{h}", label_visibility="collapsed"),
            "AG": r[3].number_input("AG", 0, 100, 0, key=f"p_ag_{h}", label_visibility="collapsed"),
            "FG": r[4].number_input("FG", 0, 100, 0, key=f"p_fg_{h}", label_visibility="collapsed"),
            "COP": r[5].number_input("COP", 0, 100, 0, key=f"p_co_{h}", label_visibility="collapsed"),
            "BIAN": r[6].number_input("BIAN", 0, 100, 0, key=f"p_bi_{h}", label_visibility="collapsed")
        } 
        # --- SALVATAGGIO DATI ZONA ---
        if t_h:
                n_gov = len([n for n in t_h if "⭐" in n])
                n_spl = len([n for n in t_h if "🌙" in n])
                n_pt = len([n for n in t_h if "🕒" in n])
                n_std = len(t_h) - n_gov - n_spl - n_pt
                info_txt = f"G:{n_gov} Std:{n_std} 🕒:{n_pt} 🌙:{n_spl}"
                
                ris.append({
                    "Hotel": zona, 
                    "Team": ", ".join(t_h), 
                    "Req": round(o_n, 1), 
                    "Info": info_txt
                })
        
        # Questa riga deve essere allineata al tasto "GENERA"
        st.session_state['res_v_fin'] = ris
        st.rerun()

    # --- VISUALIZZAZIONE RISULTATI ---
    if 'res_v_fin' in st.session_state:
        st.divider()
        final_l = []
        for i, r in enumerate(st.session_state['res_v_fin']):
            # Mostra i box con i conteggi corretti (G, Std, PT, Spl)
            with st.expander(f"📍 {r['Hotel']} | {r.get('Info','')} | {r['Req']}h"):
                # Pulizia icone per il multiselect
                def_p = [n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🌙 ", "").replace("🕒 ", "").strip() for n in r['Team'].split(",")]
                s = st.multiselect(f"Modifica {r['Hotel']}", nomi_db, default=def_p, key=f"e_{i}")
                final_l.append({"Hotel": r['Hotel'], "Team": ", ".join(s)})
        
        if st.button("🧊 SCARICA PDF"):
            pdf = genera_pdf_planning(data_p_str, final_l, st.session_state.get('spl_v_fin', []), assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
