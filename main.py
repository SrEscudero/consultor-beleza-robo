# ==============================================================================
# SCRIPT DE DIAGNÓSTICO (VERSÃO DE TESTE)
# ==============================================================================
import os
from flask import Flask

# Esta parte é a mesma
app = Flask(__name__)

# Esta é a nossa rota de teste
@app.route("/")
def hello_world():
    """
    Função de teste para verificar se o serviço está no ar e se consegue ler o segredo.
    """
    print(">>> Função de diagnóstico iniciada...")
    
    # Tentamos ler o segredo, exatamente como no script principal
    api_key_secret = os.environ.get("GEMINI_API_KEY")
    
    if api_key_secret and len(api_key_secret) > 4:
        # Se encontramos a chave, mostramos apenas uma parte dela por segurança
        status_chave = f"Chave da API encontrada com sucesso! Final: ...{api_key_secret[-4:]}"
        print(status_chave)
    else:
        status_chave = "!!! ERRO: Chave da API NÃO encontrada nas variáveis de ambiente."
        print(status_chave)

    mensagem_final = f"Serviço consultor-beleza-robo está online. Status do segredo: {status_chave}"
    
    return mensagem_final, 200

# Esta parte é para o Gunicorn encontrar o 'app'
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))