"""Página 1 — Visão Geral."""

import streamlit as st

import app_utils as utils

st.title("🌱 Conecta Impacto")
st.subheader(
    "Plataforma de inteligência de dados para conectar projetos sociais "
    "a doadores, voluntários e empresas com agenda ESG"
)

stats, origem = utils.obter_estatisticas()
st.caption(utils.rotulo_origem(origem))

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Projetos na base", stats["total_projetos"])
m2.metric("Cadastrados via API/upload", stats["total_projetos_enviados"])
m3.metric("Causas", stats["n_causas"])
m4.metric("UFs", stats["n_ufs"])
m5.metric("Notícias coletadas", stats["total_noticias"])

col1, col2 = st.columns([2, 1])

with col1:
    st.header("O problema de negócio")
    st.write(
        """
        Organizações da sociedade civil (OSCs), sobretudo de pequeno e médio porte,
        têm dificuldade em ganhar visibilidade e demonstrar, com dados, o impacto de
        seus projetos sociais. Empresas com compromissos **ESG** e pessoas físicas
        dispostas a doar ou atuar como voluntárias não têm um canal simples para
        **descobrir, comparar e priorizar** projetos sociais confiáveis, alinhados às
        causas e aos Objetivos de Desenvolvimento Sustentável (ODS) que desejam apoiar.
        """
    )

    st.header("Como o projeto evoluiu")
    st.markdown(
        """
        | Etapa | Entrega |
        |---|---|
        | **TP1** | Proposta, Project Charter, Data Summary Report (esboço) e demo estática |
        | **TP2** | Interface em abas, scraping com BeautifulSoup, cache, sessão e upload/download |
        | **TP3** | **Aplicação multipágina**, **API FastAPI** (GET/POST), scraping dinâmico (Selenium) e **preparação dos dados para LLMs** |
        """
    )

    st.header("Arquitetura (TP3)")
    st.code(
        "Fontes web (BeautifulSoup / Selenium / API IBGE)\n"
        "        │\n"
        "        ▼\n"
        "  Data/Raw ──► preparar_dados.py ──► Data/Processed (CSV)\n"
        "                                          │\n"
        "                          ┌───────────────┴───────────────┐\n"
        "                          ▼                               ▼\n"
        "                 API FastAPI (Code/API)        corpus_llm.jsonl (TP4)\n"
        "                          │\n"
        "                          ▼\n"
        "              App Streamlit multipágina\n"
        "        (usa os arquivos locais se a API estiver fora do ar)",
        language="text",
    )

with col2:
    st.success("**ODS 17** — Parcerias e Meios de Implementação (principal)")
    st.info("**ODS 10** — Redução das Desigualdades (secundário)")
    st.header("Público-alvo")
    st.markdown(
        "- Empresas com agenda ESG\n"
        "- Doadores e voluntários (pessoa física)\n"
        "- OSCs/ONGs de pequeno e médio porte"
    )
    st.header("Navegue pelo menu")
    st.markdown(
        "- 🗂️ **Projetos** — filtros, busca e favoritos\n"
        "- 📊 **Estatísticas** — gráficos e progresso das metas\n"
        "- 📰 **Notícias** — corpus e nuvem de palavras\n"
        "- 📤 **Meus Dados** — upload, cadastro e download\n"
        "- 🔌 **Console da API** — teste os endpoints\n"
        "- 🤖 **Preparação para LLMs** — casos de uso da próxima etapa"
    )
