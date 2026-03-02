# 🧠 Estratégias de Engenharia de Prompt (Prompt Engineering Notes)

Este documento detalha as técnicas arquiteturais e cognitivas aplicadas na construção dos prompts dinâmicos para o Hub Educacional. O objetivo principal foi garantir saídas estruturadas (JSON) de alta qualidade, minimizando alucinações e maximizando a personalização pedagógica.

## 1. Persona Prompting & System Context
**Técnica Aplicada:** Definição de papel estrito e injeção de contexto.
**Implementação:** Todos os prompts iniciam definindo o modelo como um "Especialista em Pedagogia e Design Instrucional".
**Por que funciona:** LLMs tendem a generalizar respostas. Ao forçar uma persona pedagógica, o vocabulário gerado se torna mais didático, empático e focado no aprendizado, evitando jargões técnicos excessivos (a menos que o perfil do aluno seja "Avançado").

## 2. Dynamic Context Injection (Injeção de Perfil)
**Técnica Aplicada:** Variáveis de template substituídas em tempo de execução.
**Implementação:** O motor Python injeta o `{nome}`, `{idade}`, `{nivel}` e `{estilo_aprendizado}` diretamente na raiz do prompt.
**Por que funciona:** Garante que a IA não crie um conteúdo genérico. Um exemplo prático para uma criança de 10 anos visual será radicalmente diferente de um exemplo para um adulto de 25 anos cinestésico.

## 3. Chain-of-Thought (CoT) para Explicações Conceituais
**Técnica Aplicada:** Indução de raciocínio passo a passo.
**Implementação:** Na função de "Explicação Conceitual", o prompt exige explicitamente a chave `"raciocinio_pedagogico"` no JSON de saída antes do `"conteudo_final"`. O comando utilizado é: *"Pense passo a passo sobre como desconstruir este conceito para a idade do aluno antes de redigir a explicação final."*
**Por que funciona:** Reduz erros lógicos e alucinações. Ao forçar a IA a gerar seu processo de pensamento primeiro, a saída final (`conteudo_final`) atinge um nível de clareza e precisão muito superior.

## 4. Strict Output Formatting (Few-Shot & JSON Constraints)
**Técnica Aplicada:** Formatação estrita de saída para integração de sistemas.
**Implementação:** Os prompts terminam com uma diretriz inescapável: *"Retorne EXCLUSIVAMENTE um objeto JSON válido. Não inclua marcações markdown (```json). Não inclua texto introdutório."*
**Por que funciona:** Elimina o problema crônico de LLMs adicionarem textos conversacionais (ex: "Aqui está o seu JSON..."), o que quebraria a lógica de parsing do backend Python.

## 5. Estratégia de Versionamento e Comparação
Para fins de avaliação, o sistema permite alternar entre os templates `v1` (diretrizes simples) e `v2` (diretrizes com CoT avançado e formatação estrita). A comparação das saídas na pasta `/samples` demonstra empiricamente o ganho de qualidade gerado pela engenharia de prompt estruturada.