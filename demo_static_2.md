## Contexto

Problema:
Ideia:
Escopo:
Talvez explicar um pouco porque precisa dessa peça e como que essa gestao de e-mails acontece hoje
E comentar que isso é um reuso da peça de RT Cross 
E talvez explicar qual que era a ideal total: categorizar e-mails + tipificacao + DI4

## Objetivo 
Responsável por fazer a **triagem de emails** na caixa de implantação de seguros saúde e **categorizá-los** conforme regras de negócio pré-definidas, facilitando o encaminhamento para as equipes responsáveis e otimizando o tempo de resposta.

* **Etapa 1 – Identificar Empresa:** Chamar agente para **extrair CNPJ** da empresa no título do e-mail 
* **Etapa 2 – Classificar Demanda:** Chamar agente para **classificar e-mail** com base no contexto do e-mail e regras de negócio

## Etapa 1 – Identificar Empresa 
**Objetivo**:
  Extrair e validar CNPJ a partir do `título` do **e-mail**

**Entrada**:

* `e-mail` (JSON): As informações do e-mail recebido, incluindo o título e o corpo do e-mail em formato JSON.   

**Saída**:
* `cnpj` (str): O CNPJ extraído e validado a partir do título do e-mail.
* `flag_cnpj` (bool): Indica se o CNPJ extraído é válido ou não.


### Exemplos de Entrada 

```json
{
  "titulo": "Implantação - Proposta 12345 - CNPJ: 12.345.678/0001-90",
  "corpo": "Prezado, segue a proposta para implantação do seguro saúde..."
}
```

### Tarefas
* Analisar o título do e-mail para localizar o CNPJ.
* Detectar padrão de CNPJ (14 dígitos, com ou sem formatação).
* Validar o CNPJ com calculo oficial dos digitos verificadores.
* Retornar o CNPJ extraído e a flag de validação.

###  Exemplos de Saída

```json
{
  "cnpj": "12.345.678/0001-90",
  "flag_cnpj": true
}
```
