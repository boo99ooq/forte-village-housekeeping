import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resort Staff Manager", layout="wide")

# --- NOME DEL FILE CARICATO ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'

def load_staff():
    if os.path.exists(FILE_STAFF):
        df = pd.read_csv(FILE_STAFF)
        # Pulizia intestazioni da spazi bianchi 
        df.columns = [c.strip() for c in df.columns]
        return df.fillna("")
    else:
        st.error(f"File {FILE_STAFF} non trovato. Caricalo nella cartella dell'app.")
        st.stop()

def save_staff(df):
    # Salvataggio locale delle modifiche apportate nell'app
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        # Calcolo stelle solo per le Cameriere 
        if 'ameriera' not in str(row['Ruolo']).lower(): 
            return "N/A", 0.0
            
        # Pesi ponderati basati sulle colonne del file 
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        
        # Conversione in base 5 con arrotondamento alla mezza unità
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        
        full = int(voto_5)
        half = 1 if (voto_5 % 1) >= 0.5 else 0
        empty = 5 - full - half
        return "🟩" * full + "🟨" * half + "⬜" * empty, voto_5
    except:
        return "⬜⬜⬜⬜⬜", 0.0

# --- LOGICA APPLICATIVA ---
df = load_staff()

with st.sidebar:
    st.header("👤 Pannello Gestione")
    mode = st.radio("Azione:", ["Modifica/Nuovo", "Elimina"])
    
    nomi = ["--- NUOVO ---"] + sorted(df['Nome'].tolist())
    sel = st.selectbox("Seleziona collaboratore:", nomi)
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    if mode == "Modifica/Nuovo":
        with st.form("form_staff"):
            f_nome = st.text_input("Nome", value=current['Nome'] if current is not None else "")
            f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], 
                                   index=0 if current is None else (0 if "Cameriera" in current['Ruolo'] else 1))
            
            c1, c2 = st.columns(2)
            # Caricamento valori dal CSV 
            f_pro = c1.number_input("Prof.", 0, 10, int(pd.to_numeric(current['Professionalita'], errors='coerce') or 5) if current is not None else 5)
            f_esp = c2.number_input("Esp.", 0, 10, int(pd.to_numeric(current['Esperienza'], errors='coerce') or 5) if current is not None else 5)
            f_ten = c1.number_input("Fisico", 0, 10, int(pd.to_numeric(current['Tenuta_Fisica'], errors='coerce') or 5) if current is not None else 5)
            f_dis = c2.number_input("Disp.", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
            f_emp = c1.number_input("Empatia", 0, 10, int(pd.to_numeric(current['Empatia'], errors='coerce') or 5) if current is not None else 5)
            f_gui = c2.number_input("Guida", 0, 10, int(pd.to_numeric(current['Capacita_Guida'], errors='coerce') or 5) if current is not None else 5)
            
            f_zone = st.text_input("Zone", value=current['Zone_Padronanza'] if current is not None else "")
            f_auto = st.text_input("Auto", value=current['Auto'] if current is not None else "")

            if st.form_submit_button("💾 SALVA"):
                # Mappatura campi per il file Housekeeping_DB - Staff.csv 
                nuova_riga = {
                    "Nome": f_nome, "Ruolo": f_ruolo, "Professionalita": f_pro, "Esperienza": f_esp,
                    "Tenuta_Fisica": f_ten, "Disponibilita": f_dis, "Empatia": f_emp,
                    "Capacita_Guida": f_gui, "Zone_Padronanza": f_zone, "Auto": f_auto
                }
                if sel != "--- NUOVO ---":
                    df = df[df['Nome'] != sel]
                df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
                save_staff(df)
                st.success(f"Scheda di {f_nome} salvata!")
                st.rerun()
    else:
        if sel != "--- NUOVO ---" and st.button("🗑️ ELIMINA DEFINITIVAMENTE"):
            df = df[df['Nome'] != sel]
            save_staff(df)
            st.rerun()

# --- DASHBOARD ---
df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)

st.title("🏆 Dashboard Housekeeping Resort")
# Visualizzazione basata sulle colonne caricate [cite: 1, 3]
st.dataframe(df[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto']].sort_values('Nome'), 
             use_container_width=True, hide_index=True)
