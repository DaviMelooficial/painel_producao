import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px

# Função para carregar e preparar os dados do banco
def carregar_dados_sql():
    conn = sqlite3.connect('dados.db')
    query = "SELECT * FROM hora_hora"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['Horário'] = pd.to_datetime(df['Horário'], format='%H:%M:%S').dt.time
    return df

# Função para agrupar os dados por hora e somar métricas específicas
def agrupar_por_hora(df, data_inicio, data_fim, carteiras, horario_inicio, horario_fim, cobrador):
    df_filtered = df[(df['Data'].dt.date.between(data_inicio, data_fim))]

    Ordem = [
        'Horário', 'Data', 'Carteira', 'ALÔ', 'CPC', '%CPC', 'TARGET', '%TARGET', 'ACORDO', '%CONV'
    ]

    if carteiras:
        df_filtered = df_filtered[df_filtered['Carteira'].isin(carteiras)]

    if cobrador:
        df_filtered = df_filtered[df_filtered['Cobrador'].isin(cobrador)]

    # Aplica o filtro de horário para o intervalo selecionado
    if horario_inicio and horario_fim:
        df_filtered = df_filtered[(df_filtered['Horário'] >= horario_inicio) & (df_filtered['Horário'] <= horario_fim)]

    metrics_to_sum = ['ALÔ', 'CPC', 'TARGET', 'ACORDO']
    df_filtered = df_filtered.groupby('Horário', as_index=False)[metrics_to_sum].sum()

    df_filtered['%CPC'] = round((df_filtered['CPC'] / df_filtered['ALÔ']) * 100, 1)
    df_filtered['%TARGET'] = round((df_filtered['TARGET'] / df_filtered['CPC']) * 100, 1)
    df_filtered['%CONV'] = round((df_filtered['ACORDO'] / df_filtered['TARGET']) * 100, 1)

    df_filtered = df_filtered.reindex(columns=Ordem)
    return df_filtered

