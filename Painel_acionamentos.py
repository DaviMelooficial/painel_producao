import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import sqlite3
import os

# Função para carregar e preparar os dados
def carregar_dados_sql():
    conn = sqlite3.connect('dados.db')
    query_visualizacao = "SELECT * FROM visualizacao"
    visualizacao = pd.read_sql_query(query_visualizacao, conn)
    conn.close()
    
    # Converter a coluna de data para o formato correto
    visualizacao['Data Inclusão'] = pd.to_datetime(visualizacao['Data Inclusão']).dt.date
    return visualizacao

# Função para carregar dados filtrados do banco de dados com SQL
def carregar_dados_filtrados(data_inicio, data_fim, carteiras=None, supervisores=None, operadores=None):
    conn = sqlite3.connect('dados.db')
    
    # Converte as datas para string no formato YYYY-MM-DD para que o SQLite trate corretamente
    data_inicio_str = data_inicio.strftime('%Y-%m-%d')
    data_fim_str = data_fim.strftime('%Y-%m-%d')

    # Verifica se o usuário selecionou uma única data
    if data_inicio == data_fim:
        # Consulta para considerar apenas a data, ignorando o horário
        query = "SELECT * FROM visualizacao WHERE DATE(`Data Inclusão`) = ?"
        params = [data_inicio_str]
    else:
        # Consulta com filtro por intervalo de datas, também ignorando horários
        query = "SELECT * FROM visualizacao WHERE DATE(`Data Inclusão`) BETWEEN ? AND ?"
        params = [data_inicio_str, data_fim_str]
    
    # Filtro por carteiras
    if carteiras:
        query += " AND `Carteira` IN ({})".format(','.join(['?'] * len(carteiras)))
        params.extend(carteiras)
    
    # Filtro por supervisores
    if supervisores:
        query += " AND `Supervisor` IN ({})".format(','.join(['?'] * len(supervisores)))
        params.extend(supervisores)
    
    # Filtro por operadores
    if operadores:
        query += " AND `Cobrador` IN ({})".format(','.join(['?'] * len(operadores)))
        params.extend(operadores)
    
    # Executa a query com os filtros
    dados_filtrados = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Converter a coluna de data para o formato correto no DataFrame
    dados_filtrados['Data Inclusão'] = pd.to_datetime(dados_filtrados['Data Inclusão']).dt.date
    return dados_filtrados

