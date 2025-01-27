import pandas as pd
import os

# Acionamentos
df = pd.read_excel("C:/Users/davi.melo/Desktop/Análise de CPC - V2/Acionamentos.xlsx")

# Convertendo a coluna de data e extraindo apenas a parte da data
df['Data Inclusão'] = pd.to_datetime(df['Data Inclusão']).dt.date

# Operadores
df2 = pd.read_excel('C:/Users/davi.melo/Desktop/Análise de CPC - V2/Acompanhamento_acionamentos/Operadores.xlsx')
# Acionamentos
df3 = pd.read_excel('C:/Users/davi.melo/Desktop/Análise de CPC - V2/Acompanhamento_acionamentos/Ocorrencias.xlsx')

# Filtrando os dados com base nos operadores presentes
df_main = df[df['Cobrador'].isin(df2['Cobrador'])]

# ------ Definindo DataFrames ------
acionamentos_operador = df_main.groupby(['Cobrador', 'Data Inclusão']).agg({
    'ID': 'nunique',
}).rename(columns={'ID': 'Clientes alcançados'}).reset_index()

# Adicionando a coluna de Tentativas
acionamentos_operador['Tentativas'] = df_main.groupby(['Cobrador', 'Data Inclusão'])['ID'].count().values

# Merge para trazer carteiras e supervisores
acionamentos_operador = pd.merge(acionamentos_operador, df2[['Cobrador', 'Carteira']], on='Cobrador', how='left')
acionamentos_operador = pd.merge(acionamentos_operador, df2[['Cobrador', 'Supervisor']], on='Cobrador', how='left')

# Realizando o merge entre as tabelas de Acionamentos e acionamentos
df_merged = pd.merge(df_main, df3[['Acionamento', 'Classificação']], 
                     left_on='Acionamento', right_on='Acionamento', how='left')

# Contagem unique de ALÔ, CPC e CPC TARGET por 'Cobrador' e 'Data Inclusão'
contagem_alo = df_merged[df_merged['Classificação'].isin(['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDO'])].groupby(['Cobrador', 'Data Inclusão'])['ID'].nunique().reset_index()
contagem_cpc = df_merged[df_merged['Classificação'].isin(['CPC', 'CPC - TARGET', 'ACORDO'])].groupby(['Cobrador', 'Data Inclusão'])['ID'].nunique().reset_index()
contagem_cpcT = df_merged[df_merged['Classificação'].isin(['CPC - TARGET', 'ACORDO'])].groupby(['Cobrador', 'Data Inclusão'])['ID'].nunique().reset_index()
contagem_acordo = df_merged[df_merged['Classificação'].isin(['ACORDO'])].groupby(['Cobrador', 'Data Inclusão'])['ID'].nunique().reset_index()

# Renomeando as colunas
contagem_alo.rename(columns={'ID': 'ALÔ'}, inplace=True)
contagem_cpc.rename(columns={'ID': 'CPC'}, inplace=True)
contagem_cpcT.rename(columns={'ID': 'CPC - TARGET'}, inplace=True)
contagem_acordo.rename(columns={'ID': 'ACORDOS'}, inplace=True)

# Definição das colunas ALÔ, CPC e CPC TARGET por data
acionamentos_operador = acionamentos_operador.merge(contagem_alo, on=['Cobrador', 'Data Inclusão'], how='left')
acionamentos_operador['%ALÔ'] = ((acionamentos_operador['ALÔ'] / acionamentos_operador['Clientes alcançados']) * 100).round(1)

acionamentos_operador = acionamentos_operador.merge(contagem_cpc, on=['Cobrador', 'Data Inclusão'], how='left')
acionamentos_operador['%CPC'] = ((acionamentos_operador['CPC'] / acionamentos_operador['ALÔ']) * 100).round(1)

acionamentos_operador = acionamentos_operador.merge(contagem_cpcT, on=['Cobrador', 'Data Inclusão'], how='left')
acionamentos_operador['%TARGET'] = ((acionamentos_operador['CPC - TARGET'] / acionamentos_operador['CPC']) * 100).round(1)

acionamentos_operador = acionamentos_operador.merge(contagem_acordo, on=['Cobrador', 'Data Inclusão'], how='left')
acionamentos_operador['%CONVERSÃO'] = ((acionamentos_operador['ACORDOS'] / acionamentos_operador['CPC - TARGET']) * 100).round(1)

# Nova ordem para o DataFrame
Ordem = [
    'Cobrador',
    'Carteira', 
    'Supervisor', 
    'Data Inclusão', 
    'Tentativas', 
    'Clientes alcançados', 
    'ALÔ', 
    '%ALÔ', 
    'CPC', 
    '%CPC', 
    'CPC - TARGET', 
    '%TARGET',
    'ACORDOS',
    '%CONVERSÃO' 
]

acionamentos_visualizacao = acionamentos_operador.reindex(columns=Ordem)
print(acionamentos_visualizacao)

# Criação do arquivo excel que será lido no Streamlit
if os.path.isfile('Visualizacao_acionamentos.xlsx'):
    os.remove('Visualizacao_acionamentos.xlsx')
    acionamentos_visualizacao.to_excel('Visualizacao_acionamentos.xlsx', index=False)
else:
    acionamentos_visualizacao.to_excel('Visualizacao_acionamentos.xlsx', index=False)
