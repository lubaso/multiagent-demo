TEST_CASES = [
    # 1) CNPJ válido + envio claro de docs (cliente, pdf)
    {
        "name": "valid_cnpj_documento_valido_pdf_cliente",
        "email": {
            "filename": "email1.eml",
            "subject": "Envio de documentos CNPJ 12.345.678/0001-95 conforme solicitado",
            "text_body": "Bom dia, segue em anexo a documentação solicitada para o cadastro.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "contrato_social.pdf"},
                {"name": "cartao_cnpj.pdf"}
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            "doc_intent_likelihood": "HIGH"
        },
        "expected_final": {
            "cnpj": "12.345.678/0001-95",    # assumindo que é um CNPJ válido
            "tag": "DOCUMENTO_VALIDO"
        }
    },

    # 2) CNPJ válido, mas sem evidência de envio de documento
    {
        "name": "valid_cnpj_sem_documento",
        "email": {
            "filename": "email2.eml",
            "subject": "Atualização cadastral CNPJ 12.345.678/0001-95",
            "text_body": "Olá, apenas confirmando o telefone para contato.",
            "sender": "cliente@gmail.com",
            "attachments": []
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            "doc_intent_likelihood": "LOW"
        },
        "expected_final": {
            "cnpj": "12.345.678/0001-95",
            "tag": "CPNJ_VALIDO"
        }
    },

    # 3) Sem CNPJ, só número de proposta
    {
        "name": "sem_cnpj_com_numero_proposta",
        "email": {
            "filename": "email3.eml",
            "subject": "Proposta 123456 - envio de documentos",
            "text_body": "Boa tarde, seguem os documentos da proposta 123456.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "rg_cliente.pdf"}
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": False
        },
        "expected_final": {
            "cnpj": "sem identificação",
            "tag": "NO_CNPJ"
        }
    },

    # 4) CNPJ válido, mas só imagem de assinatura (image123.png)
    {
        "name": "valid_cnpj_apenas_assinatura_imagem",
        "email": {
            "filename": "email4.eml",
            "subject": "Retorno sobre CNPJ 12.345.678/0001-95",
            "text_body": "Atenciosamente, João.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "image123.png"}  # assinatura
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            # classificador pode marcar MEDIUM ou LOW (depende do quão sensível vc quer)
            # aqui vamos assumir LOW, porque não há texto de envio de docs
            "doc_intent_likelihood": "LOW"
        },
        "expected_final": {
            "cnpj": "12.345.678/0001-95",
            # VALIDADOR deve entender que é só assinatura -> NÃO é documento pendente
            "tag": "CPNJ_VALIDO"
        }
    },

    # 5) CNPJ válido, texto fala de documentos, mas remetente é domínio corporativo
    {
        "name": "valid_cnpj_docs_mas_dominio_corporativo",
        "email": {
            "filename": "email5.eml",
            "subject": "Documentação CNPJ 12.345.678/0001-95",
            "text_body": "Segue documentação para conferência interna.",
            "sender": "analista@nome-da-empresa.com.br",
            "attachments": [
                {"name": "documentos_internos.pdf"}
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            "doc_intent_likelihood": "HIGH"
        },
        "expected_final": {
            "cnpj": "12.345.678/0001-95",
            # Regra de negócio: domínio corporativo → em regra NÃO é cliente enviando pendência
            "tag": "CPNJ_VALIDO"
        }
    },

    # 6) CNPJ candidato inválido (14 dígitos mas DV errado)
    {
        "name": "cnpj_invalido_no_subject",
        "email": {
            "filename": "email6.eml",
            "subject": "Envio dados CNPJ 11.111.111/1111-11",
            "text_body": "Segue em anexo.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "documento_qualquer.pdf"}
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True
        },
        "expected_final": {
            "cnpj": "sem identificação",  # validador reprova pelo DV
            "tag": "NO_CNPJ"
        }
    },

    # 7) Dois CNPJs no subject
    {
        "name": "dois_cnpjs_no_subject",
        "email": {
            "filename": "email7.eml",
            "subject": "Documentos CNPJ 12.345.678/0001-95 e 98.765.432/0001-10",
            "text_body": "Segue documentação referente ao CNPJ principal conforme solicitado.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "documentacao_principal.pdf"}
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            "doc_intent_likelihood": "HIGH"
        },
        "expected_final": {
            # Você pode decidir sua regra de negócio (primeiro CNPJ, ou outro critério)
            "cnpj": "12.345.678/0001-95",
            "tag": "DOCUMENTO_VALIDO"
        }
    },

    # 8) CNPJ válido, cliente envia doc mesmo com assinatura.png junto
    {
        "name": "valid_cnpj_docs_mais_assinatura",
        "email": {
            "filename": "email8.eml",
            "subject": "Envio dos documentos CNPJ 12.345.678/0001-95",
            "text_body": "Conforme solicitado, seguem em anexo os documentos da empresa.",
            "sender": "cliente@gmail.com",
            "attachments": [
                {"name": "cartao_cnpj.pdf"},
                {"name": "image001.png"}  # assinatura
            ]
        },
        "expected_classifier": {
            "has_cnpj_candidate": True,
            "doc_intent_likelihood": "HIGH"
        },
        "expected_final": {
            # VALIDADOR ignora assinatura, mas vê o PDF + contexto → DOCUMENTO_VALIDO
            "cnpj": "12.345.678/0001-95",
            "tag": "DOCUMENTO_VALIDO"
        }
    }
]

def test_multiagent_flow():
    for case in TEST_CASES:
        result = process_email_multiagent(case["email"])
        print(case["name"], result)
        # aqui você pode fazer asserts do tipo:
        # assert result["tag"] == case["expected_final"]["tag"]

from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END

class EmailState(TypedDict, total=False):
    email: Dict[str, Any]
    classifier_output: Dict[str, Any]
    final_output: Dict[str, Any]

def classifier_node(state: EmailState) -> EmailState:
    email = state["email"]
    classifier_output = run_classifier(email)  # função que usa CLASSIFIER_SCHEMA
    return {
        **state,
        "classifier_output": classifier_output
    }

def validator_node(state: EmailState) -> EmailState:
    email = state["email"]
    classifier_output = state["classifier_output"]
    validator_output = run_validator(email, classifier_output)  # usa VALIDATOR_SCHEMA
    return {
        **state,
        "final_output": validator_output
    }

def should_go_to_validator(state: EmailState) -> str:
    """
    Decide o próximo passo após o classifier.

    Retornos:
    - "validator": se existe candidato a CNPJ.
    - "__end__": se não há candidato a CNPJ (encerra o fluxo).
    """
    cls = state.get("classifier_output", {})
    has_cnpj_candidate = cls.get("has_cnpj_candidate", False)

    if has_cnpj_candidate:
        return "validator"
    else:
        # Neste caso já podemos setar final_output aqui,
        # para o consumidor não precisar tratar None.
        state["final_output"] = {
            "cnpj": "sem identificação",
            "tag": "NO_CNPJ",
            "reasoning": "Classificador não identificou candidato a CNPJ no subject."
        }
        return "__end__"

def build_email_graph() -> StateGraph:
    builder = StateGraph(EmailState)

    # Adiciona nós
    builder.add_node("classifier", classifier_node)
    builder.add_node("validator", validator_node)

    # Ponto de entrada
    builder.set_entry_point("classifier")

    # A partir do classifier, decidir condicionalmente
    builder.add_conditional_edges(
        "classifier",
        should_go_to_validator,
        {
            "validator": "validator",
            "__end__": END
        }
    )

    # Se for para o validator, depois termina
    builder.add_edge("validator", END)

    graph = builder.compile()
    return graph

email_graph = build_email_graph()

def process_email_with_langgraph(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envia o e-mail para o grafo e retorna o final_output.
    """
    initial_state: EmailState = {"email": email}
    final_state = email_graph.invoke(initial_state)
    return final_state["final_output"]

for case in TEST_CASES:
    result = process_email_with_langgraph(case["email"])
    print(case["name"], "→", result)
