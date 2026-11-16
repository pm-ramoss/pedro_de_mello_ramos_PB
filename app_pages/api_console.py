"""Página 6 — Console da API: documentação e testes dos endpoints."""

import json

import requests
import streamlit as st

import app_utils as utils

st.title("🔌 Console da API")

status = utils.status_api()
if status:
    st.success(f"API online em `{utils.API_URL}` · versão {status.get('versao', '?')}")
    st.markdown(f"Documentação interativa (Swagger): [{utils.API_URL}/docs]({utils.API_URL}/docs)")
else:
    st.warning(
        f"A API não respondeu em `{utils.API_URL}`. Inicie-a em outro terminal:\n\n"
        "```bash\nuvicorn main:app --reload --app-dir Code/API --port 8000\n```\n"
        "Enquanto isso, as demais páginas usam os arquivos locais."
    )

st.subheader("Endpoints")
st.markdown(
    """
    | Método | Rota | Função |
    |---|---|---|
    | GET | `/saude` | Verifica se a API está no ar |
    | GET | `/projetos` | Lista projetos (filtros `causa`, `uf`, `ods`, `busca`; paginação `limite`/`offset`) |
    | GET | `/projetos/{id}` | Busca um projeto pelo id (404 se não existir) |
    | **POST** | `/projetos` | Cadastra um projeto (valida UF/link; 409 se duplicado) |
    | GET | `/noticias` | Lista notícias (filtros `ods`, `busca`) |
    | GET | `/estatisticas` | Contagens por causa, UF e ODS |
    | GET | `/llm/documentos` | Documentos texto + metadados prontos para LLMs |
    | GET | `/llm/status` | Modelos locais configurados e se já foram carregados |
    | **POST** | `/processar_texto` | Resumo ou sentimento de um texto com LLM local (use a página 🧠) |
    """
)

st.subheader("Testar um endpoint (GET)")
c1, c2 = st.columns([1, 2])
rota = c1.selectbox(
    "Rota",
    ["/saude", "/projetos", "/noticias", "/estatisticas", "/llm/documentos", "/llm/status"],
)
params: dict = {}
if rota == "/projetos":
    p1, p2, p3 = c2.columns(3)
    params = {"uf": p1.text_input("uf", max_chars=2), "ods": p2.text_input("ods"), "busca": p3.text_input("busca")}
elif rota == "/noticias":
    p1, p2 = c2.columns(2)
    params = {"ods": p1.text_input("ods"), "busca": p2.text_input("busca")}
elif rota == "/llm/documentos":
    params = {"tipo": c2.selectbox("tipo", ["", "projeto", "noticia"])}
params = {k: v for k, v in params.items() if v}

if st.button("Enviar requisição", type="primary"):
    try:
        resp = utils.chamar_api("GET", rota, params=params)
        st.caption(f"`GET {resp.url}` → **{resp.status_code}** em {resp.elapsed.total_seconds() * 1000:.0f} ms")
        st.json(resp.json())
    except requests.RequestException as exc:
        st.error(f"Não foi possível chamar a API: {exc}")

st.subheader("Exemplos de uso fora do app")
exemplo_post = json.dumps(
    {
        "nome_projeto": "Cozinha Solidária do Bairro",
        "organizacao": "Associação Mesa Cheia",
        "causa": "Segurança alimentar",
        "ods_relacionado": "ODS 2 - Fome Zero",
        "cidade": "Recife",
        "uf": "PE",
    },
    ensure_ascii=False,
)
st.code(
    "# consultar projetos de SP ligados ao ODS 4\n"
    f'curl "{utils.API_URL}/projetos?uf=SP&ods=4"\n\n'
    "# cadastrar um projeto\n"
    f"curl -X POST \"{utils.API_URL}/projetos\" -H \"Content-Type: application/json\" -d '{exemplo_post}'",
    language="bash",
)
