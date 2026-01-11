import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- DATABASE E CONFIGURAZIONE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    return pd.DataFrame()

# --- FUNZIONE PDF MIGLIORATA ---
def genera_pdf(data_str, schieramento, split_list):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # Intestazione
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    
    y = h - 100
    p.setFont("Helvetica-Bold", 12)
    
    for res in schieramento:
        if y < 150: # Controllo fine pagina
            p.showPage()
            y = h - 70
            p.setFont("Helvetica-Bold", 12)

        # Box Zona
        p.setFillColorRGB(0.9, 0.9, 0.9)
        p.rect(50, y - 5, 490, 20, fill=1, stroke=0)
        p.setFillColorRGB(0, 0, 0)
        p.drawString(55, y, f"ZONA: {res['Hotel'].upper()}")
        y -= 25
        
        p.setFont("Helvetica", 11)
        p.drawString(65, y, f"Team: {res['Team']}")
        y -= 20
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(65, y, f"Responsabile: {res['Responsabile']}")
        y -= 35

    # Sezione Spezzato fissa in fondo o nuova pagina
    if y < 150:
        p.showPage()
        y = h - 70

    p.line(50, y, 540, y)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(60, y, f"Cameriere: {', '.join(split_list) if split_list else 'Nessuna'}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- LOGICA PLANNING ---
df = load_data()
with st.container():
    st.header("🚀 Elaborazione Planning")
    
    # ... (Qui carichi i tuoi dati di input camere: AI, FI, COP, BIA) ...
    # Assumiamo di avere una lista 'current_plan' con i dati inseriti
    
    if st.button("🚀 GENERA E CONTROLLA CARICO ORE"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(st.session_state.get('assenti', []))]
        
        # 1. Identificazione Split (per pesare correttamente il diurno)
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)]
        nomi_split = pool_split.sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        schieramento_per_pdf = []
        
        for hotel in lista_hotel:
            # --- CALCOLO ORE NECESSARIE ---
            # (Prendi i valori inseriti nei number_input per quell'hotel)
            h_c = conf_df[conf_df['Hotel'] == hotel].iloc[0] if not conf_df.empty else {"Arr_Ind":60, "Fer_Ind":30, "Arr_Gru":45, "Fer_Gru":20}
            # Supponiamo row sia il dizionario con i dati inseriti per l'hotel
            ore_servono = 15.0 # Esempio: calcolato da (AI*60 + FI*30 + ...) / 60
            
            # --- CALCOLO ORE FORNITE ---
            # Supponiamo che team_zona siano i nomi assegnati a quell'hotel
            team_zona = ["Marcella", "Isotta"] 
            ore_fornite = 0
            for n in team_zona:
                p_info = attive[attive['Nome'] == n].iloc[0]
                # Se PT o Split -> 5h. Se Full -> 7.5h.
                if str(p_info['Part_Time']) in ["1", "True"] or n in nomi_split:
                    ore_fornite += 5.0
                else:
                    ore_fornite += 7.5
            
            diff = ore_fornite - ore_servono
            
            # Mostra Alert
            if ore_servono > 0:
                if diff < 0:
                    st.error(f"⚠️ **{hotel}**: Mancano **{abs(diff)}h**. (Servono {ore_servono}h, fornite {ore_fornite}h)")
                else:
                    st.success(f"✅ **{hotel}**: Coperto! (+{diff}h)")

            schieramento_per_pdf.append({
                "Hotel": hotel,
                "Team": ", ".join(team_zona),
                "Responsabile": "Governante di Zona"
            })

        # --- BOTTONE PDF ---
        pdf_data = genera_pdf(datetime.now().strftime("%d/%m/%Y"), schieramento_per_pdf, nomi_split)
        st.download_button("📥 SCARICA PLANNING PDF", pdf_data, f"Planning_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
