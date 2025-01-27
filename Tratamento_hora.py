import pandas as pd

# Carregar os dados
df = pd.read_excel('Acionamentos.xlsx')
df2 = pd.read_excel('Ocorrencias.xlsx')
df3 = pd.read_excel('Operadores.xlsx')

# Convertendo 'Data Inclusão' para o formato de data, com tratamento de erros
df['Data Inclusão'] = pd.to_datetime(df['Data Inclusão']).dt.date

# Filtrando os dados com base nos operadores presentes
df_main = df[df['Cobrador'].isin(df3['Cobrador'])]

# Merge para adicionar Carteira e Supervisor ao df_main
df_main = pd.merge(df_main, df3[['Cobrador', 'Carteira', 'Supervisor']], on='Cobrador', how='left')

# Merge para adicionar Classificação ao df_main
df_main = pd.merge(df_main, df2[['Acionamento', 'Classificação']], on='Acionamento', how='left')

# Contar acionamentos únicos com base nas condições hierárquicas
count_alo = df_main[df_main['Classificação'].isin(['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDO'])].groupby(
    ['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], as_index=False)['ID'].nunique().rename(columns={'ID': 'ALÔ'})

count_cpc = df_main[df_main['Classificação'].isin(['CPC', 'CPC - TARGET', 'ACORDO'])].groupby(
    ['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], as_index=False)['ID'].nunique().rename(columns={'ID': 'CPC'})

count_cpc_target = df_main[df_main['Classificação'].isin(['CPC - TARGET', 'ACORDO'])].groupby(
    ['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], as_index=False)['ID'].nunique().rename(columns={'ID': 'TARGET'})

count_acordo = df_main[df_main['Classificação'] == 'ACORDO'].groupby(
    ['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], as_index=False)['ID'].nunique().rename(columns={'ID': 'ACORDO'})

# Mesclar as contagens de CPC, TARGET e ACORDO no mesmo DataFrame
df_final = count_alo.merge(count_cpc, on=['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], how='left')
df_final = df_final.merge(count_cpc_target, on=['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], how='left')
df_final = df_final.merge(count_acordo, on=['Horário', 'Data Inclusão', 'Carteira', 'Cobrador'], how='left')

# Calcular percentuais
df_final['%CPC'] = (df_final['CPC'] / df_final['ALÔ'].sum() * 100).round(1)
df_final['%TARGET'] = (df_final['TARGET'] / df_final['CPC'].sum() * 100).round(1)
df_final['%CONV'] = (df_final['ACORDO'] / df_final['TARGET'].sum() * 100).round(1)

df_final.rename(columns={"Data Inclusão": "Data"}, inplace=True)

# Organizar colunas na ordem final
Ordem = [
    'Cobrador',
    'Horário',
    'Data',
    'Carteira',
    'ALÔ',
    'CPC',
    '%CPC',
    'TARGET',
    '%TARGET',
    'ACORDO',
    '%CONV'
]

df_final = df_final.reindex(columns=Ordem)

# Salvar em um arquivo Excel
df_final.to_excel('hora_hora.xlsx', index=False)
print('Acompanhamento hora a hora gerado!')
