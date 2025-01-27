import sqlite3
import bcrypt

# Função para conectar ao banco de dados SQLite
def connect_db():
    return sqlite3.connect("dados.db")

# Função para criar tabela de usuários
def criar_tabela_usuarios():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            senha BLOB NOT NULL,  -- Senhas armazenadas como BLOB (bytes)
            cargo TEXT NOT NULL,
            setor TEXT NOT NULL
        );
        """)
        conn.commit()

# Função para gerar hash seguro da senha
def gerar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

# Função para cadastrar usuário
def cadastrar_usuario(email, senha, cargo, setor):
    with connect_db() as conn:
        cursor = conn.cursor()

        # Gerar hash da senha
        senha_hashed = gerar_hash_senha(senha)

        try:
            # Inserir o usuário no banco de dados
            cursor.execute("""
            INSERT INTO usuarios (email, senha, cargo, setor)
            VALUES (?, ?, ?, ?)
            """, (email, senha_hashed, cargo, setor))
            conn.commit()
            print(f"Usuário '{email}' cadastrado com sucesso!")
        except sqlite3.IntegrityError:
            print(f"Erro: O email '{email}' já está cadastrado.")
        except Exception as e:
            print(f"Erro inesperado ao cadastrar usuário '{email}': {e}")

# Função para verificar credenciais do usuário
def autenticar_usuario(email, senha):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()

        if result:
            senha_hashed = result[0]
            # Verificar se a senha fornecida corresponde ao hash armazenado
            if bcrypt.checkpw(senha.encode(), senha_hashed):
                return True
        return False

# Função principal
if __name__ == "__main__":
    # Criar tabela de usuários, se ainda não existir
    criar_tabela_usuarios()

    # Lista de usuários para cadastrar
    usuarios = [
        ("visitante.teste@teste.net.br", "@teste", "ADM", "Operações")
    ]

    # Cadastrar os usuários na lista
    for email, senha, cargo, setor in usuarios:
        cadastrar_usuario(email, senha, cargo, setor)

    # Exemplo de autenticação
    email_teste = "visitante.teste@teste.net.br"
    senha_teste = "@teste"
    if autenticar_usuario(email_teste, senha_teste):
        print("Usuário autenticado com sucesso!")
    else:
        print("Falha na autenticação. Verifique o email e a senha.")