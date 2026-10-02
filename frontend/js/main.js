// Foto na Tela - Etapa 3: integração Front-End + Back-End via Fetch API
// Se "localhost" não conectar no seu computador, troque por http://127.0.0.1:5000
const API = "http://localhost:5000";

function mostrarMensagem(texto, tipo) {
  const el = document.getElementById("mensagem");
  el.textContent = texto;
  el.className = tipo; // "ok" ou "erro"
}

// ---------- POST: envia o formulário como JSON ----------
async function cadastrarUsuario(event) {
  event.preventDefault(); // impede o recarregamento da página

  const dados = {
    nome_usuario: document.getElementById("nome_usuario").value,
    email: document.getElementById("email").value,
    senha: document.getElementById("senha").value,
    confirmar_senha: document.getElementById("confirmar_senha").value,
  };

  try {
    const resposta = await fetch(`${API}/api/usuarios`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.json(); // o Flask responde JSON tanto no sucesso quanto no erro

    if (resposta.ok) {
      mostrarMensagem(corpo.mensagem, "ok");
      alert("Usuário cadastrado com sucesso no banco SQLite!");
      document.getElementById("form-cadastro").reset();
      carregarUsuarios(); // atualiza a lista na tela sem recarregar a página
    } else {
      mostrarMensagem("Erro: " + corpo.erro, "erro");
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível conectar ao servidor. O Flask está rodando?", "erro");
  }
}

// ---------- GET: busca usuários e monta a lista no DOM ----------
async function carregarUsuarios() {
  const lista = document.getElementById("lista-usuarios");
  try {
    const resposta = await fetch(`${API}/api/usuarios`);
    const usuarios = await resposta.json(); // converte o JSON em array

    lista.innerHTML = "";
    if (usuarios.length === 0) {
      lista.textContent = "Nenhum usuário cadastrado ainda.";
      return;
    }
    usuarios.forEach((u) => {
      const item = document.createElement("li");
      item.textContent = `${u.nome_usuario} - ${u.total_posts} post(s)`;
      lista.appendChild(item);
    });
  } catch (erro) {
    lista.textContent = "Servidor indisponível.";
  }
}

// ---------- GET: busca o feed e monta os cards no DOM ----------
async function carregarFeed() {
  const container = document.getElementById("lista-feed");
  try {
    const resposta = await fetch(`${API}/api/feed`);
    const posts = await resposta.json();

    container.innerHTML = "";
    if (posts.length === 0) {
      container.textContent = "Nenhuma foto publicada ainda.";
      return;
    }
    posts.forEach((p) => {
      const card = document.createElement("div");
      card.className = "card";

      const autor = document.createElement("strong");
      autor.textContent = p.nome_usuario;

      const img = document.createElement("img");
      img.src = p.imagem_url;
      img.alt = p.legenda || "Foto de " + p.nome_usuario;

      const legenda = document.createElement("p");
      legenda.textContent = p.legenda;

      const info = document.createElement("small");
      info.textContent = `${p.total_curtidas} curtida(s) - ${p.total_comentarios} comentário(s)`;

      card.append(autor, img, legenda, info);
      container.appendChild(card);
    });
  } catch (erro) {
    container.textContent = "Servidor indisponível.";
  }
}

document.getElementById("form-cadastro").addEventListener("submit", cadastrarUsuario);

// Executa as buscas assim que a página carrega
window.onload = () => {
  carregarUsuarios();
  carregarFeed();
};