# Função para configurar o estilo do Streamlit
def configurar_estilo():
    st.markdown("""
        <style>
        .main {
            padding: 1rem;
        }
        .block-container {
            max-width: 1200px;
            margin: auto.
        }
        /* Responsividade para o dashboard */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

# Função para gerar gráfico de linha dos acordos
def gerar_grafico_acordos(df_agrupado_1, df_agrupado_2):
    fig = px.line()
    
    fig.add_scatter(x=df_agrupado_1['Horário'], y=df_agrupado_1['ACORDO'], mode='lines+markers+text',
                    text=df_agrupado_1['ACORDO'], name='Acordos Atual', textposition="top center")
    
    fig.add_scatter(x=df_agrupado_2['Horário'], y=df_agrupado_2['ACORDO'], mode='lines+markers+text',
                    text=df_agrupado_2['ACORDO'], name='Acordos Comparação', textposition="top center")

    fig.update_layout(
        title="Número de Acordos por Hora",
        xaxis_title="Horário",
        yaxis_title="Número de Acordos",
        legend_title="Séries",
        autosize=True, 
        responsive=True
    )
    return fig

def calcular_totais(dados_agrupados):
    colunas_numericas = ['ALÔ', 'CPC', 'TARGET', 'ACORDO']
    totais = dados_agrupados[colunas_numericas].sum().fillna(0).to_dict()

    totais['%CPC'] = round((totais['CPC'] / totais['ALÔ'] * 100), 0) if totais['ALÔ'] > 0 else 0
    totais['%TARGET'] = round((totais['TARGET'] / totais['CPC'] * 100), 0) if totais['CPC'] > 0 else 0
    totais['%CONV'] = round((totais['ACORDO'] / totais['TARGET'] * 100), 0) if totais['TARGET'] > 0 else 0

    linha_total = pd.DataFrame(totais, index=['Total']).reindex(columns=[
        'ALÔ', 'CPC', '%CPC', 'TARGET', '%TARGET', 'ACORDO', '%CONV'])

    for col in ['%CPC', '%TARGET', '%CONV']:
        linha_total[col] = linha_total[col].apply(lambda x: f'{x:.0f}%')

    return linha_total

# Função principal para rodar o dashboard hora a hora
def rodar_dashboard_hora():
    configurar_estilo()
    
    df = carregar_dados_sql()
    df = df[df['Data'].notna()]
    
    data_hoje = datetime.today().date()
    min_data = df['Data'].min().date() if not df['Data'].isnull().all() else data_hoje
    max_data = df['Data'].max().date() if not df['Data'].isnull().all() else data_hoje
    
    if data_hoje < min_data or data_hoje > max_data:
        data_hoje = max_data

    st.title('Dashboard Hora a Hora')
    col1, col2 = st.columns(2)


    with col1:
        st.subheader('Atual')
        data_inicio_1 = st.date_input("Data de início", value=data_hoje, min_value=min_data, max_value=max_data)
        data_fim_1 = st.date_input("Data de fim", value=max_data, min_value=min_data, max_value=max_data)

        col1_filtro1, col2_filtro1 = st.columns(2)

        with col1_filtro1:
            carteiras_1 = st.multiselect("Carteiras", options=df['Carteira'].unique().tolist())
        with col2_filtro1:
            cobrador_1 =  st.multiselect("Cobrador", options=df['Cobrador'].unique().tolist())

        horario_inicio_1, horario_fim_1 = st.slider(
            "Selecione o intervalo de horários", 
            min_value=datetime.strptime("07:00", "%H:%M").time(),
            max_value=datetime.strptime("18:30", "%H:%M").time(),
            value=(datetime.strptime("07:00", "%H:%M").time(), datetime.strptime("18:30", "%H:%M").time())
        )

        df_agrupado_1 = agrupar_por_hora(df, data_inicio_1, data_fim_1, carteiras_1, horario_inicio_1, horario_fim_1, cobrador_1)

        for col in ['%CPC', '%TARGET', '%CONV']:
            df_agrupado_1[col] = df_agrupado_1[col].fillna(0).round(0).astype(int).apply(lambda x: f'{x:.0f}%')

        st.dataframe(df_agrupado_1.drop(columns=['Data', 'Carteira'], errors='ignore').set_index('Horário'))
        linha_total = calcular_totais(df_agrupado_1)
        st.dataframe(linha_total)

    with col2:
        st.subheader('Comparação')
        data_inicio_2 = st.date_input("Data de início ", value=(data_hoje - timedelta(days=1)), min_value=min_data, max_value=max_data)
        data_fim_2 = st.date_input("Data de fim ", value=(data_hoje - timedelta(days=1)), min_value=min_data, max_value=max_data)

        col1_filtro2, col2_filtro2 = st.columns(2)

        with col1_filtro2:
            carteiras_2 = st.multiselect("Carteiras ", options=df['Carteira'].unique().tolist())
        with col2_filtro2:
            cobrador_2 =  st.multiselect("Cobrador ", options=df['Cobrador'].unique().tolist())

        horario_inicio_2, horario_fim_2 = st.slider(
            "Selecione o intervalo de horários ", 
            min_value=datetime.strptime("07:00", "%H:%M").time(),
            max_value=datetime.strptime("18:30", "%H:%M").time(),
            value=(datetime.strptime("07:00", "%H:%M").time(), datetime.strptime("18:30", "%H:%M").time())
        )

        df_agrupado_2 = agrupar_por_hora(df, data_inicio_2, data_fim_2, carteiras_2, horario_inicio_2, horario_fim_2, cobrador_2)

        for col in ['%CPC', '%TARGET', '%CONV']:
            df_agrupado_2[col] = df_agrupado_2[col].fillna(0).round(0).astype(int).apply(lambda x: f'{x:.0f}%')

        st.dataframe(df_agrupado_2.drop(columns=['Data', 'Carteira'], errors='ignore').set_index('Horário'))
        linha_total = calcular_totais(df_agrupado_2)
        st.dataframe(linha_total)

    fig_acordos = gerar_grafico_acordos(df_agrupado_1, df_agrupado_2)
    st.plotly_chart(fig_acordos, use_container_width=True)

if __name__ == '__main__':
    rodar_dashboard_hora()
