# 🎓 V-LAB — Motor de Engenharia de Prompts

> **Desafio Técnico — Estágio em IA e Engenharia de Prompt**

---

## ⚡ Além do Desafio: Integração Full-Stack Real em Produção

Este projeto foi desenvolvido **além dos requisitos do desafio de IA**, sendo integrado ao **Hub Fullstack** submetido simultaneamente para a vaga de Estágio Full-Stack.

| Projeto | Domínio | Função |
|---|---|---|
| 🤖 **Motor de IA** (este repositório) | [`ia.rlight.com.br`](https://ia.rlight.com.br) | Gera aulas pedagógicas personalizadas via API FastAPI |
| 🏫 **Hub Fullstack** | [`edu.rlight.com.br`](https://edu.rlight.com.br) | Consome o motor de IA para enriquecer recursos educacionais com geração automática de descrições e conteúdo |

Os dois sistemas foram **vinculados em produção**: o "Smart Assist" do Hub Fullstack (`edu.rlight.com.br`) chama diretamente a API deste motor (`ia.rlight.com.br/gerar_aula`), demonstrando integração real entre os dois desafios com domínios próprios e CORS configurado.

---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Demonstração](#demonstração)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Requisitos Cumpridos](#requisitos-cumpridos)
- [Engenharia de Prompt — Destaques](#engenharia-de-prompt--destaques)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Setup e Instalação](#setup-e-instalação)
- [Como Usar](#como-usar)
- [Testes Automatizados](#testes-automatizados)
- [Exemplos de Output](#exemplos-de-output)
- [Decisões Técnicas](#decisões-técnicas)

---

## Visão Geral

O **V-LAB Motor de Prompts** é uma plataforma educativa que gera conteúdo pedagógico personalizado para alunos com diferentes perfis. O sistema recebe um tópico e as características do aluno (idade, nível de conhecimento, estilo de aprendizado) e utiliza técnicas avançadas de Engenharia de Prompt para produzir 4 tipos distintos de material educativo via API Google Gemini.

**Técnicas de Prompt Engineering implementadas:**
- Persona Prompting com identidade específica e credencial
- Dynamic Context Injection com guias pedagógicas pré-computadas
- Chain-of-Thought (CoT) estruturado com protocolo de 5 etapas
- Bloom's Taxonomy Scaffolding para calibração cognitiva
- Constraint-Based Generation para controle de qualidade
- Strict Output Formatting via JSON Contract
- Language Anchoring para garantia de idioma

---

## Demonstração

**Interface Web:** [`ia.rlight.com.br`](https://ia.rlight.com.br)

**API REST:** [`ia.rlight.com.br/docs`](https://ia.rlight.com.br/docs) (Swagger UI)

**Hub Fullstack integrado:** [`edu.rlight.com.br`](https://edu.rlight.com.br)

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    edu.rlight.com.br                     │
│              Hub Fullstack (React + FastAPI)             │
│                                                          │
│  [Smart Assist] ──POST /gerar_aula──────────────────┐   │
└─────────────────────────────────────────────────────│───┘
                                                       │ CORS
┌─────────────────────────────────────────────────────▼───┐
│                    ia.rlight.com.br                      │
│              Motor de IA (FastAPI + Streamlit)           │
│                                                          │
│  app_web.py ──── Interface Streamlit (professores)       │
│  api.py     ──── API REST FastAPI (consumo externo)      │
│  engine.py  ──── PromptBuilder + json_parser             │
│       │                                                  │
│       └──── Google Gemini 2.5 Flash API                  │
└──────────────────────────────────────────────────────────┘
```

### Fluxo de uma requisição

```
Usuário informa perfil do aluno + tópico
        │
        ▼
PromptBuilder._persona_block()        ← Persona Prompting
        +
PromptBuilder._student_context_block() ← Context Injection
        +
PromptBuilder._output_language_rule()  ← Language Anchoring
        +
PromptBuilder.build_*_prompt()         ← CoT / Bloom / Constraints
        +
PromptBuilder._json_contract()         ← Output Formatting
        │
        ▼
   Gemini 2.5 Flash
        │
        ▼
   json_parser() (4 passagens de resiliência)
        │
        ▼
   JSON estruturado → Interface / API / Download PDF
```

---

## Requisitos Cumpridos

### ✅ Requisitos Funcionais

| Requisito | Status | Implementação |
|---|---|---|
| Receber parâmetros do aluno (idade, nível, estilo) | ✅ | `PromptBuilder.__init__()` em `engine.py` |
| Receber tópico a ser ensinado | ✅ | Parâmetro `topico` em todos os métodos `build_*` |
| Explicação conceitual com Chain-of-Thought | ✅ | `build_conceitual_prompt()` — protocolo CoT de 5 etapas |
| Exemplos práticos contextualizados | ✅ | `build_pratico_prompt()` — exemplos em complexidade ascendente |
| Perguntas de reflexão com pensamento crítico | ✅ | `build_reflexao_prompt()` — Bloom's Taxonomy Scaffolding |
| Resumo em formato visual (ASCII/diagrama) | ✅ | `build_visual_prompt()` — lógica de seleção de 4 tipos de diagrama |
| Salvar resultados em JSON estruturado | ✅ | `app.py` salva em `/samples` com timestamp |
| Comparação entre versões de prompts | ✅ | Aba "Laboratório (Teste A/B)" na interface web |
| 3–5 perfis de alunos em JSON | ✅ | `perfis_mock.json` |
| Arquivo .env para chaves de API | ✅ | `.env.example` documentado |
| Sistema de cache | ✅ | `@st.cache_data` no Streamlit; `@st.cache_resource` para o cliente |
| CLI ou interface web | ✅ | Interface Streamlit (`app_web.py`) + CLI (`app.py`) |
| Selecionar aluno, tópico e tipo de conteúdo | ✅ | Sidebar do Streamlit com todos os controles |

### ✅ Requisitos Técnicos

| Requisito | Status | Detalhe |
|---|---|---|
| Python | ✅ | Python 3.11+ |
| API Google Gemini | ✅ | `gemini-2.5-flash` via `google-genai` SDK |
| `python-dotenv` | ✅ | Carregamento seguro de variáveis de ambiente |
| Chaves não expostas no código | ✅ | Somente via `.env`, `.gitignore` configurado |
| Tratamento robusto de erros | ✅ | `json_parser` com 4 passagens + try/except em todos os fluxos |

### ✅ Extras e Diferenciais

| Extra | Status | Detalhe |
|---|---|---|
| Interface web | ✅ | Streamlit com sidebar, tabs, quiz de perfil |
| Deploy em nuvem | ✅ | [`ia.rlight.com.br`](https://ia.rlight.com.br) com domínio próprio |
| Testes automatizados | ✅ | `pytest` com 4 casos em `tests/test_prompt_engine.py` |
| Download de resultados | ✅ | Export JSON e PDF com formatação V-LAB |
| API REST | ✅ | FastAPI em `api.py` consumida pelo Hub Fullstack |
| Integração cross-projeto | ✅ | Motor de IA vinculado ao Hub Fullstack em produção |
| PROMPT_ENGINEERING_NOTES.md | ✅ | Documentação técnica com 10 referências acadêmicas |

---

## Engenharia de Prompt — Destaques

> Documentação completa em [`PROMPT_ENGINEERING_NOTES.md`](./PROMPT_ENGINEERING_NOTES.md)

### Por que prompts em inglês com saída em português?

LLMs como Gemini são pré-treinados predominantemente em inglês. Instruções de raciocínio complexo (Chain-of-Thought, planejamento pedagógico) ativam padrões internos mais ricos nessa língua. O sistema combina prompts em inglês com uma regra explícita e inegociável de saída em pt-BR:

```
## Language Rule (NON-NEGOTIABLE)
You MUST write ALL content exclusively in Brazilian Portuguese (pt-BR).
Violation of this rule renders the entire response invalid.
```

### Arquitetura modular de 5 blocos

Todo prompt é composto por blocos independentes e testáveis:

```
1. _persona_block()          → Quem a IA é (Dr. Maya, especialista em Design Instrucional)
2. _student_context_block()  → Dados do aluno + guias pedagógicas pré-computadas (VARK + nível)
3. _output_language_rule()   → Regra de idioma posicionada estrategicamente
4. task block (por tipo)     → Tarefa específica com CoT / Bloom / restrições
5. _json_contract()          → Schema exato da saída
```

### Chain-of-Thought estruturado (Explicação Conceitual)

Em vez do genérico "pense passo a passo", o sistema força um **protocolo de 5 perguntas**:

```
1. What are the 3-5 core sub-concepts that build up '{topico}'?
2. What misconceptions does a {nivel}-level student typically hold?
3. Which analogy best fits a {estilo} learner aged {idade}?
4. In what order should sub-concepts be introduced (cognitive load)?
5. What single 'aha moment' should this explanation build toward?
```

Cada pergunta induz um tipo diferente de raciocínio: decomposição analítica, teoria da mente, raciocínio por analogia, planejamento sequencial e síntese narrativa.

### Bloom's Taxonomy no prompt de Reflexão

O sistema calcula automaticamente o "teto cognitivo" por nível e instrui o modelo a não ultrapassá-lo, evitando frustração:

```python
bloom_ceiling = {
    "iniciante":     "comprehension and application (Bloom levels 1-3)",
    "intermediário": "analysis and evaluation (Bloom levels 4-5)",
    "avançado":      "evaluation and creation (Bloom levels 5-6)",
}
```

---

## Estrutura do Projeto

```
vlab-desafio-prompt-engine/
│
├── engine.py                   # Motor principal: PromptBuilder + json_parser
├── app_web.py                  # Interface Streamlit (interface web)
├── app.py                      # CLI para geração e salvamento de amostras
├── api.py                      # API REST FastAPI (consumida pelo Hub Fullstack)
│
├── prompts/
│   ├── v1_templates.py         # Templates da versão 1 (simples, para comparação A/B)
│   └── v2_templates.py         # Templates da versão 2 (otimizados)
│
├── tests/
│   └── test_prompt_engine.py   # Testes automatizados com pytest
│
├── samples/
│   └── aula_20260301_215936.json   # Exemplo de output gerado
│
├── PROMPT_ENGINEERING_NOTES.md # Documentação técnica das estratégias de prompt
├── favicon.svg                 # Ícone da interface web
├── perfis_mock.json            # 3–5 perfis de alunos para teste
├── requirements.txt            # Dependências do projeto
├── .env.example                # Template de variáveis de ambiente
└── .gitignore                  # Garante que .env nunca seja commitado
```

---

## Setup e Instalação

### Pré-requisitos

- Python 3.11+
- Chave de API do [Google Gemini](https://aistudio.google.com/) (gratuita no free tier)

### 1. Clone o repositório

```bash
git clone https://github.com/willianrupert/vlab-desafio-prompt-engine
cd vlab-desafio-prompt-engine
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com sua chave real:

```env
GEMINI_API_KEY=sua_chave_real_aqui_sem_aspas
```

> ⚠️ **Nunca commite o arquivo `.env`.** Ele já está no `.gitignore`.

---

## Como Usar

### Interface Web (recomendado)

```bash
streamlit run app_web.py
```

Acesse `http://localhost:8501`. A interface oferece:

- **Sidebar:** configuração completa do perfil do aluno (nome, idade, nível, estilo) + quiz automático de descoberta de estilo
- **Aba "Gerador de Aulas":** seleção de tópico e tipo de conteúdo, visualização do raciocínio Chain-of-Thought, download em JSON e PDF
- **Aba "Laboratório (Teste A/B)":** comparação lado a lado entre prompt genérico e prompt otimizado V-LAB

### CLI (linha de comando)

```bash
python app.py
```

Gera uma aula completa para o aluno de teste (`Willian, 22 anos, avançado, cinestésico`) sobre "Arquitetura de Microsserviços" e salva o resultado em `/samples/aula_<timestamp>.json`.

### API REST (FastAPI)

```bash
uvicorn api:app --reload
```

Acesse a documentação interativa em `http://localhost:8000/docs`.

**Endpoint principal:**

```http
POST /gerar_aula
Content-Type: application/json

{
  "aluno": {
    "nome": "Ana",
    "idade": 17,
    "nivel": "iniciante",
    "estilo_aprendizado": "visual"
  },
  "topico": "Fotossíntese",
  "tipo_conteudo": "Conceitual"
}
```

**Resposta:**

```json
{
  "raciocinio": "1. Os sub-conceitos centrais são: ...",
  "conteudo": "Olá, Ana! Imagine que as plantas são pequenas fábricas de energia..."
}
```

**Tipos de conteúdo disponíveis:** `"Conceitual"`, `"Prático"`, `"Reflexão"`, `"Visual"`

---

## Testes Automatizados

```bash
pytest tests/ -v
```

```
tests/test_prompt_engine.py::test_injecao_de_contexto_no_prompt     PASSED
tests/test_prompt_engine.py::test_diretriz_chain_of_thought_presente PASSED
tests/test_prompt_engine.py::test_validacao_de_formato_json          PASSED
tests/test_prompt_engine.py::test_metodos_adicionais_existem         PASSED

4 passed in 0.12s
```

Os testes verificam sem precisar chamar a API:

1. **Injeção de contexto:** nome, idade e estilo do aluno aparecem corretamente no prompt gerado
2. **Diretriz CoT:** o protocolo Chain-of-Thought está presente (`step-by-step`)
3. **Parser JSON resiliente:** o `json_parser` extrai corretamente JSON envolto em fences de markdown
4. **Métodos obrigatórios:** os 4 métodos `build_*` existem e estão acessíveis

---

## Exemplos de Output

### Explicação Conceitual — "Arquitetura de Microsserviços" (Willian, 22 anos, avançado, cinestésico)

```json
{
  "raciocinio": "1. Os sub-conceitos centrais são: (a) Transformação Linear como ação...",
  "conteudo": "E aí, Willian! Imagine que você está montando um sistema de robôs especializados..."
}
```

> O arquivo completo está em [`samples/aula_20260301_215936.json`](./samples/aula_20260301_215936.json)

### Diferença A/B — "Física Quântica"

| Prompt Genérico | Prompt Otimizado V-LAB |
|---|---|
| Explicação genérica enciclopédica, sem considerar o perfil | Explicação com analogias cinestésicas específicas para 22 anos, vocabulário avançado, sequenciamento por carga cognitiva |
| Sem raciocínio pedagógico | CoT completo com 5 etapas de planejamento |
| JSON simples com `conteudo` | JSON com `raciocinio` + `conteudo` estruturado |

---

## Decisões Técnicas

### Google Gemini 2.5 Flash
Escolhido pelo custo-benefício (free tier generoso), latência baixa e excelente conformidade com instruções de formato JSON quando combinado com `response_mime_type="application/json"`.

### `json_parser` com 4 passagens
O Gemini ocasionalmente "vaza" texto fora do objeto JSON (fragmentos após o `}`). O parser implementa recuperação progressiva: parse direto → strip de markdown → busca por chaves → trim de lixo à direita. Garante zero quebras na experiência do usuário para falhas parciais do modelo.

### FastAPI + Streamlit
Duas interfaces complementares: Streamlit para uso direto por professores/educadores, FastAPI para integração programática — incluindo o Hub Fullstack em `edu.rlight.com.br`.

### Prompts em inglês
Decisão baseada em evidências empíricas (Shi et al., 2022): LLMs raciocinam de forma mais robusta em inglês mesmo quando a saída deve ser em outro idioma. A regra de idioma de saída é posicionada estrategicamente no prompt com framing inegociável.

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Chave da API Google Gemini (obtenha em [aistudio.google.com](https://aistudio.google.com)) |
| `OPENAI_API_KEY` | ❌ | Opcional, para extensões futuras com GPT |

---

## Referências

A fundamentação teórica completa das técnicas de prompt utilizadas está documentada em [`PROMPT_ENGINEERING_NOTES.md`](./PROMPT_ENGINEERING_NOTES.md), incluindo 10 referências acadêmicas (Wei et al. 2022, Brown et al. 2020, Bloom 1956, Vygotsky 1978, entre outros).

---

*Desenvolvido por **Willian Rupert** para o Desafio Técnico de Estágio em IA e Engenharia de Prompt — V-LAB, 2026.*