import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

def carregar_acessos():
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

    def connect_db():
        return sqlite3.connect("dados.db")

    # Função para consultar acessos
    def query_acessos(period_start, period_end):
        conn = connect_db()
        query = "SELECT * FROM acessos WHERE DATE(`data_hora`) BETWEEN ? AND ?"
        params = (str(period_start), str(period_end))
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    # Função para criar o gráfico de acessos
    def grafico_acessos(df):
        # Contar acessos por email
        acessos_por_usuario = df.groupby('email').size().reset_index(name='numero_acessos')

        # Criar gráfico de barras
        fig = px.bar(acessos_por_usuario, 
            x='email', 
            y='numero_acessos', 
            title='Número de Acessos por Usuário',
            labels={'email': 'Usuário', 'numero_acessos': 'Acessos'},
            text_auto=True
        )
        
        fig.update_traces(textfont_size=12, 
            textangle=0, 
            textposition="outside", 
            cliponaxis=False, 
            responsive=True
        )
        
        return fig

    configurar_estilo()

    # Divisão da página em duas seções
    with st.container():
        st.title("Pesquisa de Acessos")

        filtros1, filtros2 = st.columns([1, 1])
        with filtros1:
            period_start = st.date_input("Data Inicial")
        with filtros2:
            period_end = st.date_input("Data Final")

        if st.button("Pesquisar Acessos"):
            st.session_state.results = query_acessos(period_start, period_end)
    
    # Exibição dos resultados
    if "results" in st.session_state and not st.session_state.results.empty:
        st.subheader("Resultados da Consulta")
        # Exibir o DataFrame sem índice
        st.dataframe(st.session_state.results.style.hide(axis='index'), use_container_width=True)

        # Exibição do gráfico
        st.subheader("Gráfico de Acessos")
        fig = grafico_acessos(st.session_state.results)
        st.plotly_chart(fig, use_container_width=True)
    elif "results" in st.session_state:
        st.warning("Nenhum acesso encontrado para os filtros aplicados.")

# Executa a aplicação
if __name__ == "__main__":
    carregar_acessos()