import os
import datetime
import json
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def buscar_e_atualizar():
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    # Carrega a base completa de dados atual
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            dados_atuais = f.read()
    except FileNotFoundError:
        dados_atuais = "{}"

    # Prompt otimizado para evitar estouro de cota (429), mantendo toda a riqueza de detalhes
    prompt = f"""
    Você é um editor sênior de concursos públicos da área fiscal (Receita Federal, SEFAZ e ISS).
    Data de referência: {data_hoje}.
    
    Aqui está a base completa atual do painel em JSON:
    {dados_atuais}
    
    Sua tarefa é atuar sobre esta base mantendo TODOS os concursos cadastrados, sem omitir nenhum órgão, estado ou município. 
    Atualize a data de referência para "{data_hoje}" e certifique-se de que a estrutura JSON permaneça absolutamente completa, contendo todas as esferas, etapas de 1 a 7, indicadores e novidades.
    
    Retorne APENAS o objeto JSON válido, sem blocos de código markdown (sem ```json e sem ```).
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Chamada limpa e direta sem ferramentas de busca web simultâneas pesadas
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    texto_resposta = response.text.strip()
    
    # Limpeza de formatação markdown
    if texto_resposta.startswith("```json"):
        texto_resposta = texto_resposta[7:]
    if texto_resposta.startswith("```"):
        texto_resposta = texto_resposta[3:]
    if texto_resposta.endswith("```"):
        texto_resposta = texto_resposta[:-3]
        
    try:
        json_obj = json.loads(texto_resposta.strip())
        json_obj["atualizacao"] = data_hoje
        
        with open("dados.json", "w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=2)
            
        print("Painel atualizado com sucesso mantendo toda a base de dados!")
    except json.JSONDecodeError as e:
        print(f"Erro ao processar JSON: {e}")
        print("Resposta recebida:", texto_resposta)
        raise e

if __name__ == "__main__":
    buscar_e_atualizar()
