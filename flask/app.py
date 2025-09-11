from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import os
import uuid  # Para gerar nomes únicos
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = "uma_chave_super_secreta"  # Necessário para flash e sessões

ADMIN_SENHA = "123456"  # substitua pela senha real do admin

# Pasta onde as fotos serão salvas
UPLOAD_FOLDER = "static/fotos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Função para conectar ao banco
def conectar_banco():
    return sqlite3.connect("database.db")

# Rota para listar alunos com proteção por senha admin
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        senha = request.form.get("senha")
        if senha == ADMIN_SENHA:
            session['admin_logado'] = True
            return redirect(url_for("index"))
        else:
            flash("Senha incorreta!")

    # Verifica se o admin está logado
    if session.get("admin_logado"):
        conn = conectar_banco()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios ORDER BY id DESC")
        alunos = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        alunos = []  # não mostramos os alunos se não estiver logado

    return render_template("index.html", alunos=alunos, graduacoes=graduacoes)

@app.route("/logout")
def logout():
    session.pop("admin_logado", None)
    flash("Você foi deslogado com sucesso!")
    return redirect(url_for("index"))

# Lista de graduações
graduacoes = [
    ('Aluno', [
        (0, 'Crua'),
        (1, 'Crua ponta Cinza'),
        (2, 'Crua ponta Verde'),
        (3, 'Crua ponta Amarela'),
        (4, 'Crua ponta Azul'),
        (5, 'Cinza'),
        (6, 'Cinza e Verde'),
        (7, 'Verde'),
        (8, 'Cinza e Amarelo'),
        (9, 'Amarelo'),
        (10, 'Cinza e Azul'),
        (11, 'Azul'),
    ]),
    ('Aluno Graduado', [
        (12, 'Verde e Amarelo'),
        (13, 'Verde e Azul'),
        (14, 'Amarelo e Azul'),
    ]),
    ('Estagiário', [
        (15, 'Amarelo e Vermelho'),
    ]),
    ('Formado', [
        (16, 'Verde Amarelo e Azul - Instrutor'),
        (17, 'Verde e Branco - Monitor'),
        (18, 'Amarelo e Branco - Professor'),
        (19, 'Azul e Branco - Contra Mestre'),
    ]),
    ('Mestre', [
        (20, 'Branco Lacre Verde'),
        (21, 'Branco Lacre Amarelo'),
        (22, 'Branco Lacre Azul'),
        (23, 'Branco'),
    ]),
]

# Rota principal
@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        # Capturando todos os campos do formulário
        nome_completo = request.form.get("nome_completo")
        apelido = request.form.get("apelido")
        idade = request.form.get("idade")
        telefone = request.form.get("telefone")
        mensalidade = request.form.get("mensalidade")
        batizado = request.form.get("batizado")
        graduacao_atual = request.form.get("graduacao_atual")  # já será o nome da graduação
        graduacao_tamanho = request.form.get("graduacao_tamanho")
        camisa_tamanho = request.form.get("camisa_tamanho")
        calsa_tamanho = request.form.get("calsa_tamanho")
        foto = request.files.get("foto")
        nucleo = request.form.get("nucleo")
        responsavel = request.form.get("responsavel")

        foto_filename = None
        if foto:
            ext = os.path.splitext(foto.filename)[1]
            foto_filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_filename))

        # Salvar no banco
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (
                nome_completo, apelido, idade, telefone, mensalidade, batizado,
                graduacao_atual, graduacao_tamanho, camisa_tamanho, calsa_tamanho,
                foto, nucleo, responsavel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome_completo, apelido, idade, telefone, mensalidade, batizado,
            graduacao_atual, graduacao_tamanho, camisa_tamanho, calsa_tamanho,
            foto_filename, nucleo, responsavel
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/")

    return render_template("cadastrar.html", graduacoes=graduacoes)

@app.route("/editar/<int:aluno_id>", methods=["GET", "POST"])
def editar(aluno_id):
    conn = conectar_banco()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Buscar os dados do aluno
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()

    if request.method == "POST":
        # Capturando os campos do formulário
        nome_completo = request.form.get("nome_completo")
        apelido = request.form.get("apelido")
        idade = request.form.get("idade")
        telefone = request.form.get("telefone")
        mensalidade = request.form.get("mensalidade")
        batizado = request.form.get("batizado")
        graduacao_atual = request.form.get("graduacao_atual")
        graduacao_tamanho = request.form.get("graduacao_tamanho")
        camisa_tamanho = request.form.get("camisa_tamanho")
        calsa_tamanho = request.form.get("calsa_tamanho")
        foto = request.files.get("foto")
        nucleo = request.form.get("nucleo")
        responsavel = request.form.get("responsavel")

        foto_filename = aluno["foto"]  # manter a foto atual se não enviar nova
        if foto:
            # Excluir a foto antiga se existir e não for default
            if aluno["foto"] and aluno["foto"] != "default.png":
                caminho_antigo = os.path.join(app.config["UPLOAD_FOLDER"], aluno["foto"])
                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)

            # Salvar a nova foto
            ext = os.path.splitext(foto.filename)[1]
            foto_filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_filename))

        # Atualizar no banco incluindo a foto
        cursor.execute("""
            UPDATE usuarios SET 
                nome_completo=?, apelido=?, idade=?, telefone=?, mensalidade=?, batizado=?,
                graduacao_atual=?, graduacao_tamanho=?, camisa_tamanho=?, calsa_tamanho=?,
                nucleo=?, responsavel=?, foto=?
            WHERE id=?
        """, (
            nome_completo, apelido, idade, telefone, mensalidade, batizado,
            graduacao_atual, graduacao_tamanho, camisa_tamanho, calsa_tamanho,
            nucleo, responsavel, foto_filename,
            aluno_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/")

    cursor.close()
    conn.close()
    return render_template("editar.html", aluno=aluno, graduacoes=graduacoes)

PASTA_FOTOS = 'static/fotos'  # pasta que será backupada
BANCO_DADOS = 'database.db'   # banco de dados SQLite

@app.route('/backup')
def backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta_temp = f'backup_temp_{timestamp}'
    os.makedirs(pasta_temp, exist_ok=True)

    # Copiar banco de dados
    shutil.copy2(BANCO_DADOS, pasta_temp)

    # Copiar pasta de fotos
    shutil.copytree(PASTA_FOTOS, os.path.join(pasta_temp, 'fotos'))

    # Criar zip final
    backup_zip = f'backup_{timestamp}.zip'
    shutil.make_archive(f'backup_{timestamp}', 'zip', pasta_temp)

    # Remover pasta temporária
    shutil.rmtree(pasta_temp)

    # Retornar arquivo para download
    return send_file(backup_zip, as_attachment=True)

if __name__ == "__main__":
    conn = conectar_banco()
    cursor = conn.cursor()

    # Cria tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            apelido TEXT,
            idade TEXT NOT NULL,
            telefone TEXT,
            mensalidade TEXT NOT NULL,
            batizado TEXT NOT NULL,
            graduacao_atual TEXT NOT NULL,
            graduacao_tamanho TEXT NOT NULL,
            camisa_tamanho TEXT,
            calsa_tamanho TEXT,
            foto TEXT,
            nucleo TEXT NOT NULL,
            responsavel TEXT
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    app.run(debug=False, host='0.0.0.0')