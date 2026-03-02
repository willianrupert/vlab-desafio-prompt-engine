import pytest
from engine import PromptBuilder, json_parser

ALUNO_MOCK = {
    "nome": "Willian",
    "idade": 22,
    "nivel": "avançado",
    "estilo_aprendizado": "cinestésico"
}

def test_injecao_de_contexto_no_prompt():
    builder = PromptBuilder(ALUNO_MOCK)
    prompt_gerado = builder.build_conceitual_prompt(topico="Machine Learning")
    
    assert "Willian" in prompt_gerado
    assert "22 anos" in prompt_gerado
    assert "cinestésico" in prompt_gerado
    assert "Machine Learning" in prompt_gerado

def test_diretriz_chain_of_thought_presente():
    builder = PromptBuilder(ALUNO_MOCK)
    prompt_gerado = builder.build_conceitual_prompt(topico="Física")
    
    assert "passo a passo" in prompt_gerado.lower() or "step-by-step" in prompt_gerado.lower()

def test_validacao_de_formato_json():
    resposta_suja_da_ia = '''
    Claro, aqui está o JSON solicitado:
    ```json
    {"raciocinio": "Pensei assim...", "conteudo": "A resposta é..."}
    ```
    Espero que ajude!
    '''
    resultado_limpo = json_parser(resposta_suja_da_ia)
    
    assert type(resultado_limpo) == dict
    assert "raciocinio" in resultado_limpo

def test_metodos_adicionais_existem():
    builder = PromptBuilder(ALUNO_MOCK)
    
    assert hasattr(builder, 'build_conceitual_prompt')
    assert hasattr(builder, 'build_pratico_prompt')
    assert hasattr(builder, 'build_reflexao_prompt')
    assert hasattr(builder, 'build_visual_prompt')