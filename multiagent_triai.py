CLASSIFIER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "EmailCNPJClassifier",
    "type": "object",
    "additionalProperties": False,
    "required": ["has_cnpj_candidate", "cnpj_candidate", "doc_intent_likelihood", "notes"],
    "properties": {
        "has_cnpj_candidate": {
            "type": "boolean",
            "description": "True se o subject aparentemente contém um CNPJ ou número com cara de CNPJ."
        },
        "cnpj_candidate": {
            "type": "string",
            "description": "Número de CNPJ em qualquer formato se houver candidato; caso contrário string vazia."
        },
        "doc_intent_likelihood": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"],
            "description": "Quão provável é que o e-mail seja envio de documentos solicitados previamente."
        },
        "notes": {
            "type": "string",
            "description": "Frase curta explicando o raciocínio do classificador."
        }
    }
}


CLASSIFIER_SYSTEM_PROMPT = """
Você é um CLASSIFICADOR rápido e econômico para e-mails.

Sua tarefa é APENAS:
1) Verificar se o campo `subject` parece conter um CNPJ ou número com cara de CNPJ.
2) Estimar se o e-mail, em termos gerais, parece tratar de envio de documentos solicitados previamente.

Você NÃO precisa validar dígitos do CNPJ. Isso é trabalho do VALIDADOR.
Você deve ser sensível, mas pode errar para mais (falso positivo) aqui, pois haverá segunda checagem.

Entrada: um JSON com campos:
- subject (string)
- text_body (string)
- sender (string)
- attachments: lista de objetos com pelo menos `name`.

Preencha:
- has_cnpj_candidate = true se houver qualquer número no subject com formato de CNPJ (com ou sem máscara).
- cnpj_candidate = o número encontrado (como está no subject) ou string vazia se não houver.
- doc_intent_likelihood:
    - HIGH se texto e anexos sugerem fortemente envio de documentos ("segue em anexo", "conforme solicitado", PDFs etc.).
    - MEDIUM se há alguma indicação vaga de documentos ou anexos possivelmente relevantes.
    - LOW se não há sinal claro de envio de documentos.
- notes = uma frase curta explicando o porquê.

Sua resposta FINAL deve obedecer exatamente ao JSON Schema fornecido.
"""


VALIDATOR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "EmailCNPJDocumentAnalysis",
    "type": "object",
    "additionalProperties": False,
    "required": ["cnpj", "tag", "reasoning"],
    "properties": {
        "cnpj": {
            "type": "string",
            "description": "CNPJ válido extraído do subject ou 'sem identificação'."
        },
        "tag": {
            "type": "string",
            "enum": ["NO_CNPJ", "CPNJ_VALIDO", "DOCUMENTO_VALIDO"],
            "description": "Resultado final da análise."
        },
        "reasoning": {
            "type": "string",
            "minLength": 5,
            "maxLength": 300,
            "description": "Frase curta explicando a decisão."
        }
    }
}


VALIDATOR_SYSTEM_PROMPT = """
Você é um VALIDADOR rigoroso de CNPJ e de envio de documentos.

Você recebe:
1) Um JSON com os dados do e-mail (subject, text_body, sender, attachments).
2) Opcionalmente, um JSON com o resultado do CLASSIFICADOR (has_cnpj_candidate, cnpj_candidate, doc_intent_likelihood, notes).

Sua função:
- Validar se há um CNPJ realmente válido no subject (14 dígitos + dígitos verificadores).
- Verificar se o e-mail indica envio de documentos solicitados previamente pelo cliente, usando:
  - text_body
  - attachments
  - sender
- Aplicar as regras:
  - Se NÃO houver CNPJ válido -> cnpj = "sem identificação", tag = "NO_CNPJ".
  - Se houver CNPJ válido e NÃO ficar claro que é envio de documento solicitado -> tag = "CPNJ_VALIDO".
  - Se houver CNPJ válido E ficar claro (corpo + anexos + sender) que está enviando documento solicitado -> tag = "DOCUMENTO_VALIDO".

Regras:
- Ignorar anexos que são provavelmente assinatura (image123.png, logo.png etc.).
- Domínio corporativo (@nome-da-empresa) normalmente NÃO é cliente enviando documento pendente.
- Seja conservador: em caso de dúvida, NÃO marque DOCUMENTO_VALIDO.

Sua resposta FINAL deve obedecer exatamente ao JSON Schema fornecido.
"""


from openai import OpenAI
import json

client = OpenAI()

def run_classifier(email: dict) -> dict:
    resp = client.responses.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(email, ensure_ascii=False)}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": CLASSIFIER_SCHEMA
        },
        temperature=0
    )
    return resp.output_parsed  # já vem dict

def run_validator(email: dict, classifier_output: dict) -> dict:
    combined_input = {
        "email": email,
        "classifier_hint": classifier_output
    }
    resp = client.responses.create(
        model="gpt-4.1-mini",  # ou um modelo mais forte, se quiser
        messages=[
            {"role": "system", "content": VALIDATOR_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(combined_input, ensure_ascii=False)}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": VALIDATOR_SCHEMA
        },
        temperature=0
    )
    return resp.output_parsed

def process_email_multiagent(email: dict) -> dict:
    """
    Fluxo:
    1) Classificador rápido.
    2) Se não há CNPJ candidato -> já devolve NO_CNPJ.
       Se há candidato -> chama validador rigoroso.
    """
    cls = run_classifier(email)

    if not cls.get("has_cnpj_candidate", False):
        # atalho
        return {
            "cnpj": "sem identificação",
            "tag": "NO_CNPJ",
            "reasoning": "Classificador não identificou nenhum CNPJ candidato no subject."
        }

    # Há candidato: chama validador rigoroso
    validated = run_validator(email, cls)
    return validated

