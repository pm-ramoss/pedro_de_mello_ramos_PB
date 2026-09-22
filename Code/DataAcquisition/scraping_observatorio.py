"""
Web Scraping de projetos sociais do Observatório do Terceiro Setor.

Extrai a lista de projetos sociais por causa a partir da página pública:
https://observatorio3setor.org.br/carrossel/lista-conheca-projetos-sociais-de-15-causas-diferentes/

Uso:
    python scraping_observatorio.py --saida ../../Data/Raw/projetos_observatorio.csv

Observação:
    - Este script depende de acesso à internet.
    - A estrutura HTML de sites de terceiros pode mudar; os seletores usados
      aqui (`SELECTORS`) devem ser revisados periodicamente.
    - Respeite o robots.txt e os termos de uso do site-fonte. Este scraper é
      de baixa frequência e uso acadêmico/não comercial.
"""

import argparse
import csv
import sys
import time
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

# Seletores CSS usados para localizar os elementos de artigo/projeto na página.
# Ajustar conforme a estrutura real do site no momento da execução.
SELECTORS = {
    "artigo": "article",
    "titulo": "h2, h3",
    "resumo": "p",
    "link": "a",
}


def buscar_pagina(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extrair_projetos(soup: BeautifulSoup) -> list[dict]:
    projetos = []
    artigos = soup.select(SELECTORS["artigo"])

    for artigo in artigos:
        titulo_tag = artigo.select_one(SELECTORS["titulo"])
        resumo_tag = artigo.select_one(SELECTORS["resumo"])
        link_tag = artigo.select_one(SELECTORS["link"])

        titulo = titulo_tag.get_text(strip=True) if titulo_tag else None
        if not titulo:
            continue  # ignora blocos sem título (prováveis elementos de layout)

        projetos.append(
            {
                "nome_projeto": titulo,
                "descricao": resumo_tag.get_text(strip=True) if resumo_tag else "",
                "link": link_tag["href"] if link_tag and link_tag.has_attr("href") else "",
                "fonte": "Observatório do Terceiro Setor",
            }
        )

    return projetos


def salvar_csv(projetos: list[dict], saida: Path) -> None:
    saida.parent.mkdir(parents=True, exist_ok=True)
    campos = ["nome_projeto", "descricao", "link", "fonte"]
    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(projetos)
    print(f"{len(projetos)} projetos salvos em: {saida}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraping de projetos sociais do Observatório do Terceiro Setor."
    )
    parser.add_argument(
        "--saida",
        default="../../Data/Raw/projetos_observatorio.csv",
        help="Caminho do arquivo CSV de saída",
    )
    args = parser.parse_args()

    soup = buscar_pagina(URL)
    time.sleep(1)  # boa prática: espaçar requisições
    projetos = extrair_projetos(soup)
    salvar_csv(projetos, Path(args.saida))


if __name__ == "__main__":
    sys.exit(main())
