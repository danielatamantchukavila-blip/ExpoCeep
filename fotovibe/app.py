"""
app.py
------
Aplicação Flask do Foto Vibe.

Toda a lógica de rotas, sessão de usuário e upload de arquivos vive aqui.
Todo o acesso a dados vive em database.py — este arquivo nunca executa SQL
diretamente, apenas chama as funções do módulo `database`.
"""

import os
import uuid
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, send_from_directory, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import database as db

# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "troque-esta-chave-por-uma-bem-aleatoria-antes-de-publicar"

PASTA_UPLOADS = os.path.join(app.root_path, "static", "uploads")
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}
TAMANHO_MAXIMO_MB = 8

app.config["MAX_CONTENT_LENGTH"] = TAMANHO_MAXIMO_MB * 1024 * 1024
os.makedirs(PASTA_UPLOADS, exist_ok=True)

# Garante que as tabelas existam assim que o módulo é carregado — funciona
# tanto rodando "python app.py" quanto com "flask run" ou um servidor WSGI
# de produção (gunicorn, uwsgi), que nunca passam pelo bloco __main__.
db.inicializar_banco()


# --------------------------------------------------------------------------
# Funções auxiliares
# --------------------------------------------------------------------------

def extensao_valida(nome_arquivo):
    return (
        "." in nome_arquivo
        and nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS
    )


def salvar_imagem(arquivo):
    """Salva o arquivo enviado com um nome único e devolve o nome salvo."""
    nome_original = secure_filename(arquivo.filename)
    extensao = nome_original.rsplit(".", 1)[1].lower()
    nome_novo = f"{uuid.uuid4().hex}.{extensao}"
    arquivo.save(os.path.join(PASTA_UPLOADS, nome_novo))
    return nome_novo


def login_obrigatorio(view):
    """Decorator que bloqueia o acesso a rotas privadas sem login."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Você precisa entrar para acessar essa página.", "erro")
            return redirect(url_for("login", proximo=request.path))
        return view(*args, **kwargs)
    return wrapper


@app.context_processor
def injetar_usuario_logado():
    """Deixa o usuário logado disponível em todos os templates como 'usuario_logado'."""
    usuario = None
    if "usuario_id" in session:
        usuario = db.buscar_usuario_por_id(session["usuario_id"])
    return {"usuario_logado": usuario}


# --------------------------------------------------------------------------
# Rotas de autenticação
# --------------------------------------------------------------------------

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome_usuario or not email or not senha:
            flash("Preencha todos os campos.", "erro")
        elif len(senha) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "erro")
        elif senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
        elif db.buscar_usuario_por_nome(nome_usuario):
            flash("Esse nome de usuário já está em uso.", "erro")
        else:
            senha_hash = generate_password_hash(senha)
            try:
                usuario_id = db.criar_usuario(nome_usuario, email, senha_hash)
            except Exception:
                flash("Esse e-mail já está cadastrado.", "erro")
            else:
                session["usuario_id"] = usuario_id
                flash("Conta criada com sucesso! Bem-vindo(a) ao Foto Vibe.", "sucesso")
                return redirect(url_for("feed"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identificador = request.form.get("identificador", "").strip()
        senha = request.form.get("senha", "")

        usuario = db.buscar_usuario_por_login(identificador)
        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session["usuario_id"] = usuario["id"]
            flash(f"Olá de novo, {usuario['nome_usuario']}!", "sucesso")
            proximo = request.args.get("proximo")
            return redirect(proximo or url_for("feed"))

        flash("Usuário/e-mail ou senha incorretos.", "erro")

    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# Feed e posts
# --------------------------------------------------------------------------

@app.route("/")
def feed():
    usuario_id = session.get("usuario_id")
    posts = db.listar_feed(usuario_atual_id=usuario_id)
    return render_template("feed.html", posts=posts)


@app.route("/publicar", methods=["GET", "POST"])
@login_obrigatorio
def publicar():
    if request.method == "POST":
        arquivo = request.files.get("imagem")
        legenda = request.form.get("legenda", "").strip()

        if not arquivo or arquivo.filename == "":
            flash("Selecione uma foto para publicar.", "erro")
        elif not extensao_valida(arquivo.filename):
            flash("Formato inválido. Use PNG, JPG, GIF ou WEBP.", "erro")
        else:
            nome_arquivo = salvar_imagem(arquivo)
            db.criar_post(session["usuario_id"], nome_arquivo, legenda)
            flash("Foto publicada!", "sucesso")
            return redirect(url_for("feed"))

    return render_template("publicar.html")


@app.route("/post/<int:post_id>")
def ver_post(post_id):
    usuario_id = session.get("usuario_id")
    post = db.buscar_post_por_id(post_id, usuario_atual_id=usuario_id)
    if not post:
        abort(404)
    comentarios = db.listar_comentarios(post_id)
    return render_template("post.html", post=post, comentarios=comentarios)


@app.route("/post/<int:post_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir_post(post_id):
    sucesso = db.excluir_post(post_id, session["usuario_id"])
    if sucesso:
        flash("Post excluído.", "sucesso")
    else:
        flash("Você não pode excluir esse post.", "erro")
    return redirect(url_for("feed"))


@app.route("/post/<int:post_id>/curtir", methods=["POST"])
@login_obrigatorio
def curtir(post_id):
    db.alternar_curtida(post_id, session["usuario_id"])
    proximo = request.form.get("proximo") or url_for("feed")
    return redirect(proximo)


@app.route("/post/<int:post_id>/comentar", methods=["POST"])
@login_obrigatorio
def comentar(post_id):
    texto = request.form.get("texto", "").strip()
    if texto:
        db.criar_comentario(post_id, session["usuario_id"], texto)
    return redirect(url_for("ver_post", post_id=post_id))


# --------------------------------------------------------------------------
# Perfil
# --------------------------------------------------------------------------

@app.route("/perfil/<nome_usuario>")
def perfil(nome_usuario):
    usuario = db.buscar_usuario_por_nome(nome_usuario)
    if not usuario:
        abort(404)
    posts = db.listar_posts_do_usuario(usuario["id"])
    return render_template("perfil.html", usuario=usuario, posts=posts)


@app.route("/perfil/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar_perfil():
    usuario = db.buscar_usuario_por_id(session["usuario_id"])

    if request.method == "POST":
        bio = request.form.get("bio", "").strip()
        arquivo = request.files.get("foto_perfil")
        nome_arquivo = None

        if arquivo and arquivo.filename != "":
            if extensao_valida(arquivo.filename):
                nome_arquivo = salvar_imagem(arquivo)
            else:
                flash("Formato de imagem inválido para a foto de perfil.", "erro")
                return render_template("editar_perfil.html", usuario=usuario)

        db.atualizar_perfil(usuario["id"], bio, nome_arquivo)
        flash("Perfil atualizado.", "sucesso")
        return redirect(url_for("perfil", nome_usuario=usuario["nome_usuario"]))

    return render_template("editar_perfil.html", usuario=usuario)


# --------------------------------------------------------------------------
# Arquivos estáticos de upload (imagens enviadas pelos usuários)
# --------------------------------------------------------------------------

@app.route("/static/uploads/<nome_arquivo>")
def arquivo_upload(nome_arquivo):
    return send_from_directory(PASTA_UPLOADS, nome_arquivo)


# --------------------------------------------------------------------------
# Rota de teste (Etapa 1 - CEEP)
# --------------------------------------------------------------------------

@app.route("/api/status")
def status():
    return jsonify({"status": "ok", "app": "Foto Vibe"})


# --------------------------------------------------------------------------
# Ponto de entrada
# --------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
