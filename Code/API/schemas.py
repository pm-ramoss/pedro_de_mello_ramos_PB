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
