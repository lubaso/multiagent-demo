#!/usr/bin/env python
# coding: utf-8

# In[11]:


# IMPORT PACKAGES
import json
import unicodedata
import yaml
import aisuite as ai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


# In[2]:


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


# In[3]:


def normalize_bool(value):
    """Converte representações comuns (Sim/Não, True/False, 0/1 etc.) em bool.

    Qualquer coisa que não seja claramente "true" é tratada como False.
    """
    true_values = {
        True, 1, "1", "true", "True", "sim", "Sim", "SIM",
        "yes", "Yes", "YES", "y", "Y", "s", "S"
    }
    false_values = {
        False, 0, "0", "false", "False",
        "não", "Nao", "NAO", "nao", "Não",
        "no", "No", "NO", "",
        None, "nan", "NaN", "null", "None"
    }

    if value in true_values:
        return True
    if value in false_values:
        return False

    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"sim", "s", "yes", "y", "1", "true"}:
            return True
        if v in {"não", "nao", "n", "no", "0", "false", "nan", "null", "none", ""}:
            return False

    return False


# In[4]:


def get_porte(qtd_vidas):
    """Converte QTD_VIDAS no rótulo de porte esperado no YAML."""
    try:
        qtd = int(qtd_vidas)
    except Exception:
        # fallback conservador
        return "ATE_29_VIDAS"

    if qtd <= 29:
        return "ATE_29_VIDAS"
    return "ACIMA_DE_29_VIDAS"


# In[5]:


# -------------------------------------------------------------------
# Seguradora lookup (Sulamérica / SULAMERICA / sulamerica etc.)
# -------------------------------------------------------------------
def _normalize_seg_name(name: str) -> str:
    if not isinstance(name, str):
        name = "" if name is None else str(name)

    # espaços, caixa baixa e underscore
    name = name.strip().lower().replace(" ", "_")

    # remover acentos
    name = unicodedata.normalize("NFD", name)
    name = "".join(ch for ch in name if unicodedata.category(ch) != "Mn")

    return name


def find_seg_key(kb: dict, seg_name: str):
    """Encontra a chave da seguradora no YAML, ignorando acentos, caixa e espaços.

    Ex.: "Sulamérica" (payload) -> "SULAMERICA" (YAML).
    """
    seg_root = kb.get("SEGURADORA", {})
    target = _normalize_seg_name(seg_name)

    for key in seg_root.keys():
        if _normalize_seg_name(key) == target:
            return key

    return None


# -------------------------------------------------------------------
# Document formatting helpers
# -------------------------------------------------------------------
def format_items(items):
    """Garante ';' no fim de cada item e remove duplicados mantendo a ordem."""
    seen = set()
    result = []
    for raw in items or []:
        text = (raw or "").rstrip(";") + ";"
        if text not in seen:
            seen.add(text)
            result.append(text)
    return result


# -------------------------------------------------------------------
# Core rule engine
# -------------------------------------------------------------------
def get_documents(payload_item: dict, kb: dict):
    """Gera a lista de documentos para um item de proposta."""
    seg_name = payload_item.get("SEGURADORA", "") or ""
    qtd_vidas = payload_item.get("QTD_VIDAS", "") or ""

    porte = get_porte(qtd_vidas)
    seg_key = find_seg_key(kb, seg_name)

    if not seg_key:
        # seguradora não encontrada no YAML
        return {"LISTA_DOCUMENTOS": []}

    seg_block = kb["SEGURADORA"][seg_key]
    porte_block = seg_block["PORTE"].get(porte)
    if porte_block is None:
        # porte não mapeado para essa seguradora
        return {"LISTA_DOCUMENTOS": []}

    empresa_group = porte_block["DOCUMENTOS_DA_EMPRESA"]
    benef_group = porte_block["DOCUMENTOS_DOS_BENEFICIARIOS"]

    # --------------------
    # EMPRESA
    # --------------------
    # sempre incluir GERAL
    empresa_docs = format_items(empresa_group.get("GERAL", []))
    empresa_cond_docs = []

    # condicionais de empresa mapeadas no YAML
    for cond_key in ["POSSUI_COLIGADAS_NO_PLANO", "SOCIOS"]:
        if normalize_bool(payload_item.get(cond_key, False)):
            docs = format_items(empresa_group.get(cond_key, []))
            if docs:
                empresa_cond_docs.extend(docs)

    # --------------------
    # BENEFICIÁRIOS
    # --------------------
    # sempre incluir GERAL
    benef_docs = format_items(benef_group.get("GERAL", []))
    benef_cond_docs = []

    # aqui o payload tem ESTAGIARIOS_JOVEM_APRENDIZ, igual ao YAML
    for cond_key in ["FUNCIONARIOS", "AFASTADOS", "ESTAGIARIOS_JOVEM_APRENDIZ"]:
        if normalize_bool(payload_item.get(cond_key, False)):
            docs = format_items(benef_group.get(cond_key, []))
            if docs:
                benef_cond_docs.extend(docs)

    # --------------------
    # Monta lista final (única) de documentos
    # --------------------
    all_docs = []
    all_docs.extend(empresa_docs)
    all_docs.extend(benef_docs)
    all_docs.extend(empresa_cond_docs)
    all_docs.extend(benef_cond_docs)

    # deduplicação final
    all_docs = format_items(all_docs)

    return {
        "LISTA_DOCUMENTOS": all_docs
    }




