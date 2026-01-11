import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Importiamo reportlab con un controllo di sicurezza
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import_pdf_ok = True
except ImportError:
    import_pdf_ok = False

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_LAST_PLAN = 'ultimo_planning_caricato.csv'

def load_data():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        for col in ['Part_Time', 'Indisp_Spezzato', 'Conteggio_Spezzati']:
            if col not in df.columns: df[col] = 0
        return df.fillna("")
    return pd.DataFrame()

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- FUNZIONE PDF ---
def genera_pdf(data_str, schieramento, split_list):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, f"PLANNING HOUSEKEEPING - {data_str}")
    p.line(50, h - 60, 540, h - 60)
    
    y = h - 100
    for res in schieramento:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"ZONA: {res['Hotel']}")
        y -= 15
        p.setFont("Helvetica", 10)
        p.drawString(60, y, f"Team: {res['Team']}")
        y -= 25
        if y < 100:
            p.showPage()
            y = h - 50
    
    y -= 20
    p.line(50, y, 540, y)
    y -= 30
    p.setFont("Helvetica-Bold", 13)
    p.drawString(50, y, "🌙 COPERTURA SERALE (19:00 - 22:00)")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Personale: {', '.join(split_list)}")
    p.save()
    buffer.seek(0)
    return buffer

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning", "📅 Storico"])

with t3:
    st.header("🚀 Elaborazione e Controllo Ore")
    data_sel = st.date_input("Data Planning:", datetime.now())
    assenti = st.multiselect("🛌 Assenti/Riposi:", sorted(df['Nome'].tolist()))
    
    # Inserimento dati camere (simulato)
    st.write("### Inserimento Carico Lavoro")
    # ... qui il codice dei number_input per AI, FI, COP ...
    
    if st.button("🚀 GENERA E CONTROLLA"):
        conf_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
        attive = df[~df['Nome'].isin(assenti)]
        
        # 1. Scelta Split
        pool_split = attive[(attive['Part_Time'] == 0) & (attive['Indisp_Spezzato'] == 0)]
        nomi_split = pool_split.sort_values('Conteggio_Spezzati').head(4)['Nome'].tolist()
        
        # 2. Analisi e Alert
        schieramento_finale = []
        for h in lista_hotel:
            # Esempio: calcoliamo le ore necessarie per l'hotel (logica FI/AI)
            ore_servono = 15.0 # Dato simulato
            
            # Calcoliamo le ore fornite dal team assegnato
            # (Qui dovresti avere la logica che assegna i nomi)
            team_nomi = ["Marcella", "Isotta"] 
            ore_fornite = 0
            for n in team_nomi:
                persona = attive[attive['Nome'] == n].iloc[0]
                if str(persona['Part_Time']) in ["1", "True"] or n in nomi_split:
                    ore_fornite += 5.0
                else:
                    ore_fornite += 7.5
            
            diff = ore_fornite - ore_servono
            if diff < 0:
                st.error(f"⚠️ **{h}**: Mancano {abs(diff)} ore! Team attuale fornisce solo {ore_fornite}h su {ore_servono}h necessarie.")
            else:
                st.success(f"✅ **{h}**: Coperto ({ore_fornite}h fornite).")
            
            schieramento_finale.append({"Hotel": h, "Team": ", ".join(team_nomi), "Ore": ore_fornite})

        # --- EXPORT PDF ---
        st.divider()
        if import_pdf_ok:
            pdf = genera_pdf(data_sel.strftime("%d/%m/%Y"), schieramento_finale, nomi_split)
            st.download_button("📥 SCARICA PDF PER GOVERNANTI", data=pdf, file_name=f"Planning_{data_sel}.pdf", mime="application/pdf")
        else:
            st.warning("Installa 'reportlab' via requirements.txt per scaricare il PDF.")
