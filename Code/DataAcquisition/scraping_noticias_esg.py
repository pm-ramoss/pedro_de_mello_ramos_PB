"""
Web Scraping (BeautifulSoup) de notícias sobre ESG / Agenda 2030 / ODS — TP2.

Extrai título, data, resumo (primeiros parágrafos) e URL de uma lista
configurável de páginas de notícias (`FONTES`), e salva:
  1. um CSV consolidado com os metadados (`--saida-csv`);
  2. um arquivo .txt por notícia com o texto (título + resumo) em
     `--saida-txt-dir`, usado depois para gerar a nuvem de palavras e as
     estatísticas básicas exibidas na aplicação Streamlit.

Uso:
    python scraping_noticias_esg.py \
        --saida-csv ../../Data/Raw/noticias_esg_ods.csv \
        --saida-txt-dir ../../Data/Raw/noticias_txt

Observação:
    - Depende de acesso à internet; ajuste a lista `FONTES` com as URLs de
      notícias que deseja acompanhar (ex.: buscas no Google News, portais de
      ESG, o próprio Observatório do Terceiro Setor etc.).
    - Este script é deliberadamente simples (extrai <title>, <h1> e os
      primeiros <p> do corpo) para funcionar num leque amplo de portais sem
      precisar de um parser dedicado por site. Ajuste `SELECTORS` para um
      site específico se quiser mais precisão.
    - Respeite o robots.txt e os termos de uso de cada site-fonte. Uso
      acadêmico/não comercial, baixa frequência de requisições.
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ConectaImpactoBot/1.0; "
        "+projeto academico ESG/Agenda2030)"
    )
}

# Lista de páginas de notícias a coletar. Preencha com as URLs de interesse
# antes de rodar o script (uma consulta prévia no Google/Bing por termos como
# "ESG Agenda 2030 Brasil" ajuda a montar essa lista).
FONTES: list[dict] = [
    {
        "url": "https://atlaspublico.com.br/noticias/governo-convoca-1-conferencia-nacional-dos-ods-para-debater-22787",
        "fonte": "Atlas Público",
        "ods_relacionado": "ODS 17 - Parcerias",
    },
    {
        "url": "https://www.portaltela.com/noticias/economia/2026/06/01/onu-reune-empresas-para-impulsionar-decada-decisiva-da-agenda-esg/",
        "fonte": "Portal Tela",
        "ods_relacionado": "ODS 17 - Parcerias",
    },
    {
        "url": "https://radardigitalbrasilia.com.br/noticias-corporativas-dino/288613-praticas-esg-estimulam-empresas-a-aderirem-a-agenda-2030/",
        "fonte": "Radar Digital Brasília",
        "ods_relacionado": "ODS 8 - Trabalho Decente",
    },
    {
        "url": "https://www.folhape.com.br/noticia/amp/279852/objetivos-de-desenvolvimento-sustentavel-da-agenda-2030-estao-em/",
        "fonte": "Folha de Pernambuco",
        "ods_relacionado": "ODS 17 - Parcerias",
    },
    {
        "url": "https://www.sicredi.com.br/coop/aliancarssces/noticias/cooperativismo/sicredi-alianca-destina-cerca-de-r-2-milhoes-para-projetos-contemplados-no-fundo-social-2026/",
        "fonte": "Sicredi Aliança",
        "ods_relacionado": "ODS 1 - Erradicação da Pobreza",
    },
]

N_PARAGRAFOS_RESUMO = 3


def limpar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def extrair_noticia(url: str) -> dict | None:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    titulo_tag = soup.find("h1") or soup.find("title")
    titulo = limpar_texto(titulo_tag.get_text()) if titulo_tag else "(sem título)"

    paragrafos = [limpar_texto(p.get_text()) for p in soup.find_all("p")]
    paragrafos = [p for p in paragrafos if len(p) > 40]  # ignora legendas/menus
    resumo = " ".join(paragrafos[:N_PARAGRAFOS_RESUMO])

    return {"titulo": titulo, "resumo": resumo, "url": url}


def salvar_csv(noticias: list[dict], saida: Path) -> None:
    saida.parent.mkdir(parents=True, exist_ok=True)
    campos = ["titulo", "fonte", "url", "resumo", "ods_relacionado"]
    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(noticias)
    print(f"{len(noticias)} notícias salvas em: {saida}")


def salvar_txt(noticias: list[dict], saida_dir: Path) -> None:
    saida_dir.mkdir(parents=True, exist_ok=True)
    for i, n in enumerate(noticias, start=1):
        caminho = saida_dir / f"noticia_{i:02d}.txt"
        caminho.write_text(f"{n['titulo']}\n\n{n['resumo']}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraping de notícias ESG/ODS.")
    parser.add_argument(
        "--saida-csv", default="../../Data/Raw/noticias_esg_ods.csv"
    )
    parser.add_argument(
        "--saida-txt-dir", default="../../Data/Raw/noticias_txt"
    )
    args = parser.parse_args()

    if not FONTES:
        print(
            "Aviso: a lista FONTES está vazia. Edite este script e adicione as "
            "URLs de notícias que deseja coletar antes de rodar em produção. "
            "O CSV e os .txt já entregues em Data/Raw/ foram gerados numa "
            "coleta anterior e podem ser usados como estão para a demo."
        )
        return

    noticias = []
    for fonte in FONTES:
        try:
            dados = extrair_noticia(fonte["url"])
            if dados:
                dados["fonte"] = fonte.get("fonte", "")
                dados["ods_relacionado"] = fonte.get("ods_relacionado", "")
                noticias.append(dados)
        except requests.RequestException as exc:
            print(f"Aviso: falha ao coletar {fonte['url']} ({exc})")
        time.sleep(1)  # boa prática: espaçar requisições

    salvar_csv(noticias, Path(args.saida_csv))
    salvar_txt(noticias, Path(args.saida_txt_dir))


if __name__ == "__main__":
    sys.exit(main())
