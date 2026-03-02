import streamlit as st
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from engine import PromptBuilder, json_parser

# --- Configuração da Página ---
st.set_page_config(page_title="V-LAB | Motor de Prompts", page_icon="🎓", layout="wide")

# --- Autenticação da API ---
@st.cache_resource
def get_genai_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Chave GEMINI_API_KEY não encontrada no arquivo .env!")
        st.stop()
    return genai.Client(api_key=api_key)

client = get_genai_client()

# --- Função de Geração com Cache ---
@st.cache_data(show_spinner=False)
def gerar_conteudo_ia(_aluno, topico, tipo_conteudo, prompt_generico=False):
    builder = PromptBuilder(_aluno)
    
    # Se for o teste A/B, usa um prompt burro/simples
    if prompt_generico:
        prompt = f"Me explique sobre {topico}. Retorne em JSON no formato {{\"conteudo\": \"sua explicacao\"}}"
    else:
        if tipo_conteudo == "Conceitual":
            prompt = builder.build_conceitual_prompt(topico)
        elif tipo_conteudo == "Prático":
            prompt = builder.build_pratico_prompt(topico)
        elif tipo_conteudo == "Reflexão":
            prompt = builder.build_reflexao_prompt(topico)
        else:
            prompt = builder.build_visual_prompt(topico)

    try:
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        texto_bruto = resposta.text
        
        # Tenta parsear. Se der erro, retorna o texto bruto para debug na tela
        try:
            return json_parser(texto_bruto)
        except Exception:
            return {"erro_critico": True, "raw": texto_bruto}
            
    except Exception as e:
        return {"erro_critico": True, "raw": str(e)}

# --- Interface Visual (Sidebar) ---
st.sidebar.markdown("# 🎓 V-LAB Hub")
st.sidebar.caption("Motor de Engenharia de Prompts v1.0")
st.sidebar.divider()

st.sidebar.markdown("### 👤 Perfil do Aluno")

# Feature Inovadora: Quiz de Perfil
with st.sidebar.expander("❓ Não sabe seu estilo? Descubra!"):
    st.markdown("<small>Responda para inferir seu estilo:</small>", unsafe_allow_html=True)
    resposta_quiz = st.radio(
        "Como você entende melhor um conceito novo?",
        ["Lendo um manual", "Ouvindo uma explicação", "Testando na prática", "Vendo um gráfico"],
        label_visibility="collapsed"
    )
    estilo_inferido = "Leitura/Escrita"
    if "prática" in resposta_quiz: estilo_inferido = "Cinestésico"
    if "gráfico" in resposta_quiz: estilo_inferido = "Visual"
    if "Ouvindo" in resposta_quiz: estilo_inferido = "Auditivo"
    
    st.info(f"💡 Estilo sugerido: **{estilo_inferido}**")

nome_aluno = st.sidebar.text_input("Nome", "Willian")
idade_aluno = st.sidebar.number_input("Idade", min_value=5, max_value=100, value=22)
nivel_aluno = st.sidebar.selectbox("Nível de Conhecimento", ["Iniciante", "Intermediário", "Avançado"], index=2)
estilo_aluno = st.sidebar.selectbox("Estilo de Aprendizado", ["Visual", "Auditivo", "Leitura/Escrita", "Cinestésico"], index=3)

aluno_atual = {
    "nome": nome_aluno,
    "idade": idade_aluno,
    "nivel": nivel_aluno,
    "estilo_aprendizado": estilo_aluno
}

# --- Área Principal ---
st.title("Hub Inteligente de Geração Pedagógica 🤖")
st.markdown("Sistema avançado de geração de conteúdo utilizando *Chain-of-Thought* e *Persona Prompting*.")

aba_gerador, aba_comparacao = st.tabs(["📚 Gerador de Aulas", "⚖️ Laboratório (Teste A/B)"])

# ================= ABA 1: GERADOR =================
with aba_gerador:
    st.markdown("### O que vamos ensinar hoje?")
    col1, col2 = st.columns([3, 1])
    with col1:
        topico_input = st.text_input("Digite o tópico:", "Arquitetura de Microsserviços", key="topico_gerador")
    with col2:
        tipo_input = st.selectbox("Tipo de Conteúdo:", ["Conceitual", "Prático", "Reflexão", "Visual"])

    if st.button("🚀 Gerar Aula Personalizada", use_container_width=True, type="primary"):
        with st.spinner("🧠 Estruturando raciocínio pedagógico (CoT)..."):
            resultado = gerar_conteudo_ia(aluno_atual, topico_input, tipo_input)
            
            if resultado.get("erro_critico"):
                st.error("A IA gerou um formato inválido. Veja a saída bruta abaixo para debugar:")
                st.code(resultado.get("raw"), language="json")
            else:
                st.success("Conteúdo gerado com sucesso!")
                
                with st.expander("👁️ Ver Raciocínio da IA (Chain-of-Thought)", expanded=False):
                    st.info(resultado.get("raciocinio", "Raciocínio não retornado."))
                
                st.markdown("### Resultado Final")
                conteudo_final = {k: v for k, v in resultado.items() if k != "raciocinio"}
                st.write(conteudo_final.get("conteudo") or conteudo_final.get("exemplos") or conteudo_final.get("perguntas") or conteudo_final.get("representacao_visual") or conteudo_final)
                
                # Feature: Download JSON
                json_string = json.dumps(resultado, indent=4, ensure_ascii=False)
                st.download_button(
                    label="📥 Baixar Resultado (JSON)",
                    file_name=f"aula_{topico_input.replace(' ', '_').lower()}.json",
                    mime="application/json",
                    data=json_string
                )

# ================= ABA 2: TESTE A/B =================
with aba_comparacao:
    st.markdown("### Comparativo de Qualidade de Prompts")
    st.write("Veja a diferença entre um prompt genérico e o nosso motor de prompt otimizado.")
    
    topico_ab = st.text_input("Tópico para o Teste A/B:", "Física Quântica", key="topico_ab")
    
    if st.button("⚖️ Executar Teste A/B", use_container_width=True):
        col_esq, col_dir = st.columns(2)
        
        with col_esq:
            st.markdown("#### ❌ Prompt Genérico (Comum)")
            with st.spinner("Gerando..."):
                res_ruim = gerar_conteudo_ia(aluno_atual, topico_ab, "Conceitual", prompt_generico=True)
                if res_ruim.get("erro_critico"):
                    st.code(res_ruim.get("raw"))
                else:
                    st.write(res_ruim.get("conteudo", res_ruim))
                    
        with col_dir:
            st.markdown("#### ✅ Prompt Otimizado (V-LAB Engine)")
            with st.spinner("Gerando com Contexto e CoT..."):
                res_bom = gerar_conteudo_ia(aluno_atual, topico_ab, "Conceitual", prompt_generico=False)
                if res_bom.get("erro_critico"):
                    st.code(res_bom.get("raw"))
                else:
                    st.success("Nota-se a adaptação ao nível e idade do aluno.")
                    st.write(res_bom.get("conteudo", res_bom))