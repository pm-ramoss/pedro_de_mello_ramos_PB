"""
Web Scraping (BeautifulSoup) da lista de causas sociais do Observatório do
Terceiro Setor — TP2.

Extrai a lista numerada de causas sociais (ex.: "Educação de crianças e
jovens", "Empoderamento feminino" etc.) usada para padronizar a taxonomia de
causas do dataset consolidado do projeto.

Uso:
    python scraping_causas_sociais.py \
        --saida ../../Data/Raw/causas_observatorio.csv

Observação:
    - Depende de acesso à internet; a estrutura HTML do site-fonte pode
      mudar sem aviso prévio (revisar `SELECTORS` periodicamente).
    - Caso a página não possa ser acessada (rede indisponível, mudança de
      estrutura, bloqueio temporário), o script cai em uma lista de
      contingência (`CAUSAS_FALLBACK`) coletada manualmente na última
      execução bem-sucedida, garantindo que o pipeline de dados não quebre.
    - Respeite o robots.txt e os termos de uso do site-fonte. Uso
      acadêmico/não comercial, baixa frequência de requisições.
"""

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = (
    "https://observatorio3setor.org.br/carrossel/"
    "lista-conheca-projetos-sociais-de-15-causas-diferentes/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ConectaImpactoBot/1.0; "
        "+projeto academico ESG/Agenda2030)"
    )
}

# Seletor do bloco de conteúdo onde a lista numerada de causas aparece.
SELECTOR_CONTEUDO = "article, .entry-content, .post-content"

# Lista de contingência: última extração bem-sucedida (usada como fallback
# caso a página esteja fora do ar ou a estrutura HTML tenha mudado).
CAUSAS_FALLBACK = [
    "Combate ao abuso infantil e apoio às vítimas",
    "Educação de crianças e jovens",
    "Crianças desaparecidas",
    "Apoio a mulheres vítimas de violência",
    "Empoderamento feminino",
    "Combate à desigualdade racial",
    "Apoio a pessoas em situação de rua",
]


def buscar_pagina(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extrair_causas(soup: BeautifulSoup) -> list[str]:
    """Extrai itens de lista numerada (1 – Causa, 2 – Causa, ...) do artigo."""
    bloco = soup.select_one(SELECTOR_CONTEUDO)
    if bloco is None:
        return []

    causas = []
    for li in bloco.find_all(["li", "p"]):
        texto = li.get_text(strip=True)
        # Filtra linhas no padrão "<número> – <causa>" ou "<número>. <causa>"
        if texto and texto[0].isdigit() and ("–" in texto or "-" in texto or "." in texto):
            causa = texto.split("–", 1)[-1].split("-", 1)[-1].split(".", 1)[-1].strip()
            if causa:
                causas.append(causa)
    return causas


def salvar_csv(causas: list[str], saida: Path, fonte_url: str) -> None:
    saida.parent.mkdir(parents=True, exist_ok=True)
    hoje = dt.date.today().isoformat()
    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ordem", "causa", "fonte", "url_fonte", "data_coleta"])
        for i, causa in enumerate(causas, start=1):
            writer.writerow(
                [i, causa, "Observatório do Terceiro Setor", fonte_url, hoje]
            )
    print(f"{len(causas)} causas salvas em: {saida}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraping da lista de causas sociais do Observatório do Terceiro Setor."
    )
    parser.add_argument(
        "--saida",
        default="../../Data/Raw/causas_observatorio.csv",
        help="Caminho do arquivo CSV de saída",
    )
    args = parser.parse_args()

    try:
        soup = buscar_pagina(URL)
        causas = extrair_causas(soup)
        if not causas:
            print("Aviso: nenhuma causa extraída da página; usando lista de contingência.")
            causas = CAUSAS_FALLBACK
    except requests.RequestException as exc:
        print(f"Aviso: falha ao acessar {URL} ({exc}); usando lista de contingência.")
        causas = CAUSAS_FALLBACK

    salvar_csv(causas, Path(args.saida), URL)


if __name__ == "__main__":
    sys.exit(main())
