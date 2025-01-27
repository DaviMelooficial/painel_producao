import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import plotly.express as px

def estrategias():
    # Conectar ao banco de dados
    def connect_db():
        return sqlite3.connect("dados.db")

    # Configurar o estilo
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
            </style>
            """, unsafe_allow_html=True)

    # Consultar estratégias
    def query_strategies(period_start, portfolio, tipo):
        conn = connect_db()
        if portfolio == 'GERAL':
            if tipo == 'GERAL':
                query = """
                SELECT id, data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                    carteira, numero_contratos, type, status, observacao
                FROM estrategias
                WHERE (? BETWEEN data_inicial AND data_final)
                """
                params = (str(period_start),)
            else:
                query = """
                SELECT id, data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                    carteira, numero_contratos, type, status, observacao
                FROM estrategias
                WHERE (? BETWEEN data_inicial AND data_final)
                AND (? = '' OR type = ?)
                """
                params = (str(period_start), tipo, tipo)
        else:
            if tipo == 'GERAL':
                query = """
                SELECT id, data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                    carteira, numero_contratos, type, status, observacao
                FROM estrategias
                WHERE (? BETWEEN data_inicial AND data_final)
                AND (? = '' OR carteira = ?)
                """
                params = (str(period_start), portfolio, portfolio)
            else:
                query = """
                SELECT id, data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                    carteira, numero_contratos, type, status, observacao
                FROM estrategias
                WHERE (? BETWEEN data_inicial AND data_final)
                AND (? = '' OR carteira = ?)
                AND (? = '' OR type = ?)
                """
                params = (str(period_start), portfolio, portfolio, tipo, tipo)
        df = pd.read_sql_query(query, conn, params=params, index_col="id")
        conn.close()
        return df

    # Inserir nova estratégia
    def insert_strategy(data_inicial, data_final, hora_inicial, hora_final, carteira,
                        numero_contratos, tipo, status, observacao):
        conn = connect_db()
        query = """
        INSERT INTO estrategias (data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                                 carteira, numero_contratos, type, status, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        data_criacao = date.today()
        conn.execute(query, (data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                             carteira, numero_contratos, tipo, status, observacao))
        conn.commit()
        conn.close()

    # Atualizar uma estratégia existente
    def update_strategy(strategy_id, data_inicial, data_final, hora_inicial, hora_final, carteira,
                        numero_contratos, tipo, status, observacao):
        conn = connect_db()
        query = """
        UPDATE estrategias
        SET data_inicial = ?, data_final = ?, hora_inicial = ?, hora_final = ?, 
            carteira = ?, numero_contratos = ?, type = ?, status = ?, observacao = ?
        WHERE id = ?
        """
        conn.execute(query, (data_inicial, data_final, hora_inicial, hora_final, carteira,
                             numero_contratos, tipo, status, observacao, strategy_id))
        conn.commit()
        conn.close()

    # Duplicar uma estratégia existente
    def duplicate_strategy(strategy_id):
        conn = connect_db()
        query = """
        INSERT INTO estrategias (data_criacao, data_inicial, data_final, hora_inicial, hora_final,
                                 carteira, numero_contratos, type, status, observacao)
        SELECT ?, data_inicial, data_final, hora_inicial, hora_final, carteira, numero_contratos,
               type, status, observacao
        FROM estrategias WHERE id = ?
        """
        data_criacao = date.today()
        conn.execute(query, (data_criacao, strategy_id))
        conn.commit()
        conn.close()

    def gerar_grafico_gantt(df, selected_date):
        if df.empty:
            st.warning("Nenhuma estratégia encontrada para o dia selecionado.")
            return

        # Corrigir formatos inválidos em 'hora_inicial' e 'hora_final'
        df['hora_inicial'] = df['hora_inicial'].astype(str).str.extract(r'(\d{2}:\d{2})', expand=False)
        df['hora_final'] = df['hora_final'].astype(str).str.extract(r'(\d{2}:\d{2})', expand=False)

        # Preencher valores inválidos ou ausentes com um horário padrão
        df['hora_inicial'].fillna("00:00", inplace=True)
        df['hora_final'].fillna("00:00", inplace=True)

        try:
            # Ajustar horários para o dia selecionado
            df['inicio'] = pd.to_datetime(f"{selected_date} " + df['hora_inicial'], format="%Y-%m-%d %H:%M")
            df['fim'] = pd.to_datetime(f"{selected_date} " + df['hora_final'], format="%Y-%m-%d %H:%M")
        except ValueError as e:
            st.error(f"Erro ao converter horários: {e}")
            return

        # Criar uma coluna combinada de "carteira" e "tipo" para diferenciar cores
        df['carteira_tipo'] = df['carteira'] + " - " + df['type']

        # Criar gráfico de Gantt
        fig = px.timeline(
            df,
            x_start="inicio",
            x_end="fim",
            y="carteira",
            color="carteira_tipo",  # Usar a coluna combinada para definir cores
            title=f"Gráfico de Gantt - Estratégias para {selected_date}",
            labels={"carteira": "Carteira", "type": "Tipo", "carteira_tipo": "Carteira - Tipo"}
        )
        fig.update_layout(
            xaxis_title="Horas",
            yaxis_title="Carteira",
            autosize=True,
            margin=dict(l=0, r=0, t=30, b=0),
             responsive=True
        )
        st.plotly_chart(fig, use_container_width=True)

    configurar_estilo()

    carteiras = ['GERAL', 'SHOPPING', 'CONDOMÍNIOS', 'CNHI', 'DIVERSOS', 'EDUCACIONAL', 'FINSOL', 'GCD', 'GMAC', 'OMNI', 'PIFPAF', 'RHP']
    tipos = ['GERAL', 'Preditiva', 'Manual', 'Eletrônica']

    st.title("Estratégias e Resultados")

    # Filtros
    col1, col2 = st.columns([2, 1])
    with col1:
        filtros1, filtros2 = st.columns([1, 1])
        with filtros1:
            period_start = st.date_input("Data Inicial")
            tipo = st.selectbox('Selecionar tipo', options=tipos)
        with filtros2:
            portfolio = st.selectbox("Selecionar Carteira", options=carteiras)
    with col2:
        if st.button("Pesquisar Estratégias"):
            st.session_state.results = query_strategies(period_start, portfolio, tipo)
        # Exibir botão de criação somente para Administrador
        if st.session_state.get("cargo") == "Administrador" and st.button("Cadastrar Estratégias"):
            st.session_state.show_form = not st.session_state.get("show_form", False)

    # Formulário para criar nova estratégia
    if st.session_state.get("show_form", False):
        st.subheader("Cadastrar Nova Estratégia")
        with st.form("Cadastro de Estratégia", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                data_inicial = st.date_input("Data Inicial")
                hora_inicial = st.text_input("Hora Inicial (HH:MM)", placeholder="Ex: 08:00")
            with col2:
                data_final = st.date_input("Data Final")
                hora_final = st.text_input("Hora Final (HH:MM)", placeholder="Ex: 18:00")
            with col3:
                carteira = st.selectbox("Selecionar Carteira", options=carteiras)
                numero_contratos = st.number_input("Número de Contratos", min_value=1, step=1)

            column_type, column_status = st.columns([1, 1])
            with column_type:
                tipo = st.selectbox("Tipo", options=tipos)
            with column_status:
                status = st.selectbox("Status", options=["Ativa", "Inativa"])

            observacao = st.text_area("Observação")

            if st.form_submit_button("Salvar"):
                insert_strategy(data_inicial, data_final, hora_inicial, hora_final, carteira,
                                numero_contratos, tipo, status, observacao)
                st.success("Estratégia cadastrada com sucesso!")
                st.session_state.show_form = False

    # Exibição dos resultados
    if "results" in st.session_state and not st.session_state.results.empty:
        st.subheader("Resultados da Consulta")
        df = st.session_state.results
        st.dataframe(df, use_container_width=True)

        st.subheader("Gráfico de Gantt das Estratégias")
        gerar_grafico_gantt(df, period_start)

        # Seletor de estratégias
        selected_strategy_id = st.selectbox(
            "Selecione uma estratégia para visualizar, editar ou duplicar:",
            options=df.index,
            format_func=lambda x: f"Estratégia ID {x}"
        )
        
        if selected_strategy_id:
            st.subheader("Detalhes da Estratégia")
            strategy = df[df.index == selected_strategy_id].iloc[0]

            # Exibir informações fora do formulário para não administradores
            if st.session_state.get("cargo") != "Administrador":
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Data Inicial", value=pd.to_datetime(strategy['data_inicial']).date(), disabled=True)
                    st.text_input("Hora Inicial (HH:MM)", value=strategy['hora_inicial'], disabled=True)
                with col2:
                    st.text_input("Data Final", value=pd.to_datetime(strategy['data_final']).date(), disabled=True)
                    st.text_input("Hora Final (HH:MM)", value=strategy['hora_final'], disabled=True)
                with col3:
                    st.text_input("Carteira", value=strategy['carteira'], disabled=True)
                    st.number_input("Número de Contratos", min_value=1, step=1, value=int(strategy['numero_contratos']), disabled=True)

                column_type, column_status = st.columns([1, 1])
                with column_type:
                    st.text_input("Tipo", value=strategy['type'], disabled=True)
                with column_status:
                    st.text_input("Status", value=strategy['status'], disabled=True)

                st.text_area("Observação", value=strategy['observacao'], disabled=True)
                        
            # Formulário para administradores
            else:
                with st.form(f"Editar Estratégia {selected_strategy_id}", clear_on_submit=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        data_inicial = st.date_input("Data Inicial", value=pd.to_datetime(strategy['data_inicial']).date())
                        hora_inicial = st.text_input("Hora Inicial (HH:MM)", value=strategy['hora_inicial'])
                    with col2:
                        data_final = st.date_input("Data Final", value=pd.to_datetime(strategy['data_final']).date())
                        hora_final = st.text_input("Hora Final (HH:MM)", value=strategy['hora_final'])
                    with col3:
                        carteira = st.selectbox("Selecionar Carteira", options=carteiras, index=carteiras.index(strategy['carteira']))
                        numero_contratos = st.number_input("Número de Contratos", min_value=1, step=1, value=int(strategy['numero_contratos']))

                    column_type, column_status = st.columns([1, 1])
                    with column_type:
                        tipo = st.selectbox("Tipo", options=tipos, index=tipos.index(strategy['type']))
                    with column_status:
                        status = st.selectbox("Status", options=["Ativa", "Inativa"], index=["Ativa", "Inativa"].index(strategy['status']))

                    observacao = st.text_area("Observação", value=strategy['observacao'])

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Salvar Alterações"):
                            update_strategy(selected_strategy_id, data_inicial, data_final, hora_inicial, hora_final, carteira,
                                            numero_contratos, tipo, status, observacao)
                            st.success("Estratégia atualizada com sucesso!")
                    with col2:
                        if st.form_submit_button("Duplicar Estratégia"):
                            duplicate_strategy(selected_strategy_id)
                            st.success("Estratégia duplicada com sucesso!")

    elif "results" in st.session_state:
        st.warning("Nenhuma estratégia encontrada para os filtros aplicados.")
