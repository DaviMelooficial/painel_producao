import streamlit as st
import sqlite3
import bcrypt
from Painel_acionamentos import rodar_dashboard_acionamentos
from Painel_HORAxHORA import rodar_dashboard_hora
from Estrategias_dia import estrategias
from Acompanhamento_acessos import carregar_acessos
from Painel_debates import painel_debates
from datetime import datetime

st.set_page_config(
    page_title="Acompanhamento de produção",
)

# Conexão ao banco
def connect_db():
    return sqlite3.connect("dados.db")

# Criação da tabela de usuários
def create_user_table():
    with connect_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha BLOB NOT NULL, 
            cargo TEXT NOT NULL,
            setor TEXT NOT NULL
        );
        """)
        conn.commit()

# Adiciona usuário com hash 
def add_user(email, senha, cargo, setor):
    senha_hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    with connect_db() as conn:
        try:
            conn.execute("INSERT INTO usuarios (email, senha, cargo, setor) VALUES (?, ?, ?, ?)",
                         (email, senha_hashed, cargo, setor))
            conn.commit()
            print(f"Usuário {email} adicionado com sucesso.")
        except sqlite3.IntegrityError:
            print(f"Erro: O email '{email}' já está cadastrado.")

# Autenticação de usuário
def authenticate_user(email, senha):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT senha, cargo, setor FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()

    if result:
        senha_hashed, cargo, setor = result
        if bcrypt.checkpw(senha.encode(), senha_hashed): 
            return cargo, setor
    return None

def registrar_acesso(email):
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with connect_db() as conn:
        query = "INSERT INTO acessos (email, data_hora) VALUES (?, ?);"
        conn.execute(query, (email, data_hora))
        conn.commit()

def login():
    st.title("Sistema de Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Login"):
        user_info = authenticate_user(email, senha)
        if user_info:
            # Atualiza o estado do login
            st.session_state.logged_in = True
            st.session_state.email = email
            st.session_state.cargo, st.session_state.setor = user_info
            st.session_state.page = "Acompanhamento de Acordos"

            # Registrar o acesso
            registrar_acesso(email)

            st.rerun()
        else:
            st.error("Credenciais inválidas.")

def mostrar_painel():
    paineis = {
        "Acompanhamento de Acordos": rodar_dashboard_acionamentos,
        "Visão por Hora": rodar_dashboard_hora,
        "Visão de Estratégias": estrategias,
        "Consulta de acessos": carregar_acessos,
        "Apontamentos estratégicos": painel_debates
    }

    st.sidebar.title("Menu de Navegação")
    st.sidebar.markdown(f"**Usuário:** {st.session_state.email}")
    st.sidebar.markdown(f"**Cargo:** {st.session_state.cargo}")
    st.sidebar.markdown(f"**Setor:** {st.session_state.setor}")

    # Menu baseado nas permissões
    permissoes = {
        "Administrador": ["Acompanhamento de Acordos", "Visão por Hora", "Visão de Estratégias", "Consulta de acessos", "Apontamentos estratégicos"],
        "Gerente": ["Acompanhamento de Acordos", "Visão de Estratégias", "Visão por Hora", "Consulta de acessos", "Apontamentos estratégicos"],
        "Coordenador": ["Acompanhamento de Acordos", "Visão por Hora", "Visão de Estratégias", "Apontamentos estratégicos"],
        "Supervisor": ["Acompanhamento de Acordos", "Visão por Hora", "Visão de Estratégias", "Apontamentos estratégicos"],
        "ADM": ["Acompanhamento de Acordos", "Visão por Hora", "Visão de Estratégias", "Apontamentos estratégicos"]
    }

    opcoes = permissoes.get(st.session_state.cargo, [])
    if opcoes:
        painel_selecionado = st.sidebar.radio("Selecione o Painel", opcoes, index=0)
        st.session_state.page = painel_selecionado

        # Executa o painel selecionado
        if st.session_state.page in paineis:
            paineis[st.session_state.page]()
        else:
            st.error("Painel não encontrado.")
    else:
        st.error("Você não tem permissão para acessar os dashboards.")

    # Botão de logout
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "Login"
        st.rerun()

# Função principal
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.page = "Login"

    if not st.session_state.logged_in:
        login()
    else:
        mostrar_painel()

# Executa a aplicação
if __name__ == "__main__":
    main()