import json
import re

class PromptBuilder:
    """
    Responsible for building dynamic, optimized prompts based on the student's
    pedagogical profile. Applies research-backed prompt engineering techniques
    including Persona Prompting, Dynamic Context Injection, Chain-of-Thought (CoT),
    Few-Shot Exemplars, and Strict Output Formatting.

    All prompts are written in English to maximize LLM performance, while
    instructing the model to respond exclusively in Brazilian Portuguese (pt-BR).
    """

    # ── Style-to-pedagogy mapping ────────────────────────────────────────────
    _STYLE_GUIDANCE = {
        "visual": (
            "Use vivid spatial metaphors, diagrams described in text, colour-coded "
            "comparisons and hierarchical structures. Prioritise 'seeing' language: "
            "'imagine', 'picture', 'observe', 'map out'."
        ),
        "auditivo": (
            "Use rhythmic language, verbal repetition and mnemonic devices. Favour "
            "conversational tone with dialogue-like explanations. Prioritise 'hearing' "
            "language: 'listen', 'notice how', 'sounds like', 'say aloud'."
        ),
        "leitura/escrita": (
            "Use well-structured prose, numbered lists, definitions and written "
            "summaries. Prioritise precise vocabulary and textbook-style explanations "
            "with key terms highlighted."
        ),
        "cinestésico": (
            "Ground every concept in hands-on actions, real-world processes and "
            "step-by-step procedures the student can physically replicate. Prioritise "
            "'doing' language: 'build', 'run', 'try', 'feel', 'construct'."
        ),
    }

    # ── Vocabulary calibration by level ─────────────────────────────────────
    _LEVEL_GUIDANCE = {
        "iniciante": (
            "Use everyday language only. Avoid all jargon. Each new term must be "
            "immediately defined with a simple analogy. Maximum sentence complexity: "
            "short, direct sentences."
        ),
        "intermediário": (
            "Use domain vocabulary freely but explain any advanced sub-concept. "
            "Connect new ideas to things the student likely already knows."
        ),
        "avançado": (
            "Use precise technical vocabulary without over-explaining basics. "
            "Challenge the student with nuance, trade-offs, and edge cases."
        ),
    }

    def __init__(self, aluno_perfil: dict):
        self.nome   = aluno_perfil.get("nome", "Estudante")
        self.idade  = aluno_perfil.get("idade", "não informada")
        self.nivel  = aluno_perfil.get("nivel", "iniciante").lower()
        self.estilo = aluno_perfil.get("estilo_aprendizado", "visual").lower()

        # Resolved guidance strings (fallback to visual / intermediário if key not found)
        self._style_hint = self._STYLE_GUIDANCE.get(
            self.estilo, self._STYLE_GUIDANCE["visual"]
        )
        self._level_hint = self._LEVEL_GUIDANCE.get(
            self.nivel, self._LEVEL_GUIDANCE["intermediário"]
        )

    # ── Shared building blocks ───────────────────────────────────────────────

    def _persona_block(self) -> str:
        """
        Persona Prompting: establishes a stable expert identity for the model.
        Research shows assigning a specific role significantly improves response
        quality and consistency (Brown et al., 2020; Reynolds & McDonell, 2021).
        """
        return (
            "You are Dr. Maya, a world-renowned expert in Instructional Design and "
            "Cognitive Science with 20+ years of experience adapting complex subjects "
            "to diverse learners. You apply evidence-based pedagogical frameworks "
            "(Bloom's Taxonomy, Constructivism, VAK/VARK) to craft explanations that "
            "genuinely resonate with each individual student.\n\n"
        )

    def _student_context_block(self) -> str:
        """
        Dynamic Context Injection: injects all student variables so the model
        can tailor every dimension of its response.
        """
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

    def _output_language_rule(self) -> str:
        """
        Explicit language instruction placed close to the output spec to ensure
        the model does not 'forget' it by the time it generates output.
        """
        return (
            "## Language Rule (NON-NEGOTIABLE)\n"
            "You MUST write ALL content — reasoning, explanations, examples, "
            "questions, everything — exclusively in **Brazilian Portuguese (pt-BR)**. "
            "Only the JSON keys must remain in English as specified below. "
            "Violation of this rule renders the entire response invalid.\n\n"
        )

    def _json_contract(self, schema_example: str) -> str:
        """
        Strict Output Formatting: explicitly specifies the exact JSON schema.
        The 'contract' framing (Schulhoff et al., 2023) reduces hallucinations
        about format and eliminates conversational wrappers.
        """
        return (
            "## Output Contract\n"
            "Return ONLY a single, valid JSON object. No markdown fences, no "
            "preamble, no postamble, no comments. Any deviation breaks the parser.\n\n"
            f"Required schema (exact keys, no extras):\n{schema_example}\n"
        )

    # ── Public prompt builders ───────────────────────────────────────────────

    def build_conceitual_prompt(self, topico: str) -> str:
        """
        Conceptual Explanation — uses Chain-of-Thought (CoT) to force the model
        to plan its pedagogical strategy before writing the final explanation.

        Technique stack:
          • Persona Prompting
          • Dynamic Context Injection
          • Chain-of-Thought (explicit reasoning key before content key)
          • Role-specific Few-Shot hint
          • Strict JSON contract
          • Language anchoring
        """
        schema = (
            '{\n'
            '  "raciocinio": "<CoT: step-by-step pedagogical strategy in pt-BR>",\n'
            '  "conteudo": "<final conceptual explanation written directly to the student in pt-BR>"\n'
            '}'
        )

        cot_instruction = (
            "## Task: Conceptual Explanation\n"
            f"Topic: **{topico}**\n\n"
            "### Step-by-step thinking protocol (Chain-of-Thought)\n"
            "Before writing a single word of the explanation, you MUST reason through "
            "the following questions and store that reasoning in the `raciocinio` key:\n"
            f"  1. What are the 3-5 core sub-concepts that build up '{topico}'?\n"
            f"  2. What misconceptions does a {self.nivel}-level student typically hold about this topic?\n"
            f"  3. Which analogy or metaphor best fits a {self.estilo} learner aged {self.idade}?\n"
            "  4. In what order should the sub-concepts be introduced to minimise cognitive load?\n"
            "  5. What single 'aha moment' should this explanation build toward?\n\n"
            "Only after completing this reasoning, write the `conteudo` explanation "
            f"directly addressing {self.nome}. The explanation must:\n"
            "  • Open with a hook that connects to something familiar for this student\n"
            "  • Introduce sub-concepts in the order determined in step 4\n"
            "  • Include at least one concrete analogy matching the learning style\n"
            "  • End with a one-sentence 'big picture' summary\n\n"
        )

        return (
            self._persona_block()
            + self._student_context_block()
            + self._output_language_rule()
            + cot_instruction
            + self._json_contract(schema)
        )

    def build_pratico_prompt(self, topico: str) -> str:
        """
        Practical Examples — contextualises examples to the student's real life.

        Technique stack:
          • Persona Prompting
          • Dynamic Context Injection
          • Contextual Grounding (age/level-aware scenario selection)
          • Constraint-based generation (exactly 3 examples, increasing complexity)
          • Strict JSON contract
          • Language anchoring
        """
        schema = (
            '{\n'
            '  "raciocinio": "<justification for the chosen examples in pt-BR>",\n'
            '  "exemplos": [\n'
            '    "<example 1 — foundational, in pt-BR>",\n'
            '    "<example 2 — intermediate, in pt-BR>",\n'
            '    "<example 3 — advanced/challenge, in pt-BR>"\n'
            '  ]\n'
            '}'
        )

        task = (
            "## Task: Practical Examples\n"
            f"Topic: **{topico}**\n\n"
            "### Instructions\n"
            f"Generate exactly **3 practical examples** of '{topico}' for {self.nome}.\n\n"
            "Contextualisation rules:\n"
            f"  • Each example must be immediately recognisable to a {self.idade}-year-old with "
            f"{self.nivel}-level knowledge.\n"
            f"  • Match the {self.estilo} learning style: examples should involve "
            f"{'actions and processes' if 'cin' in self.estilo else 'visuals/diagrams' if self.estilo == 'visual' else 'sounds/narratives' if 'audit' in self.estilo else 'text and definitions'}.\n"
            "  • Arrange examples in **ascending difficulty**: example 1 is immediately "
            "accessible, example 3 gently stretches the student.\n"
            "  • Each example must be a self-contained mini-scenario (2-4 sentences), "
            "not just a label.\n\n"
            "In `raciocinio`, briefly justify why these specific scenarios were chosen "
            "for this student's profile.\n\n"
        )

        return (
            self._persona_block()
            + self._student_context_block()
            + self._output_language_rule()
            + task
            + self._json_contract(schema)
        )

    def build_reflexao_prompt(self, topico: str) -> str:
        """
        Reflection Questions — uses Bloom's Taxonomy to scaffold cognitive depth.

        Technique stack:
          • Persona Prompting
          • Dynamic Context Injection
          • Bloom's Taxonomy scaffolding (comprehension → analysis → synthesis/evaluation)
          • Anti-frustration constraint (level-appropriate ceiling)
          • Strict JSON contract
          • Language anchoring
        """
        bloom_ceiling = {
            "iniciante":    "comprehension and application (Bloom levels 1-3)",
            "intermediário": "analysis and evaluation (Bloom levels 4-5)",
            "avançado":     "evaluation and creation (Bloom levels 5-6)",
        }.get(self.nivel, "analysis and evaluation (Bloom levels 4-5)")

        schema = (
            '{\n'
            '  "raciocinio": "<Bloom scaffolding rationale in pt-BR>",\n'
            '  "perguntas": [\n'
            '    "<question 1 — lower cognitive demand, in pt-BR>",\n'
            '    "<question 2 — medium cognitive demand, in pt-BR>",\n'
            '    "<question 3 — higher cognitive demand, in pt-BR>"\n'
            '  ]\n'
            '}'
        )

        task = (
            "## Task: Reflection Questions\n"
            f"Topic: **{topico}**\n\n"
            "### Instructions\n"
            f"Generate exactly **3 reflection questions** about '{topico}' for {self.nome}.\n\n"
            "Design rules:\n"
            f"  • Target cognitive level ceiling: **{bloom_ceiling}**. Do NOT exceed this "
            "ceiling — questions that are too hard demotivate the student.\n"
            "  • Question 1 checks understanding (can the student explain/identify?).\n"
            "  • Question 2 probes deeper thinking (can the student compare/apply?).\n"
            "  • Question 3 challenges creatively within the ceiling "
            "(can the student evaluate/design/connect?).\n"
            f"  • All questions must be answerable by someone with {self.nivel} knowledge — "
            "avoid requiring external knowledge not covered in a standard explanation.\n"
            f"  • Frame questions in a way that suits the {self.estilo} learner "
            "(e.g., for kinesthetic: 'What would happen if you…'; "
            "for visual: 'How would you diagram…').\n\n"
            "In `raciocinio`, explain the Bloom's level targeted by each question.\n\n"
        )

        return (
            self._persona_block()
            + self._student_context_block()
            + self._output_language_rule()
            + task
            + self._json_contract(schema)
        )

    def build_visual_prompt(self, topico: str) -> str:
        """
        Visual Summary — generates a structured ASCII diagram or concept map.

        Technique stack:
          • Persona Prompting
          • Dynamic Context Injection
          • Structural scaffolding (explicit diagram type selection logic)
          • Information hierarchy constraint (max 3 levels deep)
          • Strict JSON contract
          • Language anchoring
        """
        schema = (
            '{\n'
            '  "raciocinio": "<diagram type choice and hierarchy rationale in pt-BR>",\n'
            '  "representacao_visual": "<ASCII diagram or structured concept map in pt-BR>"\n'
            '}'
        )

        task = (
            "## Task: Visual Summary\n"
            f"Topic: **{topico}**\n\n"
            "### Instructions\n"
            f"Create a **visual summary** of '{topico}' tailored to {self.nome}.\n\n"
            "Diagram selection logic — choose the MOST appropriate format:\n"
            "  • **Hierarchical tree** (└──, ├──): for topics with clear parent-child relationships\n"
            "  • **Flow diagram** (→, ⟶, [box]→[box]): for processes and sequences\n"
            "  • **Comparison table** (|col|col|): for contrasting two or more concepts\n"
            "  • **Concept map** (central node + radiating branches): for interconnected ideas\n\n"
            "Design constraints:\n"
            "  • Maximum **3 levels of depth** — deeper hierarchies overwhelm working memory.\n"
            "  • Each node/cell must contain only the **essential label** (≤ 6 words).\n"
            "  • Include a one-line **legend or title** at the top.\n"
            f"  • Since {self.nome} is a {self.estilo} learner, prioritise "
            f"{'spatial layout and colour-coded symbols' if self.estilo == 'visual' else 'sequential flow and action verbs' if 'cin' in self.estilo else 'labelled lists with definitions' if 'leit' in self.estilo else 'narrative labels with verbal cues'}.\n\n"
            "In `raciocinio`, explain which diagram type you chose and why it suits "
            "this student's profile and the topic's inherent structure.\n\n"
        )

        return (
            self._persona_block()
            + self._student_context_block()
            + self._output_language_rule()
            + task
            + self._json_contract(schema)
        )


