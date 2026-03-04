import streamlit as st
import os
import json
import re
from fpdf import FPDF
from google import genai
from google.genai import types
from dotenv import load_dotenv
from engine import PromptBuilder, json_parser

# --- Configuração da Página ---
st.set_page_config(page_title="motor Hub V-Lab", page_icon="favicon.svg", layout="wide")

# --- CONFIGURAÇÃO DO PDF ---
class PDFVLab(FPDF):
    def header(self):
        # Fundo Roxo no Cabeçalho (Padrão V-LAB: RGB 139, 92, 246)
        self.set_fill_color(139, 92, 246)
        self.rect(0, 0, 210, 20, 'F')
        
        # Texto do Cabeçalho
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_y(6)
        self.cell(0, 8, 'VLab Hub Educacional', align='C')
        self.ln(15)

    def footer(self):
        # Rodapé a 15mm do fundo
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

def gerar_pdf(dados_aula, topico, perfil):
    pdf = PDFVLab()
    pdf.add_page()
    
    # Nova função aprimorada para limpar marcações pesadas de Markdown
    def processar_texto(texto):
        if not isinstance(texto, str):
            texto = str(texto)
        # 1. Remove os '#' de cabeçalhos do markdown (ex: ### Título vira só Título)
        texto = re.sub(r'^#+\s+', '', texto, flags=re.MULTILINE)
        # 2. Transforma caracteres problemáticos mantendo o básico (latin-1)
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # Título do Material
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(15, 23, 42) # Azul escuro
    pdf.cell(0, 10, processar_texto(f"Plano de Aula: {topico}"), ln=True)
    
    # Subtítulo (Perfil)
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 116, 139) # Cinzento
    texto_perfil = f"Aluno(a): {perfil['nome']} | Idade: {perfil['idade']} anos | Nível: {perfil['nivel']} | Estilo: {perfil['estilo_aprendizado']}"
    pdf.cell(0, 6, processar_texto(texto_perfil), ln=True)
    pdf.ln(8)

    # Raciocínio da IA
    if "raciocinio" in dados_aula:
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(139, 92, 246) # Roxo
        pdf.cell(0, 8, processar_texto("Raciocínio Pedagógico:"), ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)
        
        texto_raciocinio = processar_texto(dados_aula["raciocinio"])
        try:
            # Ativando o markdown aqui também!
            pdf.multi_cell(0, 6, txt=texto_raciocinio, markdown=True)
        except Exception:
            # Fallback de segurança se o markdown vier quebrado
            texto_raciocinio_limpo = texto_raciocinio.replace('**', '').replace('*', '')
            pdf.multi_cell(0, 6, txt=texto_raciocinio_limpo)
            
        pdf.ln(5)

    # Conteúdo Principal
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, processar_texto("Conteúdo da Aula:"), ln=True)
    
    # Reseta a fonte para o texto base
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    # Extrai o conteúdo independentemente do formato
    conteudo_texto = dados_aula.get("conteudo") or dados_aula.get("exemplos") or dados_aula.get("perguntas") or dados_aula.get("representacao_visual") or json.dumps(dados_aula, indent=2, ensure_ascii=False)
    
    # Formata listas e dicionários
    if isinstance(conteudo_texto, list):
        conteudo_texto = "\n".join([f"- {item}" for item in conteudo_texto])
    elif isinstance(conteudo_texto, dict):
        conteudo_texto = json.dumps(conteudo_texto, indent=2, ensure_ascii=False)

    texto_final = processar_texto(conteudo_texto)
    
    # Tenta usar o markdown=True para converter ** em negrito e * em itálico
    try:
        # A mágica acontece neste parâmetro: markdown=True
        pdf.multi_cell(0, 6, txt=texto_final, markdown=True)
    except Exception:
        # Fallback de segurança: se o markdown da IA vier quebrado, tira os asteriscos e imprime liso
        texto_limpo = texto_final.replace('**', '').replace('*', '')
        pdf.multi_cell(0, 6, txt=texto_limpo)
    
    return bytes(pdf.output())

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
                
                # --- Botões de Download (JSON e PDF) ---
                st.markdown("<br>", unsafe_allow_html=True)
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    json_string = json.dumps(resultado, indent=4, ensure_ascii=False)
                    st.download_button(
                        label="📥 Baixar Resultado (JSON)",
                        file_name=f"aula_{topico_input.replace(' ', '_').lower()}.json",
                        mime="application/json",
                        data=json_string,
                        use_container_width=True
                    )
                
                with col_down2:
                    pdf_bytes = gerar_pdf(resultado, topico_input, aluno_atual)
                    st.download_button(
                        label="📄 Baixar Resultado (PDF)",
                        file_name=f"aula_{topico_input.replace(' ', '_').lower()}.pdf",
                        mime="application/pdf",
                        data=pdf_bytes,
                        use_container_width=True,
                        type="primary"
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