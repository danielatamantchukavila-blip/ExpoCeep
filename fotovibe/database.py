"""
database.py
------------
Camada de acesso a dados do Foto Vibe.

Este módulo é o único responsável por falar com o banco SQLite.
Nenhum outro arquivo do projeto deve abrir uma conexão sqlite3 diretamente:
tudo passa pelas funções definidas aqui. Isso deixa o projeto fácil de
manter e, no futuro, fácil de trocar o SQLite por outro banco sem mexer
nas rotas do Flask.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

CAMINHO_BANCO = "fotovibe.db"


# --------------------------------------------------------------------------
# Conexão
# --------------------------------------------------------------------------

@contextmanager
def obter_conexao():
    """
    Abre uma conexão com o banco e garante que ela seja fechada no final,
    mesmo se ocorrer um erro. Usada com 'with obter_conexao() as con:'.
    """
    con = sqlite3.connect(CAMINHO_BANCO)
    con.row_factory = sqlite3.Row      # permite acessar colunas por nome: linha["nome"]
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# --------------------------------------------------------------------------
# Criação das tabelas
# --------------------------------------------------------------------------

def inicializar_banco():
    """
    Cria as tabelas do zero, caso ainda não existam.
    Chamado uma vez quando o app.py sobe.
    """
    with obter_conexao() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_usuario    TEXT NOT NULL UNIQUE,
                email           TEXT NOT NULL UNIQUE,
                senha_hash      TEXT NOT NULL,
                bio             TEXT DEFAULT '',
                foto_perfil     TEXT DEFAULT '',
                criado_em       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS posts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id      INTEGER NOT NULL,
                imagem          TEXT NOT NULL,
                legenda         TEXT DEFAULT '',
                criado_em       TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS curtidas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id         INTEGER NOT NULL,
                usuario_id      INTEGER NOT NULL,
                criado_em       TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                UNIQUE (post_id, usuario_id)
            );

            CREATE TABLE IF NOT EXISTS comentarios (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id         INTEGER NOT NULL,
                usuario_id      INTEGER NOT NULL,
                texto           TEXT NOT NULL,
                criado_em       TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_posts_usuario ON posts (usuario_id);
            CREATE INDEX IF NOT EXISTS idx_curtidas_post ON curtidas (post_id);
            CREATE INDEX IF NOT EXISTS idx_comentarios_post ON comentarios (post_id);
            """
        )


def _agora():
    return datetime.utcnow().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Usuários
# --------------------------------------------------------------------------

def criar_usuario(nome_usuario, email, senha_hash):
    with obter_conexao() as con:
        cursor = con.execute(
            """INSERT INTO usuarios (nome_usuario, email, senha_hash, criado_em)
               VALUES (?, ?, ?, ?)""",
            (nome_usuario, email, senha_hash, _agora()),
        )
        return cursor.lastrowid


def buscar_usuario_por_id(usuario_id):
    with obter_conexao() as con:
        linha = con.execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(linha) if linha else None


def buscar_usuario_por_login(identificador):
    """Aceita nome de usuário OU e-mail para o login."""
    with obter_conexao() as con:
        linha = con.execute(
            "SELECT * FROM usuarios WHERE nome_usuario = ? OR email = ?",
            (identificador, identificador),
        ).fetchone()
        return dict(linha) if linha else None


def buscar_usuario_por_nome(nome_usuario):
    with obter_conexao() as con:
        linha = con.execute(
            "SELECT * FROM usuarios WHERE nome_usuario = ?", (nome_usuario,)
        ).fetchone()
        return dict(linha) if linha else None


def atualizar_perfil(usuario_id, bio, foto_perfil=None):
    with obter_conexao() as con:
        if foto_perfil:
            con.execute(
                "UPDATE usuarios SET bio = ?, foto_perfil = ? WHERE id = ?",
                (bio, foto_perfil, usuario_id),
            )
        else:
            con.execute(
                "UPDATE usuarios SET bio = ? WHERE id = ?", (bio, usuario_id)
            )


# --------------------------------------------------------------------------
# Posts (fotos)
# --------------------------------------------------------------------------

def criar_post(usuario_id, imagem, legenda):
    with obter_conexao() as con:
        cursor = con.execute(
            """INSERT INTO posts (usuario_id, imagem, legenda, criado_em)
               VALUES (?, ?, ?, ?)""",
            (usuario_id, imagem, legenda, _agora()),
        )
        return cursor.lastrowid


