import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Import di sicurezza per ReportLab
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

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
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

def genera_pdf(data_str, schieramento, split_list, lista_assenti):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    y = h - 85
    if lista_assenti:
        p.setFont("Helvetica-Bold", 10); p.setFillColorRGB(0.7, 0, 0)
        p.drawString(50, y, f"🛌 ASSENTI: {', '.join(lista_assenti)}")
        y -= 25; p.setFillColorRGB(0, 0, 0)
    for res in schieramento:
        if y < 100: p.showPage(); y = h - 70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    y -= 20; p.line(50, y, 540, y); p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y - 30, "🌙 COPERTURA SERALE")
    p.setFont("Helvetica", 11); p.drawString(60, y - 50, f"Personale: {', '.join(split_list)}")
    p.save(); buffer.seek(0)
    return buffer

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Gestione Staff")
    lista_nomi = sorted(df['Nome'].tolist()) if not df.empty else []
    sel = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + lista_nomi)
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None
    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if not current or "Cameriera" in str(current['Ruolo']) else 1)
        c_opt = st.columns(2)
        f_pt = c_opt[0].checkbox("🕒 Part-Time", value=bool(current['Part_Time']) if current is not None else False)
        f_indisp = c_opt[1].checkbox("🚫 No Spezzato", value=bool(current['Indisp_Spezzato']) if current is not None else False)
        opzioni_auto = ["Nessuno"] + [n for n in lista_nomi if n != f_nome]
        v_attuale = str(current['Auto']) if current is not None and str(current['Auto']) != "0" else "Nessuno"
        f_auto = st.selectbox("Viaggia con...", opzioni_auto, index=opzioni_auto.index(v_attuale) if v_attuale in opzioni_auto else 0)
        f_zone = st.selectbox("Zona Padronanza", lista_hotel, index=lista_hotel.index(str(current['Zone_Padronanza'])) if current is not None and str(current['Zone_Padronanza']) in lista_hotel else 0)
        st.write("**Valutazioni**")
        col1, col2 = st.columns(2)
        v_pro = col1.number_input("Prof.", 1, 10, int(current['Professionalita']) if current is not None else 5)
        v_esp = col2.number_input("Esp.", 1, 10, int(current['Esperienza']) if current is not None else 5)
        v_ten = col1.number_input("Tenuta Fis.", 1, 10, int(current['Tenuta_Fisica']) if current is not None else 5)
        v_dis = col2.number_input("Disp.", 1, 10, int(current['Disponibilita']) if current is not None else 5)
        v_emp = col1.number_input("Empatia", 1, 10, int(current['Empatia']) if current is not None else 5)
        v_gui = col2.number_input("Guida", 1, 10, int(current['Capacita_Guida']) if current is not None else 5)
        if st.form_submit_button("💾 SALVA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_indisp else 0, 
                       "Auto": f_auto if f_auto != "Nessuno" else "", "Zone_Padronanza": f_zone, "Professionalita": v_pro, "Esperienza": v_esp, 
                       "Tenuta_Fisica": v_ten, "Disponibilita": v_dis, "Empatia": v_emp, "Capacita_Guida": v_gui}
            if current is not None: df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'Conteggio_Spezzati', 'Auto']], use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        vs = [60, 30, 45, 20] 
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI", 5, 200, vs[0], key=f"t_ai_{h}")
        fi = cols[2].number_input("FI", 5, 200, vs[1], key=f"t_fi_{h}")
        ag = cols[3].number_input("AG", 5, 200, vs[2], key=f"t_ag_{h}")
        fg = cols[4].number_input("FG", 5, 200, vs[3], key=f"t_fg_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"): pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Salvati!")

