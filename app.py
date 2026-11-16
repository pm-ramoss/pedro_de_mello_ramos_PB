"""
Conecta Impacto — Aplicação Streamlit multipágina (TP3).

Este arquivo é apenas o ponto de entrada: configura a página, monta o menu de
navegação (`st.navigation`) e executa a página escolhida. O conteúdo de cada
seção fica em `app_pages/`.

Executar:  streamlit run app.py
(Opcional) API:  uvicorn main:app --reload --app-dir Code/API --port 8000
"""

import streamlit as st

import app_utils as utils

st.set_page_config(
    page_title="Conecta Impacto | ESG & Agenda 2030",
    page_icon="🌱",
    layout="wide",
)

utils.iniciar_estado()

navegacao = st.navigation(
    {
        "Conecta Impacto": [
            st.Page("app_pages/visao_geral.py", title="Visão Geral", icon="📌", default=True),
            st.Page("app_pages/projetos.py", title="Projetos Sociais", icon="🗂️"),
            st.Page("app_pages/estatisticas.py", title="Estatísticas e Gráficos", icon="📊"),
            st.Page("app_pages/noticias.py", title="Notícias e Nuvem de Palavras", icon="📰"),
            st.Page("app_pages/analise_texto.py", title="Análise de Texto (LLM local)", icon="🧠"),
        ],
        "Dados e integração": [
            st.Page("app_pages/meus_dados.py", title="Meus Dados (Upload/Download)", icon="📤"),
            st.Page("app_pages/api_console.py", title="Console da API", icon="🔌"),
            st.Page("app_pages/preparacao_llm.py", title="Preparação para LLMs", icon="🤖"),
        ],
    }
)

with st.sidebar:
    st.divider()
    status = utils.status_api()
    if status:
        st.success(f"API online · v{status.get('versao', '?')}")
    else:
        st.warning("API offline — usando arquivos locais")
    st.caption(f"Endpoint: `{utils.API_URL}`")

navegacao.run()

st.divider()
st.caption(
    "Conecta Impacto · TP4 · Python, Streamlit, FastAPI, Web Scraping e LLM local "
    "(HuggingFace), alinhado à Agenda 2030 da ONU."
)
