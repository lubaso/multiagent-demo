def transform_email_payload(source: dict) -> dict:
    email = source.get("email", {})

    # Build the "input" string exactly as required
    input_str = (
        f"\"id\":\"{email.get('filename','')}\", "
        f"\"subject\":\"{email.get('subject','')}\", "
        f"\"text_body\":\"{email.get('text_body','')}\","
        f"\"to_recipients\":[\"Ludimila Helena <ludmila.castro@mailer.com.br>\"],"
        f"\"cc_recipients\":[\"Implantacao Saude <implantacao_saude@nome-da-empresa.com>\"],"
        f"\"bcc_recipients\":\"\", "
        f"\"sender\":\"{email.get('sender','')}\""
    )

    return {
        "agent": "SEGUROS",
        "input": input_str,
        "attachments": email.get("attachments", [])
    }


# -------------------------
# Example usage
# -------------------------

source_payload = {
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
    }
}

transformed_payload = transform_email_payload(source_payload)

print(transformed_payload)
