"""Testes do serviço de LLM com pipelines simulados (não baixam modelos)."""

import time

import pytest

import llm_service as ls
from llm_service import (
    EntradaInvalidaError, InferenciaError, ModeloIndisponivelError, ServicoLLM, TempoLimiteError,
)

TEXTO_LONGO = ("O programa de educação comunitária ampliou o acesso de jovens à robótica e à programação. " * 4).strip()


def fabrica_ok(tarefa, modelo):
    if tarefa == "resumo":
        return lambda texto, **kw: [{"summary_text": "Programa amplia acesso de jovens à robótica."}]
    return lambda texto, **kw: [[
        {"label": "positive", "score": 0.81}, {"label": "neutral", "score": 0.15}, {"label": "negative", "score": 0.04},
    ]]


@pytest.fixture
def servico():
    return ServicoLLM(fabrica_pipeline=fabrica_ok, timeout_s=2)


def test_resumo_ok(servico):
    r = servico.processar("resumo", TEXTO_LONGO)
    assert r["resumo"].startswith("Programa amplia")
    assert r["modelo"] == ls.MODELO_RESUMO_PADRAO
    assert r["tempo_ms"] >= 0


def test_sentimento_ok_e_traducao_de_rotulos(servico):
    r = servico.processar("sentimento", "Adorei o projeto, muito bom!")
    assert r["rotulo"] == "positivo"
    assert r["confianca"] == 0.81
    assert set(r["pontuacoes"]) == {"positivo", "neutro", "negativo"}


def test_sentimento_aceita_saida_sem_lista_aninhada():
    s = ServicoLLM(lambda t, m: (lambda x, **k: [{"label": "LABEL_0", "score": 0.7}, {"label": "LABEL_2", "score": 0.3}]))
    assert s.processar("sentimento", "ruim")["rotulo"] == "negativo"


def test_modelo_e_carregado_uma_unica_vez():
    chamadas = []

    def fabrica(t, m):
        chamadas.append(t)
        return fabrica_ok(t, m)

    s = ServicoLLM(fabrica, timeout_s=2)
    s.processar("sentimento", "ok bom")
    s.processar("sentimento", "ok bom de novo")
    assert chamadas == ["sentimento"]
    assert s.status()["sentimento"]["carregado"] is True
    assert s.status()["resumo"]["carregado"] is False


@pytest.mark.parametrize("tarefa,texto", [
    ("sentimento", ""), ("sentimento", "   "), ("resumo", "curto demais"),
    ("sentimento", "x" * (ls.MAX_CARACTERES + 1)), ("traduzir", "texto qualquer"),
])
def test_entradas_invalidas_retornam_422(servico, tarefa, texto):
    with pytest.raises(EntradaInvalidaError) as e:
        servico.processar(tarefa, texto)
    assert e.value.codigo_http == 422


def test_falha_ao_carregar_modelo_retorna_503_e_registra_erro():
    def fabrica(t, m):
        raise ModeloIndisponivelError("sem internet para baixar o modelo")

    s = ServicoLLM(fabrica, timeout_s=2)
    with pytest.raises(ModeloIndisponivelError) as e:
        s.processar("sentimento", "texto ok")
    assert e.value.codigo_http == 503
    assert "sem internet" in s.status()["sentimento"]["ultimo_erro"]


def test_excecao_generica_na_carga_vira_503():
    def fabrica(t, m):
        raise OSError("disco cheio")

    with pytest.raises(ModeloIndisponivelError):
        ServicoLLM(fabrica).processar("sentimento", "texto ok")


def test_timeout_retorna_504():
    def fabrica(t, m):
        return lambda x, **k: (time.sleep(0.4), [[{"label": "positive", "score": 1.0}]])[1]

    s = ServicoLLM(fabrica, timeout_s=0.05)
    with pytest.raises(TempoLimiteError) as e:
        s.processar("sentimento", "texto ok")
    assert e.value.codigo_http == 504


def test_erro_na_inferencia_retorna_500():
    def fabrica(t, m):
        def pipe(x, **k):
            raise RuntimeError("out of memory")
        return pipe

    with pytest.raises(InferenciaError) as e:
        ServicoLLM(fabrica, timeout_s=2).processar("sentimento", "texto ok")
    assert e.value.codigo_http == 500 and "out of memory" in str(e.value)


def test_resumo_vazio_retorna_500():
    s = ServicoLLM(lambda t, m: (lambda x, **k: [{"summary_text": "  "}]), timeout_s=2)
    with pytest.raises(InferenciaError):
        s.processar("resumo", TEXTO_LONGO)


def test_modelo_configuravel_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("CONECTA_MODELO_SENTIMENTO", "meu/modelo-local")
    assert ServicoLLM.nome_modelo("sentimento") == "meu/modelo-local"


def test_sem_transformers_instalado_retorna_503():
    try:
        import transformers  # noqa: F401
        pytest.skip("transformers instalado")
    except ImportError:
        pass
    with pytest.raises(ModeloIndisponivelError):
        ls.criar_pipeline_hf("sentimento", "qualquer/modelo")
