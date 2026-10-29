"""Atualiza dados.json do boletim de concursos fiscais usando Gemini com busca na web.

Fluxo: lê dados.json -> pede ao Gemini (com Google Search) a versão atualizada ->
valida o resultado -> só então grava. Se algo falhar, o dados.json antigo é mantido
e o job termina com erro (visível na aba Actions).
"""
import copy
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

ARQ = "dados.json"
MODELOS = [m.strip() for m in os.environ.get("GEMINI_MODELS", "gemini-3.8-flash").split(",") if m.strip()]
TENTATIVAS = 5
ESFERAS = {"Federal", "Estaduais", "Municipais"}
TIPOS = {"prazo", "prova", "previsao"}
RE_DATA = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
CAMPOS_TEXTO = ["sphere", "name", "status", "cargo", "vagas", "education", "salary",
                "bank", "dates", "next", "perspective", "source"]


def hoje():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d")
    except Exception:
        return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d")


def extrair_json(texto):
    """Aceita resposta com ```json, texto antes/depois; devolve o objeto JSON."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("resposta sem objeto JSON")
    return json.loads(t[i:j + 1])


def validar(novo, antigo):
    """Devolve lista de problemas; lista vazia = JSON aceito."""
    if not isinstance(novo, dict):
        return ["a raiz não é um objeto"]
    e = [f"falta a chave '{k}'" for k in ("meta", "news", "contests", "panorama") if k not in novo]
    if e:
        return e
    cs = novo["contests"]
    if not isinstance(cs, list) or not cs:
        return ["'contests' vazio ou inválido"]
    nomes = set()
    for i, c in enumerate(cs):
        if not isinstance(c, dict):
            e.append(f"contests[{i}] inválido")
            continue
        r = f"contests[{i}] ({c.get('name')})"
        for k in CAMPOS_TEXTO:
            if not isinstance(c.get(k), str) or not c[k].strip():
                e.append(f"{r}: campo '{k}' ausente ou vazio")
        if c.get("sphere") not in ESFERAS:
            e.append(f"{r}: sphere inválida")
        st = c.get("stage")
        if not isinstance(st, int) or isinstance(st, bool) or not 0 <= st <= 6:
            e.append(f"{r}: stage deve ser inteiro de 0 a 6")
        if c.get("name") in nomes:
            e.append(f"{r}: nome duplicado")
        nomes.add(c.get("name"))
        if c.get("url") and not re.match(r"^https?://", str(c["url"])):
            e.append(f"{r}: url inválida")
        for ev in c.get("events", []):
            if not (isinstance(ev, dict) and RE_DATA.match(str(ev.get("date", ""))) and ev.get("tipo") in TIPOS and ev.get("label")):
                e.append(f"{r}: evento inválido {ev}")
    if not isinstance(novo["news"], list):
        e.append("'news' deve ser lista")
    else:
        for n in novo["news"]:
            if not (isinstance(n, dict) and RE_DATA.match(str(n.get("date", ""))) and n.get("title") and n.get("text")):
                e.append(f"novidade inválida: {str(n)[:80]}")
    p = novo["panorama"]
    for k in ("Federal", "Estaduais", "Municipais"):
        if not isinstance(p, dict) or not str(p.get(k, "")).strip():
            e.append(f"panorama.{k} ausente")
    ant = len(antigo.get("contests", []))
    if ant and len(cs) < ant * 0.8:
        e.append(f"perda suspeita de concursos: {ant} -> {len(cs)}")
    return e


def resumo_mudancas(antigo, novo):
    a = {c["name"]: c for c in antigo.get("contests", [])}
    n = {c["name"]: c for c in novo.get("contests", [])}
    add, rem = sorted(set(n) - set(a)), sorted(set(a) - set(n))
    alt = sorted(k for k in set(a) & set(n) if a[k] != n[k])
    return add, rem, alt


def montar_prompt(dados, data):
    return f"""Você atualiza o banco de dados de um boletim semanal de concursos da área fiscal do Brasil
