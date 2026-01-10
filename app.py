import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Executive Housekeeping - Forte Village", layout="wide")

# --- FILE DI SISTEMA ---
FILE_DATA = 'housekeeping_database.csv'
FILE_HOTELS = 'hotel_list.csv'
FILE_CONFIG = 'config_tempi.csv'

# --- FUNZIONI CARICAMENTO ---
def load_data():
    if os.path.exists(FILE_DATA):
        try:
            df_temp = pd.read_csv(FILE_DATA)
            if not df_temp.empty:
                df_temp['Nome'] = df_temp['Nome'].astype(str).str.strip()
                df_temp['Zone_Padronanza'] = df_temp['Zone_Padronanza'].astype(str).str.strip()
            return df_temp
        except: return pd.DataFrame()
    return pd.DataFrame()

def load_hotels():
    hotel_default = ["Hotel Castello", "Hotel Castello Garden", "Le Dune", "Villa del Parco", "Bouganville", "Le Palme", "Il Borgo", "Le Ville"]
    if os.path.exists(FILE_HOTELS):
        try:
            lista = pd.read_csv(FILE_HOTELS)['Nome_Hotel'].str.strip().tolist()
            return [h for h in lista if h] if (lista and len(lista) > 0) else hotel_default
        except: return hotel_default
    return hotel_default

df = load_data()
lista_hotel = load_hotels()

