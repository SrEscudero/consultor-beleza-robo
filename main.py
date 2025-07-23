# ==============================================================================
# SCRIPT DE INTELIGÊNCIA DE MERCADO (VERSÃO 4.1 - CORRIGIDA PARA CLOUD RUN)
# ==============================================================================

import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from flask import Flask

# --- PASSO CRÍTICO: DEFINIÇÃO DO APLICATIVO 'APP' ---
# Esta linha PRECISA estar aqui, no início do script. É o que o Gunicorn procura.
app = Flask(__name__)

# ==============================================================================
# FUNÇÕES DO ROBÔ (COLE SUAS FUNÇÕES JÁ TESTADAS AQUI)
# ==============================================================================

def coletar_noticias_anvisa(palavras_chave, numero_de_paginas=3):
    """Navega pelas páginas de notícias da ANVISA via GET e usa BeautifulSoup."""
    url_base = "https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa"
    conteudo_relevante = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f">>> Iniciando varredura em {numero_de_paginas} páginas da ANVISA...")
    try:
        for i in range(numero_de_paginas):
            start_index = i * 20
            url_pagina = f"{url_base}?b_start:int={start_index}"
            print(f"  - Lendo página {i+1}...")

            response = requests.get(url_pagina, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            resultados = soup.find_all('article', class_='tileItem')

            if not resultados: break

            for noticia in resultados:
                titulo_tag = noticia.find('h2', class_='tileHeadline')
                descricao_tag = noticia.find('span', class_='description')
                url_tag = noticia.find('a')

                titulo = titulo_tag.get_text(strip=True).lower() if titulo_tag else ''
                descricao = descricao_tag.get_text(strip=True).lower() if descricao_tag else ''
                
                if any(palavra in titulo or palavra in descricao for palavra in palavras_chave):
                    titulo_original = noticia.find('h2', class_='tileHeadline').get_text(strip=True)
                    descricao_original = noticia.find('span', class_='description').get_text(strip=True)
                    url_original = url_tag['href'] if url_tag else 'N/A'
                    
                    conteudo_relevante += f"Título: {titulo_original}\nDescrição: {descricao_original}\nLink: {url_original}\n\n"
        
        return conteudo_relevante.strip() if conteudo_relevante else None
    except Exception as e:
        print(f"!!! Ocorreu um erro inesperado durante a coleta: {e}")
        return None

def analisar_conteudo(texto):
    """Envia o conteúdo para o Gemini e retorna a análise em texto puro."""
    prompt_mestre = f"""
    **Análise Estratégica para Donos de Salão de Beleza**
    **Contexto:** Você é um consultor de negócios especialista no setor de beleza. Analise o seguinte compilado de notícias recentes da ANVISA. Seu objetivo é traduzir estas informações em insights práticos.
    **Notícias para Análise:**
    ---
    {texto}
    ---
    **Sua Tarefa:** Estruture sua resposta EXATAMENTE nos seguintes tópicos. Se não houver informação, escreva "Nenhuma informação relevante encontrada.".
    **1. Alertas Regulatórios 🚨:**
       - Identifique qualquer nova norma que exija ação.
       - **Ação Recomendada:** Descreva um passo a passo claro.
    **2. Gestão & Finanças 💰:**
       - Extraia informações que impactem custos ou gestão.
       - **Ação Recomendada:** Sugira ações de gestão.
    **3. Tendências & Oportunidades 💡:**
       - Identifique insights que possam se tornar oportunidades.
       - **Ação Recomendada:** Sugira como capitalizar a tendência.
    """
    print("\n>>> Enviando texto para análise do Gemini...")
    try:
        modelo = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_mestre)
        return response.text
    except Exception as e:
        return f"!!! Ocorreu um erro ao chamar a API do Gemini: {e}"

# ==============================================================================
# PONTO DE ENTRADA DO CLOUD RUN
# ==============================================================================
@app.route("/")
def executar_robo():
    """Esta é a função que o Cloud Run vai executar quando receber um chamado."""
    
    API_KEY = os.environ.get("GEMINI_API_KEY")

    if not API_KEY:
        msg_erro = "!!! ERRO CRÍTICO: Chave API não encontrada como variável de ambiente."
        print(msg_erro)
        return msg_erro, 500

    genai.configure(api_key=API_KEY)

    palavras_chave_beleza = [
        'cosméticos', 'salão de beleza', 'procedimento estético', 'sanitária',
        'formol', 'beleza', 'estética', 'produto saneante', 'autoclave'
    ]

    print("Iniciando a execução do robô...")
    texto_noticias = coletar_noticias_anvisa(palavras_chave_beleza, numero_de_paginas=3)
    
    if texto_noticias:
        resultado_analise = analisar_conteudo(texto_noticias)
        print("Execução finalizada com sucesso. Relatório gerado.")
        return f"Relatório gerado com sucesso:\n{resultado_analise}", 200
    else:
        msg = "Nenhuma notícia relevante encontrada hoje."
        print(msg)
        return msg, 200

# Esta parte SÓ roda no seu computador local, para testes. O Cloud Run ignora isso.
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))