"""Testes HTTP da rota /processar_texto (requer fastapi e httpx instalados)."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from llm_service import ServicoLLM  # noqa: E402

TEXTO = ("A cozinha solidária distribui refeições para famílias em vulnerabilidade todos os dias. " * 4).strip()


def _fabrica(tarefa, modelo):
    if tarefa == "resumo":
        return lambda t, **k: [{"summary_text": "Cozinha distribui refeições a famílias."}]
    return lambda t, **k: [[{"label": "positive", "score": 0.9}, {"label": "neutral", "score": 0.07}, {"label": "negative", "score": 0.03}]]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "servico_llm", ServicoLLM(_fabrica, timeout_s=2))
    return TestClient(main.app)


def test_sentimento(client):
    r = client.post("/processar_texto", json={"tarefa": "sentimento", "texto": "Projeto excelente!"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["resultado"]["tarefa"] == "sentimento" and corpo["resultado"]["rotulo"] == "positivo"
    assert corpo["texto_entrada"] == "Projeto excelente!"


def test_resumo(client):
    r = client.post("/processar_texto", json={"tarefa": "resumo", "texto": TEXTO, "max_palavras_resumo": 30})
    assert r.status_code == 200
    assert r.json()["resultado"]["resumo"].startswith("Cozinha")


def test_texto_curto_para_resumo_422_padronizado(client):
    r = client.post("/processar_texto", json={"tarefa": "resumo", "texto": "curto"})
    assert r.status_code == 422 and r.json()["codigo"] == "entrada_invalida"


def test_corpo_invalido_422_do_fastapi(client):
    assert client.post("/processar_texto", json={"tarefa": "traduzir", "texto": "x"}).status_code == 422
    assert client.post("/processar_texto", json={"tarefa": "resumo", "texto": "   "}).status_code == 422


def test_modelo_indisponivel_503(monkeypatch):
    from llm_service import ModeloIndisponivelError

    def falha(t, m):
        raise ModeloIndisponivelError("modelo não baixado")

    monkeypatch.setattr(main, "servico_llm", ServicoLLM(falha))
    r = TestClient(main.app).post("/processar_texto", json={"tarefa": "sentimento", "texto": "ok"})
    assert r.status_code == 503
    assert set(r.json()) == {"codigo", "mensagem", "dica"} and r.json()["codigo"] == "modelo_indisponivel"


def test_status_llm(client):
    assert client.get("/llm/status").json()["sentimento"]["carregado"] is False
