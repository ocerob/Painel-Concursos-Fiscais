import os
import datetime
import requests
from google import genai

# Configuração da API do Gemini via variáveis de ambiente do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def buscar_e_atualizar():
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    # Prompt enviado para o modelo atualizar o código mantendo a estrutura exata
    prompt = f"""
    Você é um assistente encarregado de atualizar um painel interativo semanal em HTML sobre concursos fiscais do Brasil (Receita Federal, SEFAZ e ISS/SEFIN).
    
    A data de hoje para a atualização é: {data_hoje}.
    
    Por favor, leia o arquivo index.html atual do repositório, faça uma busca/análise das movimentações recentes sobre concursos fiscais no Brasil e gere a versão ATUALIZADA do HTML mantendo EXATAMENTE o mesmo CSS, JavaScript, abas e estrutura visual.
    
    Regras obrigatorias:
    1. Retorne APENAS o código HTML completo e válido, sem explicações em markdown fora do código.
    2. Atualize os indicadores do cabeçalho, a seção de 'Novidades da Semana' com movimentações reais recentes e os cartões nas etapas corretas.
    3. Mantenha a agenda e as perspectivas dos próximos 12 meses no final da página.
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    novo_html = response.text.strip()
    
    # Remove marcações de bloco de código se o modelo as incluir
    if novo_html.startswith("```html"):
        novo_html = novo_html[7:]
    if novo_html.startswith("```"):
        novo_html = novo_html[3:]
    if novo_html.endswith("```"):
        novo_html = novo_html[:-3]
        
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(novo_html.strip())

    print("Painel atualizado com sucesso!")

if __name__ == "__main__":
    buscar_e_atualizar()
