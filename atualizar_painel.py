import os
import datetime
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def buscar_e_atualizar():
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
    
    # Carrega os dados existentes para manter a estrutura e o histórico de referência
    try:
        with open("dados.json", "r", encoding="utf-8") as f:
            dados_atuais = f.read()
    except FileNotFoundError:
        dados_atuais = "{}"

    # Prompt refinado com rigor de checagem, priorização de fontes oficiais e busca ativa
    prompt = f"""
    Você é um pesquisador sênior e auditor especializado em concursos públicos da área fiscal brasileira (Receita Federal, SEFAZ estaduais e ISS municipais).
    Data de referência da pesquisa: {data_hoje}.
    
    Sua missão é realizar uma pesquisa ATUALIZADA na internet para esta nova edição. Não reutilize cegamente informações anteriores sem checar a situação atual.
    
    DIRETRIZES DE FONTE E HIERARQUIA DE VERIFICAÇÃO:
    1. Utilize obrigatoriamente Gran Cursos Online e Estratégia Concursos como fontes de mapeamento recorrente.
    2. Amplie e confirme as informações prioritariamente em fontes primárias:
       a) Diários Oficiais (União, Estados e Municípios);
       b) Páginas oficiais dos órgãos (RFB, Secretarias de Fazenda/Finanças);
       c) Páginas oficiais das bancas organizadoras (Cebraspe, FGV, FCC, Vunesp, etc.);
       d) Editais e retificações oficiais;
       e) Portais de transparência e legislação aplicável.
    
    CRITÉRIO DE RIGOR TÉCNICO:
    - Confirme informações em fontes primárias sempre que possível.
    - Uma notícia sobre banca escolhida NÃO comprova, por si só, contrato assinado.
    - Uma previsão de edital NÃO equivale a cronograma oficial.
    - Uma autorização NÃO significa que as inscrições estejam próximas.
    - Differentiate claramente autorização, comissão, banca definida, contrato assinado e edital publicado.
    - Cite a fonte específica (ex: "DOE-AL / Cebraspe") junto a cada cartão/informação correspondente.

    ESTRUTURA DE DADOS ATUAL PARA REFERÊNCIA:
    {dados_atuais}

    REGRAS ESTRITAS DO JSON DE SAÍDA:
    - Retorne EXCLUSIVAMENTE um objeto JSON válido.
    - NÃO inclua blocos de código markdown (sem ```json e sem ```) e nenhum texto explicativo fora do JSON.
    - Mantenha na íntegra a estrutura das chaves: "atualizacao", "indicadores", "novidades", "federal", "estadual", "municipal", "agenda" e "nota_rodape".
    - Nas esferas "federal", "estadual" e "municipal", organize os concursos obrigatoriamente dentro das etapas de "1" a "7".
    - Cada objeto de concurso deve conter: "titulo", "sub", "badge_class", "status_badge", "cargo", "vagas", "remuneracao", "banca", "perspectiva", "movimentacao", e "fonte".
    """
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Habilita a busca na web via Google Search grounding para garantir dados em tempo real
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}]
        )
    )
    
    texto_resposta = response.text.strip()
    
    # Limpeza de marcações markdown
    if texto_resposta.startswith("```json"):
        texto_resposta = texto_resposta[7:]
    if texto_resposta.startswith("```"):
        texto_resposta = texto_resposta[3:]
    if texto_resposta.endswith("```"):
        texto_resposta = texto_resposta[:-3]
        
    # Validação e gravação do JSON
    try:
        json_obj = json.loads(texto_resposta.strip())
        
        # Garante que a data de atualização seja gravada corretamente
        json_obj["atualizacao"] = data_hoje
        
        with open("dados.json", "w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=2)
            
        print(f"Pesquisa atualizada e verificada em {data_hoje} concluída com sucesso!")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON gerado pela IA: {e}")
        print("Resposta recebida:", texto_resposta)
        raise e

if __name__ == "__main__":
    buscar_e_atualizar()
