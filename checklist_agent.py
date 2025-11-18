#!/usr/bin/env python
# coding: utf-8

# In[2]:


#TODO


# In[3]:


# IMPORT PACKAGES
from dotenv import load_dotenv
load_dotenv()

import aisuite as ai
import json
import yaml


# In[ ]:


# ===============================
# CONNECT TO LLM
# ===============================
CLIENT = ai.Client()


# In[10]:


# ===============================
# LOAD DATA
# ===============================
# JSON payload with proposals
json_path = "payload.json"
with open(json_path, 'r', encoding='utf-8') as f:
    payload = json.load(f)
# YAML with curated documents per operadora
doc_list_path = "lista_docs.yaml"
with open(doc_list_path, 'r', encoding='utf-8') as f:
    doc_list = yaml.safe_load(f)
# Load SYSTEM PROMPT
system_prompt_path = "system_prompt.yaml"
with open(system_prompt_path, 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT = yaml.safe_load(f)
if isinstance(SYSTEM_PROMPT, dict) and 'SYSTEM_PROMPT' in SYSTEM_PROMPT:
    SYSTEM_PROMPT = SYSTEM_PROMPT['SYSTEM_PROMPT']


# In[ ]:


openai:o4-mini


# In[8]:


# ===============================
# DEFINE FUNCTIONS
# ===============================

def build_user_message(payloads, checklist_yaml):
    return (
        "Payload JSON (lista de propostas):\n"
        + json.dumps(payloads, ensure_ascii=False, indent=2)
        + "\n\nDoc list YAML:\n"
        + yaml.dump(checklist_yaml, allow_unicode=True)
        + "\nTarefa: Para cada proposta do payload, produza a saída no formato exigido."
    )
def run_checklist_agent(payloads, checklist_yaml, model="openai:gpt-4o"):
    """
    Envia o payload e o YAML ao LLM com o system prompt e retorna o texto gerado.
    A seleção e formatação são feitas exclusivamente pelo LLM.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(payloads, checklist_yaml)},
    ]

    resp = CLIENT.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    return resp.choices[0].message.content


# In[ ]:


# TODO
# 1.Testar com KB mockado
# 2.Estruturar saída em formado json junto com o payload?
# 3.Otimizar funcao para rodar mais rapido
# 4.Reescrever codigo com langchain/langgraph


# In[11]:


# ===============================
# RUN AGENT
# ===============================

output = run_checklist_agent(payload, doc_list)
print(output)

