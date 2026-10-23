import os
import datetime
import json
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def buscar_e_atualizar():
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    # Carrega os dados atuais de concursos
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            dados_atuais = f.read()
    except FileNotFoundError:
        dados_atuais = "{}"

    prompt = f"""
    Você é um assistente de atualização de dados de concursos fiscais no Brasil.
    Data de referência: {data_hoje}.
    
    Aqui estão os dados atuais em JSON:
    {dados_atuais}
    
    Por favor, pesquise mentalmente por movimentações recentes de concursos fiscais (Receita Federal, SEFAZ, ISS) e retorne APENAS um objeto JSON válido (sem blocos de código markdown, sem texto antes ou depois) atualizando a data de atualização, os números dos indicadores e as novidades da semana, mantendo a mesma estrutura.
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    texto_resposta = response.text.strip()
    
    # Limpa formatação markdown se houver
    if texto_resposta.startswith("```json"):
        texto_resposta = texto_resposta[7:]
    if texto_resposta.startswith("```"):
        texto_resposta = texto_resposta[3:]
    if texto_resposta.endswith("```"):
        texto_resposta = texto_resposta[:-3]
        
    # Salva os novos dados atualizados
    with open("dados.json", "w", encoding="utf-8") as f:
        f.write(texto_resposta.strip())

    print("Dados atualizados com sucesso via JSON!")

if __name__ == "__main__":
    buscar_e_atualizar()
