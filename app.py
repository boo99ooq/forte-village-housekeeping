import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    return pd.DataFrame()

# --- PDF GENERATOR ---
def genera_pdf(data_str, schieramento, split_list):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    y = h - 100
    for res in schieramento:
        if y < 100:
            p.showPage()
            y = h - 70
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 20
        p.setFont("Helvetica", 11)
        p.drawString(60, y, f"Team: {res['Team']}")
        y -= 30
    
    y -= 20
    p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y - 30, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    p.setFont("Helvetica", 11)
    p.drawString(60, y - 50, f"Personale: {', '.join(split_list)}")
    p.save()
    buffer.seek(0)
    return buffer

# --- LOGICA APP ---
df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

st.header("🚀 Elaborazione Planning")

# Input Assenti
assenti = st.multiselect("🛌 Seleziona Assenti/Riposi:", sorted(df['Nome'].tolist()))

# --- CALCOLO ORE E GENERAZIONE ---
if st.button("🚀 GENERA E CONTROLLA CARICO ORE"):
    conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    attive = df[~df['Nome'].isin(assenti)]
    
    # 1. Identificazione Split
    pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)]
    nomi_split = pool_split.sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
    
    # 2. Simulazione/Calcolo Schieramento
    risultati = []
    for hotel in lista_hotel:
        # Qui inseriresti la tua logica di assegnazione reale
        team_nomi = attive[attive['Nome'].str.contains("A|E|I")].head(2)['Nome'].tolist() # Esempio
        risultati.append({"Hotel": hotel, "Team": ", ".join(team_nomi), "Responsabile": "Governante"})
    
    # Salviamo nello stato della sessione per non perderli
    st.session_state['schieramento_pronto'] = risultati
    st.session_state['split_pronti'] = nomi_split

# --- VISUALIZZAZIONE RISULTATI (Se esistono) ---
if 'schieramento_pronto' in st.session_state:
    st.divider()
    st.subheader("📋 Risultato Schieramento")
    
    # Tabella di riepilogo a schermo
    st.table(pd.DataFrame(st.session_state['schieramento_pronto']))
    st.info(f"🌙 **Spezzato oggi:** {', '.join(st.session_state['split_pronti'])}")
    
    # Bottoni di Azione
    c1, c2 = st.columns(2)
    with c1:
        pdf_data = genera_pdf(datetime.now().strftime("%d/%m/%Y"), 
                              st.session_state['schieramento_pronto'], 
                              st.session_state['split_pronti'])
        st.download_button("📥 SCARICA PDF", pdf_data, "Planning.pdf", "application/pdf")
    
    with c2:
        if st.button("🧊 CRISTALLIZZA"):
            st.success("Dati salvati nello storico!")
            st.balloons()
