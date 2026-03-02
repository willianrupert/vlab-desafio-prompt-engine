import json
import re

class PromptBuilder:
    """
    Classe responsável por construir prompts dinâmicos e otimizados baseados 
    no perfil pedagógico do aluno.
    """
    def __init__(self, aluno_perfil: dict):
        self.nome = aluno_perfil.get("nome", "Estudante")
        self.idade = aluno_perfil.get("idade", "Não informada")
        self.nivel = aluno_perfil.get("nivel", "Iniciante")
        self.estilo = aluno_perfil.get("estilo_aprendizado", "Visual")

    def _get_base_context(self) -> str:
        """
        Aplica a técnica de 'Persona Prompting' e 'Context Setting'.
        """
        return (
            f"Você é um professor experiente em Pedagogia e Design Instrucional.\n"
            f"Seu objetivo é criar um material educacional altamente personalizado para o seguinte aluno:\n"
            f"- Nome: {self.nome}\n"
            f"- Idade: {self.idade} anos\n"
            f"- Nível de conhecimento: {self.nivel}\n"
            f"- Estilo de aprendizado preferido: {self.estilo}\n\n"
        )

    def build_conceitual_prompt(self, topico: str) -> str:
        """Monta o prompt para a Explicação Conceitual."""
        base_context = self._get_base_context()
        tarefa = (
            f"Tarefa: Crie uma explicação conceitual sobre o tópico '{topico}'.\n\n"
            f"Diretrizes Pedagógicas:\n"
            f"1. Adapte rigorosamente o vocabulário para a idade do aluno.\n"
            f"2. Utilize metáforas ou analogias que combinem com o estilo de aprendizado {self.estilo}.\n"
            f"3. Pense passo a passo (Chain-of-Thought) sobre como desconstruir este conceito antes de redigir a explicação final.\n\n"
            f"Formato de Saída Obrigatório:\n"
            f"Retorne EXCLUSIVAMENTE um objeto JSON válido, sem formatação markdown e sem nenhum texto de introdução ou conclusão. O JSON deve conter estritamente as seguintes chaves:\n"
            f'{{\n'
            f'  "raciocinio": "Seu pensamento passo a passo sobre a estratégia pedagógica adotada",\n'
            f'  "conteudo": "A explicação conceitual final, redigida diretamente para o aluno"\n'
            f'}}\n'
        )
        return base_context + tarefa

    def build_pratico_prompt(self, topico: str) -> str:
        """Monta o prompt para os Exemplos Práticos."""
        base_context = self._get_base_context()
        tarefa = (
            f"Tarefa: Crie exemplos práticos sobre o tópico '{topico}'.\n\n"
            f"Diretrizes Pedagógicas:\n"
            f"1. Os exemplos devem ser altamente contextualizados para a realidade de alguém com {self.idade} anos e com o nível {self.nivel}.\n"
            f"2. Pense passo a passo (Chain-of-Thought) sobre quais as situações do dia a dia que fazem mais sentido para este perfil de aluno.\n\n"
            f"Formato de Saída Obrigatório:\n"
            f"Retorne EXCLUSIVAMENTE um objeto JSON válido, sem formatação markdown. O JSON deve conter estritamente as seguintes chaves:\n"
            f'{{\n'
            f'  "raciocinio": "Justificação da escolha destes exemplos para o perfil indicado",\n'
            f'  "exemplos": ["Exemplo prático 1", "Exemplo prático 2", "Exemplo prático 3"]\n'
            f'}}\n'
        )
        return base_context + tarefa

    def build_reflexao_prompt(self, topico: str) -> str:
        """Monta o prompt para as Perguntas de Reflexão."""
        base_context = self._get_base_context()
        tarefa = (
            f"Tarefa: Elabore perguntas de reflexão sobre o tópico '{topico}'.\n\n"
            f"Diretrizes Pedagógicas:\n"
            f"1. Crie 3 perguntas que estimulem o pensamento crítico, perfeitamente adequadas ao nível de conhecimento {self.nivel}.\n"
            f"2. Pense passo a passo (Chain-of-Thought) sobre como desafiar cognitivamente o aluno sem criar frustração, respeitando o seu estilo {self.estilo}.\n\n"
            f"Formato de Saída Obrigatório:\n"
            f"Retorne EXCLUSIVAMENTE um objeto JSON válido, sem formatação markdown. O JSON deve conter as seguintes chaves:\n"
            f'{{\n'
            f'  "raciocinio": "Análise pedagógica sobre a formulação destas perguntas específicas",\n'
            f'  "perguntas": ["Pergunta de reflexão 1", "Pergunta de reflexão 2", "Pergunta de reflexão 3"]\n'
            f'}}\n'
        )
        return base_context + tarefa

    def build_visual_prompt(self, topico: str) -> str:
        """Monta o prompt para o Resumo Visual."""
        base_context = self._get_base_context()
        tarefa = (
            f"Tarefa: Crie um resumo visual sobre o tópico '{topico}'.\n\n"
            f"Diretrizes Pedagógicas:\n"
            f"1. O resumo deve ser uma representação visual (como um diagrama ou mapa mental utilizando arte ASCII) ou uma descrição visual estruturada, focando no estilo de aprendizado {self.estilo}.\n"
            f"2. Pense passo a passo (Chain-of-Thought) sobre como hierarquizar a informação visualmente para maximizar a retenção do conhecimento.\n\n"
            f"Formato de Saída Obrigatório:\n"
            f"Retorne EXCLUSIVAMENTE um objeto JSON válido, sem formatação markdown. O JSON deve conter as seguintes chaves:\n"
            f'{{\n'
            f'  "raciocinio": "Explicação da estrutura visual escolhida e como esta auxilia o aluno",\n'
            f'  "representacao_visual": "O diagrama em arte ASCII ou a descrição estruturada do mapa mental"\n'
            f'}}\n'
        )
        return base_context + tarefa


def json_parser(resposta_llm: str) -> dict:
    """
    Função de resiliência para limpar a resposta do LLM e extrair apenas o JSON.
    """
    try:
        return json.loads(resposta_llm)
    except json.JSONDecodeError:
        pass
    
    match_markdown = re.search(r'```(?:json)?\s*(.*?)\s*```', resposta_llm, re.DOTALL)
    if match_markdown:
        try:
            return json.loads(match_markdown.group(1))
        except json.JSONDecodeError:
            pass
            
    match_chaves = re.search(r'\{.*\}', resposta_llm, re.DOTALL)
    if match_chaves:
        try:
            return json.loads(match_chaves.group(0))
        except json.JSONDecodeError:
            pass
            
    raise ValueError("Falha crítica: Não foi possível extrair um JSON válido da resposta do LLM.")