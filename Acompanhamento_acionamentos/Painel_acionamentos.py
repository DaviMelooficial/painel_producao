import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import os

# Função para carregar e preparar os dados
def carregar_dados(caminho):
    visualizacao = pd.read_excel('Visualizacao.xlsx')
    visualizacao['Data Inclusão'] = pd.to_datetime(visualizacao['Data Inclusão']).dt.date
    ultima_execucao = datetime.fromtimestamp(os.path.getmtime(caminho)).strftime('%d/%m/%Y %H:%M:%S')
    return visualizacao, ultima_execucao

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

# Função para exibir o cabeçalho e os filtros de data
def exibir_filtros(visualizacao, ultima_execucao):
    st.title('Dashboard de Acionamentos')
    st.metric(label="Última Atualização", value=ultima_execucao)
    st.subheader('Selecione os filtros para visualização')
    
    data_min, data_max = visualizacao['Data Inclusão'].min(), visualizacao['Data Inclusão'].max()
    data_inicio, data_fim = st.date_input(
        'Filtrar por data', [datetime.today().date(), data_max], 
        min_value=data_min, max_value=data_max
    )
    return data_inicio, data_fim

# Função para aplicar os filtros de carteiras, supervisores e operadores
def aplicar_filtros(visualizacao, data_inicio, data_fim):
    dados_filtrados = visualizacao[(visualizacao['Data Inclusão'] >= data_inicio) & (visualizacao['Data Inclusão'] <= data_fim)]
    
    filtro_carteira = ['GERAL', 'BANCO CNH', 'GCD', 'SHOPPING', 'GMAC', 'DIVERSOS', 'FOCO', 'CONDOMINIO', 'OMNI', 'FINSOL', 'PIFPAF']
    filtro_supervisor = visualizacao['Supervisor'].unique().tolist()
    filtro_operador = visualizacao['Cobrador'].unique().tolist()
    
    col1_DF, col2_DF, col3_DF = st.columns([1, 1, 1])
    coluna_filtro = col1_DF.multiselect(' ', filtro_carteira, placeholder="Escolha as carteiras", label_visibility='collapsed')
    coluna_filtro_supervisor = col2_DF.multiselect(' ', filtro_supervisor, placeholder="Escolha os supervisores", label_visibility='collapsed')
    coluna_filtro_operador = col3_DF.multiselect(' ', filtro_operador, placeholder="Escolha os operadores", label_visibility='collapsed')
    
    if not coluna_filtro or 'GERAL' in coluna_filtro:
        dados_filtrados = dados_filtrados
    else:
        dados_filtrados = dados_filtrados[dados_filtrados['Carteira'].isin(coluna_filtro)]
    
    if coluna_filtro_operador:
        dados_filtrados = dados_filtrados[dados_filtrados['Cobrador'].isin(coluna_filtro_operador)]
        
    if coluna_filtro_supervisor:
        dados_filtrados = dados_filtrados[dados_filtrados['Supervisor'].isin(coluna_filtro_supervisor)]
    
    return dados_filtrados

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
    
    # Arredondar as colunas % para inteiros e formatar com %
    for col in ['%ALÔ', '%CPC', '%TARGET', '%CONVERSÃO']:
        dados_agrupados[col] = dados_agrupados[col].fillna(0).round(0).astype(int).apply(lambda x: f'{x:.0f}%')
    
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
        
        fig.update_traces(textfont_size=14, textposition='outside')
        return fig
    return None

# Função para gerar o gráfico de funil
def gerar_grafico_funil(dados_filtrados):
    soma_dados = dados_filtrados[['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDOS']].sum()
    etapas = ['ALÔ', 'CPC', 'CPC - TARGET', 'ACORDOS']
    valores = [soma_dados['ALÔ'], soma_dados['CPC'], soma_dados['CPC - TARGET'], soma_dados['ACORDOS']]
    
    fig2 = px.funnel(x=valores, y=etapas, title='Funil de Conversão:')
    fig2.update_layout(autosize=True, height=400, yaxis_title=None, margin=dict(l=50))
    return fig2

# Função principal para rodar o dashboard
def rodar_dashboard_acionamentos():
    configurar_estilo()

    visualizacao, ultima_execucao = carregar_dados('Visualizacao.xlsx')
    data_inicio, data_fim = exibir_filtros(visualizacao, ultima_execucao)
    
    dados_filtrados = aplicar_filtros(visualizacao, data_inicio, data_fim)
    dados_agrupados = agrupar_dados(dados_filtrados)
    
    st.dataframe(dados_agrupados)
    linha_total = calcular_totais(dados_agrupados)
    st.dataframe(linha_total)
    
    col_grafico1, col_grafico2 = st.columns([2, 1])
    
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