# ── Utility ──────────────────────────────────────────────────────────────────

def json_parser(resposta_llm: str) -> dict:
    """
    Resilient JSON extractor. Attempts parsing in four passes:

      1. Direct parse          — model obeyed the output contract perfectly.
      2. Markdown fence        — model wrapped JSON in ```json ... ```.
      3. Brace-anchored search — model added prose around the JSON object.
      4. Trailing-garbage trim — model leaked extra text AFTER the closing brace
                                 (observed with Gemini: valid JSON followed by a
                                  stray sentence outside the object). This pass
                                 finds the last valid closing brace by scanning
                                 backwards, trimming everything after it.

    Raises ValueError with a descriptive message if all passes fail.
    """
    text = resposta_llm.strip()

    # Pass 1 — clean direct JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Pass 2 — strip markdown fences
    match_md = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match_md:
        try:
            return json.loads(match_md.group(1))
        except json.JSONDecodeError:
            pass

    # Pass 3 — find outermost JSON object (greedy: first { to last })
    match_braces = re.search(r'\{[\s\S]*\}', text)
    if match_braces:
        try:
            return json.loads(match_braces.group(0))
        except json.JSONDecodeError:
            pass

    # Pass 4 — trailing-garbage trim
    # Walk backwards from the last '}' and try progressively larger substrings.
    # This recovers from Gemini's habit of appending stray text after the JSON object.
    last_brace = text.rfind('}')
    while last_brace > 0:
        candidate = text[:last_brace + 1]
        first_brace = candidate.find('{')
        if first_brace != -1:
            try:
                return json.loads(candidate[first_brace:])
            except json.JSONDecodeError:
                pass
        last_brace = text.rfind('}', 0, last_brace)

    raise ValueError(
        "json_parser: All four extraction passes failed. "
        "The LLM response does not contain a parseable JSON object.\n"
        f"Raw response (first 300 chars): {text[:300]}"
    )