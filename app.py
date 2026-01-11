import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. CONFIGURAZIONE E DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'
FILE_CONFIG = 'config_tempi.csv'
FILE_HISTORY = 'storico_planning.csv'

def inizializza_files():
    if not os.path.exists(FILE_STAFF):
        pd.DataFrame(columns=['Nome', 'Ruolo', 'Part_Time', 'Indisp_Spezzato', 'Conteggio_Spezzati', 'Ultimo_Riposo', 'Zone_Padronanza', 'Auto']).to_csv(FILE_STAFF, index=False)
    if not os.path.exists(FILE_CONFIG):
        pd.DataFrame(columns=['Hotel', 'Arr_Ind', 'Fer_Ind', 'Arr_Gru', 'Fer_Gru']).to_csv(FILE_CONFIG, index=False)
    if not os.path.exists(FILE_HISTORY):
        pd.DataFrame(columns=['Data', 'Hotel', 'Team', 'Responsabile', 'Team_Spezzato']).to_csv(FILE_HISTORY, index=False)

inizializza_files()

def load_data():
    df = pd.read_csv(FILE_STAFF)
    return df.fillna("")

# --- 2. FUNZIONE PDF ---
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

# --- 3. INTERFACCIA PRINCIPALE ---
st.title("🏨 Forte Village - Housekeeping Management")

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

t1, t2, t3, t4 = st.tabs(["🏆 Dashboard Staff", "⚙️ Configurazione Tempi", "🚀 Planning Giornaliero", "📅 Storico"])

# --- TAB 1: DASHBOARD ---
with t1:
    st.header("🏆 Performance e Stato Staff")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nessun dipendente censito. Usa la Sidebar a sinistra per aggiungere staff.")

# --- TAB 2: TEMPI ---
with t2:
    st.header("⚙️ Tempi Standard per Camera")
    st.write("Inserisci i minuti necessari per ogni tipologia di pulizia.")
    # (Codice per editing tempi...)

# --- TAB 3: PLANNING (Quello che ti mancava) ---
with t3:
    st.header("🚀 Elaborazione Planning")
    
    col_data, col_assenti = st.columns([1, 2])
    data_plan = col_data.date_input("Giorno:", datetime.now())
    assenti = col_assenti.multiselect("🛌 Seleziona Assenti/Riposi:", sorted(df['Nome'].tolist()) if not df.empty else [])

    st.subheader("📊 Inserimento Carico Lavoro")
    # Griglia per inserire il numero di camere (AI, FI, COP, BIA)
    current_input = []
    for h in lista_hotel:
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        c1.write(f"**{h}**")
        ai = c2.number_input("AI", 0, 100, 0, key=f"ai_{h}")
        fi = c3.number_input("FI", 0, 100, 0, key=f"fi_{h}")
        cop = c4.number_input("COP", 0, 100, 0, key=f"cop_{h}")
        bia = c5.number_input("BIA", 0, 100, 0, key=f"bia_{h}")
        current_input.append({"Hotel": h, "AI": ai, "FI": fi, "COP": cop, "BIA": bia})

    if st.button("🚀 GENERA SCHIERAMENTO"):
        attive = df[~df['Nome'].isin(assenti)]
        # Logica di assegnazione (semplificata per visualizzazione)
        nomi_split = attive[(attive['Part_Time'] == 0)].head(4)['Nome'].tolist()
        
        risultati = []
        for inp in current_input:
            if (inp['AI'] + inp['FI']) > 0:
                risultati.append({"Hotel": inp['Hotel'], "Team": "Nome Esempio 1, Nome Esempio 2", "Responsabile": "Gov. Esempio"})
        
        st.session_state['risultati'] = risultati
        st.session_state['split'] = nomi_split

    if 'risultati' in st.session_state:
        st.divider()
        st.subheader("📋 Risultato Proposto")
        st.table(pd.DataFrame(st.session_state['risultati']))
        st.info(f"🌙 **Spezzato:** {', '.join(st.session_state['split'])}")
        
        pdf_data = genera_pdf(data_plan.strftime("%d/%m/%Y"), st.session_state['risultati'], st.session_state['split'])
        st.download_button("📥 SCARICA PDF", pdf_data, f"Planning_{data_plan}.pdf", "application/pdf")

# --- TAB 4: STORICO ---
with t4:
    st.header("📅 Storico Planning")
    # (Visualizzazione file FILE_HISTORY)

# --- SIDEBAR SEMPRE VISIBILE ---
with st.sidebar:
    st.header("👤 Aggiungi/Modifica Staff")
    # (Modulo form_staff visto nei messaggi precedenti)