# In[6]:


# ajuste o nome do JSON se estiver usando outro arquivo
payload_path = "payload.json"
yaml_path = "doc_list.yaml"

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

with open(yaml_path, "r", encoding="utf-8") as f:
    list_docs = yaml.safe_load(f)


# In[7]:


resultados = []

for item in payload:
    doc_info = get_documents(item, list_docs)
    merged = { **item, **doc_info }
    resultados.append(merged)

print(json.dumps(resultados, ensure_ascii=False, indent=2))


# In[8]:


resultados = []
for item in payload:
    doc_info = get_documents(item, list_docs)
    # Mantém o ID_PROPOSTA junto com a lista para facilitar debug
    saida = {
        "ID_PROPOSTA": item.get("ID_PROPOSTA"),
        **doc_info,
    }
    resultados.append(saida)

print(json.dumps(resultados, ensure_ascii=False, indent=2))


# In[9]:


# ===============================
# CONNECT TO LLM
# ===============================
CLIENT = ai.Client()


# In[18]:


def load_payload(path: str | Path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_doc_kb(path: str | Path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
def load_prompt_template(path: str | Path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# In[13]:


def build_user_prompt(payload_item: dict, doc_kb: dict) -> str:
    payload_json = json.dumps(payload_item, ensure_ascii=False, indent=2)
    # você pode reduzir o YAML só para a seguradora em questão se quiser otimizar
    doc_yaml_str = yaml.safe_dump(doc_kb, allow_unicode=True, sort_keys=False)

    prompt = (
        PROMPT_TEMPLATE
        .replace("<<<PAYLOAD_JSON>>>", payload_json)
        .replace("<<<DOC_LIST_YAML>>>", doc_yaml_str)
    )
    return prompt


# In[23]:


def call_llm(prompt: str) -> dict:
    response = CLIENT.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um assistente que SEMPRE responde com um JSON válido, "
                    "no mesmo schema do payload de entrada."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    # AQUI estava o problema: usar atributo, não índice
    output_text = response.choices[0].message.content

    # `output_text` deve ser uma string JSON
    return json.loads(output_text)


# In[21]:


#def call_llm(prompt: str) -> dict:
#    response = CLIENT.chat.completions.create(
#        model=MODEL_NAME,
#        messages=[
#            {"role": "system", "content": "Você é um assistente especializado em seguros empresariais."},
#            {"role": "user", "content": prompt}
#        ],
#        temperature=0,
#    )

#    output_text = response.choices[0].message["content"]

    # assume que o modelo retorna um JSON válido (usei temperature 0)
#    return json.loads(output_text)


# In[14]:


#def call_llm(prompt: str) -> dict:
#    """
#    Chama o modelo e retorna o JSON já parseado.
#    """
#    response = CLIENT.responses.create(
#        model=MODEL_NAME,
#        input=[
#            {
#                "role": "user",
#                "content": prompt,
#            }
#        ],
#        response_format={"type": "json_object"},
#    )

#    content = response.output[0].content[0].text
#    return json.loads(content)


# In[15]:


def process_payload(payload_path: str | Path,
                    yaml_path: str | Path,
                    output_path: str | Path):
    payload = load_payload(payload_path)
    doc_kb = load_doc_kb(yaml_path)

    # payload_sintetico.json, no seu caso, é uma lista de propostas
    processed_records = []

    for record in payload:
        prompt = build_user_prompt(record, doc_kb) # colocar prompt template como parametro
        updated_record = call_llm(prompt)
        processed_records.append(updated_record)

    output_path = Path(output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(processed_records, f, ensure_ascii=False, indent=2)


# In[16]:


MODEL_NAME = "openai:gpt-4.1"


# In[19]:


PROMPT_TEMPLATE = """
Você é um assistente especializado em seguros de saúde empresariais.
Sua tarefa é analisar um registro de proposta (payload) e um arquivo YAML
com a lista de documentos exigidos por seguradora, porte e tipo de beneficiário.

Regras importantes:
1. NÃO invente documentos. Use EXCLUSIVAMENTE a lista de documentos do YAML fornecido.
2. Você deve:
   a) Ler o campo FUNCIONARIOS do payload.
   b) Ler o campo COMENTARIO_CONSULTOR do payload.
   c) Avaliar se o comentário contradiz FUNCIONARIOS.
3. Definição de contradição:
   - Consideramos que HÁ CONTRADIÇÃO se, e somente se:
     (i) FUNCIONARIOS é falso (False, "False", "Não", "Nao", "nan", "", "0", etc.)
     E
     (ii) O COMENTARIO_CONSULTOR afirma ou indica que existem funcionários ativos
          ou que funcionários entrarão no plano (ex.: "há funcionários", "funcionários ativos",
          "funcionários entrando no plano", "colaboradores da empresa serão incluídos" etc.).
   - Caso o comentário não mencione funcionários ou seja neutro/irrelevante, NÃO há contradição.
4. Se NÃO houver contradição:
   - Retorne o payload ORIGINAL, sem alterar o campo LISTA_DOCUMENTOS.
5. Se HOUVER contradição:
   a) Use SEGURADORA e QTD_VIDAS do payload para determinar o porte e localizar
      no YAML quais documentos de FUNCIONARIOS devem ser incluídos.
      - QTD_VIDAS até 29 → categoria "ATE_29_VIDAS"
      - QTD_VIDAS acima de 29 → categoria "ACIMA_DE_29_VIDAS"
   b) Dentro da seguradora correta e do porte correto, use a seção:
      SEGURADORA -> [nome da seguradora normalizado] -> PORTE -> [porte]
        -> DOCUMENTOS_DOS_BENEFICIARIOS -> FUNCIONARIOS
   c) Pegue essa lista de documentos de FUNCIONARIOS do YAML.
   d) Adicione TODOS esses documentos ao campo LISTA_DOCUMENTOS do payload,
      SEM remover documentos já existentes e evitando entradas duplicadas.
6. Retorne SEMPRE um JSON VÁLIDO que siga EXATAMENTE o mesmo schema do payload de entrada
   (mesmos campos, mesmos nomes de chaves), apenas com o campo LISTA_DOCUMENTOS atualizado
   quando houver contradição.

Formato JSON de saída:
- Um único objeto JSON representando o registro de proposta processado.

---

A seguir está o payload de entrada (um único registro, em JSON):

<<<PAYLOAD_JSON>>>

Este é o conteúdo relevante do arquivo YAML com a lista de documentos:

<<<DOC_LIST_YAML>>>

Tarefas:
1. Verifique se o campo COMENTARIO_CONSULTOR contradiz o campo FUNCIONARIOS,
   conforme as regras acima.
2. Se houver contradição, busque no YAML os documentos de FUNCIONARIOS
   para a SEGURADORA e QTD_VIDAS informadas, e atualize LISTA_DOCUMENTOS.
3. Retorne APENAS o JSON final do registro, sem texto adicional.
"""


# In[24]:


process_payload(
    payload_path="payload_sintetico.json",
    yaml_path="doc_list.yaml",
    output_path="payload_sintetico_processado.json",
)


# In[26]:


# LER PAYLOAD COM COMENTÁRIOS SINTÉTICOS
payload_path = "payload_sintetico_processado.json"

with open(payload_path, "r", encoding="utf-8") as f:
    payload_data = json.load(f)


# In[27]:


payload_data

# TODO
# 1.Testar com payload sintético com outras propostas
# 2.Adicionar outros comentários fakes, ajustar prompt e avaliar 
# 3.Simplificar código --> visão Andrew NG
# 4.Converter para LangChain/LangGraph
# 5.Testar LLM + LLM
# 6.Testar LLM + TOOL

