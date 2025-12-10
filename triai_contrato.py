from openai import OpenAI
import json

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(email_payload)}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": EMAIL_CNPJ_SCHEMA
    },
    temperature=0
)

result = response.output_parsed
