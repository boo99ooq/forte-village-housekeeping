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
        p.drawString(50, y, f"🛌 ASSENTI: {', '.join(lista_assenti)}")
        y -= 25; p.setFillColorRGB(0,0,0)

    ordine_pref = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"]
    mappa_res = {r['Hotel']: r for r in schieramento}
    final_ordered = [mappa_res[pref] for pref in ordine_pref if pref in mappa_res]
    final_ordered += [r for r in schieramento if r['Hotel'] not in ordine_pref]

    for res in final_ordered:
        if y < 100: p.showPage(); y = h-70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()} ({res.get('Bilancio', '')})")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    y -= 20; p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 13); p.drawString(50, y-30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11); p.drawString(60, y-50, f"Personale: {', '.join(split_list) if split_list else 'Non assegnato'}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Staff")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_nome = st.selectbox("Seleziona:", ["--- NUOVO ---"] + nomi_db)
    curr = df[df['Nome'] == sel_nome].iloc[0] if sel_nome != "--- NUOVO ---" else None
    with st.form("form_v_final"):
        f_n = st.text_input("Nome", value=str(curr['Nome']) if curr is not None else "")
        idx_r = 1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0
        f_r = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=idx_r)
        z_attuali = [z.strip() for z in str(curr['Zone_Padronanza']).split(",")] if curr is not None else []
        f_zn = st.multiselect("Zone Padronanza", lista_hotel, default=[z for z in z_attuali if z in lista_hotel])
        f_pt = st.checkbox("🕒 Part-Time", value=bool(curr.get('Part_Time', 0)) if curr is not None else False)
        f_lbc = st.selectbox("Lavora Bene Con", ["Nessuna"] + nomi_db, index=nomi_db.index(curr['Lavora_Bene_Con'])+1 if curr is not None and curr['Lavora_Bene_Con'] in nomi_db else 0)
        if st.form_submit_button("💾 SALVA"):
            nuova = {"Nome": f_n, "Ruolo": f_r, "Zone_Padronanza": ", ".join(f_zn), "Part_Time": 1 if f_pt else 0, "Lavora_Bene_Con": f_lbc}
            df = df[df['Nome'] != sel_nome] if curr is not None else df
            df = pd.concat([df, pd.DataFrame([nuova])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t2:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        cols = st.columns([2,1,1])
        cols[0].write(f"**{h}**")
        m_ai, m_fi = 60, 30
        if not c_df.empty and 'Hotel' in c_df.columns:
            t_row = c_df[c_df['Hotel'] == h]
            if not t_row.empty:
                m_ai = int(t_row.iloc[0].get('Arr_Ind', 60)); m_fi = int(t_row.iloc[0].get('Fer_Ind', 30))
        ai = cols[1].number_input("AI", 5, 120, m_ai, key=f"t_ai_{h}")
        fi = cols[2].number_input("FI", 5, 120, m_fi, key=f"t_fi_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Salvati!")

with t3:
    st.header("🚀 Planning")
    data_p = st.date_input("Giorno:", datetime.now(), key="d_v_fin")
    assenti = st.multiselect("🛌 Assenti:", nomi_db, key="a_v_fin")
    cur_inp = {}
    for h in lista_hotel:
        r = st.columns([2, 1, 1, 1, 1])
        r[0].write(f"**{h}**")
        cur_inp[h] = {
            "AI": r[1].number_input("AI", 0, 100, 0, key=f"v_ai_{h}", label_visibility="collapsed"),
            "FI": r[2].number_input("FI", 0, 100, 0, key=f"v_fi_{h}", label_visibility="collapsed"),
            "CO": r[3].number_input("COP", 0, 100, 0, key=f"v_co_{h}", label_visibility="collapsed"),
            "BI": r[4].number_input("BIA", 0, 100, 0, key=f"v_bi_{h}", label_visibility="collapsed")
        }

    if st.button("🚀 GENERA SCHIERAMENTO"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)].copy()
        pool_spl = attive[attive['Ruolo'] == 'Cameriera'].head(4)['Nome'].tolist()
        
        fabb = {}
        for h in lista_hotel:
            m_ai, m_fi = 60, 30
            if not conf_df.empty and 'Hotel' in conf_df.columns:
                t_r = conf_df[conf_df['Hotel'] == h]
                if not t_r.empty:
                    m_ai = t_r.iloc[0].get('Arr_Ind', 60); m_fi = t_r.iloc[0].get('Fer_Ind', 30)
            fabb[h] = (cur_inp[h]["AI"]*m_ai + cur_inp[h]["FI"]*m_fi + cur_inp[h]["CO"]*(m_fi/3) + cur_inp[h]["BI"]*(m_fi/4)) / 60
        
        fabb["MACRO: PALME & GARDEN"] = fabb.get("Le Palme", 0) + fabb.get("Hotel Castello Garden", 0)
        z_ordine = ["Hotel Castello", "Hotel Castello 4 Piano", "MACRO: PALME & GARDEN"] + [h for h in lista_hotel if h not in ["Hotel Castello", "Hotel Castello 4 Piano", "Le Palme", "Hotel Castello Garden"]]
        
        gia_a = set()
        ris = []
        for zona in z_ordine:
            o_n, t_h, o_f = fabb.get(zona, 0), [], 0
            
            # 1. GOVERNANTI
            gov = attive[(attive['Ruolo'] == 'Governante') & (~attive['Nome'].isin(gia_a))]
            mask_g = gov['Zone_Padronanza'].str.contains(zona.replace("Hotel ", ""), case=False, na=False)
            for _, g in gov[mask_g].iterrows():
                t_h.append(f"⭐ {g['Nome']} (Gov.)"); gia_a.add(g['Nome'])
            
            # 2. CAMERIERE (AFFINITÀ)
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
            
            # 3. PAREGGIAMENTO
            if len(t_h) > 0 and len(t_h) % 2 != 0:
                rest = attive[(attive['Ruolo'] == 'Cameriera') & (~attive['Nome'].isin(gia_a))].copy()
                if not rest.empty:
                    rest['Pr'] = rest['Zone_Padronanza'].apply(lambda x: 0 if zona.replace("Hotel ", "").lower() in str(x).lower() else 1)
                    rinf = rest.sort_values(['Pr'], ascending=True).iloc[0]
                    t_h.append(rinf['Nome']); gia_a.add(rinf['Nome'])

            if t_h: ris.append({"Hotel": zona, "Team": ", ".join(t_h), "Req": round(o_n, 1)})
        st.session_state['res_v_fin'] = ris; st.session_state['spl_v_fin'] = pool_spl

    if 'res_v_fin' in st.session_state:
        st.divider()
        tutte_attive = set(n for n in nomi_db if n not in assenti)
        
        # LOGICA CALCOLO BILANCIO DINAMICO
        final_list = []
        tutti_scelti = set()
        
        for i, r in enumerate(st.session_state['res_v_fin']):
            key = f"edt_f_{i}"
            attuali = st.session_state.get(key, [n.strip() for n in r['Team'].split(",") if n.strip()])
            
            # Calcolo ore coperte per questo hotel
            ore_coperte = 0
            for nome in attuali:
                n_pulito = nome.replace("⭐ ", "").replace(" (Gov.)", "").strip()
                if n_pulito in df['Nome'].values:
                    p_data = df[df['Nome'] == n_pulito].iloc[0]
                    # Governanti = 0 ore lavoro fisico (o 7.5 se vuoi contarle), qui contiamo solo cameriere
                    if p_data['Ruolo'] == 'Cameriera':
                        ore_coperte += 5.0 if (p_data.get('Part_Time', 0) == 1 or n_pulito in st.session_state['spl_v_fin']) else 7.5
            
            diff = round(ore_coperte - r['Req'], 1)
            bilancio_str = f"✅ OK (+{diff}h)" if diff >= 0 else f"⚠️ SOTTO ({diff}h)"
            
            tutti_scelti.update([n.replace("⭐ ", "").replace(" (Gov.)", "").strip() for n in attuali])
            
            with st.expander(f"📍 {r['Hotel']} | Servono: {r['Req']}h | Coperti: {ore_coperte}h | {bilancio_str}"):
                vere_libere = sorted(list(tutte_attive - tutti_scelti))
                opts = sorted(list(set(attuali) | set(vere_libere)))
                if len(attuali) % 2 != 0: st.warning("⚠️ Numero dispari.")
                scelta = st.multiselect(f"Team {r['Hotel']}", opts, default=attuali, key=key)
                final_list.append({"Hotel": r['Hotel'], "Team": ", ".join(scelta), "Bilancio": bilancio_str})

        # Riepilogo finale
        vere_libere_finali = sorted(list(tutte_attive - tutti_scelti))
        st.sidebar.metric("Libere in Panchina", len(vere_libere_finali))
        if vere_libere_finali:
            st.info(f"🏃 IN PANCHINA: {', '.join(vere_libere_finali)}")

        if st.button("🧊 SCARICA PDF"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, st.session_state['spl_v_fin'], assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
