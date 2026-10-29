import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import errors

def buscar_e_atualizar():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erro: GEMINI_API_KEY não configurada.")
        return

    client = genai.Client(api_key=api_key)
    
    # Carrega o dados.json existente
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            dados_atuais = json.load(f)
    except Exception as e:
        print(f"Aviso ao ler dados.json: {e}")
        dados_atuais = {}

    data_hoje = datetime.now().strftime("%d de %B de %Y")

    prompt = f"""
    Você é um assistente responsável por atualizar a data e validar a integridade do banco de dados de um painel de concursos fiscais.
    
    Data de Hoje: {data_hoje}
    Conteúdo Atual do dados.json:
    {json.dumps(dados_atuais, ensure_ascii=False)}

    INSTRUÇÕES:
    1. Atualize o campo "atualizacao" com a data de hoje ({data_hoje}).
    2. Preserve integralmente todos os concursos, esferas, abas, etapas (1 a 7), indicadores, novidades e agenda contidos no JSON.
    3. Retorne EXCLUSIVAMENTE o objeto JSON válido atualizado, sem formatação markdown extra, sem blocos de código ```json.
    """

    # Modelo atualizado recomendado pela API do Google
    modelos = ["gemini-3.8-flash"]
    response_text = None
    
    for modelo in modelos:
        print(f"Tentando comunicação com o modelo: {modelo}...")
        for tentativa in range(1, 4):  # Tenta até 3 vezes
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt
                )
                response_text = response.text
                print(f"Sucesso com o modelo {modelo} na tentativa {tentativa}!")
                break
            except (errors.ServerError, errors.APIError) as e:
                print(f"Instabilidade no modelo {modelo} (Tentativa {tentativa}/3). Aguardando 10s... Erro: {e}")
                time.sleep(10)
            except Exception as e:
                print(f"Erro no modelo {modelo}: {e}")
                break
        
        if response_text:
            break

    # Se a API falhar completamente
    if not response_text:
        print("Aviso: API do Google indisponível no momento. Aplicando atualização de data via fallback local...")
        dados_atuais["atualizacao"] = data_hoje
        with open("dados.json", "w", encoding="utf-8") as f:
            json.dump(dados_atuais, f, ensure_ascii=False, indent=2)
        print("Data atualizada localmente com sucesso! O workflow será concluído sem erros.")
        return

    # Limpeza e salvamento do JSON retornado pela IA
    texto_limpo = response_text.strip()
    if texto_limpo.startswith("```json"):
        texto_limpo = texto_limpo[7:]
    if texto_limpo.startswith("```"):
        texto_limpo = texto_limpo[3:]
    if texto_limpo.endswith("```"):
        texto_limpo = texto_limpo[:-3]
    texto_limpo = texto_limpo.strip()

    try:
        json_validado = json.loads(texto_limpo)
        with open("dados.json", "w", encoding="utf-8") as f:
            json.dump(json_validado, f, ensure_ascii=False, indent=2)
        print("dados.json atualizado e salvo com sucesso via API!")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da API: {e}. Mantendo arquivo local atualizado.")

if __name__ == "__main__":
    buscar_e_atualizar()
