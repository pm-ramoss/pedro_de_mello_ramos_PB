# Escolha e integração do modelo LLM local — Conecta Impacto (TP4)

## 1. Tarefas escolhidas e por quê

Entre as opções do enunciado (geração, resumo, classificação de sentimento), foram
escolhidas **duas tarefas de PLN**, porque cada uma atende a uma necessidade real do
projeto e são as que modelos *pequenos* executam bem em CPU:

| Tarefa | Uso no Conecta Impacto |
|---|---|
| **Resumo** | Resumir notícias longas sobre ESG/Agenda 2030 para o doador ler rapidamente |
| **Classificação de sentimento** | Medir o tom da cobertura de ESG/ODS nas notícias coletadas |

Geração livre de texto e Q&A exigiriam modelos bem maiores (GPUs ou muita RAM) para
qualidade aceitável em português, o que contraria a restrição de rodar localmente em
uma máquina de desenvolvimento comum.

## 2. Critérios de seleção

1. **Desempenho:** modelo treinado para a tarefa **e para o português** (ou multilíngue).
2. **Custo computacional local:** rodar em **CPU**, com poucos GB de RAM.
3. **Acessibilidade local:** disponível no HuggingFace Hub, carregável com `transformers`
   e utilizável offline após o download.

> Tamanhos e detalhes abaixo são **aproximados e vêm do que consta nos *model cards***;
> confirme-os no Hub antes de citá-los na apresentação. Nenhum modelo foi avaliado em
> benchmark próprio — a avaliação prática está descrita na seção 6.

## 3. Sentimento — candidatos e decisão

| Modelo | Tipo / dados | Tamanho aprox. | Observações |
|---|---|---|---|
| **`lxyuan/distilbert-base-multilingual-cased-sentiments-student`** ✅ | DistilBERT multilíngue destilado; rótulos positivo/neutro/negativo | ~135 M parâmetros (~0,5 GB) | Inclui o **português**; leve; saída com 3 classes, igual à pedida no enunciado |
| `cardiffnlp/twitter-xlm-roberta-base-sentiment` | XLM-RoBERTa treinado em **tweets** | ~280 M parâmetros (~1,1 GB) | Maior e especializado em linguagem de redes sociais, que difere de notícias |
| `nlptown/bert-base-multilingual-uncased-sentiment` | BERT multilíngue, 1–5 estrelas (**avaliações de produtos**) | ~170 M parâmetros | Escala de estrelas e domínio de reviews; não tem classe "neutro" explícita |

**Decisão:** `lxyuan/distilbert-base-multilingual-cased-sentiments-student`. É o menor
dos três, cobre português, devolve exatamente 3 rótulos e roda bem em CPU.
*Limitação:* não foi treinado em notícias de ESG; notícias tendem a ser neutras por estilo,
então o resultado deve ser lido como indicador, não como verdade.

## 4. Resumo — candidatos e decisão

| Modelo | Tipo / dados | Tamanho aprox. | Observações |
|---|---|---|---|
| **`recogna-nlp/ptt5-base-summ`** ✅ | PTT5 (T5 pré-treinado em português) ajustado para **resumo de notícias** em PT | ~220 M parâmetros (~0,9 GB) | Específico para português e para o gênero "notícia", como nosso corpus |
| `csebuetnlp/mT5_multilingual_XLSum` | mT5 multilíngue (45 idiomas) treinado no XL-Sum | ~580 M parâmetros (~2,3 GB) | Atende português, mas é ~2,5× maior e mais lento em CPU |
| `facebook/bart-large-cnn` | BART em inglês (CNN/DailyMail) | ~400 M parâmetros | **Descartado:** apenas inglês |
| GPT-2 (usado nos exercícios de FastAPI) | Gerador causal | 124 M parâmetros | **Descartado:** não é treinado para resumir; geraria texto livre e alucinaria |

**Decisão:** `recogna-nlp/ptt5-base-summ`, por ser em português, treinado para o gênero
do nosso corpus e ~2,5× menor que a alternativa multilíngue.
*Limitação:* resumos abstrativos podem omitir ou distorcer detalhes; por isso a API
devolve também o texto de entrada e a taxa de compressão para comparação.

## 5. Custo computacional local

| Recurso | Necessário |
|---|---|
| Hardware | **CPU basta**; GPU é opcional (o código não exige) |
| RAM | ~4 GB livres para carregar os dois modelos juntos (pesos ≈ 1,5 GB + sobrecarga do PyTorch) |
| Disco | ~2 GB para os pesos + o PyTorch (versão CPU) |
| Latência | 1ª chamada de cada tarefa: carregamento do modelo (segundos a dezenas de segundos); depois, em CPU, de centenas de ms (sentimento) a alguns segundos (resumo) — **valores a medir na sua máquina** e anotar na seção 6 |

Os modelos são carregados **sob demanda** (só quando a tarefa é usada pela primeira vez)
e mantidos em memória, para não pagar o carregamento a cada requisição nem ocupar RAM com
um modelo que não está em uso.

## 6. Como a integração local foi feita

```
Streamlit (página 🧠) ──HTTP──► FastAPI  POST /processar_texto
                                   │  valida entrada (Pydantic)
                                   ▼
                          Code/API/llm_service.py  (ServicoLLM)
                                   │  carrega 1x, em memória, via transformers.pipeline
                                   ▼
                        modelo HuggingFace em disco local (cache)
```