(auditor fiscal, fiscal de tributos, auditor tributário; esferas federal, estadual e municipal).
Data de hoje: {data}. Última atualização dos dados: {dados.get('meta', {}).get('atualizadoEm')}.

TAREFA
1. Use a busca na web para verificar o que mudou desde a última atualização. Priorize fontes oficiais
   (editais, diários oficiais, sites das prefeituras/secretarias e das bancas); depois portais especializados.
2. Atualize apenas o que tiver confirmação: etapa (stage), status, vagas, banca, datas, próximo passo,
   eventos da agenda e novas novidades. Novos concursos fiscais podem ser adicionados.
3. Remova um concurso somente se foi homologado ou encerrado de vez, e registre isso em news.
4. NÃO invente. Sem confirmação, mantenha o texto atual. Divulgação de imprensa ou previsão não é ato oficial:
   use palavras como "divulgado" ou "previsto" nesses casos. Se as fontes divergirem, escreva "Fontes divergem".
5. Toda data de prova ou prazo citada em "dates" deve existir em "events" do concurso
   (date AAAA-MM-DD, ou AAAA-MM se só o mês for conhecido; tipo: prazo | prova | previsao; label; obs opcional).
6. "news": no máximo 6 itens da última semana (date AAAA-MM-DD, title, tag, warn true/false, text, source, url opcional).
7. "panorama": mantenha o texto, e só reescreva uma esfera se algo mudou; 1 a 2 frases, sem números nem listas.
8. Não altere "meta"; o script cuida das datas.

FORMATO (mesmos nomes de campos, nada além disso)
sphere: "Federal" | "Estaduais" | "Municipais"
stage: 0 edital aberto/publicado, 1 inscrições encerradas, 2 banca definida, 3 banca em contratação,
       4 autorizado, 5 comissão/planejamento, 6 previsão/expectativa

Responda SOMENTE com o JSON completo atualizado, sem markdown e sem comentários.

JSON ATUAL:
{json.dumps(dados, ensure_ascii=False)}
"""


def chamar_gemini(prompt, api_key):
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=api_key)
    cfg = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
    )
    for modelo in MODELOS:
        print(f"Modelo: {modelo}")
        for t in range(1, TENTATIVAS + 1):
            try:
                resp = client.models.generate_content(model=modelo, contents=prompt, config=cfg)
                if resp.text:
                    print(f"Resposta recebida (tentativa {t}).")
                    return resp.text
                print("Resposta vazia.")
            except errors.APIError as ex:
                print(f"Tentativa {t}/{TENTATIVAS} falhou: {ex}")
            if t < TENTATIVAS:
                time.sleep(t * 15)
    return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Erro: GEMINI_API_KEY não configurada.")
    with open(ARQ, encoding="utf-8") as f:
        atual = json.load(f)

    data = hoje()
    texto = chamar_gemini(montar_prompt(atual, data), api_key)
    if not texto:
        sys.exit("Erro: a API não respondeu após todas as tentativas. dados.json mantido.")

    try:
        novo = extrair_json(texto)
    except (ValueError, json.JSONDecodeError) as ex:
        sys.exit(f"Erro: resposta não é JSON válido ({ex}). dados.json mantido.")

    problemas = validar(novo, atual)
    if problemas:
        print("Resposta REJEITADA pela validação:")
        for p in problemas[:30]:
            print(" -", p)
        sys.exit("dados.json mantido.")

    add, rem, alt = resumo_mudancas(atual, novo)
    print(f"Concursos adicionados: {add or '-'}")
    print(f"Concursos removidos: {rem or '-'}")
    print(f"Concursos alterados: {alt or '-'}")

    mudou = {k: v for k, v in novo.items() if k != "meta"} != {k: v for k, v in atual.items() if k != "meta"}
    meta = copy.deepcopy(atual.get("meta", {}))
    meta["atualizadoEm"] = data
    if mudou:
        meta["edicao"] = data
    novo["meta"] = meta

    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(novo, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("dados.json salvo." + (" Conteúdo atualizado." if mudou else " Sem mudanças de conteúdo."))


if __name__ == "__main__":
    main()
