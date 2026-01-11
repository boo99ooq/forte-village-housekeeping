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
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    
    sel_n = st.selectbox("Seleziona collaboratrice per modificare:", ["--- NUOVA ---"] + nomi_db)
    
    curr = None
    if sel_n != "--- NUOVA ---":
        match = df[df['Nome'] == sel_n]
        if not match.empty:
            curr = match.iloc[0]
    
    with st.form("form_staff_definitivo"):
        c1, c2, c3 = st.columns(3)
        f_nome = c1.text_input("Nome e Cognome", value=str(curr['Nome']) if curr is not None else "")
        f_ruolo = c2.selectbox("Ruolo", ["Cameriera", "Governante"], 
                               index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        
        # Padronanza Zone
        def_padro = []
        if curr is not None and curr['Zone_Padronanza']:
            def_padro = [z.strip() for z in str(curr['Zone_Padronanza']).split(",") if z.strip() in lista_hotel]
        f_padro = c3.multiselect("Zone di Padronanza", lista_hotel, default=def_padro)
        
        st.divider()
        
        # --- SEZIONE STATO E LOGISTICA ---
        c4, c5, c6 = st.columns(3)
        with c4:
            st.write("**Stato Operativo**")
            f_pt = st.checkbox("🕒 Part-Time", value=bool(curr['Part_Time']) if curr is not None else False)
            f_jol = st.checkbox("🃏 Jolly", value=bool(curr['Jolly']) if curr is not None else False)
            f_pen = st.checkbox("🚌 Pendolare", value=bool(curr['Pendolare']) if curr is not None else False)
        
        with c5:
            st.write("**Relazioni**")
            idx_v = nomi_db.index(curr['Viaggia_Con'])+1 if curr is not None and curr['Viaggia_Con'] in nomi_db else 0
            f_via = st.selectbox("🚗 Viaggia con...", ["Nessuna"] + nomi_db, index=idx_v)
            
            idx_l = nomi_db.index(curr['Lavora_Bene_Con'])+1 if curr is not None and curr['Lavora_Bene_Con'] in nomi_db else 0
            f_lbc = st.selectbox("🤝 Lavora bene con...", ["Nessuna"] + nomi_db, index=idx_l)
            
            if f_via != "Nessuna" and f_via == f_lbc:
                st.info(f"💡 {f_nome} viaggia e lavora con {f_via}.")

        with c6:
            st.write("**Gestione Riposi**")
            opzioni_r = ["Nessuno", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica", "DATA SPECIFICA"]
            
            val_rip = str(curr['Riposo_Pref']) if curr is not None else "Nessuno"
            idx_r = opzioni_r.index(val_rip) if val_rip in opzioni_r else (8 if val_rip != "" and "/" in val_rip else 0)
            
            f_rip_tipo = st.selectbox("Tipo Riposo", opzioni_r, index=idx_r)
            
            # Calendario sempre presente per evitare errori del form
            try:
                d_def = datetime.strptime(val_rip, "%d/%m/%Y")
            except:
                d_def = datetime.now()
            
            f_data_s = st.date_input("Calendario (solo se Data Specifica)", d_def, format="DD/MM/YYYY")
            
            # Decidiamo cosa salvare
            f_rip_final = f_data_s.strftime("%d/%m/%Y") if f_rip_tipo == "DATA SPECIFICA" else f_rip_tipo

        st.divider()
        
        # --- SEZIONE VALUTAZIONI ---
        st.write("**Valutazioni Professionali (1-10)**")
        v1, v2, v3 = st.columns(3)
        f_prof = v1.slider("Professionalità", 1, 10, int(curr['Professionalita']) if curr is not None else 5)
        f_esp = v2.slider("Esperienza", 1, 10, int(curr['Esperienza']) if curr is not None else 5)
        f_ten = v3.slider("Tenuta Fisica", 1, 10, int(curr['Tenuta_Fisica']) if curr is not None else 5)
        f_dis = v1.slider("Disponibilità", 1, 10, int(curr.get('Disponibilita', 5)) if curr is not None else 5)
        f_emp = v2.slider("Empatia", 1, 10, int(curr.get('Empatia', 5)) if curr is not None else 5)
        f_gui = v3.slider("Capacità Guida", 1, 10, int(curr.get('Capacita_Guida', 5)) if curr is not None else 5)

        # IL PULSANTE DI SALVATAGGIO (Mandatorio)
        save_btn = st.form_submit_button("💾 SALVA SCHEDA")
        if save_btn:
            if f_nome:
                nuova_r = {
                    "Nome": f_nome.strip(), "Ruolo": f_ruolo, "Zone_Padronanza": ", ".join(f_padro),
                    "Part_Time": 1 if f_pt else 0, "Jolly": 1 if f_jol else 0, "Pendolare": 1 if f_pen else 0,
                    "Riposo_Pref": f_rip_final, "Viaggia_Con": f_via, "Lavora_Bene_Con": f_lbc,
                    "Professionalita": f_prof, "Esperienza": f_esp, "Tenuta_Fisica": f_ten,
                    "Disponibilita": f_dis, "Empatia": f_emp, "Capacita_Guida": f_gui
                }
                df_clean = df[df['Nome'] != (curr['Nome'] if curr is not None else "---")]
                df = pd.concat([df_clean, pd.DataFrame([nuova_r])], ignore_index=True)
                save_data(df)
                st.success(f"Dati di {f_nome} salvati!")
                st.rerun()

    # Bottone PDF fuori dal Form
    if curr is not None:
        if st.button("📄 GENERA PDF SCHEDA PERSONALE"):
            pdf_s = pdf_scheda_staff(curr)
            st.download_button(f"📥 Scarica scheda {curr['Nome']}", pdf_s, f"Scheda_{curr['Nome']}.pdf")# --- TAB TEMPI ---
with t_tempi:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    h_col = st.columns([2, 1, 1, 1, 1])
    h_col[0].write("**Hotel**"); h_col[1].write("**Arr I**"); h_col[2].write("**Ferm I**"); h_col[3].write("**Arr G**"); h_col[4].write("**Ferm G**")
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

# --- TAB PLANNING ---
with t_plan:
    st.header("🚀 Generazione Planning")
    
    # --- LOGICA INTELLIGENTE RIPOSI ---
    c_d, c_a = st.columns([1, 2])
    data_p = c_d.date_input("Seleziona Data Planning:", datetime.now(), format="DD/MM/YYYY")
    
    # Prepariamo i confronti per i riposi
    data_p_str = data_p.strftime("%d/%m/%Y")
    giorni_ita = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    giorno_sett_p = giorni_ita[data_p.weekday()]

    # Identifichiamo chi dovrebbe riposare oggi
    suggeriti_assenti = []
    if not df.empty:
        for _, row in df.iterrows():
            rip_salvato = str(row.get('Riposo_Pref', ''))
            if rip_salvato == giorno_sett_p or rip_salvato == data_p_str:
                suggeriti_assenti.append(row['Nome'])

    # Multiselect con pre-caricamento dei riposi
    assenti = c_a.multiselect("🛌 Assenti/Riposi del giorno:", nomi_db, default=suggeriti_assenti)
    
    st.write("### 📊 Inserimento Quantità Camere")
    h_col = st.columns([2, 1, 1, 1, 1])
    h_col[0].write("**HOTEL**"); h_col[1].write("**Arr I**"); h_col[2].write("**Ferm I**"); h_col[3].write("**Arr G**"); h_col[4].write("**Ferm G**")
    
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

    if st.button("🚀 GENERA SCHIERAMENTO SQUADRE", use_container_width=True):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # Spezzati per coperture
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        st.session_state['spl_v_fin'] = pool_spl
        
        conf_df.columns = conf_df.columns.str.strip().str.upper()
        fabb = {}
        for h in lista_hotel:
            m = conf_df[conf_df['HOTEL'] == h]
            if not m.empty:
                m_ai = m.iloc[0]['ARR I']
                m_fi = m.iloc[0]['FERM I']
                m_ag = m.iloc[0]['ARR G']
                m_fg = m.iloc[0]['FERM G']
            else:
                m_ai, m_fi, m_ag, m_fg = 60, 30, 45, 25
            
            tot_fer = cur_inp[h]["FI"] + cur_inp[h]["FG"]
            fabb[h] = (cur_inp[h]["AI"]*m_ai + cur_inp[h]["FI"]*m_fi + cur_inp[h]["AG"]*m_ag + cur_inp[h]["FG"]*m_fg + tot_fer*15) / 60
        
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ord = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_a, ris = set(), []
        for zona in z_ord:        
        # Logica di assegnazione
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ord = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_a, ris = set(), []
        for zona in z_ord:        
        # Logica di assegnazione (Castello, Coppie, ecc.)
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ord = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_a, ris = set(), []
        for zona in z_ord:
            o_n, t_h, o_f = fabb.get(zona, 0), [], 0
            # Governanti
            gov = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_a))]
            mask_g = gov['Zone_Padronanza'].str.contains(zona.replace("Hotel ", ""), case=False, na=False)
            for _, g in gov[mask_g].iterrows():
                t_h.append(f"⭐ {g['Nome']} (Gov.)"); gia_a.add(g['Nome'])
            # Cameriere
            if o_n > 0 or zona in ["Hotel Castello", "Hotel Castello 4 Piano"]:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                cand['Pr'] = cand['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                cand = cand.sort_values(['Pr'], ascending=True)
                for _, p in cand.iterrows():
                    if p['Nome'] in gia_a: continue
                    if o_f < (o_n if o_n > 0 else 7.5):
                        t_h.append(p['Nome']); gia_a.add(p['Nome'])
                        o_f += 5.0 if (p['Part_Time'] == 1 or p['Nome'] in pool_spl) else 7.5
                        # Partner
                        c_pre = str(p.get('Lavora_Bene_Con', '')).strip()
                        if c_pre and c_pre in attive['Nome'].values and c_pre not in gia_a:
                            t_h.append(c_pre); gia_a.add(c_pre); p_c = attive[attive['Nome'] == c_pre].iloc[0]
                            o_f += 5.0 if (p_c['Part_Time'] == 1 or c_pre in pool_spl) else 7.5
                    else: break
            if t_h and len(t_h)%2 != 0:
                rest = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))]
                if not rest.empty: rinf = rest.iloc[0]['Nome']; t_h.append(rinf); gia_a.add(rinf)
            if t_h: ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Req": round(o_n, 1)})
        st.session_state['res_v_fin'] = ris

    # --- VISUALIZZAZIONE RISULTATI ---
    if 'res_v_fin' in st.session_state:
        st.divider()
        spl = st.session_state.get('spl_v_fin', [])
        t_sc = set()
        for r in st.session_state['res_v_fin']:
            t_sc.update([n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").replace("⚠️ ", "").replace(" (RIPOSO!)", "").strip() for n in r['Team'].split(",")])
        
        v_li = sorted(list(set(df[~df['Nome'].isin(assenti)]['Nome']) - t_sc))
        
        final_l = []
        for i, r in enumerate(st.session_state['res_v_fin']):
            key = f"edt_f_{i}"
            raw = st.session_state.get(key, [n.strip() for n in r['Team'].split(",")])
            pul = [n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").replace("⚠️ ", "").replace(" (RIPOSO!)", "").strip() for n in raw]
            
            o_cop = 0
            nomi_icon = []
            for np in pul:
                m_o = df[df['Nome'] == np]
                if not m_o.empty:
                    ro = m_o.iloc[0]
                    # Controllo se è un giorno di riposo forzato
                    is_rip_day = (ro['Riposo_Pref'] == data_p_str or ro['Riposo_Pref'] == giorno_sett_p)
                    prefix = "⚠️ " if is_rip_day else ""
                    suffix = " (RIPOSO!)" if is_rip_day else ""
                    
                    if "overnante" in str(ro['Ruolo']).lower(): 
                        nomi_icon.append(f"{prefix}⭐ {np} (Gov.){suffix}")
                    else:
                        is_pt = ro['Part_Time'] == 1
                        is_spl = np in spl
                        o_cop += 5.0 if (is_pt or is_spl) else 7.5
                        ico = "🌙 " if is_spl else ("🕒 " if is_pt else "")
                        nomi_icon.append(f"{prefix}{ico}{np}{suffix}")
            
            diff = round(o_cop - r['Req'], 1)
            with st.expander(f"📍 {r['Hotel']} | {'✅ OK' if diff>=0 else '⚠️ SOTTO'} ({diff}h)"):
                opts = sorted(list(set(pul) | set(v_li)))
                opts_l = []
                for o in opts:
                    mo = df[df['Nome'] == o]
                    if not mo.empty:
                        ro = mo.iloc[0]
                        is_rd = (ro['Riposo_Pref'] == data_p_str or ro['Riposo_Pref'] == giorno_sett_p)
                        pfx = "⚠️ " if is_rd else ""
                        sfx = " (RIPOSO!)" if is_rd else ""
                        if "overnante" in str(ro['Ruolo']).lower(): lbl = f"{pfx}⭐ {o} (Gov.){sfx}"
                        elif o in spl: lbl = f"{pfx}🌙 {o}{sfx}"
                        elif ro['Part_Time'] == 1: lbl = f"{pfx}🕒 {o}{sfx}"
                        else: lbl = f"{pfx}{o}{sfx}"
                        opts_l.append(lbl)
                
                s = st.multiselect(f"Team {r['Hotel']}", opts_l, default=nomi_icon, key=key)
                final_l.append({"Hotel": r['Hotel'], "Team": ", ".join(s)})
        
        if st.button("🧊 SCARICA PDF PLANNING"):
            pdf = genera_pdf_planning(data_p.strftime("%d/%m/%Y"), final_l, spl, assenti)
            st.download_button("📥 DOWNLOAD PDF", pdf, f"Planning_{data_p}.pdf")
