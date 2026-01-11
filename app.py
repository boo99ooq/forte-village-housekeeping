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
FILE_HISTORY = 'storico_planning.csv'

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

# --- PDF GENERATOR ---
def genera_pdf(data_str, schieramento, split_list, lista_assenti):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # Intestazione
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    
    y = h - 85
    if lista_assenti:
        p.setFont("Helvetica-Bold", 10)
        p.setFillColorRGB(0.7, 0, 0)
        p.drawString(50, y, f"🛌 ASSENTI / RIPOSI OGGI: {', '.join(lista_assenti)}")
        y -= 25
        p.setFillColorRGB(0, 0, 0)

    for res in schieramento:
        if y < 100: p.showPage(); y = h - 70
        p.setFont("Helvetica-Bold", 12); p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 15; p.setFont("Helvetica", 10); p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
    
    y -= 20; p.line(50, y, 540, y); p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y - 30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
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
        
        opzioni_auto = ["Auto Propria / Nessuno"] + [n for n in lista_nomi if n != f_nome]
        v_attuale = str(current['Auto']) if current is not None and str(current['Auto']) != "0" else "Auto Propria / Nessuno"
        f_auto = st.selectbox("Viaggia con...", opzioni_auto, index=opzioni_auto.index(v_attuale) if v_attuale in opzioni_auto else 0)
        
        z_attuale = str(current['Zone_Padronanza']) if current is not None else lista_hotel[0]
        f_zone = st.selectbox("Zona Padronanza", lista_hotel, index=lista_hotel.index(z_attuale) if z_attuale in lista_hotel else 0)
        
        st.write("**Valutazioni (1-10)**")
        col1, col2 = st.columns(2)
        v_pro = col1.number_input("Prof.", 1, 10, int(current['Professionalita']) if current is not None else 5)
        v_esp = col2.number_input("Esp.", 1, 10, int(current['Esperienza']) if current is not None else 5)
        v_ten = col1.number_input("Tenuta Fis.", 1, 10, int(current['Tenuta_Fisica']) if current is not None else 5)
        v_dis = col2.number_input("Disp.", 1, 10, int(current['Disponibilita']) if current is not None else 5)
        v_emp = col1.number_input("Empatia", 1, 10, int(current['Empatia']) if current is not None else 5)
        v_gui = col2.number_input("Guida", 1, 10, int(current['Capacita_Guida']) if current is not None else 5)

        if st.form_submit_button("💾 SALVA SCHEDA"):
            auto_salva = f_auto if f_auto != "Auto Propria / Nessuno" else ""
            nuova_d = {"Nome": f_nome, "Ruolo": f_ruolo, "Part_Time": 1 if f_pt else 0, "Indisp_Spezzato": 1 if f_indisp else 0, 
                       "Auto": auto_salva, "Zone_Padronanza": f_zone, "Professionalita": v_pro, "Esperienza": v_esp, 
                       "Tenuta_Fisica": v_ten, "Disponibilita": v_dis, "Empatia": v_emp, "Capacita_Guida": v_gui}
            if current is not None: df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_d])], ignore_index=True)
            save_data(df); st.rerun()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        df['G_Riposo'] = (datetime.now() - pd.to_datetime(df['Ultimo_Riposo'].replace(0, "2025-01-01"))).dt.days
        st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'G_Riposo', 'Conteggio_Spezzati', 'Auto']].sort_values('G_Riposo', ascending=False), use_container_width=True, hide_index=True)

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
    assenti = st.multiselect("🛌 Assenti/Riposi:", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    st.write("### 📊 Carico Camere")
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
        
        gia_assegnate, ris = pool_split.copy(), []
        for inp in cur_inp:
            t = conf_df[conf_df['Hotel'] == inp['Hotel']].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30}
            ore_nec = (inp['AI']*t['Arr_Ind'] + inp['FI']*t['Fer_Ind'] + inp['COP']*(t['Fer_Ind']/3) + inp['BIA']*(t['Fer_Ind']/4)) / 60
            if ore_nec > 0:
                team = attive[(attive['Zone_Padronanza'].str.contains(inp['Hotel'])) & (~attive['Nome'].isin(gia_assegnate))].head(2)['Nome'].tolist()
                gia_assegnate.extend(team)
                ris.append({"Hotel": inp['Hotel'], "Team": ", ".join(team), "Ore Servono": round(ore_nec, 1)})
        st.session_state['res'] = ris; st.session_state['spl'] = pool_split

    if 'res' in st.session_state:
        st.divider()
        final_team_list = []
        attive_all = df[(~df['Nome'].isin(assenti)) & (df['Ruolo'] == 'Cameriera')]
        
        for i, row in enumerate(st.session_state['res']):
            with st.expander(f"📍 {row['Hotel']} (Serve: {row['Ore Servono']}h)"):
                # Lista dinamica per multiselect: chi è libero o già qui
                occupate_altrove = [n for idx, r in enumerate(st.session_state['res']) if idx != i for n in r['Team'].split(", ")]
                libere = sorted(list(set(attive_all['Nome'].tolist()) - set(occupate_altrove) - set(st.session_state['spl'])))
                
                edit_team = st.multiselect(f"Modifica Team {row['Hotel']}", libere + row['Team'].split(", "), default=[n for n in row['Team'].split(", ") if n])
                ore_f = sum([5.0 if (attive_all[attive_all['Nome'] == n].iloc[0]['Part_Time'] == 1) else 7.5 for n in edit_team])
                
                if ore_f < row['Ore Servono']: st.warning(f"Mancano {round(row['Ore Servono']-ore_f,1)}h")
                else: st.success(f"Coperto! ({ore_f}h)")
                final_team_list.append({"Hotel": row['Hotel'], "Team": ", ".join(edit_team)})

        if st.button("🧊 CRISTALLIZZA E SCARICA"):
            df.loc[df['Nome'].isin(assenti), 'Ultimo_Riposo'] = data_p.strftime("%Y-%m-%d")
            df.loc[df['Nome'].isin(st.session_state['spl']), 'Conteggio_Spezzati'] += 1
            save_data(df)
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), final_team_list, st.session_state['spl'], assenti)
            st.download_button("📥 SCARICA PDF FINALE", pdf, "Planning.pdf", "application/pdf")
            st.balloons()
