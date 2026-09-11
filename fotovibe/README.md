# Foto Vibe

Site de postagem de fotos feito em Python (Flask) com banco de dados SQLite.

## Estrutura do projeto

```
fotovibe/
├── app.py              # Rotas, sessão, upload de imagens (Flask)
├── database.py         # TODO o acesso ao banco SQLite fica isolado aqui
├── requirements.txt
├── fotovibe.db          # criado automaticamente na primeira execução
├── static/
│   ├── css/style.css
│   └── uploads/          # fotos enviadas pelos usuários
└── templates/
    ├── base.html
    ├── feed.html
    ├── login.html
    ├── cadastro.html
    ├── publicar.html
    ├── post.html
    ├── perfil.html
    └── editar_perfil.html
```

A separação é proposital: **app.py nunca executa SQL diretamente** — ele
sempre chama funções do `database.py` (`db.criar_usuario`, `db.listar_feed`,
etc). Isso deixa o projeto organizado e fácil de evoluir.

## Como rodar

```bash
# 1. Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o servidor
python app.py
```

Acesse **http://127.0.0.1:5000** no navegador. O arquivo `fotovibe.db` é
criado automaticamente na primeira execução, com todas as tabelas.

## Funcionalidades incluídas

- Cadastro e login de usuários (senha protegida com hash — `werkzeug.security`)
- Publicar fotos com legenda (upload de imagem, PNG/JPG/GIF/WEBP)
- Feed com as fotos mais recentes de todos os usuários
- Curtir / descurtir posts
- Comentar em posts
- Página de perfil com galeria de fotos do usuário e edição de bio/avatar
- Excluir os próprios posts

## Próximos passos sugeridos

- Trocar `app.secret_key` por um valor aleatório antes de publicar (ex.: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Adicionar paginação no feed (`listar_feed` já aceita `limite`)
- Redimensionar/comprimir imagens no upload (ex. com `Pillow`) para economizar espaço
- Trocar `app.run(debug=True)` por um servidor de produção (gunicorn/uwsgi) antes de colocar no ar
