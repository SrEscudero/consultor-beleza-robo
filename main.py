import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from flask import Flask

# ==============================================================================
# CONFIGURAÇÃO CENTRAL DO ROBÔ
# ==============================================================================
# Todas as suas configurações agora vivem aqui, fáceis de achar e modificar.
FONTES_BELEZA = [
    "https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa"
]
KEYWORDS_BELEZA = [
    'cosméticos', 'salão de beleza', 'procedimento estético', 'sanitária',
    'formol', 'beleza', 'estética', 'produto saneante', 'autoclave',
    'vigilância sanitária', 'micropigmentação', 'cabeleireiro', 'manicure'
]

# ==============================================================================
# DEFINIÇÃO DO APLICATIVO FLASK
# ==============================================================================
app = Flask(__name__)

# ==============================================================================
# FUNÇÕES DO ROBÔ
# ==============================================================================
def coletar_noticias(fontes, palavras_chave, numero_de_paginas=3):
    """Navega por uma lista de fontes, extraindo notícias relevantes."""
    conteudo_relevante = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f">>> Iniciando varredura em {len(fontes)} fontes...")
    for url_base in fontes:
        print(f"  - Varrendo fonte: {url_base}")
        try:
            if "gov.br" in url_base:
                for i in range(numero_de_paginas):
                    start_index = i * 20
                    url_pagina = f"{url_base}?b_start:int={start_index}"
                    print(f"    - Lendo página {i+1}...")
                    response = requests.get(url_pagina, headers=headers, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    resultados = soup.find_all('article', class_='tileItem')
                    if not resultados: break
                    for noticia in resultados:
                        titulo = noticia.find('h2', class_='tileHeadline').get_text(strip=True).lower() if noticia.find('h2') else ''
                        descricao = noticia.find('span', class_='description').get_text(strip=True).lower() if noticia.find('span', 'description') else ''
                        if any(palavra in titulo or palavra in descricao for palavra in palavras_chave):
                            titulo_original = noticia.find('h2', class_='tileHeadline').get_text(strip=True)
                            descricao_original = noticia.find('span', class_='description').get_text(strip=True)
                            url_original = noticia.find('a')['href'] if noticia.find('a') else 'N/A'
                            conteudo_relevante += f"Título: {titulo_original}\nDescrição: {descricao_original}\nLink: {url_original}\n\n"
        except Exception as e:
            print(f"!!! Falha ao processar a fonte {url_base}: {e}")
            continue
    return conteudo_relevante.strip() if conteudo_relevante else None

def analisar_conteudo(texto):
    """Envia o conteúdo para o Gemini e retorna a análise em texto puro."""
    
    prompt_mestre_profissional = f"""
    **PERSONA:** Você é um consultor de estratégia e risco para o mercado da beleza no Brasil, preparando um briefing executivo para o dono de um salão. Seu tom é objetivo, direto e acionável.

    **CONTEXTO:** Analise o compilado de notícias brutas abaixo, extraídas de fontes governamentais e do setor. Sua missão é filtrar o ruído e transformar estas informações em inteligência de negócios clara e valiosa. Se o texto de entrada for None ou vazio, informe que não há atualizações relevantes.

    **NOTÍCIAS BRUTAS PARA ANÁLISE:**
    ---
    {texto}
    ---

    **TAREFA:** Estruture sua resposta EXATAMENTE no formato abaixo, com sub-tópicos para 'Impacto' e 'Ação'. Para cada categoria, avalie o impacto potencial no negócio (Baixo, Médio, Alto).

    **1. ALERTA REGULATÓRIO 🚨 (Segurança e Conformidade)**
    - **Resumo:** [Descreva a nova lei, fiscalização ou proibição de forma direta.]
    - **Impacto Potencial:** [Avalie como Alto, Médio ou Baixo e explique o porquê (ex: Risco de multa, interdição, segurança do cliente).]
    - **Plano de Ação Imediato:** [Liste em passos numerados (1., 2., 3.) o que o dono do salão deve fazer AGORA.]

    **2. GESTÃO & FINANÇAS 💰 (Operação e Lucratividade)**
    - **Resumo:** [Descreva a notícia sobre impostos, leis trabalhistas, custos de insumos, ou gestão.]
    - **Impacto Potencial:** [Avalie como Alto, Médio ou Baixo e explique o porquê (ex: Impacto na margem de lucro, necessidade de treinamento, mudança em contratos).]
    - **Plano de Ação Imediato:** [Liste em passos numerados o que o dono deve fazer.]

    **3. TENDÊNCIAS & OPORTUNIDADES 💡 (Inovação e Crescimento)**
    - **Resumo:** [Descreva a nova tendência, técnica, produto ou comportamento de consumo.]
    - **Impacto Potencial:** [Avalie como Alto, Médio ou Baixo e explique o porquê (ex: Potencial de nova fonte de receita, diferenciação de mercado, atração de novos clientes).]
    - **Plano de Ação Imediato:** [Liste em passos numerados como o salão pode explorar essa oportunidade.]
    """
    
    print("\n>>> Enviando texto para análise avançada do Gemini...")
    try:
        # LINHA CORRIGIDA/ADICIONADA:
        modelo = genai.GenerativeModel('gemini-1.5-flash')
        response = modelo.generate_content(prompt_mestre_profissional)
        return response.text
    except Exception as e:
        return f"!!! Ocorreu um erro ao chamar a API do Gemini: {e}"

@app.route("/")
def executar_robo():
    """Ponto de entrada do Cloud Run que orquestra a execução."""
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        msg_erro = "!!! ERRO CRÍTICO: Chave API não encontrada como variável de ambiente."
        print(msg_erro)
        return msg_erro, 500
    genai.configure(api_key=API_KEY)

    print("Iniciando a execução do robô...")
    texto_noticias = coletar_noticias(FONTES_BELEZA, KEYWORDS_BELEZA)
    
    if texto_noticias:
        resultado_analise = analisar_conteudo(texto_noticias)
        print("Execução finalizada com sucesso. Relatório gerado.")
        return f"Relatório gerado com sucesso:\n{resultado_analise}", 200
    else:
        msg = analisar_conteudo(None) # Pede para a IA gerar a mensagem de "céu limpo"
        print(msg)
        return msg, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
