from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importando o motor de engine.py
from engine import PromptBuilder, json_parser 

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Chave GEMINI_API_KEY não encontrada no .env")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="V-LAB Motor de Prompts API")

# Configuração de CORS: Essencial para o Vercel acessar esse servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://edu.rlight.com.br", "http://localhost:5173"], # Permite prod e dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados esperados na requisição do frontend
class Aluno(BaseModel):
    nome: str
    idade: int
    nivel: str
    estilo_aprendizado: str

class GerarAulaRequest(BaseModel):
    aluno: Aluno
    topico: str
    tipo_conteudo: str

@app.post("/gerar_aula")
async def gerar_aula(req: GerarAulaRequest):
    # Transforma o Pydantic model em dict para o PromptBuilder
    builder = PromptBuilder(req.aluno.dict())
    
    # Roteamento do tipo de prompt baseado na requisição
    if req.tipo_conteudo == "Conceitual":
        prompt = builder.build_conceitual_prompt(req.topico)
    elif req.tipo_conteudo == "Prático":
        prompt = builder.build_pratico_prompt(req.topico)
    elif req.tipo_conteudo == "Reflexão":
        prompt = builder.build_reflexao_prompt(req.topico)
    else:
        prompt = builder.build_visual_prompt(req.topico)

    try:
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        
        # Limpa e valida o JSON usando a sua função de resiliência
        dados_estruturados = json_parser(resposta.text)
        return dados_estruturados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))