# --- SIDEBAR (Rimane invariata) ---
with st.sidebar:
    st.header("⚙️ Gestione Personale")
    if not df.empty:
        csv_back = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Backup", data=csv_back, file_name='housekeeping_backup.csv', mime='text/csv')
    
    st.divider()
    modo = st.radio("Azione:", ["Inserisci Nuova", "Modifica Esistente"])
    
    nome_edit = None
    dati = {}
    if modo == "Modifica Esistente" and not df.empty:
        nome_edit = st.selectbox("Seleziona risorsa:", sorted(df['Nome'].tolist()))
        dati = df[df['Nome'] == nome_edit].iloc[0].to_dict()

    with st.form("form_staff", clear_on_submit=(modo == "Inserisci Nuova")):
        nome_in = nome_edit if modo == "Modifica Esistente" else st.text_input("Nome e Cognome")
        is_gov = st.checkbox("È una GOVERNANTE?", value=(dati.get('Ruolo') == "Governante"))
        ruolo = "Governante" if is_gov else "Cameriera"
        
        prof = st.slider("Professionalità", 1, 10, int(dati.get('Professionalita', 5)))
        esp = st.slider("Esperienza", 1, 10, int(dati.get('Esperienza', 5)))
        guida = st.slider("Capacità Guida", 1, 10, int(dati.get('Capacita_Guida', 10 if is_gov else 5)))
        
        st.divider()
        zone_at = str(dati.get('Zone_Padronanza', "")).split(", ")
        
        if is_gov:
            st.info("Assegnazione Fissa (Max 2 Hotel)")
            scelte_gov = st.multiselect("Alberghi:", lista_hotel, default=[h for h in zone_at if h in lista_hotel], max_selections=2)
            zona_assegnata = ", ".join(scelte_gov)
        else:
            st.write("**Zone di Padronanza**")
            scelte_cam = [h for h in lista_hotel if st.checkbox(h, key=f"side_{h}", value=(h in zone_at))]
            zona_assegnata = ", ".join(scelte_cam)

        relazioni = ["Nessuna"] + sorted([n for n in df['Nome'].tolist() if n != nome_in]) if not df.empty else ["Nessuna"]
        lavora_con = st.selectbox("Lavora bene con:", relazioni, index=relazioni.index(dati.get('Lavora_Bene_Con', "Nessuna")) if dati.get('Lavora_Bene_Con') in relazioni else 0)
        
        if st.form_submit_button("SALVA / AGGIORNA"):
            if nome_in:
                new_row = {
                    "Nome": nome_in.strip(), "Ruolo": ruolo, "Professionalita": prof, 
                    "Esperienza": esp, "Capacita_Guida": guida, 
                    "Zone_Padronanza": zona_assegnata, "Lavora_Bene_Con": lavora_con,
                    "Ultima_Modifica": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                if modo == "Modifica Esistente":
                    df = df[df['Nome'] != nome_edit]
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(FILE_DATA, index=False)
                st.success("Modifica registrata!")
                st.rerun()

# --- TABS ---
tab_home, tab_config, tab_planning = st.tabs(["🏆 Dashboard Staff", "⚙️ Tempi per Hotel", "🚀 Planning Giornaliero"])

with tab_home:
    if not df.empty:
        ultima_mod = df['Ultima_Modifica'].dropna().max() if 'Ultima_Modifica' in df.columns else "N/D"
        st.caption(f"🕒 Ultimo aggiornamento database: **{ultima_mod}**")
        df['Ranking'] = (df['Professionalita']*5) + (df['Esperienza']*5) + (df['Capacita_Guida']*4)
        st.dataframe(df.sort_values(['Ruolo', 'Ranking'], ascending=[False, False])[['Nome', 'Ruolo', 'Zone_Padronanza', 'Ranking', 'Lavora_Bene_Con']], use_container_width=True)

with tab_config:
    st.header("Configurazione Minuti")
    # Logica di sincronizzazione automatica
    if os.path.exists(FILE_CONFIG):
        config_df = pd.read_csv(FILE_CONFIG)
    else:
        config_df = pd.DataFrame(columns=["Hotel", "Arr_Ind", "Fer_Ind", "Arr_Gru", "Fer_Gru"])

    # Se un hotel della lista non è nel config, lo aggiungiamo subito
    presenti = config_df['Hotel'].tolist()
    mancanti = [h for h in lista_hotel if h not in presenti]
    if mancanti:
        nuovi_dati = [{"Hotel": h, "Arr_Ind": 60, "Fer_Ind": 30, "Arr_Gru": 45, "Fer_Gru": 20} for h in mancanti]
        config_df = pd.concat([config_df, pd.DataFrame(nuovi_dati)], ignore_index=True)

    with st.form("config_form"):
        updated_c = []
        for i, r in config_df.iterrows():
            if r['Hotel'] in lista_hotel:
                st.subheader(f"🏨 {r['Hotel']}")
                c1, c2 = st.columns(2)
                with c1:
                    ai = st.slider(f"Arrivo Ind.", 5, 90, int(r.get('Arr_Ind', 60)), key=f"ai_{i}")
                    ag = st.slider(f"Arrivo Gru.", 5, 90, int(r.get('Arr_Gru', 45)), key=f"ag_{i}")
                with c2:
                    fi = st.slider(f"Fermata Ind.", 5, 90, int(r.get('Fer_Ind', 30)), key=f"fi_{i}")
                    fg = st.slider(f"Fermata Gru.", 5, 90, int(r.get('Fer_Gru', 20)), key=f"fg_{i}")
                updated_c.append({"Hotel": r['Hotel'], "Arr_Ind": ai, "Fer_Ind": fi, "Arr_Gru": ag, "Fer_Gru": fg})
        
        if st.form_submit_button("SALVA CONFIGURAZIONE"):
            pd.DataFrame(updated_c).to_csv(FILE_CONFIG, index=False)
            st.success("Configurazione Tempi salvata per tutti gli hotel!")
            st.rerun()

with tab_planning:
    st.header("Planning Giornaliero")
    target = st.selectbox("Seleziona Hotel:", lista_hotel)
    if os.path.exists(FILE_CONFIG):
        c_f = pd.read_csv(FILE_CONFIG)
        # Cerchiamo i tempi per l'hotel selezionato
        h_row = c_f[c_f['Hotel'] == target]
        if not h_row.empty:
            h_c = h_row.iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Individuali**")
                n_ai = st.number_input("Arrivi", 0, 100, 0, key="p_ai")
                n_vi = st.number_input("Vuote", 0, 100, 0, key="p_vi")
                n_fi = st.number_input("Fermate", 0, 100, 0, key="p_fi")
            with col2:
                st.markdown("**Gruppi**")
                n_ag = st.number_input("Arrivi (G)", 0, 100, 0, key="p_ag")
                n_vg = st.number_input("Vuote (G)", 0, 100, 0, key="p_vg")
                n_fg = st.number_input("Fermate (G)", 0, 100, 0, key="p_fg")
            
            min_tot = ((n_ai + n_vi) * h_c['Arr_Ind']) + (n_fi * h_c['Fer_Ind']) + ((n_ag + n_vg) * h_c['Arr_Gru']) + (n_fg * h_c['Fer_Gru'])
            st.metric("Carico stimato (Ore)", f"{min_tot/60:.1f}")
            
            if st.button("CALCOLA SQUADRA"):
                govs = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                for _, g in govs.iterrows(): st.success(f"📌 Responsabile: **{g['Nome']}**")
                num_c = round((min_tot/60) / 7)
                cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(target, na=False))]
                st.table(cam.head(num_c if num_c > 0 else 3)[['Nome', 'Lavora_Bene_Con']])
        else:
            st.warning(f"Configura i tempi per {target} nel Tab precedente prima di pianificare.")
