from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify, send_from_directory
import sqlite3
import os
import uuid  # Para gerar nomes únicos
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime
import time
import random
import string
from zipfile import ZipFile, ZIP_DEFLATED

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

@app.template_filter('data_br')
def data_br(value):
    if not value:
        return '-'
    try:
        # Converte string do banco (YYYY-MM-DD) para DD/MM/YYYY
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return value

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
        iniciou_no_dia = request.form.get("iniciou_no_dia")

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
                foto, nucleo, responsavel, iniciou_no_dia
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome_completo, apelido, idade, telefone, mensalidade, batizado,
            graduacao_atual, graduacao_tamanho, camisa_tamanho, calsa_tamanho,
            foto_filename, nucleo, responsavel, iniciou_no_dia
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
        iniciou_no_dia = request.form.get("iniciou_no_dia")

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
                nucleo=?, responsavel=?, foto=?, iniciou_no_dia=?
            WHERE id=?
        """, (
            nome_completo, apelido, idade, telefone, mensalidade, batizado,
            graduacao_atual, graduacao_tamanho, camisa_tamanho, calsa_tamanho,
            nucleo, responsavel, foto_filename, iniciou_no_dia,  # <- corrigido
            aluno_id
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/")

    cursor.close()
    conn.close()
    return render_template("editar.html", aluno=aluno, graduacoes=graduacoes)

@app.route("/deletar/<int:aluno_id>", methods=["POST", "GET"])
def deletar(aluno_id):
    conn = conectar_banco()
    conn.row_factory = sqlite3.Row  # <-- ADICIONE ESTA LINHA
    cursor = conn.cursor()

    # Buscar o aluno
    cursor.execute("SELECT foto FROM usuarios WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()

    if aluno:
        # Deletar foto se existir e não for default
        if aluno["foto"] and aluno["foto"] != "default.png":
            caminho_foto = os.path.join(app.config["UPLOAD_FOLDER"], aluno["foto"])
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)

        # Deletar do banco
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (aluno_id,))
        conn.commit()
        flash("Aluno deletado com sucesso!", "success")
    else:
        flash("Aluno não encontrado!", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("index"))



PASTA_FOTOS = os.path.abspath('static/fotos')
BANCO_DADOS = os.path.abspath('database.db')
PASTA_BACKUPS = os.path.abspath('static/backups')

def corrigir_timestamps(pasta):
    for root, dirs, files in os.walk(pasta):
        for f in files:
            caminho = os.path.join(root, f)
            try:
                os.utime(caminho, (time.time(), time.time()))
            except Exception as e:
                print(f"Erro ao corrigir timestamp de {caminho}: {e}")

def nome_aleatorio(n=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

@app.route('/backup')
def backup():
    try:
        os.makedirs(PASTA_BACKUPS, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        aleatorio = nome_aleatorio()
        backup_zip_name = f'backup_{timestamp}_{aleatorio}.zip'
        backup_zip_path = os.path.join(PASTA_BACKUPS, backup_zip_name)

        # Criar zip manualmente
        with ZipFile(backup_zip_path, 'w', ZIP_DEFLATED) as zipf:
            # Banco de dados
            corrigir_timestamps(os.path.dirname(BANCO_DADOS))
            zipf.write(BANCO_DADOS, arcname=os.path.basename(BANCO_DADOS))

            # Fotos
            corrigir_timestamps(PASTA_FOTOS)
            for root, dirs, files in os.walk(PASTA_FOTOS):
                for f in files:
                    caminho_completo = os.path.join(root, f)
                    arcname = os.path.relpath(caminho_completo, os.path.dirname(PASTA_FOTOS))
                    zipf.write(caminho_completo, arcname=os.path.join('fotos', arcname))

        flash(f'Backup criado com sucesso!', 'success')
        # Guardar o arquivo criado para download
        flash(backup_zip_name, 'download')

    except Exception as e:
        flash(f'Erro ao criar backup: {e}', 'danger')

    return redirect(url_for('ferramentas'))

@app.route('/download_backup/<filename>')
def download_backup(filename):
    return send_from_directory(PASTA_BACKUPS, filename, as_attachment=True)


# Rota limpar backups
@app.route('/limpar_backups', methods=['POST'])
def limpar_backups():
    try:
        if os.path.exists(PASTA_BACKUPS):
            for arquivo in os.listdir(PASTA_BACKUPS):
                caminho = os.path.join(PASTA_BACKUPS, arquivo)
                if os.path.isfile(caminho) or os.path.islink(caminho):
                    os.remove(caminho)
                elif os.path.isdir(caminho):
                    shutil.rmtree(caminho)
        flash('Todos os backups foram removidos com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao limpar backups: {e}', 'danger')
    return redirect(url_for('ferramentas'))

# Rota resetar banco
@app.route('/resetar_banco', methods=['POST'])
def resetar_banco():
    try:
        # Limpar tabelas do banco
        conn = sqlite3.connect(BANCO_DADOS)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        for tabela in tabelas:
            nome_tabela = tabela[0]
            if nome_tabela != 'sqlite_sequence':
                cursor.execute(f"DELETE FROM {nome_tabela};")
        conn.commit()
        conn.close()

        # Deletar imagens da pasta fotos
        if os.path.exists(PASTA_FOTOS):
            for arquivo in os.listdir(PASTA_FOTOS):
                caminho = os.path.join(PASTA_FOTOS, arquivo)
                if os.path.isfile(caminho):
                    os.remove(caminho)

        flash('Banco resetado e fotos removidas com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao resetar banco: {e}', 'danger')

    return redirect(url_for('ferramentas'))

# Rota ferramentas
@app.route('/ferramentas')
def ferramentas():
    return render_template('ferramentas.html', os=os, PASTA_BACKUPS=PASTA_BACKUPS)

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
            responsavel TEXT,
            iniciou_no_dia TEXT
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    app.run(debug=False, host='0.0.0.0')