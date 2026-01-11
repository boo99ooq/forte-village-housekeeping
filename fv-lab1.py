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
        
      # --- VISUALIZZAZIONE RISULTATI E RIEPILOGO ---
    if 'res_v_fin' in st.session_state:
        st.divider()
        tutte_attive = set(n for n in nomi_db if n not in assenti)
        
        final_list = []
        tutti_scelti = set()
        
        # 1. Raccogliamo i nomi scelti per calcolare chi è libero
        for i in range(len(st.session_state['res_v_fin'])):
            val = st.session_state.get(f"edt_f_{i}", [])
            tutti_scelti.update([n.replace("⭐ ", "").replace(" (Gov.)", "").strip() for n in val])
        
        # 2. Mostriamo gli hotel e calcoliamo il bilancio ore
        for i, r in enumerate(st.session_state['res_v_fin']):
            key = f"edt_f_{i}"
            # Usiamo .get per evitare il crash se l'hotel non ha ancora i dati completi
            attuali = st.session_state.get(key, [n.strip() for n in r.get('Team', '').split(",") if n.strip()])
            
            # Calcolo ore coperte
            ore_coperte = 0
            for nome in attuali:
                n_pulito = nome.replace("⭐ ", "").replace(" (Gov.)", "").strip()
                match = df[df['Nome'] == n_pulito]
                if not match.empty:
                    p_data = match.iloc[0]
                    if p_data['Ruolo'] == 'Cameriera':
                        is_pt = p_data.get('Part_Time', 0) == 1
                        is_spl = n_pulito in st.session_state.get('spl_v_fin', [])
                        ore_coperte += 5.0 if (is_pt or is_spl) else 7.5
            
            # PROTEZIONE KEYERROR: usiamo .get('Req', 0)
            fabbisogno = r.get('Req', 0) 
            diff = round(ore_coperte - fabbisogno, 1)
            
            bilancio_str = f"✅ OK (+{diff}h)" if diff >= 0 else f"⚠️ SOTTO ({diff}h)"
            
            with st.expander(f"📍 {r['Hotel']} | Servono: {fabbisogno}h | Coperti: {ore_coperte}h | {bilancio_str}"):
                vere_libere = sorted(list(tutte_attive - tutti_scelti))
                opts = sorted(list(set(attuali) | set(vere_libere)))
                
                if len(attuali) % 2 != 0:
                    st.warning(f"👫 Squadra dispari ({len(attuali)} persone).")
                
                scelta = st.multiselect(f"Modifica Team {r['Hotel']}", opts, default=attuali, key=key)
                # Salviamo i dati aggiornati per il PDF
                final_list.append({
                    "Hotel": r['Hotel'], 
                    "Team": ", ".join(scelta), 
                    "Bilancio": bilancio_str,
                    "Req": fabbisogno
                })

        # 3. Riepilogo Panchina
        vere_libere_finali = sorted(list(tutte_attive - tutti_scelti))
        if vere_libere_finali:
            st.info(f"🏃 IN PANCHINA: {', '.join(vere_libere_finali)}")

        if st.button("🧊 CONFERMA E SCARICA PDF"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, st.session_state.get('spl_v_fin', []), assenti)
            st.download_button("📥 DOWNLOAD", pdf, f"Planning_{data_p}.pdf")
