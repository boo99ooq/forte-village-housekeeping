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

# --- DATABASE E FILE ---
FILE_STAFF = 'housekeeping_database.csv' 
FILE_CONFIG = 'config_tempi.csv'

lista_hotel = [
    "Hotel Castello", "Hotel Castello Garden", "Hotel Castello 4 Piano", 
    "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", 
    "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"
]

def load_data():
    if os.path.exists(FILE_STAFF):
        try:
            df = pd.read_csv(FILE_STAFF)
            df.columns = [c.strip() for c in df.columns]
            colonne = {'Part_Time': 0, 'Auto': 'Nessuna', 'Zone_Padronanza': '', 'Lavora_Bene_Con': ''}
            for col, d in colonne.items():
                if col not in df.columns: df[col] = d
            df['Part_Time'] = pd.to_numeric(df['Part_Time'], errors='coerce').fillna(0)
            return df.fillna("")
        except: return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def genera_pdf(data_str, schieramento, split_list, lista_assenti):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 18); p.drawString(50, h-50, f"PLANNING - {data_str}")
    p.line(50, h-60, 540, h-60); y = h-85
    if lista_assenti:
        p.setFont("Helvetica-Bold", 10); p.setFillColorRGB(0.7, 0, 0)
        p.drawString(50, y, f"🛌 ASSENTI/RIPOSI: {', '.join(lista_assenti)}")
        y -= 25; p.setFillColorRGB(0,0,0)

    for res in schieramento:
        if y < 100: p.showPage(); y = h-70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    y -= 20; p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 13); p.drawString(50, y-30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11); p.drawString(60, y-50, f"Personale: {', '.join(split_list)}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()

# --- SIDEBAR: GESTIONE STAFF ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_nome = st.selectbox("Cerca/Modifica:", ["--- NUOVO ---"] + nomi_db)
    curr = df[df['Nome'] == sel_nome].iloc[0] if sel_nome != "--- NUOVO ---" else None
    
    with st.form("form_staff"):
        f_n = st.text_input("Nome", value=str(curr['Nome']) if curr is not None else "")
        f_r = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        f_zn = st.multiselect("Zone Padronanza", lista_hotel, default=[z.strip() for z in str(curr['Zone_Padronanza']).split(",")] if curr is not None else [])
        f_pt = st.checkbox("🕒 Part-Time", value=bool(curr.get('Part_Time', 0)) if curr is not None else False)
        f_lbc = st.selectbox("Lavora Bene Con", ["Nessuna"] + nomi_db, index=nomi_db.index(curr['Lavora_Bene_Con'])+1 if curr is not None and curr['Lavora_Bene_Con'] in nomi_db else 0)
        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova = {"Nome": f_n, "Ruolo": f_r, "Zone_Padronanza": ", ".join(f_zn), "Part_Time": 1 if f_pt else 0, "Lavora_Bene_Con": f_lbc}
            df = df[df['Nome'] != sel_nome] if curr is not None else df
            df = pd.concat([df, pd.DataFrame([nuova])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t2:
    st.header("⚙️ Tempi Standard (Minuti per camera)")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        cols = st.columns([2,1,1])
        m_ai, m_fi = 60, 30
        if not c_df.empty and 'Hotel' in c_df.columns:
            t_row = c_df[c_df['Hotel'] == h]
            if not t_row.empty: m_ai, m_fi = int(t_row.iloc[0].get('Arr_Ind', 60)), int(t_row.iloc[0].get('Fer_Ind', 30))
        ai = cols[1].number_input(f"AI {h}", 5, 120, m_ai, key=f"t_ai_{h}")
        fi = cols[2].number_input(f"FI {h}", 5, 120, m_fi, key=f"t_fi_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Tempi salvati!")

with t3:
    st.header("🚀 Planning Giornaliero")
    col_d, col_a = st.columns([1, 2])
    data_p = col_d.date_input("Giorno:", datetime.now())
    assenti = col_a.multiselect("🛌 Assenti/Riposi:", nomi_db)
    
    st.divider()
    st.write("### 📊 Carico Lavoro")
    
    # --- NUOVA INTESTAZIONE A 6 CASELLE ---
    h_col = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
    h_col[0].write("**HOTEL**")
    h_col[1].write("**Arr I**")
    h_col[2].write("**Ferm I**")
    h_col[3].write("**Arr G**")
    h_col[4].write("**Ferm G**")
    h_col[5].write("**Cop**")
    h_col[6].write("**Bian**")

    cur_inp = {}
    for h in lista_hotel:
        r = st.columns([2, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
        r[0].write(f"**{h}**")
        v_ai = r[1].number_input("AI", 0, 100, 0, key=f"v_ai_{h}", label_visibility="collapsed")
        v_fi = r[2].number_input("FI", 0, 100, 0, key=f"v_fi_{h}", label_visibility="collapsed")
        v_ag = r[3].number_input("AG", 0, 100, 0, key=f"v_ag_{h}", label_visibility="collapsed")
        v_fg = r[4].number_input("FG", 0, 100, 0, key=f"v_fg_{h}", label_visibility="collapsed")
        v_co = r[5].number_input("COP", 0, 100, 0, key=f"v_co_{h}", label_visibility="collapsed")
        v_bi = r[6].number_input("BIA", 0, 100, 0, key=f"v_bi_{h}", label_visibility="collapsed")
        
        cur_inp[h] = {"AI": v_ai, "FI": v_fi, "AG": v_ag, "FG": v_fg, "CO": v_co, "BI": v_bi}

    if st.button("🚀 GENERA SCHIERAMENTO", use_container_width=True):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        
        # Spezzati
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        st.session_state['spl_v_fin'] = pool_spl
        
        fabb = {}
        for h in lista_hotel:
            m_ai, m_fi = 60, 30
            if not conf_df.empty and 'Hotel' in conf_df.columns:
                t_r = conf_df[conf_df['Hotel'] == h]
                if not t_r.empty:
                    m_ai = t_r.iloc[0].get('Arr_Ind', 60)
                    m_fi = t_r.iloc[0].get('Fer_Ind', 30)
            
            # CALCOLO ORE: I gruppi (AG/FG) pesano il 20% in meno degli individuali (stima standard)
            ore_ind = (cur_inp[h]["AI"] * m_ai + cur_inp[h]["FI"] * m_fi)
            ore_grp = (cur_inp[h]["AG"] * (m_ai * 0.8) + cur_inp[h]["FG"] * (m_fi * 0.8))
            extra = (cur_inp[h]["CO"] * 20 + cur_inp[h]["BI"] * 15)
            
            fabb[h] = (ore_ind + ore_grp + extra) / 60
        
        # ... (restante logica di generazione invariata) ...    
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ordine = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_a, ris = set(), []
        for zona in z_ordine:
            o_n, t_h, o_f = fabb.get(zona, 0), [], 0
            # Gov
            gov = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_a))]
            mask_g = gov['Zone_Padronanza'].str.contains(zona.replace("Hotel ", ""), case=False, na=False)
            for _, g in gov[mask_g].iterrows():
                t_h.append(f"⭐ {g['Nome']} (Gov.)"); gia_a.add(g['Nome'])
            # Cam + Affinità
            if o_n > 0 or zona in ["Hotel Castello", "Hotel Castello 4 Piano"]:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                cand['Pr'] = cand['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                cand = cand.sort_values(['Pr'], ascending=True)
                for _, p in cand.iterrows():
                    if p['Nome'] in gia_a: continue
                    if o_f < (o_n if o_n > 0 else 7.5):
                        t_h.append(p['Nome']); gia_a.add(p['Nome'])
                        o_f += 5.0 if (p.get('Part_Time', 0) == 1 or p['Nome'] in pool_spl) else 7.5
                        c_pref = str(p.get('Lavora_Bene_Con', '')).strip()
                        if c_pref and c_pref in attive['Nome'].values and c_pref not in gia_a:
                            t_h.append(c_pref); gia_a.add(c_pref)
                            p_c = attive[attive['Nome'] == c_pref].iloc[0]
                            o_f += 5.0 if (p_c.get('Part_Time', 0) == 1 or c_pref in pool_spl) else 7.5
                    else: break
            # Pareggio
            if t_h and len(t_h) % 2 != 0:
                rest = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))]
                if not rest.empty:
                    rinf = rest.iloc[0]['Nome']
                    t_h.append(rinf); gia_a.add(rinf)
            if t_h: ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Req": round(o_n, 1)})
        st.session_state['res_v_fin'] = ris

    # --- AREA RISULTATI ---
    if 'res_v_fin' in st.session_state:
        st.divider()
        t_attive = set(n for n in nomi_db if n not in assenti)
        spl = st.session_state.get('spl_v_fin', [])
        
        t_scelti = set()
        for i in range(len(st.session_state['res_v_fin'])):
            key = f"edt_f_{i}"
            val = st.session_state.get(key, [n.strip() for n in st.session_state['res_v_fin'][i].get('Team', '').split(",") if n.strip()])
            t_scelti.update([n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").strip() for n in val])
        
        v_libere = sorted(list(t_attive - t_scelti))
        st.metric("🏃 In Panchina", len(v_libere))
        with st.expander("Vedi Panchina"): st.write(", ".join(v_libere))

        final_list = []
        for i, r in enumerate(st.session_state['res_v_fin']):
            key = f"edt_f_{i}"
            raw = st.session_state.get(key, [n.strip() for n in r.get('Team', '').split(",") if n.strip()])
            pul = [n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").strip() for n in raw]
            
            c_ft, c_pt, c_spl, c_gov, o_cop = 0, 0, 0, 0, 0
            nomi_icon = []
            for n_p in pul:
                m = df[df['Nome'] == n_p]
                if not m.empty:
                    row = m.iloc[0]
                    is_pt, is_spl = row.get('Part_Time', 0) == 1, n_p in spl
                    if "overnante" in str(row['Ruolo']).lower(): 
                        c_gov += 1; nomi_icon.append(f"⭐ {n_p} (Gov.)")
                    elif is_spl: 
                        c_spl += 1; o_cop += 5.0; nomi_icon.append(f"🌙 {n_p}")
                    elif is_pt: 
                        c_pt += 1; o_cop += 5.0; nomi_icon.append(f"🕒 {n_p}")
                    else: 
                        c_ft += 1; o_cop += 7.5; nomi_icon.append(n_p)
            
            diff = round(o_cop - r.get('Req', 0), 1)
            b_str = f"✅ OK (+{diff}h)" if diff >= 0 else f"⚠️ SOTTO ({diff}h)"
            
            with st.expander(f"📍 {r['Hotel']} | {b_str}"):
                st.write(f"👥 **{len(pul)} persone** ({c_ft} Full, {c_pt} 🕒, {c_spl} 🌙, {c_gov} ⭐)")
                opts_p = sorted(list(set(pul) | set(v_libere)))
                opts_l = []
                for o in opts_p:
                    m_o = df[df['Nome'] == o].iloc[0]
                    if "overnante" in str(m_o['Ruolo']).lower(): lbl = f"⭐ {o} (Gov.)"
                    elif o in spl: lbl = f"🌙 {o}"
                    elif m_o.get('Part_Time', 0) == 1: lbl = f"🕒 {o}"
                    else: lbl = o
                    opts_l.append(lbl)
                
                scelta = st.multiselect(f"Team {r['Hotel']}", opts_l, default=nomi_icon, key=key)
                final_list.append({"Hotel": r['Hotel'], "Team": ", ".join(scelta)})

        st.subheader("🌙 Coperture Serali")
        st.info(f"Assegnate: {', '.join(spl)}")
        if st.button("🧊 SCARICA PDF"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, spl, assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
