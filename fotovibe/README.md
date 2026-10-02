# Foto na Tela

Site de postagem de fotos feito em Python (Flask) com banco de dados SQLite,
com uma API JSON consumida pelo front-end via `fetch`.

Projeto da disciplina **Programação Back-End** — Curso Técnico em
Desenvolvimento de Sistemas (3º C/M), CEEP. Apresentado na **EXPOCEEP**.

**Integrantes:** Lucas, Giovanna, Daniel e Davi.

## Tecnologias

- **Banco de dados:** SQLite3 (arquivo `fotovibe.db`)
- **Back-End:** Python 3 + Flask (`flask-cors` para liberar o `fetch` de outra origem)
- **Front-End:** HTML, CSS e JavaScript assíncrono (`fetch`) consumindo JSON
- **Segurança:** senhas armazenadas com hash (`werkzeug.security`)

## Estrutura do projeto

```
fotovibe/
├── app.py              # Rotas, sessão, upload de imagens e API JSON (Flask)
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

# 2. Instale as dependências (Flask, flask-cors, ...)
pip install -r requirements.txt

# 3. Rode o servidor
python app.py
```

Acesse **http://127.0.0.1:5000** no navegador. O arquivo `fotovibe.db` é
criado automaticamente na primeira execução, com todas as tabelas.

### Rodando o front-end que usa a API (`fetch`)

1. Deixe o servidor Flask rodando (`python app.py`, porta **5000**).
2. Abra a página HTML do front-end com a extensão **Live Server** do VS Code
   (normalmente na porta **5500**).
3. O `flask-cors` (`CORS(app)` no `app.py`) permite que essa página, em outra
   origem, faça `fetch` para `http://127.0.0.1:5000/api/...`.

## Funcionalidades incluídas

- Cadastro e login de usuários (senha protegida com hash — `werkzeug.security`)
- Publicar fotos com legenda (upload de imagem, PNG/JPG/GIF/WEBP)
- Feed com as fotos mais recentes de todos os usuários
- Curtir / descurtir posts
- Comentar em posts
- Página de perfil com galeria de fotos do usuário e edição de bio/avatar
- Excluir os próprios posts
- API JSON para listar usuários, cadastrar usuário e listar o feed

## Documentação da API REST (JSON)

URL base local: `http://127.0.0.1:5000`

| Verbo | Rota             | Descrição                                       | Códigos de resposta |
|-------|------------------|-------------------------------------------------|---------------------|
| GET   | `/api/status`    | Teste: confirma que a API está no ar            | 200                 |
| GET   | `/api/usuarios`  | Lista os usuários (sem e-mail e sem senha)      | 200                 |
| POST  | `/api/usuarios`  | Cadastra um novo usuário a partir de um JSON    | 201, 400, 409       |
| GET   | `/api/feed`      | Lista os posts mais recentes com a URL da imagem | 200                |

### GET `/api/status`

Resposta `200`:

```json
{ "status": "ok", "app": "Foto na Tela" }
```

### GET `/api/usuarios`

Devolve uma lista de usuários. O e-mail e a senha nunca são enviados.

Resposta `200`:

```json
[
  { "id": 1, "nome_usuario": "maria", "...": "demais campos públicos do usuário" }
]
```

### POST `/api/usuarios`

Cabeçalho obrigatório: `Content-Type: application/json`

Corpo da requisição:

```json
{
  "nome_usuario": "maria",
  "email": "maria@email.com",
  "senha": "123456",
  "confirmar_senha": "123456"
}
```

Resposta `201` (criado):

```json
{ "id": 1, "mensagem": "Usuário cadastrado com sucesso!" }
```

Respostas de erro (sempre no formato `{ "erro": "..." }`):

| Código | Quando acontece                          | Mensagem                                       |
|--------|------------------------------------------|------------------------------------------------|
| 400    | Corpo não é um JSON válido               | `Envie um JSON válido.`                        |
| 400    | Algum campo obrigatório vazio            | `Preencha todos os campos.`                    |
| 400    | Senha com menos de 6 caracteres          | `A senha precisa ter pelo menos 6 caracteres.` |
| 400    | `senha` diferente de `confirmar_senha`   | `As senhas não coincidem.`                     |
| 409    | Nome de usuário já existe                | `Esse nome de usuário já está em uso.`         |
| 409    | E-mail já cadastrado                     | `Esse e-mail já está cadastrado.`              |

### GET `/api/feed`

Devolve os posts mais recentes. Cada post traz o campo extra `imagem_url`,
com o endereço completo da foto, pronto para usar em `<img src="...">`.

Resposta `200`:

```json
[
  {
    "imagem": "a1b2c3.jpg",
    "imagem_url": "http://127.0.0.1:5000/static/uploads/a1b2c3.jpg",
    "...": "demais campos do post (legenda, autor, curtidas, ...)"
  }
]
```

### Exemplos de uso

Com `curl`:

```bash
curl http://127.0.0.1:5000/api/usuarios

curl -X POST http://127.0.0.1:5000/api/usuarios \
  -H "Content-Type: application/json" \
  -d '{"nome_usuario":"maria","email":"maria@email.com","senha":"123456","confirmar_senha":"123456"}'
```

Com JavaScript (`fetch`):

```javascript
const resposta = await fetch("http://127.0.0.1:5000/api/feed");
const posts = await resposta.json();
```

## Rotas das páginas (HTML)

Rotas que renderizam as páginas do site. As marcadas com 🔒 exigem login.

| Verbo     | Rota                            | Descrição                          |
|-----------|---------------------------------|------------------------------------|
| GET       | `/`                             | Feed com as fotos mais recentes    |
| GET, POST | `/cadastro`                     | Criar conta                        |
| GET, POST | `/login`                        | Entrar                             |
| GET       | `/sair`                         | Sair da conta                      |
| GET, POST | `/publicar` 🔒                  | Publicar foto com legenda          |
| GET       | `/post/<id>`                    | Ver um post e seus comentários     |
| POST      | `/post/<id>/excluir` 🔒         | Excluir o próprio post             |
| POST      | `/post/<id>/curtir` 🔒          | Curtir / descurtir                 |
| POST      | `/post/<id>/comentar` 🔒        | Comentar em um post                |
| GET       | `/perfil/<nome_usuario>`        | Perfil e galeria do usuário        |
| GET, POST | `/perfil/editar` 🔒             | Editar bio e foto de perfil        |
| GET       | `/static/uploads/<nome_arquivo>`| Serve as imagens enviadas          |

## Próximos passos sugeridos

- Trocar `app.secret_key` por um valor aleatório antes de publicar (ex.: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Adicionar paginação no feed (`listar_feed` já aceita `limite`)
- Criar rotas `PUT` e `DELETE` na API JSON (hoje a API tem apenas `GET` e `POST`)
- Redimensionar/comprimir imagens no upload (ex. com `Pillow`) para economizar espaço
- Trocar `app.run(debug=True)` por um servidor de produção (gunicorn/uwsgi) antes de colocar no ar