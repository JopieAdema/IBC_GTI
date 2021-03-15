# IBC_GTI
Field course proposal Machine Learning in Economics: we predict Illegal Border Crossings on Europe's outer borders with Google Trend Index data on migration-related keywords using LSTMs

## Folders
 - GTITAN. Contains the code to source GTI and Google Translate simulatanously
 - LSTM: Contains the LSTM code
 - Data: Contains all sourced and used data

## How to run: 
- Run GTITAN\Run_gtitan_create_ipynb to create the Data dataframe saved to Data\lstm_df.pkl. Note that this step sources Google Trends Index and Google Translate simultaneously. The user may run into connection issues, and may need to alter the time out, in case the internet connection is unstable. Furthermore, the user may hit the GTI and GT IP limit. This step can be skipped, as all available data is already sourced (RECOMMENDED):
- Run LSTM\MigrationLSTM.ipynb NOTE: LSTMs may take several hours to run. To reduce the workload, the number of epochs can be reduced. It also outputs some of the results in pictures and saves it in the same folder
