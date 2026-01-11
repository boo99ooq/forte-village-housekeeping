import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resort Housekeeping Master", layout="wide")

# --- DATABASE ---
FILE_STAFF = 'Housekeeping_DB - Staff.csv'

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
        d = pd.to_numeric(row.get('Disponibilita', 5), errors='coerce') or 0 * 0.15
        em = pd.to_numeric(row.get('Empatia', 5), errors='coerce') * 0.10
        g = pd.to_numeric(row.get('Capacita_Guida', 5), errors='coerce') * 0.10
        voto_5 = round(((p + e + t + d + em + g) / 2) * 2) / 2
        return "🟩" * int(voto_5) + "🟨" * (1 if (voto_5 % 1) >= 0.5 else 0) + "⬜" * (5 - int(voto_5 + 0.5)), voto_5
    except: return "⬜⬜⬜⬜⬜", 0.0

df = load_data()

# --- SIDEBAR: GESTIONE ---
with st.sidebar:
    st.header("👤 Pannello Staff")
    nomi_staff = ["--- NUOVO ---"] + sorted(df['Nome'].tolist()) if not df.empty else ["--- NUOVO ---"]
    sel = st.selectbox("Seleziona:", nomi_staff)
    current = df[df['Nome'] == sel].iloc[0] if sel != "--- NUOVO ---" else None

    with st.form("form_staff"):
        f_nome = st.text_input("Nome", value=current['Nome'] if current is not None else "")
        f_ruolo = st.selectbox("Ruolo", ["Cameriera", "Governante"], index=0 if not current or "Cameriera" in current['Ruolo'] else 1)
        f_auto = st.text_input("Auto", value=current['Auto'] if current is not None else "")
        
        st.write("Voti (1-10)")
        c1, c2 = st.columns(2)
        f_pro = c1.number_input("Prof.", 0, 10, int(pd.to_numeric(current['Professionalita'], 0)) if current is not None else 5)
        f_esp = c2.number_input("Esp.", 0, 10, int(pd.to_numeric(current['Esperienza'], 0)) if current is not None else 5)
        
        if st.form_submit_button("💾 SALVA"):
            nuova_data = {"Nome": f_nome, "Ruolo": f_ruolo, "Auto": f_auto, "Professionalita": f_pro, "Esperienza": f_esp}
            if current is not None:
                for col in df.columns:
                    if col not in nuova_data: nuova_data[col] = current[col]
                df = df[df['Nome'] != sel]
            df = pd.concat([df, pd.DataFrame([nuova_data])], ignore_index=True)
            save_data(df)
            st.rerun()

    st.divider()
    # TASTO BACKUP
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV aggiornato", csv, "Housekeeping_DB_Staff_New.csv", "text/csv")

# --- DASHBOARD ---
if not df.empty:
    df[['Performance', 'Rating_Num']] = df.apply(lambda r: pd.Series(get_rating_bar(r)), axis=1)
    st.title("🏆 Dashboard Housekeeping")
    
    # SOLUZIONE AL KEYERROR: Includiamo Rating_Num nella selezione, ordiniamo, poi la nascondiamo
    view_df = df[['Nome', 'Ruolo', 'Performance', 'Zone_Padronanza', 'Auto', 'Rating_Num']]
    st.dataframe(
        view_df.sort_values('Rating_Num', ascending=False),
        column_config={"Rating_Num": None}, # Nasconde la colonna tecnica
        use_container_width=True, 
        hide_index=True
    )
