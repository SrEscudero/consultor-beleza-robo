# -*- coding: utf-8 -*-
# ==============================================================================
# SCRIPT DE INTELIGÊNCIA DE MERCADO (VERSÃO 4.0 - MULTI-FONTE)
# ARQUITETO: SEU MENTOR
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import google.generativeai as genai

# ==============================================================================
# ARSENAL DE INTELIGÊNCIA: FONTES E PALAVRAS-CHAVE
# ==============================================================================

# Fontes de Dados para Vigilância
FONTES_REGULAMENTACAO = [
    "https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa",
    # Adicione aqui o link para o Diário Oficial do seu estado
]
FONTES_NOTICIAS_SETOR = [
    "https://beautyfair.com.br/negocios-e-noticias/",
    "https://esteticaemercado.com.br/",
    "https://www.cabeleireiros.com/"
]

# Palavras-Chave Estratégicas
KEYWORDS_REGULAMENTACAO = [
    'vigilância sanitária', 'licença de funcionamento', 'multa anvisa',
    'descarte de resíduos', 'lei do salão-parceiro', 'norma ABNT salão',
    'fiscalização salão', 'produto falsificado', 'proibição de ativo',
    'cosmético irregular', 'formaldeído', 'autoclave norma'
]
KEYWORDS_NEGOCIOS_E_TENDENCIAS = [
    'piso salarial cabeleireiro', 'gestão de salão', 'software para salão',
    'aumento de preço beleza', 'impostos salão de beleza', 'beleza limpa',
    'tendência coloração', 'skincare', 'terapia capilar', 'mercado de estética'
]


# ==============================================================================
# FUNÇÕES DO ROBÔ
# ==============================================================================

def coletar_noticias(lista_urls, palavras_chave, numero_de_paginas=2):
    """Navega por uma lista de URLs, extraindo notícias relevantes."""
    conteudo_total = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f">>> Iniciando varredura em {len(lista_urls)} fontes...")

    for url_base in lista_urls:
        print(f"\n  - Varrendo fonte: {url_base}")
        try:
            # Lógica de extração para o padrão GOV.BR
            if "gov.br" in url_base:
                for i in range(numero_de_paginas):
                    start_index = i * 20
                    url_pagina = f"{url_base}?b_start:int={start_index}"
                    
                    response = requests.get(url_pagina, headers=headers, timeout=20)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    resultados = soup.find_all('article', class_='tileItem')

                    if not resultados: break

                    for noticia in resultados:
                        titulo = noticia.find('h2', class_='tileHeadline').get_text(strip=True).lower() if noticia.find('h2') else ''
                        descricao = noticia.find('span', class_='description').get_text(strip=True).lower() if noticia.find('span', 'description') else ''
                        
                        if any(palavra in titulo or palavra in descricao for palavra in palavras_chave):
                            titulo_original = noticia.find('h2', class_='tileHeadline').get_text(strip=True)
                            url_original = noticia.find('a')['href'] if noticia.find('a') else 'N/A'
                            conteudo_total += f"Fonte: {url_base}\nTítulo: {titulo_original}\nLink: {url_original}\n\n"
            
            # AVISO DE ARQUITETO: Para cada novo tipo de site (ex: beautyfair.com.br),
            # você precisará adicionar uma nova lógica de extração aqui (um novo 'elif').
            # Cada site tem uma estrutura HTML diferente.
            # else if "beautyfair.com.br" in url_base:
            #    # ... código de scraping específico para a Beauty Fair ...
            #    pass

        except Exception as e:
            print(f"!!! Falha ao processar a fonte {url_base}: {e}")
            continue # Pula para a próxima fonte em caso de erro

    return conteudo_total.strip() if conteudo_total else None


def analisar_conteudo(texto):
    """Envia o conteúdo para o Gemini e retorna a análise estratégica."""
    prompt_mestre = f"""
    **Análise Estratégica para Donos de Salão de Beleza**
    **Contexto:** Você é um consultor de negócios sênior. Analise o seguinte compilado de notícias de diversas fontes. Seu objetivo é traduzir estas informações em insights práticos e acionáveis.
    **Notícias para Análise:**
    ---
    {texto}
    ---
    **Sua Tarefa:** Estruture sua resposta EXATAMENTE nos seguintes tópicos. Se não houver informação, escreva "Nenhuma informação relevante encontrada.".
    **1. Alertas Regulatórios Urgentes 🚨:**
       - Identifique qualquer nova norma da ANVISA ou lei que exija ação imediata para evitar multas.
       - **Ação Recomendada:** Descreva um passo a passo claro.
    **2. Gestão e Finanças do Salão 💰:**
       - Extraia informações sobre impostos, leis trabalhistas ou custos que impactem o lucro.
       - **Ação Recomendada:** Sugira ações de gestão.
    **3. Tendências e Oportunidades de Mercado 💡:**
       - Identifique novas tendências, produtos ou técnicas que possam gerar mais receita.
       - **Ação Recomendada:** Sugira como o salão pode ser pioneiro e capitalizar a tendência.
    """
    print("\n>>> Enviando compilado de notícias para análise do Gemini...")
    try:
        modelo = genai.GenerativeModel('gemini-1.5-flash')
        response = modelo.generate_content(prompt_mestre)
        return response.text
    except Exception as e:
        return f"!!! Ocorreu um erro ao chamar a API do Gemini: {e}"

def main():
    """Função principal que orquestra a execução do script."""
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")

    if not API_KEY:
        print("!!! ERRO CRÍTICO: Chave API não encontrada. Verifique seu arquivo .env")
        return

    genai.configure(api_key=API_KEY)

    # Combina todas as palavras-chave em uma única lista para a busca
    todas_as_keywords = KEYWORDS_REGULAMENTACAO + KEYWORDS_NEGOCIOS_E_TENDENCIAS
    # Por enquanto, vamos focar nas fontes de regulamentação que são mais confiáveis
    fontes_para_vigiar = FONTES_REGULAMENTACAO

    texto_noticias = coletar_noticias(fontes_para_vigiar, todas_as_keywords)
    print("-" * 50)

    if texto_noticias:
        resultado_analise = analisar_conteudo(texto_noticias)
        print("\n>>> INFORME DE INTELIGÊNCIA ESTRATÉGICA:\n")
        print(resultado_analise)
    else:
        print("Nenhuma notícia relevante para o setor de beleza encontrada hoje nas fontes vigiadas.")

if __name__ == "__main__":
    main()