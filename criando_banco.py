import sqlite3
import pandas as pd
import os
import time

os.system('python Tratamento_acionamentos.py')
time.sleep(10)

os.system('python Tratamento_hora.py')
time.sleep(10)

# Caminho para o arquivo Excel
excel_visualizacao = 'Visualizacao.xlsx'
excel_ocorrencias = 'Ocorrencias.xlsx'
excel_operadores = 'Operadores.xlsx'
hora_hora = 'hora_hora.xlsx'

df = pd.read_excel(excel_visualizacao)

df2 = pd.read_excel(excel_ocorrencias)

df3 = pd.read_excel(excel_operadores)

df4 = pd.read_excel(hora_hora)

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('dados.db')
cursor = conn.cursor()

# Criar uma tabela com as colunas do DataFrame
cursor.execute('''
    CREATE TABLE IF NOT EXISTS visualizacao (
        "Data Inclusão" TEXT,
        "Supervisor" TEXT,
        "Carteira" TEXT,
        "Cobrador" TEXT,
        "Tentativas" INTEGER,
        "Clientes alcançados" INTEGER,
        "ALÔ" INTEGER,
        "%ALÔ" REAL,
        "CPC" INTEGER,
        "%CPC" REAL,
        "CPC - TARGET" INTEGER,
        "%TARGET" REAL,
        "ACORDOS" INTEGER,
        "%CONVERSÃO" REAL
    )
''')

# Criar uma tabela com as colunas do DataFrame
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ocorrencias (
        "Acionamento" TEXT,
        "Classificação" TEXT
    )
''')

# Criar uma tabela com as colunas do DataFrame
cursor.execute('''
    CREATE TABLE IF NOT EXISTS operadores (
        "Cobrador" TEXT,
        "Carteira" TEXT,
        "Supervisor" TEXT
    )
''')

# Criar uma tabela com as colunas do DataFrame 
cursor.execute('''
    CREATE TABLE IF NOT EXISTS hora_hora (
        "Cobrador" TEXT,
        "Horário" TEXT,
        "Data" TEXT,
        "ALÔ" INTERGER,
        "CPC" INTERGER,
        "%CPC" REAL,
        "TARGET" INTERGER,
        "%TARGET" REAL,
        "ACORDO" INTERGER,
        "%CONV" REAL
    )
''')

# Inserir os dados do DataFrame no banco de dados
df.to_sql('visualizacao', conn, if_exists='replace', index=False)
df2.to_sql('ocorrencias', conn, if_exists='replace', index=False)
df3.to_sql('operadores', conn, if_exists='replace', index=False)
df4.to_sql('hora_hora', conn, if_exists='replace', index=False)

# Fechar a conexão
conn.commit()
conn.close()

print("Banco de dados criado e dados inseridos com sucesso!")