with t3:
    st.header("🚀 Planning Giornaliero")
    data_p = st.date_input("Giorno:", datetime.now())
    assenti = st.multiselect("🛌 Assenti/Riposi:", lista_nomi)
    
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

    if st.button("🚀 GENERA SCHIERAMENTO"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[(~df['Nome'].isin(assenti)) & (df['Ruolo'] == 'Cameriera')].copy()
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)].sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        gia_assegnate = []
        ris = []

        # --- 1. PRE-CALCOLO ORE PER TUTTI GLI HOTEL ---
        fabbisogno_per_hotel = {}
        for inp in cur_inp:
            t = conf_df[conf_df['Hotel'] == inp['Hotel']].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30}
            ore_nec = (inp['AI']*t['Arr_Ind'] + inp['FI']*t['Fer_Ind'] + inp['COP']*(t['Fer_Ind']/3) + inp['BIA']*(t['Fer_Ind']/4)) / 60
            fabbisogno_per_hotel[inp['Hotel']] = ore_nec

        # --- 2. LOGICA DI UNIONE (PALME + GARDEN) ---
        fabbisogno_per_hotel["UNICO: PALME & GARDEN"] = fabbisogno_per_hotel.get("Le Palme", 0) + fabbisogno_per_hotel.get("Hotel Castello Garden", 0)
        
        # Lista degli hotel da processare (escludiamo quelli singoli già uniti)
        lista_processo = [h for h in lista_hotel if h not in ["Le Palme", "Hotel Castello Garden"]]
        lista_processo.append("UNICO: PALME & GARDEN")

        # --- 3. ASSEGNAZIONE EFFETTIVA ---
        for nome_zona in lista_processo:
            ore_nec = fabbisogno_per_hotel.get(nome_zona, 0)
            
            if ore_nec > 0:
                team_hotel = []
                ore_fornite_attuali = 0
                
                candidate = attive[~attive['Nome'].isin(gia_assegnate)].copy()
                
                # Priorità: se è la zona unita, cerca chi ha padronanza in uno dei due hotel
                if nome_zona == "UNICO: PALME & GARDEN":
                    candidate['Priorita'] = candidate['Zone_Padronanza'].apply(
                        lambda x: 0 if x in ["Le Palme", "Hotel Castello Garden"] else 1
                    )
                else:
                    candidate['Priorita'] = candidate['Zone_Padronanza'].apply(
                        lambda x: 0 if x == nome_zona else 1
                    )
                
                candidate = candidate.sort_values(['Priorita', 'Rating_Num'], ascending=[True, False])
                
                for _, cam in candidate.iterrows():
                    if ore_fornite_attuali < ore_nec:
                        team_hotel.append(cam['Nome'])
                        gia_assegnate.append(cam['Nome'])
                        ore_fornite_attuali += 5.0 if (cam['Part_Time'] == 1 or cam['Nome'] in pool_split) else 7.5
                    else:
                        break
                
                ris.append({
                    "Hotel": nome_zona, 
                    "Team": ", ".join(team_hotel), 
                    "Ore Servono": round(ore_nec, 1)
                })
        
        st.session_state['res'] = ris
        st.session_state['spl'] = pool_split
        st.session_state['rimaste_libere'] = list(set(attive['Nome'].tolist()) - set(gia_assegnate))
    # Visualizzazione risultati con controllo manuale
    if 'res' in st.session_state:
        st.write(f"### 📋 Schieramento Proposto ({len(lista_nomi) - len(assenti)} persone in turno)")
        
        for i, row in enumerate(st.session_state['res']):
            with st.expander(f"📍 {row['Hotel']} - Servono {row['Ore Servono']}h"):
                # Calcolo dinamico per la modifica manuale
                current_team = [n.strip() for n in row['Team'].split(",") if n.strip()]
                
                # Mostriamo chi è assegnato e permettiamo di aggiungere chi è rimasto libero
                opzioni = current_team + st.session_state.get('rimaste_libere', [])
                nuovo_team = st.multiselect(f"Staff per {row['Hotel']}:", sorted(opzioni), default=current_team, key=f"edit_{i}")
                
                # Ricalcolo ore in tempo reale
                ore_effettive = 0
                for nome in nuovo_team:
                    p_data = df[df['Nome'] == nome].iloc[0]
                    if p_data['Part_Time'] == 1 or nome in st.session_state['spl']:
                        ore_effettive += 5.0
                    else:
                        ore_effettive += 7.5
                
                if ore_effettive < row['Ore Servono']:
                    st.error(f"Sotto-organico! Fornite: {ore_effettive}h / Richieste: {row['Ore Servono']}h")
                else:
                    st.success(f"Coperto! Fornite: {ore_effettive}h")
        if st.button("🧊 CRISTALLIZZA E SCARICA"):
            df.loc[df['Nome'].isin(assenti), 'Ultimo_Riposo'] = data_p.strftime("%Y-%m-%d")
            df.loc[df['Nome'].isin(st.session_state['spl']), 'Conteggio_Spezzati'] += 1
            save_data(df)
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_team_list, st.session_state['spl'], assenti)
            st.download_button("📥 SCARICA PDF FINALE", pdf, "Planning.pdf", "application/pdf")
            st.balloons()