# Função para configurar o estilo do Streamlit
def configurar_estilo():
    st.markdown("""
        <style>
        .main {
            padding: 1rem;
        }
        .block-container {
            max-width: 1200px;
            margin: auto;
        }
        /* Responsividade para o dashboard */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

# Função para exibir o cabeçalho e filtros interdependentes
def exibir_filtros(visualizacao, ultima_execucao):
    title_1, title_2 = st.columns([1, 1])

    with title_1:
        st.title('Dashboard de Acionamentos')
    with title_2:
        st.metric(label="Última Atualização", value=ultima_execucao)

    st.subheader('Selecione os filtros para visualização')

    # Filtro por data
    data_min, data_max = visualizacao['Data Inclusão'].min(), visualizacao['Data Inclusão'].max()
    data_hoje = datetime.today().date()

    # Garantir que a data de hoje esteja dentro do intervalo de datas disponíveis
    if data_hoje < data_min or data_hoje > data_max:
        data_hoje = data_max  # Define o valor padrão para a última data disponível no intervalo
    
    data_inicio, data_fim = st.date_input('Filtrar por data', [data_hoje, data_max], 
                                          min_value=data_min, max_value=data_max)

    # Se o usuário selecionar apenas uma data, ajustamos o comportamento
    if data_inicio == data_fim:
        data_fim = data_inicio  # Trate como uma única data

    # Filtros dinâmicos
    filtro_carteira = visualizacao['Carteira'].unique().tolist()
    visualizacao_filtrado = visualizacao

    filtro_1, filtro_2, filtro_3 = st.columns([1, 1, 1])

    # Filtro de Carteiras
    with filtro_1:
        carteiras_selecionadas = st.multiselect(
            ' ',
            filtro_carteira,
            placeholder='Selecione as Carteiras',
            label_visibility='collapsed'
        )
        if carteiras_selecionadas:
            visualizacao_filtrado = visualizacao_filtrado[
                visualizacao_filtrado['Carteira'].isin(carteiras_selecionadas)
            ]

    # Filtro de Supervisores (dependente das Carteiras)
    filtro_supervisor = visualizacao_filtrado['Supervisor'].unique().tolist()
    with filtro_2:
        supervisores_selecionados = st.multiselect(
            ' ',
            filtro_supervisor,
            placeholder='Selecione os Supervisores',
            label_visibility='collapsed'
        )
        if supervisores_selecionados:
            visualizacao_filtrado = visualizacao_filtrado[
                visualizacao_filtrado['Supervisor'].isin(supervisores_selecionados)
            ]

    # Filtro de Operadores (dependente de Supervisores e Carteiras)
    filtro_operador = visualizacao_filtrado['Cobrador'].unique().tolist()
    with filtro_3:
        operadores_selecionados = st.multiselect(
            ' ',
            filtro_operador,
            placeholder='Selecione os Operadores',
            label_visibility='collapsed'
        )

    return data_inicio, data_fim, carteiras_selecionadas, supervisores_selecionados, operadores_selecionados

# Função para agrupar e preparar os dados
def agrupar_dados(dados_filtrados):
    dados_agrupados = dados_filtrados.groupby('Cobrador').agg({
        'Carteira': 'first',
        'Supervisor': 'first',
        'Tentativas': 'sum',
        'Clientes alcançados': 'sum',
        'ALÔ': 'sum',
        '%ALÔ': 'mean',
        'CPC': 'sum',
        '%CPC': 'mean',
        'CPC - TARGET': 'sum',
        '%TARGET': 'mean',
        'ACORDOS': 'sum',
        '%CONVERSÃO': 'mean'
    }).reset_index()

    # Convert specific percentage columns to integer, adding '%' sign
    for col in ['%ALÔ', '%CPC', '%TARGET', '%CONVERSÃO']:
        dados_agrupados[col] = dados_agrupados[col].fillna(0).round(0).astype(int).apply(lambda x: f'{x:.0f}%')

    # Infer object types to prevent downcasting warnings
    dados_agrupados = dados_agrupados.infer_objects(copy=False)

    return dados_agrupados.set_index('Cobrador')

# Função para calcular e exibir os totais
def calcular_totais(dados_agrupados):
    colunas_numericas = ['Tentativas', 'Clientes alcançados', 'ALÔ', 'CPC', 'CPC - TARGET', 'ACORDOS']
    totais = dados_agrupados[colunas_numericas].sum().fillna(0).to_dict()

    totais['%ALÔ'] = round((totais['ALÔ'] / totais['Clientes alcançados'] * 100), 0) if totais['Clientes alcançados'] > 0 else 0
    totais['%CPC'] = round((totais['CPC'] / totais['ALÔ'] * 100), 0) if totais['ALÔ'] > 0 else 0
    totais['%TARGET'] = round((totais['CPC - TARGET'] / totais['CPC'] * 100), 0) if totais['CPC'] > 0 else 0
    totais['%CONVERSÃO'] = round((totais['ACORDOS'] / totais['CPC - TARGET'] * 100), 0) if totais['CPC - TARGET'] > 0 else 0

    linha_total = pd.DataFrame(totais, index=['Total']).reindex(columns=[
        'Tentativas', 'Clientes alcançados', 'ALÔ', '%ALÔ', 'CPC', '%CPC', 
        'CPC - TARGET', '%TARGET', 'ACORDOS', '%CONVERSÃO'
    ])

    for col in ['%ALÔ', '%CPC', '%TARGET', '%CONVERSÃO']:
        linha_total[col] = linha_total[col].apply(lambda x: f'{x:.0f}%')

    return linha_total

# Função para gerar o gráfico de barras
def gerar_grafico_barras(dados_agrupados):
    dados_grafico = dados_agrupados.groupby('Carteira', as_index=False)[['CPC - TARGET', 'ACORDOS']].sum()

    if not dados_grafico.empty:
        dados_grafico_melted = dados_grafico.melt(id_vars='Carteira', value_vars=['CPC - TARGET', 'ACORDOS'], 
                                                  var_name='Métrica', value_name='Total')

        fig = px.bar(dados_grafico_melted, x='Carteira', y='Total', color='Métrica', barmode='group',
                     title='CPC - TARGET e Acordos por Carteira', text_auto=True)

        fig.update_layout(
            autosize=True, 
            height=500, 
            title_font_size=18, 
            xaxis_tickangle=-45, 
            margin=dict(l=40, r=40, t=40, b=120), 
            bargap=0.2,
            showlegend=False
        )

        fig.update_traces(textfont_size=14, 
            textposition='outside', 
            responsive=True
        )
        return fig
    return None

# Função para gerar o gráfico de funil
def gerar_grafico_funil(dados_filtrados):
    soma_dados = dados_filtrados[['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDOS']].sum()
    etapas = ['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDOS']
    valores = [soma_dados['ALÔ'], soma_dados['CPC'], soma_dados['CPC - TARGET'], soma_dados['ACORDOS']]

    fig2 = px.funnel(x=valores, y=etapas, title='Funil de Conversão:')
    fig2.update_layout(autosize=True, height=400, yaxis_title=None, margin=dict(l=50), responsive=True)
    return fig2

# Função principal para rodar o dashboard
def rodar_dashboard_acionamentos():
    configurar_estilo()

    # Exibir filtros e carregar os dados com base nos filtros selecionados
    visualizacao = carregar_dados_sql()
    visualizacao_alteracao = os.path.getmtime('Visualizacao.xlsx')
    ultima_execucao = datetime.fromtimestamp(visualizacao_alteracao).strftime('%d/%m/%Y %H:%M:%S')

    # Exibir filtros de datas, carteiras, supervisores e operadores
    data_inicio, data_fim, carteiras, supervisores, operadores = exibir_filtros(visualizacao, ultima_execucao)

    # Carregar os dados filtrados diretamente do SQL
    dados_filtrados = carregar_dados_filtrados(data_inicio, data_fim, carteiras, supervisores, operadores)
    dados_agrupados = agrupar_dados(dados_filtrados)

    # Exibir dados agrupados e totais
    st.dataframe(dados_agrupados)
    linha_total = calcular_totais(dados_agrupados)
    st.dataframe(linha_total)

    # Organizar os gráficos em colunas
    col_grafico1, col_grafico2 = st.columns([2, 1])  # Proporção mais flexível entre gráficos

    with col_grafico1:
        fig = gerar_grafico_barras(dados_agrupados)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Sem dados para exibir no gráfico.")

    with col_grafico2:
        fig2 = gerar_grafico_funil(dados_filtrados)
        st.plotly_chart(fig2, use_container_width=True)

# Executa o dashboard
if __name__ == '__main__':
    rodar_dashboard_acionamentos()
