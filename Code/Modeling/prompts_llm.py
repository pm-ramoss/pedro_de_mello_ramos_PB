"""
Modelos de prompt para as tarefas de LLM planejadas para o TP4.

Nenhuma chamada a LLM é feita aqui: este módulo apenas define, para cada caso
de uso, (i) quais dados do projeto alimentam a tarefa e (ii) o prompt-base.
Isso deixa a integração da próxima etapa restrita a "enviar o prompt ao modelo".

Uso:
    from prompts_llm import montar_prompt
    prompt = montar_prompt("sentimento", texto="...")
"""

from __future__ import annotations

CASOS_DE_USO: dict[str, dict] = {
    "resumo": {
        "titulo": "Resumo automático de textos longos",
        "dados": "Corpus de notícias (`Data/Raw/noticias_txt/` e coluna `resumo`)",
        "entrada": ["texto"],
        "saida": "Resumo de até 3 frases, com os números e nomes citados no texto.",
        "prompt": (
            "Você é um analista de ESG. Resuma o texto abaixo em até 3 frases em português, "
            "preservando números, nomes de organizações e a relação com a Agenda 2030. "
            "Não acrescente informações que não estejam no texto.\n\nTEXTO:\n{texto}\n\nRESUMO:"
        ),
    },
    "sentimento": {
        "titulo": "Classificação de sentimento das notícias",
        "dados": "Notícias processadas (`titulo` + `resumo`)",
        "entrada": ["texto"],
        "saida": "Um rótulo: positivo, negativo ou neutro (+ justificativa de uma frase).",
        "prompt": (
            "Classifique o sentimento da notícia abaixo em relação ao tema ESG/Agenda 2030 como "
            "'positivo', 'negativo' ou 'neutro'. Responda em JSON com as chaves "
            "'sentimento' e 'justificativa' (uma frase).\n\nNOTÍCIA:\n{texto}"
        ),
    },
    "qa": {
        "titulo": "Perguntas e respostas sobre os projetos",
        "dados": "Documentos de `GET /llm/documentos` (projetos + notícias)",
        "entrada": ["contexto", "pergunta"],
        "saida": "Resposta fundamentada apenas nos documentos fornecidos como contexto.",
        "prompt": (
            "Responda à pergunta usando SOMENTE os documentos de contexto. Se a resposta não "
            "estiver neles, diga que não encontrou. Cite o id do documento usado.\n\n"
            "CONTEXTO:\n{contexto}\n\nPERGUNTA: {pergunta}\n\nRESPOSTA:"
        ),
    },
    "geracao": {
        "titulo": "Geração de texto / relatório de insights",
        "dados": "Estatísticas agregadas (`GET /estatisticas`)",
        "entrada": ["estatisticas"],
        "saida": "Parágrafo descritivo para doadores e empresas, com 3 insights.",
        "prompt": (
            "Com base nas estatísticas abaixo (JSON), escreva um parágrafo de até 120 palavras para "
            "um potencial doador, destacando 3 insights sobre causas, regiões e ODS mais atendidos. "
            "Use apenas os números fornecidos.\n\nESTATÍSTICAS:\n{estatisticas}"
        ),
    },
    "classificacao_ods": {
        "titulo": "Classificação de projetos por ODS (previsto no Project Charter)",
        "dados": "Projetos (`nome_projeto`, `causa`, `descricao`)",
        "entrada": ["texto"],
        "saida": "Lista de ODS (1–17) mais aderentes ao projeto, em JSON.",
        "prompt": (
            "Indique quais Objetivos de Desenvolvimento Sustentável (1 a 17) melhor se aplicam ao "
            "projeto abaixo. Responda em JSON: {{\"ods\": [numeros], \"justificativa\": \"...\"}}.\n\n"
            "PROJETO:\n{texto}"
        ),
    },
}


def montar_prompt(caso: str, **campos: str) -> str:
    """Preenche o prompt-base do caso de uso com os campos informados."""
    if caso not in CASOS_DE_USO:
        raise KeyError(f"Caso de uso desconhecido: {caso!r}. Opções: {', '.join(CASOS_DE_USO)}")
    modelo = CASOS_DE_USO[caso]
    faltando = [c for c in modelo["entrada"] if c not in campos]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes para '{caso}': {', '.join(faltando)}")
    return modelo["prompt"].format(**campos)
