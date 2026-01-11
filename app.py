import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

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

def save_data(df):
    df.to_csv(FILE_STAFF, index=False)

def get_rating_bar(row):
    try:
        if 'ameriera' not in str(row.get('Ruolo', '')).lower(): return "N/A", 0.0
        p = pd.to_numeric(row.get('Professionalita', 5), errors='coerce') * 0.25
        e = pd.to_numeric(row.get('Esperienza', 5), errors='coerce') * 0.20
        t = pd.to_numeric(row.get('Tenuta_Fisica', 5), errors='coerce') * 0.20
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        return "🟩" * int(voto_5) + "🟨" * (1 if (voto_5 % 1) >= 0.5 else 0) + "⬜" * (5 - int(voto_5 + 0.5)), voto_5
    except: return "⬜⬜⬜⬜⬜", 0.0

df = load_data()
lista_hotel = ["Hotel Castello", "Hotel Castello Garden", "Castello 4 Piano", "Cala del Forte", "Le Dune", "Villa del Parco", "Hotel Pineta", "Bouganville", "Le Palme", "Il Borgo", "Le Ville", "Spazi Comuni"]

# --- SIDEBAR: GESTIONE ---
with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=str(current['Nome']) if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], 
                               index=0 if current is None or "Cameriera" in str(current['Ruolo']) else 1)
        f_auto = st.text_input("Auto", value=str(current['Auto']) if current is not None else "")
        f_zone = st.text_input("Zone Padronanza", value=str(current['Zone_Padronanza']) if current is not None else "")
        
        st.write("--- Valutazioni (1-10) ---")
        c1, c2 = st.columns(2)
        # Inserimento di tutti i parametri per il calcolo dei mattoncini
        f_pro = c1.number_input("Professionalità", 0, 10, int(pd.to_numeric(current['Professionalita'], errors='coerce') or 5) if current is not None else 5)
        f_esp = c2.number_input("Esperienza", 0, 10, int(pd.to_numeric(current['Esperienza'], errors='coerce') or 5) if current is not None else 5)
        f_ten = c1.number_input("Tenuta Fisica", 0, 10, int(pd.to_numeric(current['Tenuta_Fisica'], errors='coerce') or 5) if current is not None else 5)
        f_dis = c2.number_input("Disponibilità", 0, 10, int(pd.to_numeric(current['Disponibilita'], errors='coerce') or 5) if current is not None else 5)
        f_emp = c1.number_input("Empatia", 0, 10, int(pd.to_numeric(current['Empatia'], errors='coerce') or 5) if current is not None else 5)
        f_gui = c2.number_input("Capacità Guida", 0, 10, int(pd.to_numeric(current['Capacita_Guida'], errors='coerce') or 5) if current is not None else 5)
        
        submitted = st.form_submit_button("💾 SALVA SCHEDA COMPLETA")
        if submitted:
            # Creiamo il dizionario con i dati aggiornati
            nuova_data = {
                "Nome": f_nome, 
                "Ruolo": f_ruolo, 
                "Auto": f_auto, 
                "Zone_Padronanza": f_zone,
                "Professionalita": f_pro, 
                "Esperienza": f_esp,
                "Tenuta_Fisica": f_ten,
                "Disponibilita": f_dis,
                "Empatia": f_emp,
                "Capacita_Guida": f_gui
            }
            
            # Se stiamo modificando, manteniamo i valori delle colonne che non sono nel form (es. Jolly, Pendolare)
            if current is not None:
                for col in df.columns:
                    if col not in nuova_data: 
                        nuova_data[col] = current[col]
                df = df[df['Nome'] != sel]
            
            df = pd.concat([df, pd.DataFrame([nuova_data])], ignore_index=True)
            save_data(df)
            st.success(f"Dati di {f_nome} aggiornati correttamente!")
            st.rerun()
# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 Dashboard", "⚙️ Tempi", "🚀 Planning"])

with t1:
    if not df.empty:
        df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
        st.subheader("Performance e Logistica")
        view_df = df[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto', 'Rating_Num']]
        st.dataframe(view_df.sort_values('Rating_Num', ascending=False), 
                     column_config={"Rating_Num": None}, use_container_width=True, hide_index=True)

with t2:
    st.header("⚙️ Configurazione Tempi")
    # Caricamento tempi
    c_df = pd.read_csv(FILE_CONFIG) if os.path.exists(FILE_CONFIG) else pd.DataFrame()
    new_config = []
    for h in lista_hotel:
        vs = [60, 30, 45, 20]
        if not c_df.empty and h in c_df['Hotel'].values:
            r = c_df[c_df['Hotel'] == h].iloc[0]
            vs = [int(r['Arr_Ind']), int(r['Fer_Ind']), int(r['Arr_Gru']), int(r['Fer_Gru'])]
        cols = st.columns([2,1,1,1,1])
        cols[0].write(f"**{h}**")
        ai = cols[1].number_input("AI", 5, 200, vs[0], key=f"ai_{h}", label_visibility="collapsed")
        fi = cols[2].number_input("FI", 5, 200, vs[1], key=f"fi_{h}", label_visibility="collapsed")
        ag = cols[3].number_input("AG", 5, 200, vs[2], key=f"ag_{h}", label_visibility="collapsed")
        fg = cols[4].number_input("FG", 5, 200, vs[3], key=f"fg_{h}", label_visibility="collapsed")
        new_config.append({"Hotel": h, "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
    if st.button("💾 Salva Tempi"):
        pd.DataFrame(new_config).to_csv(FILE_CONFIG, index=False)
        st.success("Configurazione salvata!")

with t3:
    st.header("🚀 Planning Operativo")
    assenti = st.multiselect("🏖️ Assenti:", sorted(df['Nome'].tolist()) if not df.empty else [])
    
    if st.button("🧹 Reset Planning"):
        pd.DataFrame(columns=["Hotel", "AI", "FI", "VI", "AG", "FG", "VG"]).to_csv(FILE_LAST_PLAN, index=False)
        st.rerun()

    st.divider()
    # Logistica Auto
    if assenti and 'Auto' in df.columns:
        for a in assenti:
            auto_v = df[df['Nome'] == a]['Auto'].values[0]
            if auto_v:
                comp = df[(df['Auto'] == auto_v) & (~df['Nome'].isin(assenti))]
                if not comp.empty: st.warning(f"⚠️ {a} assente. Avvisa: {', '.join(comp['Nome'].tolist())}")

    # (Logica Schieramento identica a quella funzionante sopra)
