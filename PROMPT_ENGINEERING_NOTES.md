# 🧠 Prompt Engineering Notes — V-LAB Hub Educacional

> **Versão:** 2.0 | **Autor:** Willian Rupert | **Última atualização:** 2026

---

## Sumário

1. [Visão Geral da Arquitetura de Prompts](#1-visão-geral-da-arquitetura-de-prompts)
2. [Por que Escrever Prompts em Inglês?](#2-por-que-escrever-prompts-em-inglês)
3. [Técnicas Aplicadas](#3-técnicas-aplicadas)
   - [3.1 Persona Prompting](#31-persona-prompting)
   - [3.2 Dynamic Context Injection](#32-dynamic-context-injection)
   - [3.3 Chain-of-Thought (CoT)](#33-chain-of-thought-cot)
   - [3.4 Bloom's Taxonomy Scaffolding](#34-blooms-taxonomy-scaffolding)
   - [3.5 Constraint-Based Generation](#35-constraint-based-generation)
   - [3.6 Strict Output Formatting / JSON Contract](#36-strict-output-formatting--json-contract)
   - [3.7 Language Anchoring](#37-language-anchoring)
4. [Anatomia de um Prompt — Visão Completa](#4-anatomia-de-um-prompt--visão-completa)
5. [Decisões por Tipo de Conteúdo](#5-decisões-por-tipo-de-conteúdo)
   - [5.1 Explicação Conceitual](#51-explicação-conceitual)
   - [5.2 Exemplos Práticos](#52-exemplos-práticos)
   - [5.3 Perguntas de Reflexão](#53-perguntas-de-reflexão)
   - [5.4 Resumo Visual](#54-resumo-visual)
6. [Mapeamento Pedagógico: Estilo × Nível](#6-mapeamento-pedagógico-estilo--nível)
7. [Estratégia de Versionamento (v1 vs v2)](#7-estratégia-de-versionamento-v1-vs-v2)
8. [Resiliência de Output: o json_parser](#8-resiliência-de-output-o-json_parser)
9. [Anti-Padrões Evitados](#9-anti-padrões-evitados)
10. [Referências e Estudos de Base](#10-referências-e-estudos-de-base)

---

## 1. Visão Geral da Arquitetura de Prompts

Cada prompt gerado pelo `PromptBuilder` é construído como uma **pilha modular de blocos**, onde cada bloco resolve um problema específico de comunicação com o LLM:

```
┌──────────────────────────────────────┐
│  1. _persona_block()                 │  ← Quem a IA é
├──────────────────────────────────────┤
│  2. _student_context_block()         │  ← Com quem ela está falando
├──────────────────────────────────────┤
│  3. _output_language_rule()          │  ← Em que idioma responder
├──────────────────────────────────────┤
│  4. task block (por tipo)            │  ← O que fazer, como pensar
├──────────────────────────────────────┤
│  5. _json_contract()                 │  ← Qual o formato exato da saída
└──────────────────────────────────────┘
```

Essa separação garante que cada preocupação esteja isolada, testável e intercambiável — refletindo boas práticas de software e de engenharia de prompt simultaneamente.

---

## 2. Por que Escrever Prompts em Inglês?

Esta é uma decisão técnica deliberada baseada em evidências empíricas e na natureza dos LLMs modernos.

### A razão técnica

LLMs como GPT-4 e Gemini são pré-treinados predominantemente em inglês. A vasta maioria dos dados de instruction-tuning (RLHF, FLAN, etc.) também está em inglês. Isso significa que:

- **O espaço de ativação do modelo para instruções é mais rico em inglês.** Conceitos como `Chain-of-Thought`, `Persona`, `Output Format` têm representações internas mais precisas quando expressos na língua em que foram treinados.
- **Prompts em inglês ativam padrões de raciocínio mais robustos**, especialmente para tarefas que exigem planejamento multi-passo (CoT).
- **Estudos empíricos** (Shi et al., 2022; Huang et al., 2023) mostram que traduzir problemas para inglês antes de enviá-los ao modelo melhora a performance em benchmarks de raciocínio — mesmo quando o output final deve ser em outro idioma.

### A solução implementada

Prompts em inglês + regra explícita de idioma de saída:

```
## Language Rule (NON-NEGOTIABLE)
You MUST write ALL content [...] exclusively in Brazilian Portuguese (pt-BR).
Only the JSON keys must remain in English as specified below.
```

A regra é posicionada **após** o contexto pedagógico e **antes** da tarefa, garantindo que esteja fresca na "memória de trabalho" do modelo quando ele começa a gerar.

---

## 3. Técnicas Aplicadas

### 3.1 Persona Prompting

**O que é:** Atribuir ao modelo uma identidade específica, com expertise, background e modo de operar claramente definidos.

**Implementação no projeto:**

```python
"You are Dr. Maya, a world-renowned expert in Instructional Design and
Cognitive Science with 20+ years of experience adapting complex subjects
to diverse learners. You apply evidence-based pedagogical frameworks
(Bloom's Taxonomy, Constructivism, VAK/VARK)..."
```

**Por que funciona:**

LLMs são modelos de linguagem condicionais — o início do contexto âncora fortemente o comportamento subsequente. Ao definir uma persona específica e credível:

1. O vocabulário gerado se torna mais didático e preciso.
2. O modelo "escolhe" frameworks pedagógicos reais (Bloom, VARK) em vez de senso comum.
3. A consistência de tom e profundidade é mantida ao longo de toda a resposta.

**Diferença em relação à v1:**

| v1 | v2 |
|---|---|
| "Você é um professor experiente em Pedagogia" | "You are Dr. Maya, a world-renowned expert in Instructional Design and Cognitive Science with 20+ years of experience..." |
| Genérico, sem identidade | Específico, credível, com frameworks nomeados |

A especificidade da persona importa: um "professor" é vago. Uma "doutora em Design Instrucional e Ciência Cognitiva que aplica Bloom e VARK" ativa padrões de linguagem muito mais ricos.

---

### 3.2 Dynamic Context Injection

**O que é:** Injetar dinamicamente os dados do perfil do aluno no prompt em tempo de execução, adaptando cada dimensão da resposta.

**Implementação no projeto:**

```python
def _student_context_block(self) -> str:
    return (
        "## Student Profile\n"
        f"- **Name**: {self.nome}\n"
        f"- **Age**: {self.idade} years old\n"
        f"- **Knowledge level**: {self.nivel}\n"
        f"- **Learning style**: {self.estilo} (VARK model)\n\n"
        "## Pedagogical Adaptation Rules\n"
        f"**Vocabulary & Complexity**: {self._level_hint}\n\n"
        f"**Learning Style Strategy**: {self._style_hint}\n\n"
    )
```

**O diferencial da v2:** além de injetar os dados brutos do aluno, o sistema injeta **guias pedagógicas derivadas** (`_level_hint` e `_style_hint`) — instruções pré-computadas que traduzem os dados do perfil em diretrizes de ação concretas para o modelo. O modelo não precisa inferir o que significa "cinestésico"; ele recebe explicitamente:

```
Ground every concept in hands-on actions, real-world processes and
step-by-step procedures the student can physically replicate. Prioritise
'doing' language: 'build', 'run', 'try', 'feel', 'construct'.
```

---

### 3.3 Chain-of-Thought (CoT)

**O que é:** Induzir o modelo a externalizar seu raciocínio passo a passo antes de produzir a resposta final. Introduzido por Wei et al. (2022) como uma das técnicas mais impactantes em NLP moderno.

**Implementação no projeto (Explicação Conceitual):**

```python
"### Step-by-step thinking protocol (Chain-of-Thought)\n"
"Before writing a single word of the explanation, you MUST reason through "
"the following questions and store that reasoning in the `raciocinio` key:\n"
"  1. What are the 3-5 core sub-concepts that build up '{topico}'?\n"
"  2. What misconceptions does a {nivel}-level student typically hold about this topic?\n"
"  3. Which analogy or metaphor best fits a {estilo} learner aged {idade}?\n"
"  4. In what order should the sub-concepts be introduced to minimise cognitive load?\n"
"  5. What single 'aha moment' should this explanation build toward?\n"
```

**Por que o protocolo estruturado importa:**

CoT simples ("pense passo a passo") funciona. CoT **estruturado** com perguntas específicas funciona ainda melhor — porque cada pergunta direciona o modelo a um tipo de raciocínio diferente:

| Pergunta | Tipo de raciocínio induzido |
|---|---|
| "What are the 3-5 core sub-concepts?" | Decomposição analítica |
| "What misconceptions does the student hold?" | Teoria da mente / diagnóstico |
| "Which analogy fits?" | Raciocínio por analogia |
| "In what order?" | Planejamento sequencial |
| "What 'aha moment'?" | Síntese narrativa |

O JSON retorna a chave `raciocinio` **antes** da chave `conteudo`, forçando o modelo a completar o raciocínio antes de escrever a explicação final. Isso espelha o mecanismo interno do CoT: a qualidade da saída final depende diretamente da qualidade do raciocínio que a precede.

---

### 3.4 Bloom's Taxonomy Scaffolding

**O que é:** Usar a Taxonomia de Bloom como framework para calibrar a profundidade cognitiva das perguntas de reflexão.

**Implementação no projeto:**

```python
bloom_ceiling = {
    "iniciante":     "comprehension and application (Bloom levels 1-3)",
    "intermediário": "analysis and evaluation (Bloom levels 4-5)",
    "avançado":      "evaluation and creation (Bloom levels 5-6)",
}.get(self.nivel, "analysis and evaluation (Bloom levels 4-5)")
```

```
  • Question 1 checks understanding (can the student explain/identify?).
  • Question 2 probes deeper thinking (can the student compare/apply?).
  • Question 3 challenges creatively within the ceiling.
```

**Por que o "teto" importa:**

Perguntas acima da zona de desenvolvimento proximal do aluno geram frustração, não aprendizado. Ao definir explicitamente um `bloom_ceiling` por nível, o sistema garante que as perguntas **desafiem sem desmotivar** — um princípio central da pedagogia construtivista (Vygotsky, 1978).

---

### 3.5 Constraint-Based Generation

**O que é:** Definir restrições explícitas sobre quantidade, estrutura, complexidade e formato para reduzir a variância da saída e aumentar a utilidade pedagógica.

**Exemplos no projeto:**

```
Generate exactly 3 practical examples [...] in ascending difficulty.
Maximum 3 levels of depth — deeper hierarchies overwhelm working memory.
Each node/cell must contain only the essential label (≤ 6 words).
```

**Por que funciona:**

Modelos de linguagem, sem restrições, tendem a maximizar a "completude aparente" — gerando mais itens, mais profundidade, mais texto do que necessário. Restrições explícitas forçam **escolhas editoriais** que espelham o que um bom professor faz: selecionar, não despejar.

A **carga cognitiva** (Sweller, 1988) é um fator real no aprendizado. Limitar a profundidade dos diagramas a 3 níveis não é arbitrário — é baseado nas limitações da memória de trabalho humana (Miller, 1956: 7±2 itens).

---

### 3.6 Strict Output Formatting / JSON Contract

**O que é:** Especificar o esquema de saída de forma contratual, tornando qualquer desvio uma violação explícita.

**Implementação no projeto:**

```python
def _json_contract(self, schema_example: str) -> str:
    return (
        "## Output Contract\n"
        "Return ONLY a single, valid JSON object. No markdown fences, no "
        "preamble, no postamble, no comments. Any deviation breaks the parser.\n\n"
        f"Required schema (exact keys, no extras):\n{schema_example}\n"
    )
```

**Escolhas de design:**

1. **"Output Contract"** em vez de "Output Format": o enquadramento contratual ("viola o parser") é mais imperativo do que o enquadramento de preferência ("prefiro que retorne").

2. **Schema com exemplo concreto**: o modelo vê exatamente o que deve produzir, não uma descrição abstrata. Isso é um mini-few-shot para o formato.

3. **Chave `raciocinio` antes de `conteudo` no schema**: garante que o CoT ocorra antes do conteúdo final, mesmo quando o modelo usa o JSON como âncora de planejamento.

---

### 3.7 Language Anchoring

**O que é:** Posicionar uma regra de idioma explícita e inegociável em local estratégico do prompt.

**Implementação:**

```
## Language Rule (NON-NEGOTIABLE)
You MUST write ALL content [...] exclusively in Brazilian Portuguese (pt-BR).
Only the JSON keys must remain in English as specified below.
Violation of this rule renders the entire response invalid.
```

**Por que "NON-NEGOTIABLE" e "renders the response invalid":**

LLMs são treinados para minimizar "erros" no sentido do feedback humano. Ao enquadrar a violação da regra de idioma como algo que "torna a resposta inválida", o modelo trata isso como um erro a evitar — não como uma preferência a equilibrar.

**Posicionamento estratégico:** a regra é colocada após o contexto (que está em inglês) e antes da tarefa. Isso evita que o modelo "assuma" que deve continuar em inglês por ver inglês ao redor.

---

## 4. Anatomia de um Prompt — Visão Completa

Abaixo, o prompt de Explicação Conceitual para `Willian, 22 anos, avançado, cinestésico` sobre `Arquitetura de Microsserviços` — anotado por bloco:

```
[BLOCO 1 — PERSONA]
You are Dr. Maya, a world-renowned expert in Instructional Design...

[BLOCO 2 — CONTEXTO DO ALUNO]
## Student Profile
- Name: Willian
- Age: 22 years old
- Knowledge level: avançado
- Learning style: cinestésico (VARK model)

## Pedagogical Adaptation Rules
Vocabulary & Complexity: Use precise technical vocabulary...
Learning Style Strategy: Ground every concept in hands-on actions...

[BLOCO 3 — REGRA DE IDIOMA]
## Language Rule (NON-NEGOTIABLE)
You MUST write ALL content [...] in Brazilian Portuguese (pt-BR)...

[BLOCO 4 — TAREFA + CoT]
## Task: Conceptual Explanation
Topic: Arquitetura de Microsserviços

### Step-by-step thinking protocol (Chain-of-Thought)
1. What are the 3-5 core sub-concepts...?
2. What misconceptions does an avançado-level student typically hold...?
3. Which analogy best fits a cinestésico learner aged 22?
4. In what order should the sub-concepts be introduced...?
5. What single 'aha moment' should this explanation build toward?

[BLOCO 5 — CONTRATO DE OUTPUT]
## Output Contract
Return ONLY a single, valid JSON object...
{
  "raciocinio": "...",
  "conteudo": "..."
}
```

---

## 5. Decisões por Tipo de Conteúdo

### 5.1 Explicação Conceitual

**Problema pedagógico:** Como garantir que a explicação seja construída de forma coerente e não seja apenas uma série de fatos desconexos?

**Solução:** CoT estruturado com 5 perguntas de planejamento que cobrem decomposição, diagnóstico de misconceptions, escolha de analogia, sequenciamento e síntese narrativa. O modelo é forçado a ter um "plano de aula" antes de escrever.

**Técnicas:** Persona + Context Injection + Chain-of-Thought + JSON Contract + Language Anchoring

---

### 5.2 Exemplos Práticos

**Problema pedagógico:** Exemplos genéricos não conectam ao mundo real do aluno e perdem impacto.

**Solução:** Contextualização dupla (idade + estilo de aprendizado) + restrição de complexidade ascendente. O modelo não pode dar três exemplos no mesmo nível — é forçado a construir uma progressão.

**Técnicas:** Persona + Context Injection + Constraint-Based Generation + JSON Contract + Language Anchoring

---

### 5.3 Perguntas de Reflexão

**Problema pedagógico:** Perguntas muito fáceis não estimulam; perguntas muito difíceis frustram.

**Solução:** Bloom's Taxonomy Scaffolding com teto explícito por nível + progressão interna de 3 perguntas (compreensão → análise → desafio criativo dentro do teto).

**Técnicas:** Persona + Context Injection + Bloom's Taxonomy + Constraint-Based Generation + JSON Contract + Language Anchoring

---

### 5.4 Resumo Visual

**Problema pedagógico:** "Faça um diagrama" é vago demais — o modelo escolhe formatos inapropriados para o tópico.

**Solução:** Lógica de seleção de diagrama explícita (árvore hierárquica vs. fluxo vs. tabela vs. mapa conceitual) + restrição de profundidade máxima baseada em carga cognitiva + instruções de estilo visual adaptadas ao VARK.

**Técnicas:** Persona + Context Injection + Structural Scaffolding + Constraint-Based Generation + JSON Contract + Language Anchoring

---

## 6. Mapeamento Pedagógico: Estilo × Nível

### Estilos de Aprendizado (VARK) → Linguagem de Prompt

| Estilo | Linguagem prioritária | Exemplos de metáforas |
|---|---|---|
| **Visual** | Espacial, cromática, hierárquica | "imagine", "observe", "mapa", "diagrama" |
| **Auditivo** | Rítmica, narrativa, dialógica | "escute", "soa como", "repita em voz alta" |
| **Leitura/Escrita** | Precisa, definitória, estruturada | "definição", "conceito", "termo técnico" |
| **Cinestésico** | Ação, processo, construção | "construa", "execute", "sinta", "experimente" |

### Níveis de Conhecimento → Complexidade Vocabular

| Nível | Instrução injetada |
|---|---|
| **Iniciante** | Linguagem cotidiana, sem jargão, cada termo novo imediatamente definido por analogia simples |
| **Intermediário** | Vocabulário do domínio permitido, mas sub-conceitos avançados explicados; conexão com conhecimento prévio |
| **Avançado** | Vocabulário técnico preciso sem simplificações, foco em nuances, trade-offs e edge cases |

---

## 7. Estratégia de Versionamento (v1 vs v2)

O sistema mantém `prompts/v1_templates.py` e `prompts/v2_templates.py` para permitir comparação A/B sistemática.

### Diferenças Estruturais

| Dimensão | v1 | v2 |
|---|---|---|
| Idioma do prompt | Português | Inglês (com output em pt-BR) |
| Persona | Genérica ("professor experiente") | Específica (Dr. Maya, frameworks nomeados) |
| Guias pedagógicas | Não injetadas | `_style_hint` + `_level_hint` pré-computados |
| CoT | "pense passo a passo" | Protocolo de 5 perguntas estruturadas |
| Bloom | Ausente | Teto explícito por nível |
| Diagrama | "ASCII ou descrição" | Lógica de seleção com 4 tipos + restrição de profundidade |
| Contrato de output | "sem markdown" | "Output Contract — qualquer desvio quebra o parser" |

### Como executar o Teste A/B

Na interface web (`app_web.py`), a aba **"Laboratório (Teste A/B)"** compara:
- **Prompt Genérico**: `"Me explique sobre {topico}. Retorne em JSON..."` — nenhuma das técnicas acima.
- **Prompt Otimizado (V-LAB Engine)**: todos os blocos descritos neste documento.

Os resultados são salvos em `/samples` com timestamp para análise posterior.

---

## 8. Resiliência de Output: o `json_parser`

Mesmo com o Output Contract bem definido, LLMs ocasionalmente envolvem o JSON em fences de markdown ou adicionam texto introdutório. A função `json_parser` implementa 3 passagens de extração:

```
Passagem 1: json.loads() direto → caso ideal (modelo obedeceu o contrato)
     ↓ falha
Passagem 2: regex para ```json ... ``` → modelo usou fence de markdown
     ↓ falha
Passagem 3: regex para { ... } mais externo → modelo adicionou prosa ao redor
     ↓ falha
ValueError com mensagem descritiva + primeiros 300 chars da resposta
```

Essa abordagem em cascata garante que a aplicação degrade graciosamente sem quebrar o fluxo do usuário em casos de não-conformidade parcial do modelo.

---

## 9. Anti-Padrões Evitados

| Anti-padrão | Problema | Solução adotada |
|---|---|---|
| Prompt em bloco monolítico | Difícil de manter, testar e evoluir | Blocos modulares com responsabilidade única |
| "Seja um bom professor" | Persona vaga não ancora comportamento | Persona específica com expertise e frameworks nomeados |
| "Responda em português" no final | Modelo pode ignorar ao gerar | Language Rule posicionada estrategicamente, com framing inegociável |
| CoT genérico ("pense passo a passo") | Raciocínio vago produz saída vaga | Protocolo CoT com 5 perguntas estruturadas e específicas ao domínio |
| Schema sem exemplo | Modelo pode interpretar chaves ambiguamente | Schema com exemplo concreto como mini-few-shot |
| Sem tratamento de erros no parser | Quebra silenciosa em não-conformidade | json_parser com 3 passagens e ValueError descritivo |
| Profundidade ilimitada em diagramas | Sobrecarga cognitiva do aluno | Restrição explícita: máximo 3 níveis |

---

## 10. Referências e Estudos de Base

- **Wei et al. (2022)** — *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS 2022. Base para a técnica CoT estruturada.

- **Brown et al. (2020)** — *Language Models are Few-Shot Learners*. GPT-3 paper. Base para few-shot e persona prompting.

- **Shi et al. (2022)** — *Language Models are Multilingual Chain-of-Thought Reasoners*. Evidência empírica para prompts em inglês com saída multilíngue.

- **Reynolds & McDonell (2021)** — *Prompt Programming for Large Language Models: Beyond the Few-Shot Paradigm*. Fundamento para role assignment e context setting.

- **Schulhoff et al. (2023)** — *Learn Prompting: A Free, Open Source Course on Communicating with AI*. Referência para o conceito de "Output Contract".

- **Bloom, B.S. (1956)** — *Taxonomy of Educational Objectives*. Framework para scaffolding de perguntas de reflexão.

- **Sweller, J. (1988)** — *Cognitive Load During Problem Solving*. Base para a restrição de profundidade máxima em diagramas.

- **Miller, G.A. (1956)** — *The Magical Number Seven, Plus or Minus Two*. Fundamento para limitar nós em diagramas a no máximo 7 itens por nível.

- **Fleming, N.D. (2001)** — *VARK: A Guide to Learning Styles*. Framework para o mapeamento de estilos de aprendizado.

- **Vygotsky, L.S. (1978)** — *Mind in Society*. Conceito de Zona de Desenvolvimento Proximal, base para o teto de Bloom por nível.

---

*Este documento é um artefato vivo — deve ser atualizado a cada iteração significativa dos prompts, especialmente após análises comparativas A/B que revelem novas oportunidades de melhoria.*