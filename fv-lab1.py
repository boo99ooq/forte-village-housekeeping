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
            'Part_Time': 0, 'Lavora_Bene_Con': 'Nessuna', 'Zone_Padronanza': '',
            'Professionalita': 5, 'Esperienza': 5, 'Tenuta_Fisica': 5, 
            'Disponibilita': 5, 'Empatia': 5, 'Capacita_Guida': 5
        }
        for col, val in cols_default.items():
            if col not in df.columns: df[col] = val
        df['Nome'] = df['Nome'].astype(str).str.strip()
        df['Part_Time'] = pd.to_numeric(df['Part_Time'], errors='coerce').fillna(0)
        return df.fillna("")
    return pd.DataFrame()

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        if 'overnante' in str(row.get('Ruolo', '')).lower(): return "⭐ (Coord.)", 10.0
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

# --- SIDEBAR (COMPLETA) ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_nome = st.selectbox("Collaboratrice:", ["--- NUOVO ---"] + nomi_db)
    curr = df[df['Nome'] == sel_nome].iloc[0] if sel_nome != "--- NUOVO ---" else None
    
    with st.form("form_staff"):
        f_n = st.text_input("Nome", value=str(curr['Nome']) if curr is not None else "")
        f_r = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        f_zn = st.multiselect("Padronanza", lista_hotel, default=[z.strip() for z in str(curr['Zone_Padronanza']).split(",")] if curr is not None and curr['Zone_Padronanza'] else [])
        f_pt = st.checkbox("🕒 Part-Time", value=bool(curr.get('Part_Time', 0)) if curr is not None else False)
        f_lbc = st.selectbox("Partner Preferito", ["Nessuna"] + nomi_db, index=nomi_db.index(curr['Lavora_Bene_Con'])+1 if curr is not None and curr['Lavora_Bene_Con'] in nomi_db else 0)
        
        st.write("**Valutazioni (1-10)**")
        c1, c2 = st.columns(2)
        f_prof = c1.slider("Professionalità", 1, 10, int(curr['Professionalita']) if curr is not None else 5)
        f_esp = c2.slider("Esperienza", 1, 10, int(curr['Esperienza']) if curr is not None else 5)
        f_ten = c1.slider("Tenuta Fisica", 1, 10, int(curr['Tenuta_Fisica']) if curr is not None else 5)
        f_disp = c2.slider("Disponibilità", 1, 10, int(curr['Disponibilita']) if curr is not None else 5)
        f_emp = c1.slider("Empatia", 1, 10, int(curr['Empatia']) if curr is not None else 5)
        f_guid = c2.slider("Guida", 1, 10, int(curr['Capacita_Guida']) if curr is not None else 5)
        
        if st.form_submit_button("💾 SALVA SCHEDA"):
            nuova = {"Nome": f_n.strip(), "Ruolo": f_r, "Zone_Padronanza": ", ".join(f_zn), "Part_Time": 1 if f_pt else 0, "Lavora_Bene_Con": f_lbc, 
                     "Professionalita": f_prof, "Esperienza": f_esp, "Tenuta_Fisica": f_ten, "Disponibilita": f_disp, "Empatia": f_emp, "Capacita_Guida": f_guid}
            df = df[df['Nome'] != sel_nome] if curr is not None else df
            df = pd.concat([df, pd.DataFrame([nuova])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    st.header("🏆 Performance Staff")
    if not df.empty:
        filtro_z = st.selectbox("🔍 Filtra per Zona:", ["TUTTI"] + lista_hotel)
        df_d = df.copy()
        df_d[['Performance', 'Valore']] = df_d.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        if filtro_z != "TUTTI":
            df_d = df_d[df_d['Zone_Padronanza'].str.contains(filtro_z, case=False, na=False)]
        st.dataframe(df_d[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza']], use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Tempi Standard (Minuti)")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    st.write("Configura i minuti necessari per ogni tipologia di camera:")
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
    
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Tempi salvati!")

with t3:
    st.header("🚀 Planning")
    col_d, col_a = st.columns([1, 2])
    data_p = col_d.date_input("Giorno:", datetime.now())
    assenti = col_a.multiselect("🛌 Assenti:", nomi_db)
    
    st.write("### 📊 Quantità Camere")
    h_col = st.columns([2, 1, 1, 1, 1])
    h_col[0].write("**HOTEL**"); h_col[1].write("**Arr I**"); h_col[2].write("**Ferm I**"); h_col[3].write("**Arr G**"); h_col[4].write("**Ferm G**")

    cur_inp = {}
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        v_ai = r[1].number_input("AI", 0, 100, 0, key=f"v_ai_{h}", label_visibility="collapsed")
        v_fi = r[2].number_input("FI", 0, 100, 0, key=f"v_fi_{h}", label_visibility="collapsed")
        v_ag = r[3].number_input("AG", 0, 100, 0, key=f"v_ag_{h}", label_visibility="collapsed")
        v_fg = r[4].number_input("FG", 0, 100, 0, key=f"v_fg_{h}", label_visibility="collapsed")
        cur_inp[h] = {"AI": v_ai, "FI": v_fi, "AG": v_ag, "FG": v_fg}

    if st.button("🚀 GENERA SCHIERAMENTO", use_container_width=True):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        st.session_state['spl_v_fin'] = pool_spl
        
        fabb = {}
        for h in lista_hotel:
            m = conf_df[conf_df['Hotel'] == h]
            m_ai, m_fi, m_ag, m_fg = (m.iloc[0]['AI'], m.iloc[0]['FI'], m.iloc[0]['AG'], m.iloc[0]['FG']) if not m.empty else (60, 30, 45, 25)
            
            # Calcolo automatico: Coperture e Biancheria basate su Fermate (FI + FG)
            tot_fermate = cur_inp[h]["FI"] + cur_inp[h]["FG"]
            ore_c = (cur_inp[h]["AI"]*m_ai + cur_inp[h]["FI"]*m_fi + cur_inp[h]["AG"]*m_ag + cur_inp[h]["FG"]*m_fg + tot_fermate*15) / 60
            fabb[h] = ore_c
        
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
            # Cam
            if o_n > 0 or zona in ["Hotel Castello", "Hotel Castello 4 Piano"]:
                cand = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                cand['Pr'] = cand['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                cand = cand.sort_values(['Pr'], ascending=True)
                for _, p in cand.iterrows():
                    if p['Nome'] in gia_a: continue
                    if o_f < (o_n if o_n > 0 else 7.5):
                        t_h.append(p['Nome']); gia_a.add(p['Nome'])
                        o_f += 5.0 if (p['Part_Time'] == 1 or p['Nome'] in pool_spl) else 7.5
                        c_pref = str(p.get('Lavora_Bene_Con', '')).strip()
                        if c_pref and c_pref in attive['Nome'].values and c_pref not in gia_a:
                            t_h.append(c_pref); gia_a.add(c_pref)
                            p_c = attive[attive['Nome'] == c_pref].iloc[0]
                            o_f += 5.0 if (p_c['Part_Time'] == 1 or c_pref in pool_spl) else 7.5
                    else: break
            if t_h and len(t_h)%2 != 0:
                rest = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))]
                if not rest.empty: rinf = rest.iloc[0]['Nome']; t_h.append(rinf); gia_a.add(rinf)
            if t_h: ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Req": round(o_n, 1)})
        st.session_state['res_v_fin'] = ris

    if 'res_v_fin' in st.session_state:
        st.divider()
        t_att = set(n for n in nomi_db if n not in assenti)
        spl = st.session_state.get('spl_v_fin', [])
        t_scel = set()
        for r in st.session_state['res_v_fin']:
            t_scel.update([n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").strip() for n in r['Team'].split(",")])
        v_lib = sorted(list(t_att - t_scel))
        
        final_list = []
        for i, r in enumerate(st.session_state['res_v_fin']):
            key = f"edt_f_{i}"
            raw = st.session_state.get(key, [n.strip() for n in r['Team'].split(",")])
            pul = [n.replace("⭐ ", "").replace(" (Gov.)", "").replace("🕒 ", "").replace("🌙 ", "").strip() for n in raw]
            c_ft, c_pt, c_spl, c_gov, o_cop = 0, 0, 0, 0, 0
            nomi_icon = []
            for np in pul:
                m = df[df['Nome'] == np]
                if not m.empty:
                    row = m.iloc[0]
                    if "overnante" in str(row['Ruolo']).lower(): c_gov += 1; nomi_icon.append(f"⭐ {np} (Gov.)")
                    elif np in spl: c_spl += 1; o_cop += 5.0; nomi_icon.append(f"🌙 {np}")
                    elif row['Part_Time'] == 1: c_pt += 1; o_cop += 5.0; nomi_icon.append(f"🕒 {np}")
                    else: c_ft += 1; o_cop += 7.5; nomi_icon.append(np)
            
            diff = round(o_cop - r.get('Req', 0), 1)
            with st.expander(f"📍 {r['Hotel']} | {'✅ OK' if diff>=0 else '⚠️ SOTTO'} ({diff}h)"):
                st.write(f"👥 **{len(pul)}** ({c_ft} FT, {c_pt} 🕒, {c_spl} 🌙, {c_gov} ⭐) | Req: {r['Req']}h")
                opts = sorted(list(set(pul) | set(v_lib)))
                opts_l = []
                for o in opts:
                    mo = df[df['Nome'] == o]
                    if not mo.empty:
                        ro = mo.iloc[0]
                        if "overnante" in str(ro['Ruolo']).lower(): lbl = f"⭐ {o} (Gov.)"
                        elif o in spl: lbl = f"🌙 {o}"
                        elif ro['Part_Time'] == 1: lbl = f"🕒 {o}"
                        else: lbl = o
                        opts_l.append(lbl)
                s = st.multiselect(f"Team {r['Hotel']}", opts_l, default=nomi_icon, key=key)
                final_list.append({"Hotel": r['Hotel'], "Team": ", ".join(s)})

        if st.button("🧊 SCARICA PDF"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, spl, assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
