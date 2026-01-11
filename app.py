import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Import PDF
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
    lista_nomi = sorted(df['Nome'].tolist()) if not df.empty else []
    sel = st.selectbox("Seleziona collaboratore:", ["--- NUOVO ---"] + lista_nomi)
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None
    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if not current or "Cameriera" in str(current['Ruolo']) else 1)
        f_pt = st.checkbox("🕒 Part-Time", value=bool(current['Part_Time']) if current is not None else False)
        f_ind = st.checkbox("🚫 No Spezzato", value=bool(current['Indisp_Spezzato']) if current is not None else False)
        f_auto = st.selectbox("Viaggia con...", ["Nessuno"] + [n for n in lista_nomi if n != f_nome])
        f_zone = st.selectbox("Zona Padronanza", lista_hotel)
        st.write("**Valutazioni (1-10)**")
        v_pro = st.slider("Professionalità", 1, 10, int(current['Professionalita']) if current is not None else 5)
        v_esp = st.slider("Esperienza", 1, 10, int(current['Esperienza']) if current is not None else 5)
        if st.form_submit_button("💾 SALVA"):
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_ind else 0, 
                       "Auto": f_auto, "Zone_Padronanza": f_zone, "Professionalita": v_pro, "Esperienza": v_esp}
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
    st.header("⚙️ Configurazione Tempi Standard")
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_c = []
    for h in lista_hotel:
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI", 5, 120, 60, key=f"t_ai_{h}")
        fi = cols[2].number_input("FI", 5, 120, 30, key=f"t_fi_{h}")
        new_c.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": 45, "Fer_Gru": 20})
    if st.button("💾 Salva Tempi"): pd.DataFrame(new_c).to_csv(FILE_CONFIG, index=False); st.success("Tempi Salvati!")

with t3:
    st.header("🚀 Elaborazione Planning")
    data_p = st.date_input("Data:", datetime.now())
    assenti = st.multiselect("🛌 Assenti:", lista_nomi)
    
    st.write("### 📊 Carico Lavoro")
    cur_inp = {h: {"AI": st.number_input(f"AI {h}", 0, 100, 0, key=f"ai_{h}"), "FI": st.number_input(f"FI {h}", 0, 100, 0, key=f"fi_{h}")} for h in lista_hotel}

    if st.button("🚀 GENERA SCHIERAMENTO"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[(~df['Nome'].isin(assenti))].copy()
        
        # 1. Spezzato
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0) & (attive['Ruolo'] == 'Cameriera')].sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        # 2. Macro-Zona Palme+Garden
        def calc_ore(hotel_nome):
            t = conf_df[conf_df['Hotel'] == hotel_nome].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30}
            return (cur_inp[hotel_nome]["AI"]*t["Arr_Ind"] + cur_inp[hotel_nome]["FI"]*t["Fer_Ind"]) / 60

        fabbisogni = {h: calc_ore(h) for h in lista_hotel}
        fabbisogni["MACRO: PALME & GARDEN"] = fabbisogni.get("Le Palme", 0) + fabbisogni.get("Hotel Castello Garden", 0)
        
        zone_lavoro = [h for h in lista_hotel if h not in ["Le Palme", "Hotel Castello Garden"]] + ["MACRO: PALME & GARDEN"]
        
        gia_ass, ris = [], []
        for zona in zone_lavoro:
            ore_nec = fabbisogni.get(zona, 0)
            if ore_nec > 0:
                team_h, ore_f = [], 0
                cand = attive[~attive['Nome'].isin(gia_ass)].copy()
                cand['Priorita'] = cand['Zone_Padronanza'].apply(lambda x: 0 if (x == zona or (zona == "MACRO: PALME & GARDEN" and x in ["Le Palme", "Hotel Castello Garden"])) else 1)
                cand = cand.sort_values(['Priorita', 'Rating_Num'], ascending=[True, False])
                
                for _, p in cand.iterrows():
                    if ore_f < ore_nec or (p['Ruolo'] == 'Governante' and not any("(Gov.)" in n for n in team_h)):
                        label = f"⭐ {p['Nome']} (Gov.)" if p['Ruolo'] == 'Governante' else p['Nome']
                        if p['Ruolo'] == 'Governante': team_h.insert(0, label)
                        else:
                            team_h.append(label)
                            ore_f += 5.0 if (p['Part_Time'] == 1 or p['Nome'] in pool_split) else 7.5
                        gia_ass.append(p['Nome'])
                    if ore_f >= ore_nec and any("(Gov.)" in n for n in team_h): break
                ris.append({"Hotel": zona, "Team": ", ".join(team_h), "Ore Nec": round(ore_nec, 1)})
        
        st.session_state['res'] = ris; st.session_state['spl'] = pool_split; st.session_state['libere'] = list(set(attive[attive['Ruolo']=='Cameriera']['Nome']) - set(gia_ass))

    if 'res' in st.session_state:
        final_list = []
        for i, r in enumerate(st.session_state['res']):
            with st.expander(f"📍 {r['Hotel']} (Fabbisogno: {r['Ore Nec']}h)"):
                # Multiselect per bilanciare le 65 persone
                current_t = [n.strip() for n in r['Team'].split(",")]
                opzioni = sorted(list(set(current_t) | set(st.session_state['libere'])))
                edit_t = st.multiselect(f"Team {r['Hotel']}", opzioni, default=current_t, key=f"ed_{i}")
                final_list.append({"Hotel": r['Hotel'], "Team": ", ".join(edit_t)})
        
        if st.button("🧊 SALVA E SCARICA"):
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_list, st.session_state['spl'], assenti)
            st.download_button("📥 SCARICA PDF", pdf, "Planning.pdf", "application/pdf")
