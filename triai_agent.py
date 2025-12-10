# IMPORT PACKAGES
import json
import yaml  # pip install pyyaml

from pathlib import Path
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ===============================
# CONNECT TO LLM
# ===============================

# Instantiate OpenAI's client
CLIENT = OpenAI()
# Ajuste aqui o modelo que você quiser usar
MODEL_NAME = "gpt-4.1"

# ===============================
# DEFINE FUNCTIONS
# ===============================

# ===============================
# DATA HELPERS
# ===============================
def load_prompt_template(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")

    data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError(
            f"YAML inválido ou vazio em '{path}'. "
            f"Resultado do safe_load: {data}"
        )

    if "SYSTEM_PROMPT" not in data:
        raise KeyError(
            f"Chave 'SYSTEM_PROMPT' não encontrada em '{path}'. "
            f"Chaves disponíveis: {list(data.keys())}"
        )

    return data["SYSTEM_PROMPT"]

# ===============================
# EXTRACT CNPJ
# ===============================

def extract_cnpj_from_email(email_json: Dict[str, Any],
                            prompt: str,
                            model: str = "gpt-4.1-mini") -> Dict[str, Any]:
    """
    Chama o modelo para extrair CNPJ do subject de um e-mail.

    Parâmetros
    ----------
    email_json : dict
        Exatamente no formato:
        {
          "filename": "...",
          "subject": "...",
          "text_body": "...",
          "attachments": [{"name": "..."}]
        }

    model : str
        Nome do modelo a ser usado.

    Retorno
    -------
    dict com as chaves:
        - "cnpj": str
        - "tag": str
        - "reasoning": str
    """
    # Converte o dicionário para string JSON para mandar como "user"
    email_str = json.dumps(email_json, ensure_ascii=False)

    response = CLIENT.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": email_str}
        ],
        temperature=0.0,  # comportamento mais determinístico
    )
    
    raw_text = response.choices[0].message.content.strip()

    # Tenta fazer parse do JSON de saída
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # fallback defensivo se vier algo inesperado
        result = {
            "cnpj": "sem identificação",
            "tag": "NO_CNPJ",
            "reasoning": "Falha ao interpretar o JSON retornado pelo modelo."
        }
        
    # Garantir que as chaves existam
    result.setdefault("cnpj", "sem identificação")
    result.setdefault("tag", "NO_CNPJ")
    result.setdefault("reasoning", "Resultado ajustado por fallback no código.")

    return result


email = {
    "filename": "email1.eml",
    "subject": "Proposta CNPJ 12.345.678/0001-95 - atualização cadastral",
    "text_body": "corpo do e-mail...",
    "attachments": [
        {"name": "anexo1.pdf"}
    ]
}

prompt = load_prompt_template('system_prompt.yaml')
output = extract_cnpj_from_email(email,prompt)
print(output)
# Exemplo esperado:
# {
#   'cnpj': '12.345.678/0001-95',
#   'tag': 'CPNJ_VALIDO',
#   'reasoning': 'CNPJ válido identificado no subject e validado pelos dígitos verificadores.'
# }


