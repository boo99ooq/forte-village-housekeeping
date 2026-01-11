import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- CONFIGURAZIONE E CARICAMENTO ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        return pd.read_csv(FILE_STAFF).fillna("")
    return pd.DataFrame()

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(data, schieramento, split_list):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # Intestazione
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data}")
    p.line(50, h - 60, 540, h - 60)
    
    y = h - 100
    p.setFont("Helvetica-Bold", 12)
    
    # Zone e Team
    for index, row in schieramento.iterrows():
        if row['Team']:
            p.setFont("Helvetica-Bold", 11)
            p.drawString(50, y, f"ZONA: {row['Hotel']}")
            y -= 15
            p.setFont("Helvetica", 10)
            p.drawString(60, y, f"Team: {row['Team']}")
            y -= 10
            p.setFont("Helvetica-Oblique", 9)
            p.drawString(60, y, f"Responsabile: {row['Responsabile']}")
            y -= 25
            
            if y < 100: # Nuova pagina se spazio esaurito
                p.showPage()
                y = h - 50

    # Sezione Spezzato in fondo
    y -= 20
    p.line(50, y, 540, y)
    y -= 30
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Personale: {', '.join(split_list)}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- LOGICA APP STREAMLIT ---
st.title("🚀 Planning Pro + Export PDF")

df = load_data()
if not df.empty:
    # --- CALCOLO E ALERT ---
    st.subheader("📊 Analisi Copertura Ore")
    
    # Esempio dati (da integrare con la tua logica di inserimento camere)
    ore_necessarie_esempio = 15.5 
    # Calcolo ore fornite:
    # Supponiamo: 1 Full (7.5) + 1 PT (5) = 12.5 ore
    ore_fornite_esempio = 12.5 
    
    differenza = ore_fornite_esempio - ore_necessarie_esempio
    
    if differenza < 0:
        st.error(f"⚠️ **Sotto-organico!** All'Hotel Castello mancano {abs(differenza)} ore di lavoro per completare il pomeriggio.")
    else:
        st.success(f"✅ Copertura ottimale per Hotel Castello (+{differenza} ore).")

    # --- SIMULAZIONE DATI PER PDF ---
    schieramento_finto = pd.DataFrame([
        {"Hotel": "Hotel Castello", "Team": "Marcella, Isotta (PT)", "Responsabile": "Governante A"},
        {"Hotel": "Le Dune", "Team": "Leonarda, Medusa", "Responsabile": "Governante B"}
    ])
    lista_split = ["Eudossia", "Clarimunda"]

    # --- BOTTONI EXPORT ---
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Generazione PDF
        pdf_file = genera_pdf(datetime.now().strftime("%d/%m/%Y"), schieramento_finto, lista_split)
        st.download_button(
            label="📥 Scarica Planning PDF",
            data=pdf_file,
            file_name=f"Planning_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        
    with col2:
        # Testo WhatsApp (Già implementato)
        if st.button("📋 Genera Testo WhatsApp"):
            st.code("Testo pronto da copiare...")
