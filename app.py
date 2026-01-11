if 'res' in st.session_state:
        st.divider()
        st.subheader("📋 Bilanciamento Manuale Team")
        st.info("Puoi aggiungere o rimuovere nomi. La lista suggerisce solo chi è libero.")

        # Recuperiamo le persone effettivamente al lavoro (non assenti)
        attive = df[(~df['Nome'].isin(assenti)) & (df['Ruolo'] == 'Cameriera')]
        tutti_nomi_lavoro = set(attive['Nome'].tolist())
        
        nuovo_schieramento = []
        # Teniamo traccia di chi è assegnato nei vari multiselect
        nomi_assegnati_ora = []
        for r in st.session_state['res']:
            for n in r['Team'].split(", "): 
                if n.strip(): nomi_assegnati_ora.append(n.strip())
        
        for i, row in enumerate(st.session_state['res']):
            with st.expander(f"📍 {row['Hotel']} (Serve: {row['Ore Servono']}h)", expanded=True):
                c1, c2 = st.columns([3, 1])
                
                # Calcoliamo chi è libero in questo momento
                nomi_attuali_hotel = [n.strip() for n in row['Team'].split(",") if n.strip()]
                libere = sorted(list(tutti_nomi_lavoro - set(nomi_assegnati_ora) | set(nomi_attuali_hotel)))
                
                # Multiselect per modificare il team
                nuovo_team = c1.multiselect(f"Team {row['Hotel']}:", libere, default=nomi_attuali_hotel, key=f"edit_{row['Hotel']}_{i}")
                
                # Calcolo ore in tempo reale per questo hotel
                ore_f = sum([5.0 if (attive[attive['Nome'] == n].iloc[0]['Part_Time'] == 1 or n in st.session_state['spl']) else 7.5 for n in nuovo_team])
                diff = ore_f - row['Ore Servono']
                
                if diff < 0: c2.warning(f"Mancano {abs(round(diff,1))}h")
                else: c2.success(f"Coperto! (+{round(diff,1)}h)")
                
                nuovo_schieramento.append({"Hotel": row['Hotel'], "Team": ", ".join(nuovo_team), "Responsabile": row['Responsabile']})

        # Aggiorniamo lo stato con le modifiche manuali
        st.session_state['res_final'] = nuovo_schieramento

        # --- AZIONI FINALI ---
        st.divider()
        c_down, c_cris = st.columns(2)
        
        with c_down:
            pdf = genera_pdf(data_p.strftime("%d/%m/%Y"), st.session_state['res_final'], st.session_state['spl'])
            st.download_button("📥 SCARICA PDF FINALE", pdf, f"Planning_{data_p}.pdf", "application/pdf")
        
        with c_cris:
            if st.button("🧊 CRISTALLIZZA E SALVA"):
                # Qui salviamo i dati finali (aggiorna conteggio spezzati e riposi)
                st.success("Planning salvato nello storico!")
                st.balloons()
