# CHECKLIST TOOL -- V2


import json
import unicodedata

import yaml


# In[ ]:


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


# In[2]:


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


# In[3]:


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


# In[4]:


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




# In[ ]:


# ajuste o nome do JSON se estiver usando outro arquivo
payload_path = "payload.json"
yaml_path = "doc_list.yaml"

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

with open(yaml_path, "r", encoding="utf-8") as f:
    list_docs = yaml.safe_load(f)


# In[10]:


resultados = []

for item in payload:
    doc_info = get_documents(item, list_docs)
    merged = { **item, **doc_info }
    resultados.append(merged)

print(json.dumps(resultados, ensure_ascii=False, indent=2))


# In[9]:


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






