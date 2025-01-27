import streamlit as st
import pandas as pd
import sqlite3
import os
from PIL import Image

def connect_db():
    return sqlite3.connect("dados.db")

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

# Diretório para salvar as imagens
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def salvar_imagem(uploaded_file):
    if uploaded_file:
        # Salvar a imagem com um nome único
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def painel_debates():
    st.title("Apontamentos Estratégicos")
    conn = connect_db()

    # Selecionar uma estratégia
    estrategias = pd.read_sql_query("SELECT id, carteira, type FROM estrategias", conn)
    estrategia_id = st.selectbox(
        "Selecione uma Estratégia",
        options=estrategias["id"],
        format_func=lambda x: f"ID {x} - {estrategias.loc[estrategias['id'] == x, 'carteira'].iloc[0]}"
    )

    # Exibir mensagens do chat
    if estrategia_id:
        st.subheader(f"Pontuações para Estratégia ID {estrategia_id}")

        # Função para carregar mensagens
        def carregar_mensagens(estrategia_id):
            query = """
            SELECT email, mensagem, data_hora, imagem 
            FROM debates 
            WHERE estrategia_id = ? 
            ORDER BY data_hora ASC
            """
            return pd.read_sql_query(query, conn, params=(estrategia_id,))

        mensagens = carregar_mensagens(estrategia_id)
        for _, row in mensagens.iterrows():
            st.markdown(f"**{row['email']}** ({row['data_hora']}): {row['mensagem']}")
            if row['imagem']:
                st.image(row['imagem'], use_column_width=True)

        # Campo para enviar novas mensagens e imagem
        nova_mensagem = st.text_area("Digite sua mensagem:", key="mensagem_chat")
        uploaded_image = st.file_uploader("Envie uma imagem (opcional):", type=["png", "jpg", "jpeg"])

        if st.button("Enviar"):
            if nova_mensagem.strip() or uploaded_image:
                image_path = salvar_imagem(uploaded_image) if uploaded_image else None
                query = """
                INSERT INTO debates (estrategia_id, email, mensagem, imagem) 
                VALUES (?, ?, ?, ?)
                """
                conn.execute(query, (estrategia_id, st.session_state.email, nova_mensagem.strip(), image_path))
                conn.commit()
                st.success("Mensagem enviada!")
                st.rerun()
            else:
                st.error("A mensagem e a imagem não podem estar ambas vazias.")
    conn.close()
