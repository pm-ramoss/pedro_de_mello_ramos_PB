"""Modelos Pydantic (entrada/saída) da API do Conecta Impacto — TP3."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


class ProjetoIn(BaseModel):
    """Corpo do POST /projetos."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "nome_projeto": "Cozinha Solidária do Bairro",
                "organizacao": "Associação Mesa Cheia",
                "causa": "Segurança alimentar",
                "ods_relacionado": "ODS 2 - Fome Zero; ODS 17 - Parcerias",
                "cidade": "Recife",
                "uf": "PE",
                "descricao": "Refeições gratuitas para famílias em vulnerabilidade.",
                "fonte": "Cadastro via API",
                "link": "https://exemplo.org/cozinha-solidaria",
            }
        },
    )

    nome_projeto: str = Field(min_length=3, max_length=200)
    organizacao: str = Field(min_length=2, max_length=200)
    causa: str = Field(min_length=2, max_length=100)
    ods_relacionado: str = Field(default="", max_length=200)
    cidade: str = Field(default="", max_length=100)
    uf: str = Field(min_length=2, max_length=2, description="Sigla da UF, ex.: RJ")
    descricao: str = Field(default="", max_length=1000)
    fonte: str = Field(default="Cadastro via API", max_length=100)
    link: str = Field(default="", max_length=500)

    @field_validator("uf")
    @classmethod
    def uf_valida(cls, valor: str) -> str:
        valor = valor.upper()
        if valor not in UFS_VALIDAS:
            raise ValueError(f"UF inválida: {valor!r}")
        return valor

    @field_validator("link")
    @classmethod
    def link_http(cls, valor: str) -> str:
        if valor and not valor.lower().startswith(("http://", "https://")):
            raise ValueError("O link deve começar com http:// ou https://")
        return valor


class ProjetoOut(ProjetoIn):
    id: str


class ListaProjetos(BaseModel):
    total: int = Field(description="Total de registros após os filtros (antes da paginação)")
    limite: int
    offset: int
    itens: list[ProjetoOut]


class Noticia(BaseModel):
    id: str
    titulo: str
    fonte: str
    url: str
    data_publicacao: str
    resumo: str
    ods_relacionado: str


class Estatisticas(BaseModel):
    total_projetos: int
    total_projetos_enviados: int
    total_noticias: int
    n_causas: int
    n_ufs: int
    n_ods: int
    projetos_por_causa: dict[str, int]
    projetos_por_uf: dict[str, int]
    projetos_por_ods: dict[str, int]
    noticias_por_ods: dict[str, int]


class DocumentoLLM(BaseModel):
    id: str
    tipo: str
    titulo: str
    texto: str
    metadados: dict[str, str]
    tokens_estimados: int


# --------------------------------------------------------------------------
# TP4 — processamento de texto com LLM local
# --------------------------------------------------------------------------
from typing import Annotated, Literal, Union  # noqa: E402


class ProcessarTextoIn(BaseModel):
    """Corpo do POST /processar_texto."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "tarefa": "sentimento",
                "texto": "O projeto ampliou o acesso à educação e foi muito elogiado pela comunidade.",
            }
        },
    )

    tarefa: Literal["resumo", "sentimento"] = Field(description="Tipo de análise a executar")
    texto: str = Field(min_length=1, max_length=20_000, description="Texto em português")
    max_palavras_resumo: int = Field(
        default=60, ge=15, le=200, description="Tamanho máximo aproximado do resumo (só para tarefa=resumo)"
    )


class ResultadoResumo(BaseModel):
    tarefa: Literal["resumo"] = "resumo"
    resumo: str
    n_palavras_resumo: int
    taxa_compressao: float = Field(description="palavras do resumo ÷ palavras do texto (0–1)")


class ResultadoSentimento(BaseModel):
    tarefa: Literal["sentimento"] = "sentimento"
    rotulo: Literal["positivo", "neutro", "negativo"]
    confianca: float = Field(ge=0, le=1)
    pontuacoes: dict[str, float] = Field(description="Probabilidade de cada rótulo")


class ProcessarTextoOut(BaseModel):
    tarefa: Literal["resumo", "sentimento"]
    modelo: str = Field(description="Id do modelo HuggingFace usado")
    texto_entrada: str
    n_caracteres_entrada: int
    tempo_ms: int
    resultado: Annotated[Union[ResultadoResumo, ResultadoSentimento], Field(discriminator="tarefa")]


class ErroResposta(BaseModel):
    """Formato padrão dos erros do serviço de LLM."""

    codigo: str = Field(description="Identificador estável do erro, ex.: modelo_indisponivel")
    mensagem: str = Field(description="Explicação legível do que aconteceu")
    dica: str = Field(description="O que o usuário/desenvolvedor pode fazer")


class StatusModelo(BaseModel):
    modelo: str
    carregado: bool
    ultimo_erro: str | None = None


class StatusLLM(BaseModel):
    resumo: StatusModelo
    sentimento: StatusModelo
