#!/usr/bin/env python
# coding: utf-8

# In[2]:


# IMPORT PACKAGES
from pathlib import Path
import json
import yaml  # pip install pyyaml
import aisuite as ai

from dotenv import load_dotenv
load_dotenv()


# In[3]:


# ===============================
# CONNECT TO LLM
# ===============================


# In[4]:


CLIENT = ai.Client()

# Ajuste aqui o modelo que você quiser usar
MODEL_NAME = "openai:gpt-4.1"


# In[5]:


# ===============================
# DEFINE FUNCTIONS
# ===============================


# In[6]:


# ===============================
# LOAD DATA FUNCTIONS
# ===============================


# In[7]:


def load_prompt_template(path: str) -> str:
    """
    Lê o checklist_prompt.yaml e devolve o texto do SYSTEM_PROMPT.
    """
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data["SYSTEM_PROMPT"]


def load_doc_list(path: str) -> str:
    """
    Lê o doc_list.yaml como texto bruto.
    Ele será injetado na marca <<<DOC_LIST>>> do template.
    """
    return Path(path).read_text(encoding="utf-8")


def build_prompt(template: str, doc_list_yaml: str, registro: dict) -> str:
    """
    Renderiza o prompt para um REGISTRO DE PROPOSTA específico,
    substituindo <<<DOC_LIST>>> e <<<PAYLOAD>>>.
    """
    payload_str = json.dumps(registro, ensure_ascii=False, indent=2)
    prompt = template.replace("<<<DOC_LIST>>>", doc_list_yaml)
    prompt = prompt.replace("<<<PAYLOAD>>>", payload_str)
    return prompt


# In[8]:


# ===============================
# LLM FUNCTIONS
# ===============================


# In[9]:


def call_llm(prompt: str) -> dict:
    """
    Chama a LLM com o prompt já renderizado e devolve o JSON
    (ID_PROPOSTA + LISTA_DOCUMENTOS).
    """
    response = CLIENT.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Você é um modelo que SEMPRE responde com um único JSON válido, sem texto extra."
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Se quiser fazer log para debug:
    # print("LLM raw output:", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Para debug mais fácil em produção você pode logar e/ou salvar em arquivo
        raise ValueError(f"Falha ao fazer parse do JSON retornado pela LLM: {e}\n\nResposta:\n{content}")


def process_payload(
    payload_path: str,
    prompt_yaml_path: str,
    doc_list_path: str,
    output_path: str,
) -> None:
    """
    - Lê o payload (lista de propostas)
    - Para cada proposta, chama a LLM
    - Junta LISTA_DOCUMENTOS no registro original
    - Salva o output em JSON
    """
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    template = load_prompt_template(prompt_yaml_path)
    doc_list_yaml = load_doc_list(doc_list_path)

    saida = []
    for registro in payload:
        rendered_prompt = build_prompt(template, doc_list_yaml, registro)
        llm_output = call_llm(rendered_prompt)

        lista_docs = llm_output.get("LISTA_DOCUMENTOS", [])

        # Concatena o output da LLM com o registro original
        registro_atualizado = {
            **registro,
            "LISTA_DOCUMENTOS": lista_docs,
        }
        saida.append(registro_atualizado)

    Path(output_path).write_text(
        json.dumps(saida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Arquivo gerado em: {output_path}")


# In[11]:


process_payload(
    payload_path="payload.json",
    prompt_yaml_path="checklist_prompt_v2.yaml",
    doc_list_path="doc_list.yaml",
    output_path="payload_processado.json",
)

