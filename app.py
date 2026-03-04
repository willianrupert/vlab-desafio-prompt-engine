import os
import json
from datetime import datetime
from google import genai
from google.genai import types # Adicionado para configuração da API
from dotenv import load_dotenv
from engine import PromptBuilder, json_parser

# 1. Carrega a chave da API do arquivo .env de forma segura
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Chave GEMINI_API_KEY não encontrada. Verifique o arquivo .env")

# Inicializa o cliente com o novo SDK
client = genai.Client(api_key=API_KEY)

# 2. O aluno de teste
aluno_teste = {
    "nome": "Willian",
    "idade": 23,
    "nivel": "avançado",
    "estilo_aprendizado": "cinestésico"
}

def gerar_aula():
    print("⏳ Construindo prompt personalizado...")
    builder = PromptBuilder(aluno_teste)
    
    topico = "Arquitetura de Microsserviços"
    prompt_final = builder.build_conceitual_prompt(topico)
    
    print("🤖 Enviando para o Gemini (Isso pode levar alguns segundos)...")
    try:
        # Forçando o MIME Type para application/json
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_final,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        texto_bruto = resposta.text
        # Descomentar a linha abaixo se quiser ver exatamente o que a IA está enviando antes de limpar
        # print(f"\n[DEBUG] Texto bruto recebido:\n{texto_bruto[:200]}...\n")
        
        print("🧹 Limpando e validando o JSON retornado...")
        dados_estruturados = json_parser(texto_bruto)
        
        # 3. Salvando na pasta /samples conforme o edital
        os.makedirs("samples", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"samples/aula_{timestamp}.json"
        
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados_estruturados, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Sucesso! Aula gerada e salva em: {nome_arquivo}")
        print("\n--- Resultado (Chain-of-Thought) ---")
        print(f"Raciocínio da IA: {dados_estruturados.get('raciocinio')}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar aula: {e}")
        # Se falhar novamente, o bloco abaixo vai imprimir o erro
        try:
            print(f"\n🔍 A resposta problemática enviada pelo Gemini foi:\n{resposta.text}")
        except:
            pass

if __name__ == "__main__":
    gerar_aula()