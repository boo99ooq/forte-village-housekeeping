with t3:
    st.header("🚀 Piano Operativo Globale Resort")
    st.write("Inserisci i carichi di lavoro per tutti gli hotel:")

    # Creiamo una struttura dati per l'input
    input_data = []
    
    # Intestazione colonne per chiarezza
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6, h_col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
    h_col2.caption("Arr. Ind.")
    h_col3.caption("Fer. Ind.")
    h_col4.caption("Vuo. Ind.")
    h_col5.caption("Arr. Gru.")
    h_col6.caption("Fer. Gru.")
    h_col7.caption("Vuo. Gru.")

    for h in lista_hotel:
        c = st.columns([2, 1, 1, 1, 1, 1, 1])
        c[0].markdown(f"**{h}**")
        ai = c[1].number_input("", 0, 100, 0, key=f"ai_{h}", label_visibility="collapsed")
        fi = c[2].number_input("", 0, 100, 0, key=f"fi_{h}", label_visibility="collapsed")
        vi = c[3].number_input("", 0, 100, 0, key=f"vi_{h}", label_visibility="collapsed")
        ag = c[4].number_input("", 0, 100, 0, key=f"ag_{h}", label_visibility="collapsed")
        fg = c[5].number_input("", 0, 100, 0, key=f"fg_{h}", label_visibility="collapsed")
        vg = c[6].number_input("", 0, 100, 0, key=f"vg_{h}", label_visibility="collapsed")
        input_data.append({"Hotel": h, "AI": ai, "FI": fi, "VI": vi, "AG": ag, "FG": fg, "VG": vg})

    st.divider()
    
    if st.button("🚀 GENERA PIANO DI LAVORO RESORT"):
        if os.path.exists(FILE_CONFIG):
            conf = pd.read_csv(FILE_CONFIG)
            risultati = []
            
            for row in input_data:
                h_c = conf[conf['Hotel'] == row['Hotel']].iloc[0]
                
                # Calcolo ore (usando i tempi salvati nel Tab 2)
                min_tot = ((row['AI'] + row['VI']) * h_c['Arr_Ind']) + (row['FI'] * h_c['Fer_Ind']) + \
                          ((row['AG'] + row['VG']) * h_c['Arr_Gru']) + (row['FG'] * h_c['Fer_Gru'])
                ore = min_tot / 60
                
                if ore > 0:
                    # Identifica Governante
                    gov = df[(df['Ruolo'] == "Governante") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    nomi_gov = ", ".join(gov['Nome'].tolist()) if not gov.empty else "DA ASSEGNARE"
                    
                    # Suggerimento cameriere
                    num_nec = round(ore / 7) if ore >= 7 else 1
                    cam = df[(df['Ruolo'] == "Cameriera") & (df['Zone_Padronanza'].str.contains(row['Hotel'], na=False))]
                    if cam.empty: 
                        cam = df[df['Ruolo'] == "Cameriera"].sort_values('Professionalita', ascending=False)
                    
                    nomi_cam = ", ".join(cam.head(num_nec)['Nome'].tolist())
                    
                    risultati.append({
                        "Hotel": row['Hotel'],
                        "Ore Fabbisogno": round(ore, 1),
                        "Governante": nomi_gov,
                        "Cameriere Suggerite": nomi_cam
                    })
            
            if risultati:
                st.write("### 📋 Proposta di Schieramento")
                st.table(pd.DataFrame(risultati))
            else:
                st.warning("Nessun carico di lavoro inserito.")