1. **Instalação:** `pip install -r requirements.txt` (inclui `transformers` e `torch`; para
   instalar só a versão CPU do PyTorch, veja a seção "PyTorch" do README).
2. **Download único:** `python Code/Modeling/baixar_modelos.py` (precisa de internet).
3. **Execução sem nuvem:** `CONECTA_LLM_OFFLINE=1 uvicorn main:app --app-dir Code/API --port 8000`
   — com essa variável, o `transformers` usa apenas arquivos locais (`local_files_only`).
4. **Troca de modelo sem mexer no código:** `CONECTA_MODELO_RESUMO` e
   `CONECTA_MODELO_SENTIMENTO`.

### Rotas do TP4

| Método | Rota | Função |
|---|---|---|
| POST | `/processar_texto` | Recebe `{tarefa, texto, max_palavras_resumo}` e devolve a análise |
| GET | `/llm/status` | Modelo configurado por tarefa e se já está carregado |

### Response Models (Pydantic — `Code/API/schemas.py`)

- **Entrada** `ProcessarTextoIn`: `tarefa` ∈ {resumo, sentimento}; `texto` 1–20 000
  caracteres (espaços nas pontas são removidos); `max_palavras_resumo` 15–200.
- **Saída** `ProcessarTextoOut`: `tarefa`, `modelo`, `texto_entrada`,
  `n_caracteres_entrada`, `tempo_ms` e `resultado`, que é um **tipo discriminado** por
  `tarefa`: `ResultadoResumo` (`resumo`, `n_palavras_resumo`, `taxa_compressao`) ou
  `ResultadoSentimento` (`rotulo`, `confianca` 0–1, `pontuacoes`). O FastAPI valida a
  resposta contra esse modelo antes de enviá-la.

Exemplo — `POST /processar_texto` com `{"tarefa":"sentimento","texto":"Projeto excelente!"}`:

```json
{
  "tarefa": "sentimento",
  "modelo": "lxyuan/distilbert-base-multilingual-cased-sentiments-student",
  "texto_entrada": "Projeto excelente!",
  "n_caracteres_entrada": 18,
  "tempo_ms": 120,
  "resultado": {
    "tarefa": "sentimento", "rotulo": "positivo", "confianca": 0.93,
    "pontuacoes": {"positivo": 0.93, "neutro": 0.05, "negativo": 0.02}
  }
}
```
*(valores ilustrativos do formato; os números reais dependem do modelo.)*

## 7. Tratamento de erros

Falhas do serviço viram exceções de domínio (`llm_service.py`) e um *exception handler*
global as converte em JSON padronizado `{codigo, mensagem, dica}` (modelo `ErroResposta`):

| Situação | HTTP | `codigo` | Exemplo de `dica` |
|---|---|---|---|
| Texto vazio, curto demais para resumir (< 200 caracteres) ou longo demais (> 20 000) | **422** | `entrada_invalida` | Revise o texto enviado |
| Corpo inválido (tarefa desconhecida, campo ausente, texto só com espaços) | **422** | (formato padrão do FastAPI, com `loc` e `msg` por campo) | — |
| `transformers`/PyTorch ausente, modelo não baixado ou sem memória para carregar | **503** | `modelo_indisponivel` | Instale as dependências e rode `baixar_modelos.py` |
| Inferência acima de `CONECTA_LLM_TIMEOUT_S` (60 s) | **504** | `tempo_limite_excedido` | Envie um texto menor |
| Modelo carregou, mas falhou ao processar (ex.: memória, saída vazia) | **500** | `falha_na_inferencia` | Consulte os logs |

Detalhes de implementação e limites:
- Um modelo que falhou ao carregar **não fica marcado como carregado**; a próxima
  requisição tenta de novo, e o último erro aparece em `GET /llm/status`.
- A inferência roda em um *thread* com tempo limite. O Python não consegue interromper um
  thread já em execução: após um 504 a inferência termina em segundo plano e, como há um
  único *worker*, as requisições seguintes esperam por ela.
- O app Streamlit traduz cada erro em uma mensagem na tela (`app_utils.processar_texto`).

## 8. Testes

- `tests/test_llm_service.py` — 12 testes com *pipelines simulados* (sem baixar modelos):
  resumo, sentimento, tradução de rótulos, carga única, entradas inválidas (422), falha de
  carga (503), timeout (504), erro de inferência (500) e troca de modelo por variável de
  ambiente. Rode: `pytest tests -q`.
- `tests/test_api_llm.py` — testes HTTP com `TestClient` (200, 422, 503, `/llm/status`);
  exigem `fastapi` e `httpx` e são ignorados se não estiverem instalados.

### Registro de testes com os modelos reais (preencher na sua máquina)

Rode a API e a página 🧠 (ou `curl`) com as 5 notícias do corpus e anote:

| Notícia | Tarefa | Resultado | Tempo (ms) | Avaliação (adequado? erros?) |
|---|---|---|---|---|
| 1 | sentimento | | | |
| 1 | resumo | | | |
| … | | | | |

Anote também RAM usada e tempo da 1ª chamada. Essa tabela é a evidência de desempenho
local que sustenta a justificativa deste documento.

## 9. Segurança e privacidade

- Execução local: os textos **não são enviados** a terceiros (após o download inicial).
- Os modelos vêm do HuggingFace Hub; cada um tem sua licença — consulte o *model card*
  antes de uso além do acadêmico.
- A API continua sem autenticação (uso acadêmico/local).