def listar_feed(usuario_atual_id=None, limite=30):
    """
    Retorna os posts mais recentes de todos os usuários, já com o nome de
    quem postou, a contagem de curtidas, o total de comentários e se o
    usuário logado já curtiu cada post.
    """
    with obter_conexao() as con:
        linhas = con.execute(
            """
            SELECT
                p.id, p.imagem, p.legenda, p.criado_em,
                u.id AS usuario_id, u.nome_usuario, u.foto_perfil,
                (SELECT COUNT(*) FROM curtidas c WHERE c.post_id = p.id) AS total_curtidas,
                (SELECT COUNT(*) FROM comentarios cm WHERE cm.post_id = p.id) AS total_comentarios,
                EXISTS(
                    SELECT 1 FROM curtidas c2
                    WHERE c2.post_id = p.id AND c2.usuario_id = ?
                ) AS curtido_por_mim
            FROM posts p
            JOIN usuarios u ON u.id = p.usuario_id
            ORDER BY p.id DESC
            LIMIT ?
            """,
            (usuario_atual_id or -1, limite),
        ).fetchall()
        return [dict(linha) for linha in linhas]


def listar_posts_do_usuario(usuario_id):
    with obter_conexao() as con:
        linhas = con.execute(
            """
            SELECT p.*,
                (SELECT COUNT(*) FROM curtidas c WHERE c.post_id = p.id) AS total_curtidas
            FROM posts p
            WHERE p.usuario_id = ?
            ORDER BY p.id DESC
            """,
            (usuario_id,),
        ).fetchall()
        return [dict(linha) for linha in linhas]


def buscar_post_por_id(post_id, usuario_atual_id=None):
    with obter_conexao() as con:
        linha = con.execute(
            """
            SELECT
                p.id, p.imagem, p.legenda, p.criado_em,
                u.id AS usuario_id, u.nome_usuario, u.foto_perfil,
                (SELECT COUNT(*) FROM curtidas c WHERE c.post_id = p.id) AS total_curtidas,
                EXISTS(
                    SELECT 1 FROM curtidas c2
                    WHERE c2.post_id = p.id AND c2.usuario_id = ?
                ) AS curtido_por_mim
            FROM posts p
            JOIN usuarios u ON u.id = p.usuario_id
            WHERE p.id = ?
            """,
            (usuario_atual_id or -1, post_id),
        ).fetchone()
        return dict(linha) if linha else None


def excluir_post(post_id, usuario_id):
    """Só exclui se o post pertencer ao usuário informado."""
    with obter_conexao() as con:
        cursor = con.execute(
            "DELETE FROM posts WHERE id = ? AND usuario_id = ?",
            (post_id, usuario_id),
        )
        return cursor.rowcount > 0


# --------------------------------------------------------------------------
# Curtidas
# --------------------------------------------------------------------------

def alternar_curtida(post_id, usuario_id):
    """
    Curte o post se ainda não estiver curtido, ou remove a curtida se já
    estiver. Retorna True se ficou curtido, False se ficou descurtido.
    """
    with obter_conexao() as con:
        ja_curtiu = con.execute(
            "SELECT 1 FROM curtidas WHERE post_id = ? AND usuario_id = ?",
            (post_id, usuario_id),
        ).fetchone()

        if ja_curtiu:
            con.execute(
                "DELETE FROM curtidas WHERE post_id = ? AND usuario_id = ?",
                (post_id, usuario_id),
            )
            return False
        else:
            con.execute(
                "INSERT INTO curtidas (post_id, usuario_id, criado_em) VALUES (?, ?, ?)",
                (post_id, usuario_id, _agora()),
            )
            return True


# --------------------------------------------------------------------------
# Comentários
# --------------------------------------------------------------------------

def criar_comentario(post_id, usuario_id, texto):
    with obter_conexao() as con:
        cursor = con.execute(
            """INSERT INTO comentarios (post_id, usuario_id, texto, criado_em)
               VALUES (?, ?, ?, ?)""",
            (post_id, usuario_id, texto, _agora()),
        )
        return cursor.lastrowid


def listar_comentarios(post_id):
    with obter_conexao() as con:
        linhas = con.execute(
            """
            SELECT cm.*, u.nome_usuario, u.foto_perfil
            FROM comentarios cm
            JOIN usuarios u ON u.id = cm.usuario_id
            WHERE cm.post_id = ?
            ORDER BY cm.id ASC
            """,
            (post_id,),
        ).fetchall()
        return [dict(linha) for linha in linhas]
