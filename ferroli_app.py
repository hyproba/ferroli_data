import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from datetime import datetime

st.title("Ferroli CSV Visualisatietool")

# Kies map waar CSV-bestanden staan
folder_path = st.text_input("Pad naar directory met Ferroli CSV-bestanden", value="./data")

if os.path.isdir(folder_path):
    # Vind alle .txt of .csv bestanden in de map
    file_list = sorted(glob.glob(os.path.join(folder_path, '*.txt')) +
                       glob.glob(os.path.join(folder_path, '*.csv')))

    if not file_list:
        st.warning("Geen CSV- of TXT-bestanden gevonden in deze map.")
    else:
        dataframes = []
        for file in file_list:
            try:
                df = pd.read_csv(file, sep=';', engine='python')
                df['__sourcefile'] = os.path.basename(file)
                dataframes.append(df)
            except Exception as e:
                st.error(f"Fout bij inlezen van {file}: {e}")

        if dataframes:
            df_all = pd.concat(dataframes, ignore_index=True)
            
            # Tijdkolom normaliseren
            if 'time[h:m:s]' in df_all.columns:
                df_all['time[h:m:s]'] = pd.to_datetime(df_all['time[h:m:s]'], errors='coerce')
                df_all = df_all.dropna(subset=['time[h:m:s]'])

                # Voeg kolom toe in seconden sinds middernacht voor filter
                df_all['time_in_seconds'] = df_all['time[h:m:s]'].dt.hour * 3600 + \
                                             df_all['time[h:m:s]'].dt.minute * 60 + \
                                             df_all['time[h:m:s]'].dt.second

                parameters = [col for col in df_all.columns if col not in ['time[h:m:s]', 'time_in_seconds', '__sourcefile']]
                
                selected_param = st.selectbox("Kies een parameter", parameters)
                min_time = int(df_all['time_in_seconds'].min())
                max_time = int(df_all['time_in_seconds'].max())

                start_time, end_time = st.slider(
                    "Selecteer tijdsperiode (seconden sinds middernacht)",
                    min_value=min_time, max_value=max_time,
                    value=(min_time, max_time), step=60
                )

                filtered = df_all[(df_all['time_in_seconds'] >= start_time) & (df_all['time_in_seconds'] <= end_time)]

                st.line_chart(
                    data=pd.to_numeric(filtered[selected_param], errors='coerce').reset_index(drop=True),
                    height=400
                )

                st.dataframe(filtered[['time[h:m:s]', selected_param, '__sourcefile']])

                csv_download = filtered[['time[h:m:s]', selected_param, '__sourcefile']].to_csv(index=False).encode('utf-8')
                st.download_button("Download gefilterde data als CSV", data=csv_download, file_name="ferroli_export.csv")
            else:
                st.error("Kolom 'time[h:m:s]' niet gevonden in de bestanden.")
else:
    st.info("Voer een geldig map-pad in waar de Ferroli-bestanden staan.")
