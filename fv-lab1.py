import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- CONFIGURAZIONE PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    PDF_OK = True
except ImportError:
    PDF_OK = False

# --- COSTANTI E CONFIGURAZIONE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
LISTA_HOTEL = [
    "Hotel Castello", "Hotel Castello Garden", "Hotel Castello 4 Piano", 
    "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", 
    "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"
]

# --- 1. FUNZIONI DI GESTIONE DATI ---

def load_data():
    """Carica i dati dello staff dal file CSV."""
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        df.columns = [c.strip() for c in df.columns]
        cols_default = {
            'Part_Time': 0, 'Jolly': 0, 'Pendolare': 0, 'Riposo_Pref': '',
            'Viaggia_Con': '', 'Lavora_Bene_Con': 'Nessuna', 'Zone_Padronanza': '',
            'Professionalita': 5, 'Esperienza': 5, 'Tenuta_Fisica': 5, 
            'Disponibilita': 5, 'Empatia': 5, 'Capacita_Guida': 5
        }
        for col, val in cols_default.items():
            if col not in df.columns: df[col] = val
        df['Nome'] = df['Nome'].astype(str).str.strip()
        return df.fillna("")
    return pd.DataFrame(columns=['Nome', 'Ruolo'])

def save_data(df):
    """Salva il DataFrame su CSV."""
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    """Genera la barra visiva del rating."""
    try:
        if 'overnante' in str(row.get('Ruolo', '')).lower(): return "⭐ (Coord.)"
        v = (pd.to_numeric(row.get('Professionalita', 5))*0.25 + 
             pd.to_numeric(row.get('Esperienza', 5))*0.20 + 
             pd.to_numeric(row.get('Tenuta_Fisica', 5))*0.20 + 
             pd.to_numeric(row.get('Disponibilita', 5))*0.15)
        voto = round((v/2)*2)/2
        return "🟩"*int(voto) + ("🟨" if (voto%1)>=0.5 else "")
    except: return "⬜"*5

# --- 2. FUNZIONI PDF ---

def genera_pdf_planning(data_str, schieramento, lista_assenti):
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

# --- 3. COMPONENTI DELL'INTERFACCIA (TABS) ---

def tab_dashboard(df):
    st.header("🏆 Performance Staff")
    if not df.empty:
        df_v = df.copy()
        df_v['Rating'] = df_v.apply(get_rating_bar, axis=1)
        df_v['Status'] = df_v.apply(lambda r: ("🃏 " if r['Jolly'] else "") + ("🚌 " if r['Pendolare'] else ""), axis=1)
        st.dataframe(df_v[['Status', 'Nome', 'Ruolo', 'Rating', 'Zone_Padronanza', 'Lavora_Bene_Con']], 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nessun dato disponibile. Aggiungi staff nell'anagrafica.")

def tab_anagrafica(df):
    st.header("📝 Scheda Personale")
    nomi_db = sorted(df['Nome'].unique().tolist()) if not df.empty else []
    sel_n = st.selectbox("Seleziona collaboratrice per modificare:", ["--- NUOVA ---"] + nomi_db)
    
    curr = df[df['Nome'] == sel_n].iloc[0] if sel_n != "--- NUOVA ---" else None
    
    with st.form("form_staff"):
        c1, c2, c3 = st.columns(3)
        f_nome = c1.text_input("Nome e Cognome", value=str(curr['Nome']) if curr is not None else "")
        f_ruolo = c2.selectbox("Ruolo", ["Cameriera", "Governante"], 
                               index=1 if curr is not None and "overnante" in str(curr['Ruolo']).lower() else 0)
        def_padro = [z.strip() for z in str(curr['Zone_Padronanza']).split(",") if z.strip() in LISTA_HOTEL] if curr is not None else []
        f_padro = c3.multiselect("Zone di Padronanza", LISTA_HOTEL, default=def_padro)
        
        # ... (Resto dei campi del form semplificati per brevità, mantieni i tuoi slider e checkbox)
        st.form_submit_button("💾 SALVA SCHEDA")
        # Logica di salvataggio identica alla tua...

def tab_tempi():
    st.header("⚙️ Configurazione Tempi Standard")
    # Caricamento e visualizzazione dei tempi come nel tuo codice originale
    # ...

def tab_planning(df):
    st.header("🚀 Generazione Planning")
    # Tutta la logica del calcolo e dello schieramento
    # ...

# --- 4. MAIN APP ---

def main():
    st.set_page_config(page_title="Forte Village Housekeeping", layout="wide")
    
    # Inizializzazione dati
    df = load_data()
    
    # Definizione Tab
    t_dash, t_staff, t_tempi, t_plan = st.tabs(["🏆 Dashboard", "👥 Anagrafica", "⚙️ Tempi", "🚀 Planning"])
    
    with t_dash:
        tab_dashboard(df)
        
    with t_staff:
        tab_anagrafica(df)
        
    with t_tempi:
        tab_tempi()
        
    with t_plan:
        tab_planning(df)

if __name__ == "__main__":
    main()
